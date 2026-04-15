from typing import Any

import httpx
from fastapi import HTTPException
from jose import jwt

from src.config import settings
from src.domain.models import User


class CognitoTokenValidator:
    def __init__(self):
        self.keys_url = f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}/.well-known/jwks.json"
        self._jwks: dict[str, Any] = {}

    async def _get_jwks(self) -> dict[str, Any]:
        """Descarga las llaves públicas de Cognito para validar la firma del JWT"""
        if not self._jwks:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.keys_url)
                response.raise_for_status()
                self._jwks = response.json()
        return self._jwks

    async def verify_token(self, token: str) -> User:
        try:
            jwks = await self._get_jwks()
            claims = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=settings.cognito_app_client_id,
                options={"verify_at_hash": False},
            )

            email = claims.get("email", claims.get("username", "")).lower()
            nombre = claims.get("name", email.split("@")[0])
            grupos_cognito = claims.get("cognito:groups", [])
            rol_asignado = (
                grupos_cognito[0].lower() if grupos_cognito else "sin_asignar"
            )

            return User(email=email, nombre=nombre, rol=rol_asignado)

        except Exception:
            raise HTTPException(
                status_code=401, detail="Token inválido o expirado"
            ) from None
