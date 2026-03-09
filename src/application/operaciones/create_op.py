from src.domain.interfaces import OperacionesInterface


class CreateOperacion:
    def __init__(self, repository: OperacionesInterface):
        self.repository = repository

    def execute(self, result: dict, id_op: str) -> str:
        return self.repository.create_operacion(result, id_op)
