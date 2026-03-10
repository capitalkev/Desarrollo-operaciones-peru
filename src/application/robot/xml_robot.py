from typing import Any

from fastapi import UploadFile

from src.domain.interfaces import OperacionesInterface
from src.infrastructure.xml.main import XmlParserPeru


class XmlOperacion:
    def __init__(self, operaciones_repo: OperacionesInterface) -> None:
        self.xml_parser = XmlParserPeru()
        self.operaciones_repo = operaciones_repo

    async def execute(self, files: list[UploadFile]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        for upload in files:
            content: bytes = await upload.read()
            invoice_data: Any = self.xml_parser.extract_invoice_data(content)
            if isinstance(invoice_data, dict):
                invoice_data.setdefault("source_filename", upload.filename)
                results.append(invoice_data)
            else:
                results.append(
                    {"error": "Respuesta inesperada del parser", "valid": False}
                )

        for result in results:
            if not result.get("valid"):
                continue

            numero_documento = str(result.get("document_id", ""))
            ruc_deudor = str(result.get("debtor_ruc", ""))

            if numero_documento and ruc_deudor:
                continuar = self.operaciones_repo.factura_duplicada(
                    numero_documento, ruc_deudor
                )

                if continuar is not None:
                    result["error"] = (
                        f"Factura duplicada. Ya existe en la operación: {continuar}"
                    )
                    result["valid"] = False
        print("Resultados procesados:", results)
        return results
