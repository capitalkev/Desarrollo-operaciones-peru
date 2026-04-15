from fastapi import APIRouter, Depends

from src.domain.models import Rol, User
from src.interfaces.dependencias.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Retorna la información del usuario basada puramente en el JWT de Cognito"""
    return {
        "email": current_user.email,
        "nombre": current_user.nombre,
        "rol": current_user.rol,
        "permissions": {
            "is_admin": current_user.is_admin(),
            "can_manage_users": current_user.is_admin(),
            "can_manage_operations": current_user.has_any_role(
                [Rol.ADMIN.value, Rol.GESTION.value]
            ),
            "can_view_sales_data": current_user.has_any_role(
                [Rol.ADMIN.value, Rol.GESTION.value, Rol.VENTAS.value]
            ),
        },
    }
