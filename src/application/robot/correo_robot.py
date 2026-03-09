from typing import Any

from src.infrastructure.correos.send_gmail import GmailService


class CorreoOperacion:
    def __init__(self) -> None:
        self.correo = GmailService()

    def execute(
        self, destinatarios: list, data_frontend: dict, pdf_files: list[Any], id_op: str
    ) -> Any:
        return self.correo.enviar_email(
            pdfs=pdf_files,
            mails_verificacion=destinatarios,
            data_frontend=data_frontend,
            operation_id=id_op,
        )

    def _enviar_correos_verificacion(
        self, data_frontend: dict, id_op: str, pdf_files: list[Any]
    ) -> None:
        notificaciones = data_frontend.get("notificaciones", {})
        envio_conjunto = notificaciones.get("envio_conjunto")

        if envio_conjunto:
            destinatarios = notificaciones.get("emails_globales", [])

            self.execute(
                destinatarios=destinatarios,
                data_frontend=data_frontend,
                pdf_files=pdf_files,
                id_op=id_op,
            )
        else:
            deudores = notificaciones.get("deudores", [])
            for deudor in deudores:
                destinatarios = deudor.get("emails", [])
                sustentos_nombres = deudor.get("sustentos", [])

                pdf_files_deudor = [
                    pdf for pdf in pdf_files if pdf.filename in sustentos_nombres
                ]
                data_frontend_individual = data_frontend.copy()
                data_frontend_individual["notificaciones"] = notificaciones.copy()
                data_frontend_individual["notificaciones"]["deudores"] = [deudor]

                self.execute(
                    destinatarios=destinatarios,
                    data_frontend=data_frontend_individual,
                    pdf_files=pdf_files_deudor,
                    id_op=id_op,
                )
