from src.infrastructure.xml.parser import extract_invoice_data


class XmlParserPeru:
    @staticmethod
    def extract_invoice_data(xml_content_bytes: bytes) -> dict:
        return extract_invoice_data(xml_content_bytes)
