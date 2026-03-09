from fastapi import APIRouter, Depends

from src.application.operaciones.find import FindFacturas
from src.application.operaciones.get_all import GetAllOperaciones
from src.interfaces.dependencias.operaciones import dp_facturas, dp_operaciones

router = APIRouter(prefix="/operaciones", tags=["operaciones"])


@router.get("/{gmail}")
async def extraer_deudores(
    gmail: str, action: GetAllOperaciones = Depends(dp_operaciones)
):
    return action.execute(gmail)


@router.get("/facturas/{id_operacion}")
async def extraer_facturas(
    id_operacion: str, action: FindFacturas = Depends(dp_facturas)
):
    return action.execute(id_operacion)
