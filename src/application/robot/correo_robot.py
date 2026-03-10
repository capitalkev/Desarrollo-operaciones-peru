import io
from typing import Any

from src.infrastructure.correos.send_gmail import GmailService
from src.infrastructure.excel.gloria_excel import GloriaExcelService


class InMemoryFile:
    """Clase auxiliar para imitar la estructura de un UploadFile de FastAPI en memoria"""

    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self.file = io.BytesIO(content)


class CorreoOperacion:

    RUC_GLORIA = [
        "20100190797",
        "20600679164",
        "20312372895",
        "20524088739",
        "20467539842",
        "20506475288",
        "20418453177",
        "20512613218",
        "20115039262",
        "20100814162",
        "20518410858",
        "20101927904",
        "20479079006",
        "20100223555",
        "20532559147",
        "20487268870",
        "20562613545",
        "20478963719",
        "20481694907",
        "20454629516",
        "20512415840",
        "20602903193",
        "20392965191",
        "20601225639",
        "20547999691",
        "20600180631",
        "20116225779",
        "20131823020",
        "20601226015",
        "20131867744",
        "20603778180",
        "20131835621",
        "20511866210",
        "20481640483",
    ]

    def __init__(self) -> None:
        self.correo = GmailService()
        self.gloria_excel = GloriaExcelService()

    def execute(
        self,
        destinatarios: list,
        data_frontend: dict,
        archivos_adjuntos: list[Any],
        id_op: str,
    ) -> Any:
        return self.correo.enviar_email(
            pdfs=archivos_adjuntos,
            mails_verificacion=destinatarios,
            data_frontend=data_frontend,
            operation_id=id_op,
        )

    def _enviar_correos_verificacion(
        self, data_frontend: dict, id_op: str, pdf_files: list[Any]
    ) -> None:
        notificaciones = data_frontend.get("notificaciones", {})
        envio_conjunto = notificaciones.get("envio_conjunto")
        deudores = notificaciones.get("deudores", [])

        if envio_conjunto:
            destinatarios = notificaciones.get("emails_globales", [])
            archivos_a_enviar = list(pdf_files)

            deudores_gloria = [
                d for d in deudores if str(d.get("id")) in self.RUC_GLORIA
            ]

            if deudores_gloria:
                documentos_gloria = []
                for d in deudores_gloria:
                    documentos_gloria.extend(d.get("documentos", []))

                filename, excel_bytes = self.gloria_excel.generar_excel(
                    documentos_gloria
                )
                if filename and excel_bytes:
                    archivos_a_enviar.append(InMemoryFile(filename, excel_bytes))

            self.execute(
                destinatarios=destinatarios,
                data_frontend=data_frontend,
                archivos_adjuntos=archivos_a_enviar,
                id_op=id_op,
            )
        else:
            for deudor in deudores:
                destinatarios = deudor.get("emails", [])
                sustentos_nombres = deudor.get("sustentos", [])
                ruc_deudor = str(deudor.get("id", ""))

                archivos_a_enviar = [
                    pdf for pdf in pdf_files if pdf.filename in sustentos_nombres
                ]

                if ruc_deudor in self.RUC_GLORIA:
                    documentos_deudor = deudor.get("documentos", [])
                    filename, excel_bytes = self.gloria_excel.generar_excel(
                        documentos_deudor
                    )
                    if filename and excel_bytes:
                        archivos_a_enviar.append(InMemoryFile(filename, excel_bytes))

                data_frontend_individual = data_frontend.copy()
                data_frontend_individual["notificaciones"] = notificaciones.copy()
                data_frontend_individual["notificaciones"]["deudores"] = [deudor]

                self.execute(
                    destinatarios=destinatarios,
                    data_frontend=data_frontend_individual,
                    archivos_adjuntos=archivos_a_enviar,
                    id_op=id_op,
                )
