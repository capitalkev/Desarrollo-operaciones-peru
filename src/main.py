from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.auth.firebase_init import initialize_firebase
from src.interfaces.router import auth, contactos, health, operaciones, robot


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
    initialize_firebase()

    origins = ["http://localhost:5173", "http://127.0.0.1:5173", "*"]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(auth.router)
    application.include_router(robot.router)
    application.include_router(operaciones.router)
    application.include_router(contactos.router)
    application.include_router(health.router)

    return application


app = create_application()
