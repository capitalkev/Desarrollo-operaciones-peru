# src/worker.py
import json
import os

import boto3
from dotenv import load_dotenv

from src.application.operaciones.create_op import CreateOperacion
from src.application.robot.cavali_robot import CavaliOperacion
from src.application.robot.correo_robot import CorreoOperacion
from src.application.robot.drive_robot import DriveOperacion
from src.application.robot.trello_robot import TrelloOperacion
from src.application.robot.utils import InMemoryFile
from src.infrastructure.postgresql.connection import SessionLocal
from src.infrastructure.postgresql.repositories.operaciones.operaciones import (
    OperacionesRepository,
)
from src.infrastructure.storage.s3_storage_service import S3Service

load_dotenv()

sqs = boto3.client("sqs", region_name=os.getenv("AWS_REGION", "us-east-1"))
QUEUE_URL = os.getenv("SQS_ROBOT_OPERACIONES_QUEUE_URL")
S3_BUCKET = os.getenv("AWS_S3_BUCKET_NAME")

s3_service = S3Service(bucket_name=S3_BUCKET)


def descargar_archivos_memoria(archivos_meta: list) -> list:
    """Descarga lista de archivos de S3 y devuelve una lista de InMemoryFile"""
    archivos_memoria = []
    for meta in archivos_meta:
        contenido = s3_service.download_file(meta["key"])
        archivos_memoria.append(
            InMemoryFile(
                meta["filename"],
                contenido,
                meta.get("content_type", "application/octet-stream"),
            )
        )
    return archivos_memoria


def procesar_mensaje(msg):
    sns_body = json.loads(msg["Body"])
    payload = json.loads(sns_body["Message"])

    id_op = payload["id_op"]
    data_frontend = payload["data_frontend"]
    archivos_s3 = payload["archivos_s3"]

    print(f"\n[+] Iniciando proceso para Operación: {id_op}")

    print(f"[{id_op}] Descargando archivos de S3...")
    xmls = descargar_archivos_memoria(archivos_s3["xmls"])
    pdfs = descargar_archivos_memoria(archivos_s3["pdfs"])
    respaldos = descargar_archivos_memoria(archivos_s3.get("respaldos", []))

    print(f"[{id_op}] Ejecutando Cavali...")
    cavali = CavaliOperacion()
    cavali_resultados = cavali.execute(xmls)

    print(f"[{id_op}] Enviando correos...")
    correo = CorreoOperacion()
    correo._enviar_correos_verificacion(data_frontend, id_op, pdfs)

    print(f"[{id_op}] Creando carpeta en Drive y subiendo archivos...")
    drive = DriveOperacion()
    res_drive_1 = drive.execute_primero(id_op)
    id_folder = res_drive_1["folder_id"]

    all_archivos = xmls + pdfs + respaldos
    res_drive_2 = drive.execute_secundario(all_archivos, id_folder)
    url_drive_str = str(res_drive_2.get("drive_folder_url", ""))

    print(f"[{id_op}] Creando tarjeta en Trello...")
    trello = TrelloOperacion()
    trello_archivos = pdfs + respaldos
    res_trello = trello.execute(
        data_frontend=data_frontend,
        id_op=id_op,
        trello_archivos=trello_archivos,
        url_drive=url_drive_str,
        cavali_resultados=cavali_resultados,
    )

    print(f"[{id_op}] Guardando resultados en Base de Datos...")
    db = SessionLocal()
    try:
        guardar_op = CreateOperacion(repository=OperacionesRepository(db))
        resultado_final = {
            "data_frontend": data_frontend,
            "cavali": cavali_resultados,
            "drive_secundario": res_drive_2,
            "correo": data_frontend.get("notificaciones", {}).get(
                "correo_remitente", ""
            ),
            "trello": res_trello,
        }
        guardar_op.execute(resultado_final, id_op)
        print(f"[✓] Operación {id_op} finalizada con éxito!")
    finally:
        db.close()


def escuchar_cola():
    print("🤖 Worker de Operaciones iniciado. Escuchando cola SQS...")
    while True:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
        )

        if "Messages" in response:
            for msg in response["Messages"]:
                try:
                    procesar_mensaje(msg)
                    sqs.delete_message(
                        QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"]
                    )
                except Exception as e:
                    print(f"[-] Error procesando mensaje: {e!s}")


if __name__ == "__main__":
    escuchar_cola()
