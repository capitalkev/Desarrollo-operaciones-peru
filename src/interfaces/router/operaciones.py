from capitalexpress_auth import User
from fastapi import APIRouter, Depends

from src.application.operaciones.find import FindFacturas
from src.application.operaciones.get_all import GetAllOperaciones
from src.interfaces.dependencias.auth import require_roles
from src.interfaces.dependencias.operaciones import (
    dp_facturas,
    dp_operaciones,
)

router = APIRouter(prefix="/operaciones", tags=["operaciones"])


@router.get("/{gmail}")
async def extraer_deudores(
    gmail: str,
    action: GetAllOperaciones = Depends(dp_operaciones),
    user: User = Depends(require_roles(["admin", "ventas"])),
) -> list[dict]:
    return action.execute(gmail, is_admin=user.is_admin())


@router.get("/facturas/{id_operacion}")
async def extraer_facturas(
    id_operacion: str,
    action: FindFacturas = Depends(dp_facturas),
    user: User = Depends(require_roles(["admin", "ventas"])),
) -> list[dict]:
    return action.execute(id_operacion)
