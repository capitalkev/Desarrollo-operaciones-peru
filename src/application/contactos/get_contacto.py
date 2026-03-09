from src.domain.interfaces import ContactosInterface


class GetContacto:
    def __init__(self, repository: ContactosInterface):
        self.repository = repository

    def execute(self, ruc_deudor: str) -> list[dict]:
        return self.repository.get_contactos(ruc_deudor)
