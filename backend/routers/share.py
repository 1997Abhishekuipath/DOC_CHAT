"""Secure share links with strict document-scope isolation."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from core.audit import log_analytics, log_event
from core.db import documents, share_links
from core.deps import ROLE_EDITOR, get_current_user, require_role
from core.security import (
    create_guest_token,
    generate_share_token,
    hash_share_password,
    verify_share_password,
)

router = APIRouter(prefix="/v2/share-links", tags=["share-links"])


class CreateShareLinkBody(BaseModel):
    document_ids: List[str] = Field(min_length=1)
    mode: Literal["public", "password", "expiring"] = "public"
    password: Optional[str] = None
    expires_in_hours: Optional[int] = None
    single_use: bool = False
    domain_restriction: Optional[str] = None  # e.g. "@company.com"
    title: Optional[str] = None


class ShareLinkOut(BaseModel):
    token: str
    mode: str
    document_ids: List[str]
    title: Optional[str]
    single_use: bool
    opens: int
    revoked: bool
    expires_at: Optional[str]
    created_at: str
    domain_restriction: Optional[str]


class VerifyBody(BaseModel):
    password: Optional[str] = None
    email: Optional[str] = None


@router.post("", response_model=ShareLinkOut)
async def create_share_link(
    body: CreateShareLinkBody,
    request: Request,
    user: dict = Depends(require_role(ROLE_EDITOR)),
):
    # Verify user owns (or admin) every document
    doc_query = {"id": {"$in": body.document_ids}}
    if user["role"] != "owner":
        doc_query["owner_id"] = user["id"]
    found = await documents.find(doc_query, {"_id": 0, "id": 1}).to_list(500)
    found_ids = {d["id"] for d in found}
    missing = set(body.document_ids) - found_ids
    if missing:
        raise HTTPException(status_code=403, detail=f"No access to documents: {list(missing)}")

    token = generate_share_token()
    expires_at = None
    if body.mode == "expiring":
        hours = body.expires_in_hours or 24
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()

    password_hash = None
    if body.mode == "password":
        if not body.password:
            raise HTTPException(status_code=400, detail="Password required for password mode")
        password_hash = hash_share_password(body.password)

    link = {
        "token": token,
        "mode": body.mode,
        "document_ids": body.document_ids,
        "owner_id": user["id"],
        "title": body.title,
        "password_hash": password_hash,
        "expires_at": expires_at,
        "single_use": body.single_use,
        "domain_restriction": body.domain_restriction,
        "opens": 0,
        "revoked": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await share_links.insert_one(link)
    await log_event(
        "share_link.create",
        actor_id=user["id"],
        actor_role=user["role"],
        resource_type="share_link",
        resource_id=token,
        ip=request.client.host if request.client else None,
        metadata={"mode": body.mode, "doc_count": len(body.document_ids)},
    )
    return _public_link(link)


def _public_link(link: dict) -> dict:
    return {
        "token": link["token"],
        "mode": link["mode"],
        "document_ids": link["document_ids"],
        "title": link.get("title"),
        "single_use": link.get("single_use", False),
        "opens": link.get("opens", 0),
        "revoked": link.get("revoked", False),
        "expires_at": link.get("expires_at"),
        "created_at": link["created_at"],
        "domain_restriction": link.get("domain_restriction"),
    }


@router.get("", response_model=List[ShareLinkOut])
async def list_share_links(user: dict = Depends(require_role(ROLE_EDITOR))):
    query = {} if user["role"] == "owner" else {"owner_id": user["id"]}
    links = await share_links.find(query, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)
    return [_public_link(link) for link in links]


@router.delete("/{token}")
async def revoke_share_link(
    token: str,
    request: Request,
    user: dict = Depends(require_role(ROLE_EDITOR)),
):
    link = await share_links.find_one({"token": token}, {"_id": 0})
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    if user["role"] != "owner" and link["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    await share_links.update_one({"token": token}, {"$set": {"revoked": True}})
    await log_event(
        "share_link.revoke",
        actor_id=user["id"],
        actor_role=user["role"],
        resource_type="share_link",
        resource_id=token,
        ip=request.client.host if request.client else None,
    )
    return {"ok": True}


@router.get("/{token}/info")
async def get_share_info(token: str):
    """Public endpoint: returns minimal info so frontend knows if password needed."""
    link = await share_links.find_one({"token": token}, {"_id": 0, "password_hash": 0, "owner_id": 0})
    if not link or link.get("revoked"):
        raise HTTPException(status_code=404, detail="Link not found or revoked")
    if link.get("expires_at"):
        exp = datetime.fromisoformat(link["expires_at"])
        if exp < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Link expired")
    if link.get("single_use") and link.get("opens", 0) > 0:
        raise HTTPException(status_code=410, detail="Link already used")
    # List document filenames
    docs = await documents.find(
        {"id": {"$in": link["document_ids"]}}, {"_id": 0, "id": 1, "filename": 1}
    ).to_list(100)
    return {
        "token": token,
        "mode": link["mode"],
        "title": link.get("title"),
        "requires_password": link["mode"] == "password",
        "requires_email": bool(link.get("domain_restriction")),
        "domain_restriction": link.get("domain_restriction"),
        "documents": docs,
        "expires_at": link.get("expires_at"),
    }


@router.post("/{token}/verify")
async def verify_share_link(token: str, body: VerifyBody, request: Request):
    link = await share_links.find_one({"token": token}, {"_id": 0})
    if not link or link.get("revoked"):
        raise HTTPException(status_code=404, detail="Link not found or revoked")
    if link.get("expires_at"):
        exp = datetime.fromisoformat(link["expires_at"])
        if exp < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Link expired")
    if link.get("single_use") and link.get("opens", 0) > 0:
        raise HTTPException(status_code=410, detail="Link already used")

    if link["mode"] == "password":
        if not body.password or not verify_share_password(body.password, link["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid password")

    if link.get("domain_restriction"):
        if not body.email:
            raise HTTPException(status_code=400, detail="Email required")
        if not body.email.lower().endswith(link["domain_restriction"].lower()):
            raise HTTPException(status_code=403, detail="Email domain not allowed")

    # Increment opens, issue scoped guest token
    await share_links.update_one({"token": token}, {"$inc": {"opens": 1}})
    guest_token = create_guest_token(token, link["document_ids"], ttl_seconds=3600)

    await log_event(
        "share_link.open",
        actor_id=None,
        actor_role="guest",
        resource_type="share_link",
        resource_id=token,
        ip=request.client.host if request.client else None,
        metadata={"email": body.email},
    )
    await log_analytics("share_link.open", {"token": token})

    docs = await documents.find(
        {"id": {"$in": link["document_ids"]}}, {"_id": 0, "id": 1, "filename": 1}
    ).to_list(100)

    return {
        "guest_token": guest_token,
        "document_ids": link["document_ids"],
        "documents": docs,
        "title": link.get("title"),
        "mode": link["mode"],
    }
