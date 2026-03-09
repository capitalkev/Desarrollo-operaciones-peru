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
    """Crea una instancia del caso de uso de autenticación"""
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

        return result.user

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def require_facturas_access(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.can_access_facturas():
        raise HTTPException(
            status_code=403,
            detail=f"Usuario con rol '{current_user.rol}' no tiene acceso a facturas",
        )
    return current_user


def require_verificaciones_access(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.can_access_verificaciones():
        raise HTTPException(
            status_code=403,
            detail=f"Usuario con rol '{current_user.rol}' no tiene acceso a verificaciones",
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin():
        raise HTTPException(
            status_code=403, detail="Se requieren permisos de administrador"
        )
    return current_user
