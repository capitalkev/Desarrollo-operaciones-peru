from src.domain.interfaces import OperacionesInterface


class FindFacturas:
    def __init__(self, repository: OperacionesInterface):
        self.repository = repository

    def execute(self, id_operacion: str) -> list[dict]:
        return self.repository.get_facturas(id_operacion)
