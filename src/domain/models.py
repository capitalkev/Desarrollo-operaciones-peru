from datetime import datetime

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    email: EmailStr
    nombre: str
    rol: str
    created_at: datetime | None = None

    def is_admin(self) -> bool:
        return self.rol == "admin"

    def has_any_role(self, allowed_roles: list[str]) -> bool:
        """Verifica si el string del rol del usuario está en la lista permitida"""
        return self.rol in allowed_roles
