from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel


class SecuenciaOperacion(BaseModel):
    fecha: str
    contador: int = 0


@dataclass
class AuthToken:
    """
    Token de autenticación verificado de Firebase.
    Representa la información del token sin consultar la BD.
    """

    email: str


@dataclass
class User:
    """
    Entidad de usuario del dominio.
    No depende de SQLAlchemy ni de ningún framework.
    """

    email: str
    nombre: str
    rol: str = "rol1"
    created_at: datetime | None = None

    def __post_init__(self):
        """Validaciones de negocio"""
        if not self.email or "@" not in self.email:
            raise ValueError("Email inválido")

        if self.rol not in ["admin", "rol1", "rol2"]:
            raise ValueError(f"Rol '{self.rol}' no válido")

    def is_admin(self) -> bool:
        """Regla de negocio: verificar si es admin"""
        return self.rol == "admin"

    def can_access_facturas(self) -> bool:
        """Regla de negocio: puede acceder a facturas"""
        return self.rol in ["admin", "rol1"]

    def can_access_verificaciones(self) -> bool:
        """Regla de negocio: puede acceder a verificaciones"""
        return self.rol in ["admin", "rol2"]
