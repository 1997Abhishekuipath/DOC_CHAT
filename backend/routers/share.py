"""Secure share links with strict document-scope isolation."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from core.audit import log_analytics, log_event
from core.db import documents, share_links
from core.deps import ROLE_EDITOR, require_role
from core.security import (
    create_guest_token,
    decode_guest_token,
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
    document_filenames: List[str] = []
    title: Optional[str]
    single_use: bool
    opens: int
    revoked: bool
    expires_at: Optional[str]
    created_at: str
    domain_restriction: Optional[str]
    creator_id: Optional[str] = None
    creator_role: Optional[str] = None
    creator_name: Optional[str] = None
    creator_email: Optional[str] = None


class VerifyBody(BaseModel):
    password: Optional[str] = None
    email: Optional[str] = None


@router.post("", response_model=ShareLinkOut)
async def create_share_link(
    body: CreateShareLinkBody,
    request: Request,
    user: dict = Depends(require_role(ROLE_EDITOR)),
):
    # Verify user has access to every requested document.
    # Owners can share any doc; editors can share docs they uploaded
    # OR docs explicitly assigned to them by an Owner.
    doc_query: dict = {"id": {"$in": body.document_ids}}
    if user["role"] != "owner":
        doc_query["$or"] = [
            {"owner_id": user["id"]},
            {"assigned_to": user["id"]},
        ]
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
        # Creator metadata — owner-visibility & filtering
        "creator_id": user["id"],
        "creator_role": user["role"],
        "creator_name": user.get("name"),
        "creator_email": user.get("email"),
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


def _public_link(link: dict, filenames_by_id: Optional[dict] = None) -> dict:
    doc_ids = link.get("document_ids", []) or []
    filenames = (
        [filenames_by_id.get(i) for i in doc_ids if filenames_by_id.get(i)]
        if filenames_by_id is not None
        else []
    )
    return {
        "token": link["token"],
        "mode": link["mode"],
        "document_ids": doc_ids,
        "document_filenames": filenames,
        "title": link.get("title"),
        "single_use": link.get("single_use", False),
        "opens": link.get("opens", 0),
        "revoked": link.get("revoked", False),
        "expires_at": link.get("expires_at"),
        "created_at": link["created_at"],
        "domain_restriction": link.get("domain_restriction"),
        "creator_id": link.get("creator_id") or link.get("owner_id"),
        "creator_role": link.get("creator_role"),
        "creator_name": link.get("creator_name"),
        "creator_email": link.get("creator_email"),
    }


@router.get("", response_model=List[ShareLinkOut])
async def list_share_links(user: dict = Depends(require_role(ROLE_EDITOR))):
    query = {} if user["role"] == "owner" else {"owner_id": user["id"]}
    links = await share_links.find(query, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)
    # Resolve filenames for display in the listing
    all_doc_ids = sorted({d for link in links for d in (link.get("document_ids") or [])})
    filenames_by_id: dict = {}
    if all_doc_ids:
        async for d in documents.find(
            {"id": {"$in": all_doc_ids}}, {"_id": 0, "id": 1, "filename": 1}
        ):
            filenames_by_id[d["id"]] = d["filename"]
    return [_public_link(link, filenames_by_id) for link in links]


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



@router.get("/{token}/document/{doc_id}/file")
async def serve_shared_document_file(
    token: str,
    doc_id: str,
    x_guest_token: Optional[str] = Header(None),
):
    """Serve a document file for a verified guest of this share link.
    The guest token must:
      - decode validly,
      - match the requested share-link token,
      - include the requested doc_id in its scoped document_ids.
    The link itself must still be active (not revoked / not expired).
    """
    if not x_guest_token:
        raise HTTPException(status_code=401, detail="Missing guest token")
    payload = decode_guest_token(x_guest_token)
    if not payload or payload.get("type") != "guest":
        raise HTTPException(status_code=401, detail="Invalid guest token")
    if payload.get("share_token") != token:
        raise HTTPException(status_code=403, detail="Token / link mismatch")
    if doc_id not in (payload.get("document_ids") or []):
        raise HTTPException(status_code=403, detail="Document not in scope")

    link = await share_links.find_one({"token": token}, {"_id": 0})
    if not link or link.get("revoked"):
        raise HTTPException(status_code=404, detail="Link not found or revoked")
    if link.get("expires_at"):
        exp = datetime.fromisoformat(link["expires_at"])
        if exp < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Link expired")
    if doc_id not in (link.get("document_ids") or []):
        # Defence-in-depth: link itself no longer references this doc
        raise HTTPException(status_code=403, detail="Document not in scope")

    doc = await documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    disk_path = Path(doc["disk_path"])
    if not disk_path.exists():
        raise HTTPException(status_code=404, detail="File no longer on disk")
    return FileResponse(
        path=disk_path,
        media_type=doc.get("mime_type") or "application/octet-stream",
        filename=doc.get("filename") or disk_path.name,
    )
