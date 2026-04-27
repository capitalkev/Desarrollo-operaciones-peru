import json
import os
from typing import Any

import boto3
from capitalexpress_auth import User
from fastapi import APIRouter, Depends, File, Form, UploadFile

from src.application.robot.operacion_extractor import RobotOperacionExtractor
from src.application.robot.operacion_robot import RobotOperacion
from src.infrastructure.storage.s3_storage_service import S3Service
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
async def procesar_operacion_completa(
    action: RobotOperacion = Depends(dp_robot_operacion),
    data_frontend: str = Form(...),
    xml_files: list[UploadFile] = File(...),
    pdf_files: list[UploadFile] = File(...),
    respaldo_files: list[UploadFile] = File([]),
    user: User = Depends(require_roles(["admin", "ventas"])),
) -> dict[str, Any]:

    data_frontend_dict = json.loads(data_frontend)
    id_op = action.execute(data_frontend_dict)

    # 1. Subir archivos a S3
    s3_service = S3Service(bucket_name=os.getenv("AWS_S3_BUCKET_NAME"))
    archivos_s3 = {"xmls": [], "pdfs": [], "respaldos": []}

    # Función auxiliar para no repetir código
    async def upload_files(file_list, category):
        for f in file_list:
            content = await f.read()
            key = f"temporales/{id_op}/{category}/{f.filename}"
            s3_service.upload_file(content, key=key, content_type=f.content_type)
            archivos_s3[category].append(
                {"filename": f.filename, "key": key, "content_type": f.content_type}
            )

    await upload_files(xml_files, "xmls")
    await upload_files(pdf_files, "pdfs")
    await upload_files(respaldo_files, "respaldos")

    sns_client = boto3.client("sns", region_name=os.getenv("AWS_REGION", "us-east-1"))
    topic_arn = os.getenv(
        "SNS_TOPIC_MOVE_TO_NEW_ARN", "arn:aws:sns:REGION:ACCOUNT:NOMBRE_DEL_TOPICO"
    )

    mensaje_sns = {
        "id_op": id_op,
        "data_frontend": data_frontend_dict,
        "archivos_s3": archivos_s3,
    }

    sns_client.publish(TopicArn=topic_arn, Message=json.dumps(mensaje_sns))

    # 3. Respuesta Inmediata
    return {
        "status": "success",
        "id_op": id_op,
        "message": "Operación recibida. Procesándose en segundo plano.",
    }
