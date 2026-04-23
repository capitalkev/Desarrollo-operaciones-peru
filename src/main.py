import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.interfaces.middleware.api_key_auth import ApiKeyMiddleware
from src.interfaces.router import contactos, health, operaciones, robot

load_dotenv()

CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS")


def _parse_cors_allow_origins(raw: str | None) -> list[str]:
    if raw is None:
        return []
    raw = raw.strip()
    if not raw:
        return []
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
            return parsed
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def create_application() -> FastAPI:
    """
    Application factory function.
    Returns:
        FastAPI: The configured application instance.
    """
    application = FastAPI(
        title="Operaciones SaaS Peru",
        description="API para la gestión de operaciones en Perú",
        version="1.0.0",
    )
    application.add_middleware(ApiKeyMiddleware, api_keys=settings.parsed_api_keys)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        #_parse_cors_allow_origins(CORS_ALLOW_ORIGINS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(robot.router)
    application.include_router(operaciones.router)
    application.include_router(contactos.router)
    application.include_router(health.router)

    return application


app = create_application()
