from src.domain.interfaces import OperacionesInterface


class CreateIdOperacion:
    def __init__(self, repository: OperacionesInterface):
        self.repository = repository

    def execute(self, email_usuario: str) -> str:
        return self.repository.generar_id_operacion(email_usuario)
