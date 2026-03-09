from fastapi import APIRouter, Depends, Form, HTTPException

from src.application.auth.sync import SyncFirebase
from src.domain.models import User
from src.interfaces.dependencias.auth import get_current_user, get_firebase

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/livez")
def liveness_check():
    return {"status": "ok"}


@router.get("/readyz")
def readiness_check():
    return {"status": "ready"}


@router.post("/sync")
async def sync_firebase_user(
    firebase_token: str = Form(...),
    nombre: str = Form(None),
    action: SyncFirebase = Depends(get_firebase),
):
    """
    Sincroniza un usuario de Firebase con la base de datos.
    Si el usuario no existe, lo crea con rol 'User' por defecto.
    """
    try:
        result = action.execute(firebase_token, nombre)
        user = result["user"]

        return {"email": user["email"], "nombre": user["nombre"], "rol": user["rol"]}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "nombre": current_user.nombre,
        "rol": current_user.rol,
        "permissions": {
            "is_admin": current_user.is_admin(),
            "can_access_facturas": current_user.can_access_facturas(),
            "can_access_verificaciones": current_user.can_access_verificaciones(),
        },
    }
