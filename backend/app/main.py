import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import candidates, interviews, jobs
from app.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Interview Agent API")
    from app.db.models import Base
    from app.db.session import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("Shutting down AI Interview Agent API")



def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Interview Agent",
        description="Multi-agent technical interview platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(candidates.router)
    app.include_router(jobs.router)
    app.include_router(interviews.router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
