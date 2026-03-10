import time
from typing import Any

from typing_extensions import TypedDict

from src.application.operaciones.create_id import CreateIdOperacion
from src.application.operaciones.create_op import CreateOperacion
from src.application.robot.cavali_robot import CavaliOperacion
from src.application.robot.correo_robot import CorreoOperacion
from src.application.robot.drive_robot import DriveOperacion
from src.application.robot.trello_robot import TrelloOperacion


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
        # Crear id de la operacion OP-hoy-incremental
        email_usuario = "kevin.tupac@capitalexpress.cl"

        inicio = time.perf_counter()
        id_op = self.create_id_op.execute(email_usuario)
        fin = time.perf_counter()

        print(
            f"ID de operación generado: {id_op} para el usuario: {email_usuario} en {fin - inicio:.2f} segundos"
        )

        # 2. PROCESO CAVALI
        cavali_time = time.perf_counter()
        cavali_resultados = self.cavali.execute(xml_files)
        fin_cavali = time.perf_counter()
        print(f"Cavali Terminado en {fin_cavali - cavali_time:.2f} segundos")

        # 3. ENVIO DE CORREOS
        correos_time = time.perf_counter()
        self.correo._enviar_correos_verificacion(data_frontend, id_op, pdf_files)
        fin_correos = time.perf_counter()
        print(f"Correos enviados en {fin_correos - correos_time:.2f} segundos")

        # 4. SUBIR A DRIVE
        drive_time = time.perf_counter()
        drive = self.drive.execute_primero(operacion_id=id_op)
        fin_drive = time.perf_counter()
        print(f"Drive primario terminado en {fin_drive - drive_time:.2f} segundos")

        # 5. SUBIR A DRIVE SECUNDARIO
        drive_s_time = time.perf_counter()
        all_archivos = xml_files + pdf_files + respaldo_files
        drive_s = self.drive.execute_secundario(
            documentos=all_archivos, carpeta_hijo=str(drive.get("folder_id"))
        )
        fin_drive_s = time.perf_counter()
        print(
            f"Drive secundario terminado en {fin_drive_s - drive_s_time:.2f} segundos"
        )

        url_drive_str = str(drive_s.get("drive_folder_url", "https://drive.google.com"))

        # 6. PROCESO TRELLO
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
        print(f"Trello terminado en {fin_trello - trello_time:.2f} segundos")

        result = {
            "data_frontend": data_frontend,
            "cavali": cavali_resultados,
            "drive": drive,
            "drive_secundario": drive_s,
            "correo": email_usuario,
            "trello": result_trello,
        }
        print("Resultado de la operación del robot:", result)
        self.guardar_op.execute(result, id_op)

        return {
            "cavali": cavali_resultados,
            "drive": drive,
            "drive_secundario": drive_s,
            "correo": email_usuario,
            "trello": result_trello,
        }
