import logging
import time
from typing import Any

from typing_extensions import TypedDict

from src.application.operaciones.create_id import CreateIdOperacion
from src.application.operaciones.create_op import CreateOperacion
from src.application.robot.cavali_robot import CavaliOperacion
from src.application.robot.correo_robot import CorreoOperacion
from src.application.robot.drive_robot import DriveOperacion
from src.application.robot.trello_robot import TrelloOperacion

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class RobotOperacionResult(TypedDict):
    cavali: dict[str, Any]
    drive: dict[str, Any]
    drive_secundario: dict[str, Any]
    correo: str
    trello: dict | None


class RobotOperacion:
    def __init__(
        self, create_id_op: CreateIdOperacion, guardar_op: CreateOperacion
    ) -> None:
        self.correo = CorreoOperacion()
        self.cavali = CavaliOperacion()
        self.drive = DriveOperacion()
        self.trello = TrelloOperacion()
        self.create_id_op = create_id_op
        self.guardar_op = guardar_op

    async def execute(
        self,
        data_frontend: dict[str, Any],
        xml_files: list[Any],
        pdf_files: list[Any],
        respaldo_files: list[Any],
    ) -> RobotOperacionResult:
        notificaciones = data_frontend.get("notificaciones", {})
        email_usuario = notificaciones.get("correo_remitente", "usuario@desconocido.com")

        inicio = time.perf_counter()
        id_op = self.create_id_op.execute(email_usuario)
        fin = time.perf_counter()
        logging.info(
            f"ID de operación generado: {id_op} para el usuario: {email_usuario} en {fin - inicio:.2f} segundos"
        )

        # PROCESO CAVALI
        cavali_resultados = {}
        try:
            logging.info(f"Iniciando proceso Cavali para la operación {id_op}")
            cavali_time = time.perf_counter()
            cavali_resultados = self.cavali.execute(xml_files)
            fin_cavali = time.perf_counter()
            logging.info(
                f"Proceso Cavali para la operación {id_op} terminado en {fin_cavali - cavali_time:.2f} segundos"
            )
        except Exception as e:
            logging.error(f"Error en el proceso Cavali para la operación {id_op}: {e}")
            cavali_resultados = {"error": str(e)}

        # ENVIO DE CORREOS
        try:
            logging.info(f"Iniciando envío de correos para la operación {id_op}")
            correos_time = time.perf_counter()
            self.correo._enviar_correos_verificacion(data_frontend, id_op, pdf_files)
            fin_correos = time.perf_counter()
            logging.info(
                f"Correos para la operación {id_op} enviados en {fin_correos - correos_time:.2f} segundos"
            )
        except Exception as e:
            logging.error(
                f"Error en el envío de correos para la operación {id_op}: {e}"
            )

        # SUBIR A DRIVE
        drive = {}
        try:
            logging.info(f"Iniciando subida a Drive para la operación {id_op}")
            drive_time = time.perf_counter()
            drive = self.drive.execute_primero(operacion_id=id_op)
            fin_drive = time.perf_counter()
            logging.info(
                f"Subida a Drive para la operación {id_op} terminada en {fin_drive - drive_time:.2f} segundos"
            )
        except Exception as e:
            logging.error(f"Error en la subida a Drive para la operación {id_op}: {e}")
            drive = {"error": str(e)}

        # SUBIR A DRIVE SECUNDARIO
        drive_s = {}
        try:
            logging.info(
                f"Iniciando subida a Drive secundario para la operación {id_op}"
            )
            drive_s_time = time.perf_counter()
            all_archivos = xml_files + pdf_files + respaldo_files
            drive_s = self.drive.execute_secundario(
                documentos=all_archivos, carpeta_hijo=str(drive.get("folder_id"))
            )
            fin_drive_s = time.perf_counter()
            logging.info(
                f"Subida a Drive secundario para la operación {id_op} terminada en {fin_drive_s - drive_s_time:.2f} segundos"
            )
        except Exception as e:
            logging.error(
                f"Error en la subida a Drive secundario para la operación {id_op}: {e}"
            )
            drive_s = {"error": str(e)}

        url_drive_str = str(drive_s.get("drive_folder_url", "https://drive.google.com"))

        # PROCESO TRELLO
        result_trello = None
        try:
            logging.info(f"Iniciando proceso Trello para la operación {id_op}")
            trello_time = time.perf_counter()
            trello_archivos = pdf_files + respaldo_files
            result_trello = self.trello.execute(
                data_frontend,
                id_op,
                trello_archivos,
                url_drive=url_drive_str,
                cavali_resultados=cavali_resultados,
            )
            fin_trello = time.perf_counter()
            logging.info(
                f"Proceso Trello para la operación {id_op} terminado en {fin_trello - trello_time:.2f} segundos"
            )
        except Exception as e:
            logging.error(f"Error en el proceso Trello para la operación {id_op}: {e}")
            result_trello = {"error": str(e)}

        result = {
            "data_frontend": data_frontend,
            "cavali": cavali_resultados,
            "drive": drive,
            "drive_secundario": drive_s,
            "correo": email_usuario,
            "trello": result_trello,
        }
        logging.info(f"Resultado de la operación del robot ({id_op}): {result}")
        try:
            self.guardar_op.execute(result, id_op)
            logging.info(f"Operación {id_op} guardada exitosamente.")
        except Exception as e:
            logging.error(f"Error al guardar la operación {id_op}: {e}")

        return {
            "cavali": cavali_resultados,
            "drive": drive,
            "drive_secundario": drive_s,
            "correo": email_usuario,
            "trello": result_trello,
        }
