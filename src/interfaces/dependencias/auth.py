from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from src.application.auth.authenticate import (
    AuthenticateUserCommand,
    AuthenticateUserUseCase,
)
from src.application.auth.sync import SyncFirebase
from src.domain.models import User
from src.infrastructure.postgresql.connection import get_db
from src.infrastructure.postgresql.repositories.auth.firebase import AuthRepository


def get_firebase(db: Session = Depends(get_db)) -> SyncFirebase:
    repository = AuthRepository(db)
    return SyncFirebase(repository)


def get_authenticate_user_use_case(
    db: Session = Depends(get_db),
) -> AuthenticateUserUseCase:
    """Instancia el caso de uso inyectando el repositorio de base de datos"""
    repository = AuthRepository(db)
    return AuthenticateUserUseCase(repository)


def get_current_user(
    authorization: str = Header(None),
    auth_use_case: AuthenticateUserUseCase = Depends(get_authenticate_user_use_case),
) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token no proporcionado")

    token = authorization.replace("Bearer ", "")

    try:
        result = auth_use_case.execute(
            AuthenticateUserCommand(token=token, require_db_user=True)
        )

        if not result.user:
            raise HTTPException(
                status_code=401, detail="Usuario no encontrado en el sistema."
            )

        return result.user

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None


def require_roles(allowed_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_any_role(allowed_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Permisos insuficientes. Se requiere uno de los siguientes roles: {allowed_roles}",
            )
        return current_user

    return role_checker
