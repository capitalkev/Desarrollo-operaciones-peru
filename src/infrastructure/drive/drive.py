import io
import os
from typing import Any, cast

from google.auth.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import Resource, build
from googleapiclient.http import MediaIoBaseUpload
from starlette.datastructures import UploadFile

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]


class DriveService:
    def get_drive_service(self) -> Resource:
        token_path = os.path.join(os.path.dirname(__file__), "service_account.json")

        creds: Credentials = service_account.Credentials.from_service_account_file(
            token_path, scopes=DRIVE_SCOPES
        )

        return build("drive", "v3", credentials=creds)

    def create_subfolder(
        self, servicio: Resource, operacion_id: str, carpeta_padre: str
    ) -> str:
        safe_name = operacion_id.replace("'", "\\'")
        query = (
            f"name='{safe_name}' and '{carpeta_padre}' in parents "
            "and mimeType='application/vnd.google-apps.folder' and trashed=false"
        )
        results = (
            servicio.files()
            .list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )

        files = results.get("files", [])
        if files:
            existing_id = files[0].get("id")
            if not existing_id:
                raise RuntimeError("Google Drive devolvió una carpeta sin id")
            return cast(str, existing_id)

        folder_metadata = {
            "name": operacion_id,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [carpeta_padre],
        }
        folder = (
            servicio.files()
            .create(body=folder_metadata, fields="id", supportsAllDrives=True)
            .execute()
        )

        folder_id = folder.get("id")
        if not folder_id:
            raise RuntimeError("Google Drive no devolvió el id de la carpeta creada")
        return cast(str, folder_id)

    def upload_file_to_drive(
        self,
        servicio: Resource,
        file_content: bytes,
        filename: str,
        carpeta_hijo: str,
        mime_type: str,
    ) -> dict[str, Any]:
        file_metadata = {"name": filename, "parents": [carpeta_hijo]}
        media = MediaIoBaseUpload(
            io.BytesIO(file_content),
            mimetype=mime_type,
            resumable=True,
        )

        file: dict[str, Any] = (
            servicio.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, name, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )

        return file

    def upload_to_folder(
        self,
        service: Resource,
        files: list[UploadFile],
        carpeta_hijo: str,
    ) -> dict[str, Any]:
        uploaded_files: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        for upload in files:
            try:
                filename = upload.filename or "upload.bin"
                upload.file.seek(0)
                content = upload.file.read()
                mime_type = upload.content_type or "application/octet-stream"

                result = self.upload_file_to_drive(
                    service, content, filename, carpeta_hijo, mime_type
                )

                uploaded_files.append(
                    {
                        "filename": filename,
                        "file_id": result.get("id"),
                        "web_view_link": result.get("webViewLink"),
                        "success": True,
                    }
                )

            except Exception as e:
                errors.append(
                    {
                        "filename": (upload.filename or "upload.bin"),
                        "error": str(e),
                        "success": False,
                    }
                )

        return {
            "success": len(errors) == 0,
            "total_files": len(files),
            "uploaded_count": len(uploaded_files),
            "error_count": len(errors),
            "errors": errors,
            "folder_id": carpeta_hijo,
            "drive_folder_url": f"https://drive.google.com/drive/folders/{carpeta_hijo}",
        }

    def upload_payloads_to_folder(
        self,
        service: Resource,
        payloads: list[dict[str, Any]],
        carpeta_hijo: str,
    ) -> dict[str, Any]:
        uploaded_files: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        for payload in payloads:
            try:
                filename = cast(str, payload.get("filename") or "upload.bin")
                content = cast(bytes, payload.get("content") or b"")
                mime_type = cast(
                    str, payload.get("mime_type") or "application/octet-stream"
                )

                result = self.upload_file_to_drive(
                    service, content, filename, carpeta_hijo, mime_type
                )

                uploaded_files.append(
                    {
                        "filename": filename,
                        "file_id": result.get("id"),
                        "web_view_link": result.get("webViewLink"),
                        "success": True,
                    }
                )
            except Exception as e:
                errors.append(
                    {
                        "filename": str(payload.get("filename") or "upload.bin"),
                        "error": str(e),
                        "success": False,
                    }
                )

        return {
            "success": len(errors) == 0,
            "total_files": len(payloads),
            "uploaded_count": len(uploaded_files),
            "error_count": len(errors),
            "uploaded_files": uploaded_files,
            "errors": errors,
            "folder_id": carpeta_hijo,
            "drive_folder_url": f"https://drive.google.com/drive/folders/{carpeta_hijo}",
        }
