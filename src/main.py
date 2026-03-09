from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.interfaces.router import auth, contactos, health, operaciones, robot


def create_application() -> FastAPI:
    """
    Application factory function.
    Returns:
        FastAPI: The configured application instance.
    """
    application = FastAPI(
        title="Robot Chile",
        description="Api para el manejo de operaciones y envíos de correos electrónicos.",
        version="1.0.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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
