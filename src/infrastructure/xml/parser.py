from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, cast

from lxml import etree

NS = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
}

EXPECTED_INVOICE_NAMESPACE = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"

VALID_CURRENCIES = {"PEN", "USD", "EUR"}


def _parse_xml_root(
    xml_content_bytes: bytes,
) -> tuple[etree._Element | None, str | None]:
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        recover=False,
        huge_tree=True,
        remove_blank_text=True,
    )

    # Primero intenta parsear bytes “tal cual” (lxml respeta el encoding declarado).
    try:
        return etree.fromstring(xml_content_bytes, parser=parser), None
    except etree.XMLSyntaxError:
        pass

    # Fallback: decodificación defensiva en casos con bytes raros/BOM.
    for encoding in ("iso-8859-1", "utf-8", "cp1252"):
        try:
            decoded = xml_content_bytes.decode(encoding).lstrip("\ufeff")
            return etree.fromstring(decoded.encode("utf-8"), parser=parser), None
        except (UnicodeDecodeError, etree.XMLSyntaxError):
            continue

    return None, "XML con encoding no válido o malformado"


def _xpath_first(root: etree._Element, xpath: str) -> Any | None:
    results = root.xpath(xpath, namespaces=NS)
    if isinstance(results, list):
        return results[0] if results else None
    return results


def _xpath_text(
    root: etree._Element, xpath: str, default: str | None = None
) -> str | None:
    value = _xpath_first(root, xpath)
    if value is None:
        return default

    text = value.text if isinstance(value, etree._Element) else str(value)

    text = text.strip() if text is not None else ""
    return text if text else default


def _parse_date_yyyy_mm_dd(value: str | None) -> tuple[datetime | None, str | None]:
    if not value:
        return None, None
    try:
        return datetime.strptime(value, "%Y-%m-%d"), None
    except ValueError:
        return None, f"Fecha inválida (esperado YYYY-MM-DD): {value}"


def _parse_float(value: str | None, *, field_name: str) -> tuple[float, str | None]:
    if value is None:
        return 0.0, None
    try:
        return float(value), None
    except (TypeError, ValueError):
        return 0.0, f"Valor numérico inválido para {field_name}: {value}"


def _get_currency(root: etree._Element) -> str:
    # Preferencia: DocumentCurrencyCode (si existe); fallback a currencyID del PayableAmount.
    currency_code = _xpath_text(root, ".//cbc:DocumentCurrencyCode")
    if currency_code:
        return currency_code

    payable_amount = _xpath_first(root, ".//cac:LegalMonetaryTotal/cbc:PayableAmount")
    if isinstance(payable_amount, etree._Element):
        currency_id = cast(str | None, payable_amount.get("currencyID"))
        return currency_id or "N/A"

    return "N/A"


def _validate_required_fields(root: etree._Element) -> str | None:
    required_fields = [
        ("./cbc:ID", "document_id"),
        (".//cbc:IssueDate", "issue_date"),
        (".//cac:LegalMonetaryTotal/cbc:PayableAmount", "total_amount"),
        (
            ".//cac:AccountingSupplierParty//cac:PartyLegalEntity/cbc:RegistrationName",
            "client_name",
        ),
        (
            ".//cac:AccountingCustomerParty//cac:PartyLegalEntity/cbc:RegistrationName",
            "debtor_name",
        ),
    ]

    for xpath, field_name in required_fields:
        if not _xpath_text(root, xpath):
            return f"Campo obligatorio faltante o vacío: {field_name} ({xpath})"
    return None


def _validate_currency(currency: str) -> str | None:
    if currency not in VALID_CURRENCIES:
        return f"Moneda no válida: {currency}. Válidas: {VALID_CURRENCIES}"
    return None


def _compute_due_date(
    issue_date: datetime | None, payment_form: str | None, due_date_str: str | None
) -> tuple[datetime | None, str | None]:
    due_date, due_date_error = _parse_date_yyyy_mm_dd(due_date_str)
    if due_date_error:
        return None, due_date_error

    if due_date is None:
        if issue_date is None:
            return None, None

        if payment_form and payment_form.lower() == "contado":
            return issue_date + timedelta(days=60), None
        return issue_date, None

    return due_date, None


def extract_invoice_data(xml_content_bytes: bytes) -> dict:
    """Parsea una factura UBL (Invoice-2) y devuelve un dict con datos normalizados."""

    root, error = _parse_xml_root(xml_content_bytes)
    if root is None:
        return {"error": error or "Error al parsear XML", "valid": False}

    root_ns = etree.QName(root).namespace
    if root_ns != EXPECTED_INVOICE_NAMESPACE:
        return {
            "error": f"XML no es factura UBL válida. Namespace: {root_ns}",
            "valid": False,
        }

    required_error = _validate_required_fields(root)
    if required_error:
        return {"error": required_error, "valid": False}

    currency = _get_currency(root)
    currency_error = _validate_currency(currency)
    if currency_error:
        return {"error": currency_error, "valid": False}

    issue_date_str = _xpath_text(root, ".//cbc:IssueDate")
    issue_date, issue_date_error = _parse_date_yyyy_mm_dd(issue_date_str)
    if issue_date_error:
        return {"error": issue_date_error, "valid": False}

    total_amount_str = _xpath_text(
        root, ".//cac:LegalMonetaryTotal/cbc:PayableAmount", "0"
    )

    total_amount, total_amount_error = _parse_float(
        total_amount_str, field_name="total_amount"
    )
    if total_amount_error:
        return {"error": total_amount_error, "valid": False}

    payment_form = _xpath_text(
        root, ".//cac:PaymentTerms[cbc:ID='FormaPago']/cbc:PaymentMeansID"
    )
    due_date_str = _xpath_text(root, ".//cac:PaymentTerms/cbc:PaymentDueDate")
    due_date, due_date_error = _compute_due_date(issue_date, payment_form, due_date_str)
    if due_date_error:
        return {"error": due_date_error, "valid": False}

    detraction_str = _xpath_text(
        root,
        ".//cac:PaymentTerms[cbc:ID='Detraccion']/cbc:PaymentPercent",
        "0",
    )
    detraction_amount, detraction_error = _parse_float(
        detraction_str, field_name="detraction_amount"
    )
    if detraction_error:
        return {"error": detraction_error, "valid": False}
    if detraction_amount < 0 or detraction_amount > 100:
        return {
            "error": f"Detracción fuera de rango (0-100): {detraction_amount}",
            "valid": False,
        }
    if detraction_amount < 1:
        detraction_amount *= 100
    net_amount = total_amount * (100 - detraction_amount) / 100

    return {
        "document_id": _xpath_text(root, "./cbc:ID"),
        "issue_date": issue_date.isoformat() if issue_date else None,
        "due_date": due_date.isoformat() if due_date else None,
        "currency": currency,
        "total_amount": total_amount,
        "net_amount": net_amount,
        "debtor_name": _xpath_text(
            root,
            ".//cac:AccountingCustomerParty//cac:PartyLegalEntity/cbc:RegistrationName",
        ),
        "debtor_ruc": _xpath_text(
            root, ".//cac:AccountingCustomerParty//cac:PartyIdentification/cbc:ID"
        ),
        "client_name": _xpath_text(
            root,
            ".//cac:AccountingSupplierParty//cac:PartyLegalEntity/cbc:RegistrationName",
        ),
        "client_ruc": _xpath_text(
            root, ".//cac:AccountingSupplierParty//cac:PartyIdentification/cbc:ID"
        ),
        "valid": True,
    }
