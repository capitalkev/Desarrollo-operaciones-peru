from fastapi import Depends, Header, HTTPException

from src.domain.models import User
from src.infrastructure.auth.cognito_validator import CognitoTokenValidator

cognito_validator = CognitoTokenValidator()


async def get_current_user(authorization: str = Header(None)) -> User:
    """Extrae el token del header y lo valida con Cognito"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Token no proporcionado o formato inválido"
        )

    token = authorization.replace("Bearer ", "")
    user = await cognito_validator.verify_token(token)
    return user


def require_roles(allowed_roles: list[str]):
    """Dependencia para proteger rutas basado en roles"""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.rol == "sin_asignar":
            raise HTTPException(
                status_code=403,
                detail="Tu cuenta aún no tiene un rol asignado por el administrador.",
            )

        if not current_user.has_any_role(allowed_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Permisos insuficientes. Se requiere uno de los siguientes roles: {allowed_roles}",
            )
        return current_user

    return role_checker
