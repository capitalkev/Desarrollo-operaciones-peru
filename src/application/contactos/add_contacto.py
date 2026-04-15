from src.domain.interfaces import ContactosInterface


class AddContacto:
    def __init__(self, repository: ContactosInterface):
        self.repository = repository

    def execute(self, ruc_deudor: str, gmail: str) -> None:
        return self.repository.add_correo(ruc_deudor, gmail)
