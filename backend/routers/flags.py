"""Feature flags + active provider info (read-only)."""
from fastapi import APIRouter, Depends

from core.config import (
    EMBEDDING_MODEL,
    EMBEDDING_PROVIDER,
    FEATURE_FLAGS,
    LLM_MODEL,
    LLM_PROVIDER,
)
from core.deps import get_current_user

router = APIRouter(prefix="/v2", tags=["flags"])


@router.get("/flags")
async def get_flags(_: dict = Depends(get_current_user)):
    return FEATURE_FLAGS


@router.get("/providers")
async def get_providers(_: dict = Depends(get_current_user)):
    """Report the currently active LLM + embedding providers (no secrets)."""
    return {
        "llm": {"provider": LLM_PROVIDER, "model": LLM_MODEL},
        "embedding": {"provider": EMBEDDING_PROVIDER, "model": EMBEDDING_MODEL},
    }
