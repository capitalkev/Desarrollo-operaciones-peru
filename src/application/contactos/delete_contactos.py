from src.domain.interfaces import ContactosInterface


class DeleteContacto:
    def __init__(self, repository: ContactosInterface):
        self.repository = repository

    def execute(self, ruc_deudor: str, gmail: str) -> None:
        self.repository.delete_correo(ruc_deudor, gmail)
