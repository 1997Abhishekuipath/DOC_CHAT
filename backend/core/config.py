"""Application configuration and feature flags."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")


def _bool_env(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


# Core secrets
JWT_SECRET = os.environ.get("JWT_SECRET", "docchat-dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_EXPIRE_MINUTES = 60 * 24  # 24h
JWT_REFRESH_EXPIRE_DAYS = 30
SHARE_TOKEN_SECRET = os.environ.get("SHARE_TOKEN_SECRET", JWT_SECRET + "-share")

# LLM / Embeddings
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

# Storage
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "/app/backend/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR = Path(os.environ.get("CHROMA_DIR", "/app/backend/chroma_db"))
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Feature flags
FEATURE_FLAGS = {
    "ENABLE_HYBRID_SEARCH": _bool_env("ENABLE_HYBRID_SEARCH", False),
    "ENABLE_RERANKING": _bool_env("ENABLE_RERANKING", False),
    "ENABLE_QUERY_REWRITING": _bool_env("ENABLE_QUERY_REWRITING", False),
    "ENABLE_MULTI_QUERY_EXPANSION": _bool_env("ENABLE_MULTI_QUERY_EXPANSION", False),
    "ENABLE_STREAMING": _bool_env("ENABLE_STREAMING", True),
    "ENABLE_CONFIDENCE_SCORING": _bool_env("ENABLE_CONFIDENCE_SCORING", True),
    "ENABLE_HALLUCINATION_DETECTION": _bool_env("ENABLE_HALLUCINATION_DETECTION", False),
    "ENABLE_OCR": _bool_env("ENABLE_OCR", False),
    "ENABLE_TABLE_EXTRACTION": _bool_env("ENABLE_TABLE_EXTRACTION", False),
    "ENABLE_ENTITY_EXTRACTION": _bool_env("ENABLE_ENTITY_EXTRACTION", False),
    "ENABLE_PII_MASKING": _bool_env("ENABLE_PII_MASKING", False),
    "ENABLE_RBAC": _bool_env("ENABLE_RBAC", True),
    "ENABLE_SHARE_LINKS": _bool_env("ENABLE_SHARE_LINKS", True),
    "ENABLE_EMBEDDING_CACHE": _bool_env("ENABLE_EMBEDDING_CACHE", False),
    "ENABLE_QUERY_CACHE": _bool_env("ENABLE_QUERY_CACHE", False),
    "ENABLE_BACKGROUND_INGESTION": _bool_env("ENABLE_BACKGROUND_INGESTION", True),
    "ENABLE_ANALYTICS_DASHBOARD": _bool_env("ENABLE_ANALYTICS_DASHBOARD", True),
    "ENABLE_AUDIT_LOG": _bool_env("ENABLE_AUDIT_LOG", True),
}


def is_enabled(flag: str) -> bool:
    return FEATURE_FLAGS.get(flag, False)
