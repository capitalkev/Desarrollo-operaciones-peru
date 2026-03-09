from sqlalchemy import text
from sqlalchemy.orm import Session

from src.domain.interfaces import ContactosInterface


class ContactoRepository(ContactosInterface):
    def __init__(self, db: Session):
        self.db = db

    def get_contactos(self, ruc_deudor: str) -> list[dict]:
        sql = "SELECT email from contactos_ruc_correos where ruc = :ruc_deudor"
        result = self.db.execute(text(sql), {"ruc_deudor": ruc_deudor})
        return [dict(row._mapping) for row in result]

    def add_correo(self, ruc_deudor: str, gmail: str) -> None:
        sql = "INSERT INTO contactos_ruc_correos (ruc, email) VALUES (:ruc_deudor, :gmail)"
        self.db.execute(text(sql), {"ruc_deudor": ruc_deudor, "gmail": gmail})
        return self.db.commit()

    def delete_correo(self, ruc_deudor: str, gmail: str) -> None:
        sql = "DELETE FROM contactos_ruc_correos WHERE ruc = :ruc_deudor AND email = :gmail"
        self.db.execute(text(sql), {"ruc_deudor": ruc_deudor, "gmail": gmail})
        return self.db.commit()
