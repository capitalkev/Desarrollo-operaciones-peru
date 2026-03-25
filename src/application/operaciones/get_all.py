from src.domain.interfaces import OperacionesInterface


class GetAllOperaciones:
    def __init__(self, repository: OperacionesInterface):
        self.repository = repository

    def execute(self, gmail: str, is_admin: bool = False) -> list[dict]:
        return self.repository.get_operaciones(gmail, is_admin)
