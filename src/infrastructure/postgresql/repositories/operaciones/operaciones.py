from datetime import date

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.interfaces import OperacionesInterface


class OperacionesRepository(OperacionesInterface):
    def __init__(self, db: Session):
        self.db = db

    def generar_id_operacion(self, email_usuario: str) -> str:
        """
        Genera un código de operación único y correlativo por día de forma segura
        para alta concurrencia, utilizando una tabla auxiliar 'contadores_diarios'.
        """
        today = date.today()
        hoy_str = today.strftime("%Y%m%d")
        prefijo = f"OP-{hoy_str}-"

        sql_siguiente_valor = """
            INSERT INTO contadores_diarios (fecha, ultimo_valor)
            VALUES (:fecha, 1)
            ON CONFLICT (fecha) DO UPDATE
            SET ultimo_valor = contadores_diarios.ultimo_valor + 1
            RETURNING ultimo_valor;
        """
        siguiente = self.db.execute(
            text(sql_siguiente_valor), {"fecha": today}
        ).scalar_one()

        codigo_operacion = f"{prefijo}{siguiente:03d}"

        sql_insert = """
            INSERT INTO operaciones (codigo_operacion, email_usuario)
            VALUES (:codigo_operacion, :email)
        """
        try:
            self.db.execute(
                text(sql_insert),
                {"codigo_operacion": codigo_operacion, "email": email_usuario},
            )
            self.db.commit()
            return codigo_operacion
        except IntegrityError as e:
            self.db.rollback()
            raise Exception(
                "No se pudo registrar la operación debido a un error de integridad."
            ) from e

    def get_operaciones(self, gmail: str) -> list[dict]:
        sql = "SELECT * FROM operaciones WHERE email_usuario = :gmail and estado != 'Otros' order by fecha_creacion desc limit 100"
        result = self.db.execute(text(sql), {"gmail": gmail})
        return [dict(row._mapping) for row in result]

    def get_facturas(self, id_operacion: str) -> list[dict]:
        sql = "select * from facturas where id_operacion = :id_operacion"
        result = self.db.execute(text(sql), {"id_operacion": id_operacion})
        return [dict(row._mapping) for row in result]

    def create_operacion(self, result: dict, id_op: str) -> str:
        try:
            data_front = result.get("data_frontend", {})
            condiciones = data_front.get("condiciones", {})
            notif = data_front.get("notificaciones", {})
            cierre = data_front.get("cierre", {})
            cuenta = cierre.get("cuenta_desembolso", {})
            url_drive = result.get("drive_secundario", {}).get("drive_folder_url", "")
            email_usuario = result.get("correo", "")

            # Extraer el nombre del ejecutivo del email (ej: kevin.tupac -> Kevin Tupac)
            nombre_ejecutivo = (
                " ".join(email_usuario.split("@")[0].split(".")).title()
                if email_usuario
                else ""
            )
            card_id = result.get("trello", {}).get("card_id", "")

            # Calcular monto sumatoria y obtener la moneda
            monto_sumatoria_total = 0.0
            moneda_sumatoria = "PEN"
            documentos = []

            for deudor in notif.get("deudores", []):
                for doc in deudor.get("documentos", []):
                    monto_sumatoria_total += float(doc.get("total_amount", 0))
                    moneda_sumatoria = doc.get("currency", moneda_sumatoria)
                    documentos.append(doc)

            sql_operacion = text(
                """
                UPDATE operaciones
                SET cliente_ruc = :cliente_ruc,
                    nombre_ejecutivo = :nombre_ejecutivo,
                    url_carpeta_drive = :url_carpeta_drive,
                    monto_sumatoria_total = :monto_sumatoria_total,
                    moneda_sumatoria = :moneda_sumatoria,
                    tasa_operacion = :tasa_operacion,
                    comision = :comision,
                    solicita_adelanto = :solicita_adelanto,
                    porcentaje_adelanto = :porcentaje_adelanto,
                    desembolso_banco = :desembolso_banco,
                    desembolso_tipo = :desembolso_tipo,
                    desembolso_moneda = :desembolso_moneda,
                    desembolso_numero = :desembolso_numero,
                    estado = :estado,
                    adelanto_express = :adelanto_express,
                    analista_asignado_email = :analista_asignado_email,
                    card_id = :card_id,
                    nombre_cliente = :nombre_cliente
                WHERE codigo_operacion = :codigo_operacion
                RETURNING id;
            """
            )

            params_operacion = {
                "codigo_operacion": id_op,
                "cliente_ruc": notif.get("ruc_cliente", ""),
                "nombre_ejecutivo": nombre_ejecutivo,
                "url_carpeta_drive": url_drive,
                "monto_sumatoria_total": monto_sumatoria_total,
                "moneda_sumatoria": moneda_sumatoria,
                "tasa_operacion": condiciones.get("tasa", 0.0),
                "comision": condiciones.get("comision", 0.0),
                "solicita_adelanto": str(
                    cierre.get("solicita_adelanto", False)
                ).lower(),
                "porcentaje_adelanto": cierre.get("porcentaje_adelanto", 0),
                "desembolso_banco": cuenta.get("banco", ""),
                "desembolso_tipo": cuenta.get("tipo_cuenta", ""),
                "desembolso_moneda": cuenta.get("moneda", ""),
                "desembolso_numero": cuenta.get("numero_cuenta", ""),
                "estado": "Ingresado",
                "adelanto_express": "false",
                "analista_asignado_email": "",
                "card_id": card_id,
                "nombre_cliente": notif.get("nombre_cliente", ""),
            }

            internal_id_operacion = self.db.execute(
                sql_operacion, params_operacion
            ).scalar()

            if not internal_id_operacion:
                raise ValueError(
                    f"No se encontró la operación con código {id_op} para actualizar."
                )

            cavali_process = (
                result.get("cavali", {})
                .get("estado_response", {})
                .get("response", {})
                .get("Process", {})
            )
            id_proceso_cavali = str(cavali_process.get("idProcess", ""))
            cavali_invoices = cavali_process.get("ProcessInvoiceDetail", {}).get(
                "Invoice", []
            )

            cavali_messages = {
                f"{inv.get('serie')}-{inv.get('numeration')}": inv.get("message", "")
                for inv in cavali_invoices
            }

            sql_factura = text(
                """
                INSERT INTO facturas (
                    numero_documento, deudor_ruc, fecha_emision, fecha_vencimiento, moneda,
                    monto_total, monto_neto, mensaje_cavali, id_proceso_cavali, estado, id_operacion, nombre_deudor
                ) VALUES (
                    :numero_documento, :deudor_ruc, :fecha_emision, :fecha_vencimiento, :moneda,
                    :monto_total, :monto_neto, :mensaje_cavali, :id_proceso_cavali, :estado, :id_operacion, :nombre_deudor
                );
            """
            )

            for doc in documentos:
                doc_id = doc.get("document_id", "")
                mensaje_cavali = cavali_messages.get(doc_id, "Sin mensaje Cavali")

                params_factura = {
                    "numero_documento": doc_id,
                    "deudor_ruc": doc.get("debtor_ruc", ""),
                    "fecha_emision": doc.get("issue_date"),
                    "fecha_vencimiento": doc.get("due_date"),
                    "moneda": doc.get("currency", "PEN"),
                    "monto_total": doc.get("total_amount", 0.0),
                    "monto_neto": doc.get("net_amount", 0.0),
                    "mensaje_cavali": mensaje_cavali,
                    "id_proceso_cavali": id_proceso_cavali,
                    "estado": "Ingresado",
                    "id_operacion": internal_id_operacion,
                    "nombre_deudor": doc.get("debtor_name", ""),
                }

                self.db.execute(sql_factura, params_factura)

            self.db.commit()
            return f"Operación {id_op} actualizada y facturas guardadas exitosamente."

        except IntegrityError:
            self.db.rollback()
            return f"Error de base de datos en la operación {id_op}"
        except Exception:
            self.db.rollback()
            return f"Error inesperado al procesar la operación {id_op}"

    def update_estado(self, id_operacion: str, nuevo_estado: str) -> None:
        sql = "UPDATE operaciones SET estado = :nuevo_estado WHERE codigo_operacion = :id_operacion"
        self.db.execute(
            text(sql), {"nuevo_estado": nuevo_estado, "id_operacion": id_operacion}
        )
        self.db.commit()

    def factura_duplicada(self, numero_factura: str, ruc_deudor: str) -> str | None:
        sql = """
            SELECT op.codigo_operacion
            FROM facturas fa
            JOIN operaciones op ON op.id = fa.id_operacion
            WHERE fa.numero_documento = :numero_factura
              AND fa.deudor_ruc = :ruc_deudor
            LIMIT 1
        """
        result = self.db.execute(
            text(sql), {"numero_factura": numero_factura, "ruc_deudor": ruc_deudor}
        ).scalar()

        return result
