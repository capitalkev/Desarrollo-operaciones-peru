import logging
import time
from typing import Any

from src.application.operaciones.create_id import CreateIdOperacion
from src.application.operaciones.create_op import CreateOperacion

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class RobotOperacion:
    def __init__(
        self, create_id_op: CreateIdOperacion, guardar_op: CreateOperacion
    ) -> None:
        self.create_id_op = create_id_op
        self.guardar_op = guardar_op

    def execute(
        self,
        data_frontend: dict[str, Any],
    ) -> str:
        notificaciones = data_frontend.get("notificaciones", {})
        email_usuario = notificaciones.get(
            "correo_remitente", "usuario@desconocido.com"
        )

        inicio = time.perf_counter()
        id_op = self.create_id_op.execute(email_usuario)
        fin = time.perf_counter()
        logging.info(
            f"ID de operación generado: {id_op} para el usuario: {email_usuario} en {fin - inicio:.2f} segundos"
        )
        return id_op
