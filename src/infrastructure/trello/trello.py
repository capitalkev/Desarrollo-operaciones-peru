import logging
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_LIST_ID = os.getenv("TRELLO_LIST_ID")


class TrelloOperaciones:
    def trello_card(self, title, descripcion) -> str | None:
        if not TRELLO_API_KEY or not TRELLO_TOKEN or not TRELLO_LIST_ID:
            print("Error: Faltan las variables de entorno necesarias para Trello.")
            return None

        auth_params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}

        card_payload = {"idList": TRELLO_LIST_ID, "name": title, "desc": descripcion}
        url = "https://api.trello.com/1/cards"
        response = requests.post(url, params=auth_params, json=card_payload)
        if response.status_code != 200:
            return None

        card_data = response.json()
        card_id = card_data.get("id")

        if not card_id:
            return None

        return card_id

    def trello_title(self, data_frontend, id_op) -> str:
        notificaciones = data_frontend.get("notificaciones", {})
        cliente_name = notificaciones.get("nombre_cliente", "N/A")
        deudores = notificaciones.get("deudores", [])
        usuario_email = notificaciones.get("correo_remitente")

        # Extraer moneda del primer documento disponible
        currency = "PEN"  # Default
        if deudores and deudores[0].get("documentos"):
            currency = deudores[0]["documentos"][0].get("currency", "PEN")

        total_net_amount = sum(
            doc.get("net_amount", 0)
            for d in deudores
            for doc in d.get("documentos", [])
        )

        current_date = datetime.now().strftime("%d.%m")

        # Obtener nombre del ejecutivo
        ejecutivo_nombre = "N/A"
        if usuario_email:
            ejecutivo_nombre = usuario_email.split("@")[0].capitalize()

        # Nombres de deudores simplificados para el título
        nombres_deudores = " - ".join([d.get("nombre") for d in deudores])

        card_title = f"🤖 {current_date} // CLIENTE: {cliente_name} // DEUDOR: {nombres_deudores} // MONTO: {currency} {total_net_amount:,.2f} // {ejecutivo_nombre} // OP: {id_op}"
        return card_title

    def trello_descripcion(
        self,
        cavali_resultados,
        data_frontend,
        id_op,
        drive_folder_urlstr,
    ) -> str:
        # 1. Datos de Cierre y Condiciones
        cierre = data_frontend.get("cierre", {})
        condiciones = data_frontend.get("condiciones", {})

        anticipo = cierre.get("porcentaje_adelanto", 0)
        tasa = condiciones.get("tasa", "N/A")
        comision = condiciones.get("comision", "N/A")

        # 2. Procesar Deudores y Moneda
        notificaciones = data_frontend.get("notificaciones", {})
        deudores_list = notificaciones.get("deudores", [])

        currency = "PEN"
        deudores_str = ""
        total_net_amount = 0

        for d in deudores_list:
            deudores_str += f"\n* RUC {d.get('id')}: {d.get('nombre')}"
            for doc in d.get("documentos", []):
                total_net_amount += doc.get("net_amount", 0)
                currency = doc.get("currency", currency)

        # 3. Datos Bancarios
        cuenta = cierre.get("cuenta_desembolso", {})
        banco = cuenta.get("banco", "N/A")
        n_cuenta = cuenta.get("numero_cuenta", "N/A")
        tipo_cuenta = cuenta.get("tipo_cuenta", "N/A")

        # 4. Formatear CAVALI
        cavali_str = ""

        try:
            invoice_data = (
                cavali_resultados.get("estado_response", {})
                .get("response", {})
                .get("Process", {})
                .get("ProcessInvoiceDetail", {})
            )
            invoices = invoice_data.get("Invoice", [])

            if invoices:
                for inv in invoices:
                    serie = inv.get("serie", "S/S")
                    num = inv.get("numeration", "S/N")
                    msg = inv.get("message", "Sin mensaje")
                    cavali_str += f"\n* Factura {serie}-{num}: {msg}"
            else:
                cavali_str = "\n* Pendiente de registro o sin facturas"
        except Exception:
            cavali_str = "\n* Error al procesar datos de CAVALI"
        anticipo_str = f"# ANTICIPO PROPUESTO: {anticipo} %\n\n" if anticipo else ""
        # 5. Construcción del cuerpo (Markdown)
        descripcion = (
            f"{anticipo_str}"
            f"**ID Operación:** {id_op}\n\n"
            f"**Deudores:**{deudores_str}\n\n"
            f"**Tasa:** {tasa}\n"
            f"**Comisión:** {comision}\n"
            f"**Monto Operación:** {currency} {total_net_amount:,.2f}\n"
            f"**Carpeta Drive:** [Abrir en Google Drive]({drive_folder_urlstr})\n\n"
            f"**CAVALI:**{cavali_str}\n\n"
            f"**Cuenta bancaria:**\n"
            f"* **Banco:** {banco}\n"
            f"* **N°cuenta:** {n_cuenta}\n"
            f"* **Tipo cuenta:** {tipo_cuenta}\n\n"
        )

        return descripcion

    def add_comment_to_card(self, card_id: str, comment_text: str) -> dict | None:
        """Agrega un comentario a una tarjeta existente en Trello"""
        if not TRELLO_API_KEY or not TRELLO_TOKEN:
            return None

        url = f"https://api.trello.com/1/cards/{card_id}/actions/comments"
        params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN, "text": comment_text}

        response = requests.post(url, params=params)
        if response.status_code == 200:
            return response.json()
        return None

    def attach_files_to_card(self, card_id: str, files: list) -> dict:
        """
        Adjunta archivos a una tarjeta de Trello.

        Args:
            card_id: ID de la tarjeta de Trello
            files: Lista de archivos (UploadFile o paths strings)
        """
        if not TRELLO_API_KEY or not TRELLO_TOKEN:
            return {
                "success": False,
                "error": "Credenciales de Trello no configuradas",
                "total_files": len(files),
                "attached_count": 0,
                "error_count": len(files),
            }

        auth_params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
        url = f"https://api.trello.com/1/cards/{card_id}/attachments"

        errors = []

        for file in files:
            if isinstance(file, str):
                if not os.path.exists(file):
                    raise FileNotFoundError(f"Archivo no encontrado: {file}")
                with open(file, "rb") as f:
                    file_content = f.read()
                filename = os.path.basename(file)
            else:
                file.file.seek(0)
                file_content = file.file.read()
                filename = file.filename

            if not file_content:
                raise ValueError(f"Archivo vacío: {filename}")

            # Subir archivo a Trello
            files_payload = {"file": (filename, file_content)}
            response = requests.post(url, params=auth_params, files=files_payload)

            if response.status_code != 200:
                errors.append(
                    {
                        "filename": filename,
                        "error": f"Status {response.status_code}: {response.text}",
                        "success": False,
                    }
                )
                continue

            response_data = response.json()
            attachment_id = response_data.get("id")

        return {
            "attachment_id": attachment_id,
            "total_files": len(files),
            "error_count": len(errors),
            "errors": errors,
        }


"""
  "condiciones": {
    "tasa": 1,
    "comision": 2
  },
  "notificaciones": {
    "nombre_cliente": "PLAN B S.A.C.",
    "ruc_cliente": "20511804702",
    "correo_remitente": "kevin.tupac@capitalexpress.cl",
    "envio_conjunto": false,
    "emails_globales": [],
    "deudores": [
      {
        "id": "20566558247",
        "nombre": "DEC SERVICES S.A.C.",
        "emails": [
          "kevin.tupac@unmsm.edu"
        ],
        "documentos": [
          {
            "document_id": "F001-0001824",
            "issue_date": "2026-01-29T00:00:00",
            "due_date": "2026-03-15T00:00:00",
            "currency": "USD",
            "total_amount": 3245,
            "net_amount": 2855.6,
            "debtor_name": "DEC SERVICES S.A.C.",
            "debtor_ruc": "20566558247",
            "client_name": "PLAN B S.A.C.",
            "client_ruc": "20511804702",
            "valid": true,
            "source_filename": "20511804702-01-F001-0001824 (1).xml"
          }
        ],
        "sustentos": [
          "Fact. N°2187.pdf"
        ]
      },
      {
        "id": "20100127165",
        "nombre": "PROCTER & GAMBLE PERU S.R.L",
        "emails": [
          "kevi.d@da.com"
        ],
        "documentos": [
          {
            "document_id": "F001-0001829",
            "issue_date": "2026-02-11T00:00:00",
            "due_date": "2026-06-11T00:00:00",
            "currency": "PEN",
            "total_amount": 59944,
            "net_amount": 52750.72,
            "debtor_name": "PROCTER & GAMBLE PERU S.R.L",
            "debtor_ruc": "20100127165",
            "client_name": "PLAN B S.A.C.",
            "client_ruc": "20511804702",
            "valid": true,
            "source_filename": "20511804702-01-F001-0001829 (1).xml"
          }
        ],
        "sustentos": [
          "Fact.N°2188.pdf"
        ]
      }
    ]
  },
  "cierre": {
    "comentario": "test",
    "solicita_adelanto": true,
    "porcentaje_adelanto": 80,
    "cuenta_desembolso": {
      "banco": "BCP",
      "tipo_cuenta": "Ahorros",
      "moneda": "Soles",
      "numero_cuenta": "123456789"
    }
  }
}
"""
