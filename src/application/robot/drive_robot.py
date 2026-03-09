from typing import Any

from src.infrastructure.drive.drive import DriveService


class DriveOperacion:
    def __init__(self) -> None:
        self.drive = DriveService()

    def execute_primero(
        self,
        operacion_id: str,
    ) -> dict[str, Any]:
        service = self.drive.get_drive_service()
        id_folder = self.drive.create_subfolder(
            service, operacion_id, "1dl5FE6wKk6aXfspFrjm5YuS9rHP92Q_5"
        )
        return {
            "success": True,
            "folder_id": id_folder,
        }

    def execute_secundario(
        self,
        documentos: list[Any],
        carpeta_hijo: str,
    ) -> dict[str, Any]:
        service = self.drive.get_drive_service()
        return self.drive.upload_to_folder(service, documentos, carpeta_hijo)
