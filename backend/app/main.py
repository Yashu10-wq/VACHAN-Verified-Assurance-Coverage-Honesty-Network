"""
Main FastAPI application entrypoint for InsureChain VoiceGuard.
Configures CORS, lifespan events, centralized routing, and global exception handlers.
"""

from contextlib import asynccontextmanager
import sys
from typing import AsyncGenerator

# Ensure Windows asyncio compatibility with psycopg 3
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import InsureChainException
from app.core.logging import get_logger, setup_logging
from app.db.connection import close_db_pool, init_db_pool

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing database pool connection and teardown."""
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger.info("Starting %s in %s environment...", settings.APP_NAME, settings.APP_ENV)

    # Initialize connection pool gracefully (allows liveness check even if DB is down)
    try:
        await init_db_pool()
    except Exception as exc:
        logger.warning(
            "Neon PostgreSQL pool initialization deferred: %s",
            type(exc).__name__,
        )

    yield

    logger.info("Shutting down %s...", settings.APP_NAME)
    await close_db_pool()


def create_app() -> FastAPI:
    """Application factory for InsureChain VoiceGuard backend."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description=(
            "InsureChain VoiceGuard API — Policy-Aware Insurance Claims Workflow "
            "with Blockchain-Backed Audit Integrity & ElevenLabs Voice AI."
        ),
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
        openapi_url="/openapi.json" if settings.APP_ENV != "production" else None,
        lifespan=lifespan,
    )

    # Configure CORS allowlist from explicit frontend origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.FRONTEND_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Global exception handler for application-defined errors
    @app.exception_handler(InsureChainException)
    async def insurechain_exception_handler(
        request: Request, exc: InsureChainException
    ) -> JSONResponse:
        logger.warning("Handled InsureChainException: %s", exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "type": type(exc).__name__},
        )

    # Global unhandled exception handler (scrubs internal traces from production responses)
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error("Unhandled server exception: %s", type(exc).__name__, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "An internal server error occurred.",
                "type": "InternalServerError",
            },
        )

    # Mount API routers
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
