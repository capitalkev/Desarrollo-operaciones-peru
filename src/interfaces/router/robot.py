import json
from typing import Any

from capitalexpress_auth import User
from fastapi import APIRouter, Depends, File, Form, UploadFile

from src.application.robot.operacion_extractor import RobotOperacionExtractor
from src.application.robot.operacion_robot import RobotOperacion, RobotOperacionResult
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
    xml_files: list[UploadFile] = File(...),
    pdf_files: list[UploadFile] = File(...),
    respaldo_files: list[UploadFile] = File([]),
    user: User = Depends(require_roles(["admin", "ventas"])),
) -> RobotOperacionResult:
    data_frontend_dict = json.loads(data_frontend)
    return action.execute(
        xml_files=xml_files,
        pdf_files=pdf_files,
        respaldo_files=respaldo_files,
        data_frontend=data_frontend_dict,
    )
