"""Admin analytics, audit log, users."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.db import (
    analytics_events,
    audit_log,
    documents,
    feedback,
    messages,
    share_links,
    users,
)
from core.deps import ROLE_OWNER, require_role

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/analytics")
async def analytics(days: int = 7, _: dict = Depends(require_role(ROLE_OWNER))):
    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=days)).isoformat()

    # Totals
    total_docs = await documents.count_documents({})
    total_users = await users.count_documents({})
    total_sessions = await messages.distinct("session_id")
    total_share_links = await share_links.count_documents({})
    total_messages = await messages.count_documents({"created_at": {"$gte": since}})

    # Latency
    latencies = []
    async for m in messages.find(
        {"role": "assistant", "latency_ms": {"$exists": True}, "created_at": {"$gte": since}},
        {"_id": 0, "latency_ms": 1},
    ):
        latencies.append(m["latency_ms"])
    latencies.sort()

    def pct(p):
        if not latencies:
            return 0
        idx = min(len(latencies) - 1, int(len(latencies) * p))
        return latencies[idx]

    # Feedback ratio
    up = await feedback.count_documents({"rating": 1})
    down = await feedback.count_documents({"rating": -1})

    # Daily query counts
    daily: dict[str, int] = {}
    async for ev in analytics_events.find(
        {"event_type": "chat.query", "created_at": {"$gte": since}},
        {"_id": 0, "created_at": 1},
    ):
        day = ev["created_at"][:10]
        daily[day] = daily.get(day, 0) + 1
    series = [{"day": k, "count": v} for k, v in sorted(daily.items())]

    # Confidence distribution
    conf_dist = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    async for m in messages.find(
        {"role": "assistant", "confidence": {"$exists": True}, "created_at": {"$gte": since}},
        {"_id": 0, "confidence": 1},
    ):
        c = m.get("confidence", "LOW")
        conf_dist[c] = conf_dist.get(c, 0) + 1

    return {
        "totals": {
            "documents": total_docs,
            "users": total_users,
            "sessions": len(total_sessions),
            "share_links": total_share_links,
            "messages": total_messages,
        },
        "latency_ms": {
            "p50": pct(0.5),
            "p90": pct(0.9),
            "p99": pct(0.99),
            "samples": len(latencies),
        },
        "feedback": {"up": up, "down": down, "ratio": round(up / (up + down), 2) if (up + down) else 0},
        "queries_daily": series,
        "confidence_distribution": conf_dist,
    }


@router.get("/audit-log")
async def get_audit_log(
    limit: int = Query(100, le=500),
    action: Optional[str] = None,
    actor_id: Optional[str] = None,
    _: dict = Depends(require_role(ROLE_OWNER)),
):
    query: dict = {}
    if action:
        query["action"] = action
    if actor_id:
        query["actor_id"] = actor_id
    cursor = audit_log.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(limit)


class UserUpdate(BaseModel):
    role: Optional[str] = None


@router.get("/users")
async def list_users(_: dict = Depends(require_role(ROLE_OWNER))):
    cursor = users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1)
    return await cursor.to_list(500)


@router.patch("/users/{user_id}")
async def update_user(user_id: str, body: UserUpdate, _: dict = Depends(require_role(ROLE_OWNER))):
    if body.role and body.role not in ("owner", "editor", "viewer"):
        raise HTTPException(status_code=400, detail="Invalid role")
    update: dict = {}
    if body.role:
        update["role"] = body.role
    if update:
        await users.update_one({"id": user_id}, {"$set": update})
    return {"ok": True}
