import json
from typing import Any

from capitalexpress_auth import User
from fastapi import APIRouter, Depends, File, Form, UploadFile

from src.application.robot.cavali_robot import CavaliOperacion
from src.application.robot.correo_robot import CorreoOperacion
from src.application.robot.drive_robot import DriveOperacion
from src.application.robot.operacion_extractor import RobotOperacionExtractor
from src.application.robot.operacion_robot import RobotOperacion
from src.application.robot.trello_robot import TrelloOperacion
from src.interfaces.dependencias.auth import require_roles
from src.interfaces.dependencias.operaciones import (
    dp_robot_extractor,
    dp_robot_operacion,
)

router = APIRouter(prefix="/robot", tags=["robot"])


@router.post("/extraer-deudores")
async def extraer_deudores(
    action: RobotOperacionExtractor = Depends(dp_robot_extractor),
    xml_files: list[UploadFile] = File(...),
    user: User = Depends(require_roles(["admin", "ventas"])),
) -> list[dict[str, Any]]:
    return await action.execute(xml_files)


@router.post("/procesar-completa")
def procesar_operacion_completa(
    action: RobotOperacion = Depends(dp_robot_operacion),
    data_frontend: str = Form(...),
    user: User = Depends(require_roles(["admin", "ventas"])),
) -> str:
    data_frontend_dict = json.loads(data_frontend)
    return action.execute(
        data_frontend=data_frontend_dict,
    )


@router.post("/cavali")
def procesar_cavali(
    xml_files: list[UploadFile] = File(...),
) -> dict[str, Any]:
    cavali = CavaliOperacion()
    return cavali.execute(xml_files)


@router.post("/correo")
def procesar_correo(
    data_frontend: str = Form(...),
    pdf_files: list[UploadFile] = File(...),
    id_op: str = Form(...),
) -> dict[str, Any]:
    data_frontend = json.loads(data_frontend)
    correo = CorreoOperacion()
    return correo._enviar_correos_verificacion(data_frontend, id_op, pdf_files)


@router.post("/drive")
def procesar_drive(
    id_op: str = Form(...),
) -> dict[str, Any]:
    drive = DriveOperacion()
    return drive.execute_primero(operacion_id=id_op)


@router.post("/secundario-drive")
def procesar_secundario_drive(
    carpeta_hijo: str = Form(...),
    xml_files: list[UploadFile] = File(...),
    pdf_files: list[UploadFile] = File(...),
    respaldo_files: list[UploadFile] = File([]),
) -> dict[str, Any]:
    drive = DriveOperacion()
    all_archivos = xml_files + pdf_files + respaldo_files
    return drive.execute_secundario(documentos=all_archivos, carpeta_hijo=carpeta_hijo)


@router.post("/trello")
def procesar_trello(
    id_op: str = Form(...),
    pdf_files: list[UploadFile] = File(...),
    respaldo_files: list[UploadFile] = File([]),
    url_drive_str: str = Form(...),
    cavali_resultados: str = Form(...),
    data_frontend: str = Form(...),
) -> dict[str, Any]:
    trello = TrelloOperacion()
    trello_archivos = pdf_files + respaldo_files
    data_frontend = json.loads(data_frontend)
    return trello.execute(
        data_frontend,
        id_op,
        trello_archivos,
        url_drive=url_drive_str,
        cavali_resultados=cavali_resultados,
    )


@router.post("/guardar-operacion")
def guardar_operacion(
    action: RobotOperacion = Depends(dp_robot_operacion),
    data_frontend: str = Form(...),
    id_op: str = Form(...),
    user: User = Depends(require_roles(["admin", "ventas"])),
) -> dict[str, Any]:
    data_frontend_dict = json.loads(data_frontend)
    result = {
        "data_frontend": data_frontend_dict,
        "id_op": id_op,
    }
    return action.guardar_op.execute(result, id_op)
