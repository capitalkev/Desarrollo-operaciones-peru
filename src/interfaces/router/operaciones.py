from fastapi import APIRouter, Depends

from src.application.operaciones.find import FindFacturas
from src.application.operaciones.get_all import GetAllOperaciones
from src.domain.models import Rol
from src.interfaces.dependencias.auth import require_roles
from src.interfaces.dependencias.operaciones import dp_facturas, dp_operaciones

router = APIRouter(prefix="/operaciones", tags=["operaciones"])


@router.get("/{gmail}")
async def extraer_deudores(
    gmail: str, action: GetAllOperaciones = Depends(dp_operaciones),
    user = Depends(require_roles([Rol.ADMIN.value, Rol.VENTAS.value])),
):
    return action.execute(gmail)


@router.get("/facturas/{id_operacion}")
async def extraer_facturas(
    id_operacion: str, action: FindFacturas = Depends(dp_facturas),
    user = Depends(require_roles([Rol.ADMIN.value, Rol.VENTAS.value])),
):
    return action.execute(id_operacion)
