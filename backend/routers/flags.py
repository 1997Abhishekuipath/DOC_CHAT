"""Feature flags endpoint (read-only for non-admins)."""
from fastapi import APIRouter, Depends

from core.config import FEATURE_FLAGS
from core.deps import get_current_user

router = APIRouter(prefix="/v2/flags", tags=["flags"])


@router.get("")
async def get_flags(_: dict = Depends(get_current_user)):
    return FEATURE_FLAGS
