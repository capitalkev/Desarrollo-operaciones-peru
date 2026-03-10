import base64
import logging
import os
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import pandas as pd
from fastapi import UploadFile
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build  # type: ignore
from googleapiclient.errors import HttpError  # type: ignore

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

CORREOS_AGENTES = [
    "jakeline.quispe@capitalexpress.pe",
    "jenssy.huaman@capitalexpress.pe",
    "jhonny.celay@capitalexpress.pe",
    "kevin.tupac@capitalexpress.cl",
    "guillermo.lopez@capitalexpress.pe",
    "manuel.seminario@capitalexpress.pe",
    "jose.mego@capitalexpress.pe",
]


class GmailService:
    def autenticar_gmail(self) -> Resource:
        token_path = os.path.join(os.path.dirname(__file__), "token.json")

        if not os.path.exists(token_path):
            raise FileNotFoundError(f"token.json not found at: {token_path}")

        creds: Credentials = Credentials.from_authorized_user_file(token_path, SCOPES)
        return build("gmail", "v1", credentials=creds)

    def enviar_email(
        self,
        operation_id: str,
        pdfs: list[UploadFile],
        mails_verificacion: list[str],
        data_frontend: dict,
    ) -> bool:
        try:
            service = self.autenticar_gmail()
            lista_destinatarios = CORREOS_AGENTES
            mensaje = MIMEMultipart()
            destinatarios = mails_verificacion if mails_verificacion is not None else []
            mensaje["to"] = ", ".join(destinatarios)
            mensaje["cc"] = ", ".join(CORREOS_AGENTES)
            mensaje["from"] = "me"
            notificaciones = data_frontend.get("notificaciones", {})
            cliente = notificaciones.get("nombre_cliente", "N/A")
            mensaje["subject"] = f"Confirmación de Facturas Negociables - {cliente}"
            html_data = data_frontend if data_frontend is not None else {}
            cuerpo = self.create_html_body(html_data, operation_id)
            mensaje.attach(MIMEText(cuerpo, "html"))

            if pdfs:
                for file in pdfs:
                    try:
                        file.file.seek(0)

                        contenido_pdf = file.file.read()

                        if not contenido_pdf:
                            logger.warning(f"Archivo vacío, omitiendo: {file.filename}")
                            continue
                        parte = MIMEBase("application", "octet-stream")
                        parte.set_payload(contenido_pdf)

                        encoders.encode_base64(parte)

                        filename_safe = file.filename
                        parte.add_header(
                            "Content-Disposition", "attachment", filename=filename_safe
                        )
                        mensaje.attach(parte)

                        logger.info(f"PDF adjuntado: {file.filename}")

                    except Exception:
                        logger.exception(
                            "Error al adjuntar %s",
                            getattr(file, "filename", "(sin nombre)"),
                        )

            resultado = self.enviar_mensaje_gmail(service, mensaje)
            if resultado:
                mensaje_id = resultado["id"]
                thread_id = resultado.get("threadId")
                logger.info(
                    f"Correo enviado a {len(lista_destinatarios)} destinatario(s). ID: {mensaje_id}"
                )
                logger.debug("Thread ID: %s", thread_id)
                return True
            logger.warning("No se pudo enviar el correo")
            return False

        except Exception:
            logger.exception("Error al enviar correo")
            return False

    def enviar_mensaje_gmail(
        self,
        service: Resource,
        message: MIMEMultipart,
        thread_id: str | None = None,
    ) -> dict[str, Any] | None:
        try:
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            body: dict[str, Any] = {"raw": encoded_message}

            if thread_id:
                body["threadId"] = thread_id

            message_sent: dict[str, Any] = (
                service.users().messages().send(userId="me", body=body).execute()
            )

            return message_sent
        except HttpError:
            logger.warning(
                "Error Gmail API (HttpError) al enviar mensaje", exc_info=True
            )
            return None
        except Exception:
            logger.exception("Error inesperado enviando mensaje vía Gmail API")
            return None

    def create_html_body(self, data_frontend: dict, operation_id: str) -> str:
        """
        Crea el cuerpo HTML del correo procesando la estructura anidada de deudores y documentos.
        """
        # 1. Extraer datos globales del cliente
        notificaciones = data_frontend.get("notificaciones", {})
        client_name = notificaciones.get("nombre_cliente", "N/A")
        client_ruc = notificaciones.get("ruc_cliente", "N/A")
        deudores = notificaciones.get("deudores", [])

        # 2. Aplanar la data para la tabla (Deudores -> Documentos)
        table_rows = []
        for deudor in deudores:
            # Extraemos información del deudor para repetirla en cada fila de sus documentos
            nombre_deudor = deudor.get("nombre", "N/A")
            ruc_deudor = deudor.get("id", "N/A")

            for inv in deudor.get("documentos", []):
                # Limpieza de fecha
                fecha_pago = inv.get("due_date", "")
                if "T" in str(fecha_pago):
                    fecha_pago = str(fecha_pago).split("T")[0]

                # Formateo de montos con moneda
                currency = inv.get("currency", "")
                monto_factura = f"{currency} {inv.get('total_amount', 0):,.2f}"
                monto_neto = f"{currency} {inv.get('net_amount', 0):,.2f}"

                table_rows.append(
                    {
                        "RUC Deudor": ruc_deudor,
                        "Nombre Deudor": nombre_deudor,
                        "Documento": inv.get("document_id"),
                        "Monto Factura": monto_factura,
                        "Monto Neto": monto_neto,
                        "Fecha de Pago": fecha_pago,
                    }
                )

        # 3. Generar la tabla HTML con Pandas
        df_display = pd.DataFrame(table_rows)
        tabla_html = df_display.to_html(
            index=False, border=1, justify="left", classes="invoice_table"
        )

        # 4. Construir el mensaje final
        mensaje_html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, Helvetica, sans-serif; font-size: 13px; color: #000; }}
            .container {{ max-width: 800px; }}
            p, li {{ line-height: 1.5; }}
            table.invoice_table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 20px; }}
            table.invoice_table th, table.invoice_table td {{ border: 1px solid #777; padding: 6px; text-align: left; font-size: 12px; }}
            table.invoice_table th {{ background-color: #f0f0f0; font-weight: bold; }}
            .disclaimer {{ font-style: italic; font-size: 11px; color: #555; margin-top: 25px; border-top: 1px solid #ccc; padding-top: 10px; }}
        </style>
        </head>
        <body>
        <div class="container">
            <p>Estimados señores,</p>
            <p>Por medio de la presente, les informamos que los señores de <strong>{client_name}</strong>, nos han transferido la(s) siguiente(s) factura(s) negociable(s). Solicitamos su amable confirmación sobre los siguientes puntos:</p>
            <ol>
                <li>¿La(s) factura(s) ha(n) sido recepcionada(s) conforme con sus productos o servicios?</li>
                <li>¿Cuál es la fecha programada para el pago de la(s) misma(s)?</li>
                <li>Por favor, confirmar el Monto Neto a pagar, considerando detracciones, retenciones u otros descuentos.</li>
            </ol>
            <p><strong>Detalle de las facturas:</strong></p>
            <p>Cliente: {client_name}<br>
            RUC Cliente: {client_ruc}</p>

            {tabla_html}

            <p>Agradecemos de antemano su pronta respuesta. Con su confirmación, procederemos a la anotación en cuenta en CAVALI.</p>
            <p class="disclaimer">"Sin perjuicio de lo anteriormente mencionado, nos permitimos recordarles que toda acción tendiente a simular la emisión de la referida factura negociable o letra para obtener un beneficio a título personal o a favor de la otra parte de la relación comercial, teniendo pleno conocimiento de que la misma no proviene de una relación comercial verdadera, se encuentra sancionada penalmente como delito de estafa en nuestro ordenamiento jurídico. Asimismo, en caso de que vuestra representada cometa un delito de forma conjunta y/o en contubernio con el emitente de la factura, dicha acción podría tipificarse como delito de asociación ilícita para delinquir, según el artículo 317 del Código Penal, por lo que nos reservamos el derecho de iniciar las acciones penales correspondientes en caso resulte necesario"</p>
            <p><small>ID de Operación: {operation_id}</small></p>
        </div>
        </body>
        </html>
        """
        return mensaje_html
