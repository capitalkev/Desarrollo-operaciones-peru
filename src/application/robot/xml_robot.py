from typing import Any

from fastapi import UploadFile

from src.infrastructure.xml.main import XmlParserPeru


class XmlOperacion:
    def __init__(self) -> None:
        self.xml_parser = XmlParserPeru()

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

        return results
