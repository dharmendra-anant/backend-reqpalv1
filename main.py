import logging
import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.cli.repl import app as repl_app
from app.utils.setup_logging import setup_logging

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
REQUIRED_SECRETS = [
    "OPENAI_API_KEY",
]


def verify_secrets() -> None:
    """Verify all required environment variables are set."""
    missing_secrets = [
        secret for secret in REQUIRED_SECRETS if secret not in os.environ
    ]
    if missing_secrets:
        raise ValueError(f"Missing required environment variables: {missing_secrets}")


def configure_logging() -> None:
    """Configure application logging."""
    setup_logging(
        debug=True,
        log_file="logs/app.log",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application startup and shutdown events."""
    logger.info("Starting up...")

    verify_secrets()
    yield
    logger.info("Shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(lifespan=lifespan)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(v1_router)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "Hello World"}

    return app


# verify_secrets()
configure_logging()

app = create_app()


def main() -> None:
    """Application entry point."""
    repl_app()


if __name__ == "__main__":
    main()
