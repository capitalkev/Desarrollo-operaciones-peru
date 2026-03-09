from src.domain.interfaces import OperacionesInterface


class GetAllOperaciones:
    def __init__(self, repository: OperacionesInterface):
        self.repository = repository

    def execute(self, gmail: str) -> list[dict]:
        return self.repository.get_operaciones(gmail)
