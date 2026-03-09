from fastapi import APIRouter, Depends

from src.application.contactos.add_contacto import AddContacto
from src.application.contactos.delete_contactos import DeleteContacto
from src.application.contactos.get_contacto import GetContacto
from src.domain.models import Rol
from src.interfaces.dependencias.auth import require_roles
from src.interfaces.dependencias.contactos import (
    dp_add_contactos,
    dp_contactos,
    dp_delete_contactos,
)

router = APIRouter(prefix="/contactos", tags=["contactos"])


@router.get("/{ruc_deudor}")
def extraer_deudores(ruc_deudor: str, action: GetContacto = Depends(dp_contactos), user = Depends(require_roles([Rol.ADMIN.value, Rol.VENTAS.value]))):
    return action.execute(ruc_deudor)


@router.post("/{ruc_deudor}/{gmail}")
def add_correo(
    ruc_deudor: str, gmail: str, action: AddContacto = Depends(dp_add_contactos), user = Depends(require_roles([Rol.ADMIN.value, Rol.VENTAS.value]))
):
    return action.execute(ruc_deudor, gmail)


@router.delete("/{ruc_deudor}/{gmail}")
def delete_correo(
    ruc_deudor: str, gmail: str, action: DeleteContacto = Depends(dp_delete_contactos), user = Depends(require_roles([Rol.ADMIN.value, Rol.VENTAS.value]))
):
    return action.execute(ruc_deudor, gmail)
