from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class Rol(str, Enum):
    ADMIN = "admin"
    GESTION = "gestion"
    VENTAS = "ventas"


class SecuenciaOperacion(BaseModel):
    fecha: str
    contador: int = 0


@dataclass
class AuthToken:
    email: str


@dataclass
class User:
    email: str
    nombre: str
    rol: str = Rol.VENTAS.value
    created_at: datetime | None = None

    def __post_init__(self):
        """Validaciones de negocio"""
        if not self.email or "@" not in self.email:
            raise ValueError("Email inválido")

        roles_validos = [r.value for r in Rol]
        if self.rol not in roles_validos:
            raise ValueError(
                f"Rol '{self.rol}' no válido. Debe ser uno de: {roles_validos}"
            )

    def is_admin(self) -> bool:
        return self.rol == Rol.ADMIN.value

    def has_any_role(self, allowed_roles: list[str]) -> bool:
        """Regla de negocio: verifica si el usuario tiene al menos uno de los roles permitidos"""
        return self.rol in allowed_roles
