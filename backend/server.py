"""DocChat — enterprise RAG backend."""
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from core.db import init_indexes  # noqa: E402
from routers import admin, auth, chat, documents, feedback, flags, sessions, share  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("docchat")

app = FastAPI(title="DocChat API", version="2.0.0")

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"service": "docchat", "version": "2.0.0"}


@api_router.get("/health")
async def health():
    return {"status": "ok"}


# Public share-link info (no auth)
from routers.share import router as share_router  # noqa: E402

api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(chat.router)
api_router.include_router(sessions.router)
api_router.include_router(feedback.router)
api_router.include_router(share.router)
api_router.include_router(flags.router)
api_router.include_router(admin.router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    try:
        await init_indexes()
        logger.info("MongoDB indexes initialized")
    except Exception as e:
        logger.warning("init_indexes failed: %s", e)
