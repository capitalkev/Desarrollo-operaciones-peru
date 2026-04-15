import os
from typing import Any

import httpx
from fastapi import HTTPException
from jose import jwt

from src.domain.models import User


class CognitoTokenValidator:
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
        self.app_client_id = os.getenv("COGNITO_APP_CLIENT_ID")

        if not self.user_pool_id or not self.app_client_id:
            raise ValueError("Variables de entorno de Cognito no configuradas")

        self.keys_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
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
        """Decodifica el token, lo valida y retorna el modelo User poblado"""
        try:
            jwks = await self._get_jwks()
            claims = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=self.app_client_id,
                options={"verify_at_hash": False},
            )

            # Extraer Email y Nombre
            email = claims.get("email", claims.get("username", "")).lower()
            nombre = claims.get("name", email.split("@")[0])

            # Extraer los roles (grupos de Cognito)
            grupos_cognito = claims.get("cognito:groups", [])

            # Asumimos que el usuario tiene un rol principal (el primero que venga)
            rol_asignado = (
                grupos_cognito[0].lower() if grupos_cognito else "sin_asignar"
            )

            # Retornamos directamente el modelo de dominio
            return User(email=email, nombre=nombre, rol=rol_asignado)

        except Exception:
            raise HTTPException(
                status_code=401, detail="Token inválido o expirado"
            ) from None
