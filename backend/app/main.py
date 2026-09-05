import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import candidates, interviews, jobs
from app.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


import sys
import os

# Fix Windows console UTF-8 output encoding for Phoenix emoji logs
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
os.environ["PYTHONIOENCODING"] = "utf-8"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Interview Agent API")
    
    try:
        import phoenix as px
        from openinference.instrumentation.langchain import LangChainInstrumentor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        session = px.launch_app(host="127.0.0.1", port=6006)
        
        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint="http://127.0.0.1:6006/v1/traces"))
        )
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
        logger.info("Arize Phoenix Tracing UI active at http://127.0.0.1:6006")
    except Exception as exc:
        logger.warning(f"Phoenix launch info: {exc}")

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
