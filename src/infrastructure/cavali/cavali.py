import contextlib
import json
import logging
import os
import time
from io import BytesIO
from typing import Any, Final

import requests  # pyright: ignore[reportMissingTypeStubs]
from dotenv import load_dotenv

from src.infrastructure.storage.s3_storage_service import S3Service

load_dotenv()

TOKEN_S3_KEY: Final[str] = "cavali_token.json"
TOKEN_EXPIRY_SKEW_SECONDS: Final[int] = 60
DEFAULT_AWS_REGION: Final[str] = "us-east-1"


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} no está configurado en el entorno")
    return value


class CavaliService:
    def __init__(self) -> None:
        self._log = logging.getLogger(__name__)

        self._token_url = _require_env("CAVALI_TOKEN_URL")
        self._client_id = _require_env("CAVALI_CLIENT_ID")
        self._client_secret = _require_env("CAVALI_CLIENT_SECRET")
        self._scope = os.getenv("CAVALI_SCOPE") or ""
        self._api_key = _require_env("CAVALI_API_KEY")
        self._block_url = _require_env("CAVALI_BLOCK_URL")
        self._status_url = _require_env("CAVALI_STATUS_URL")

        bucket_name = _require_env("AWS_S3_BUCKET_NAME")
        region = os.getenv("AWS_REGION") or DEFAULT_AWS_REGION
        self._s3 = S3Service(bucket_name, region_name=region)

    def get_cavali_token(self) -> dict[str, Any]:
        cached = self._read_cached_token()
        if cached is not None:
            self._log.info("Token válido obtenido desde S3.")
            return cached

        token = self._fetch_token()
        self._write_token(token)
        self._log.info("Nuevo token de Cavali guardado en S3.")
        return token

    def _read_cached_token(self) -> dict[str, Any] | None:
        try:
            token_bytes = self._s3.download_file(TOKEN_S3_KEY)
            data: Any = json.loads(token_bytes.decode("utf-8"))
            if not isinstance(data, dict):
                return None

            access_token = data.get("access_token")
            expires_at = data.get("expires_at", 0)
            if not isinstance(access_token, str) or not access_token:
                return None

            try:
                expires_at_f = float(expires_at)
            except (TypeError, ValueError):
                return None

            if expires_at_f <= (time.time() + TOKEN_EXPIRY_SKEW_SECONDS):
                return None

            return {"access_token": access_token, "expires_at": expires_at_f}
        except Exception as exc:
            self._log.info(
                "No se pudo leer token desde S3, se solicitará uno nuevo. Error: %s",
                exc,
            )
            return None

    def _fetch_token(self) -> dict[str, Any]:
        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": self._scope,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "x-api-key": self._api_key,
        }

        try:
            response = requests.post(
                self._token_url,
                data=data,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            token_data: Any = response.json()
        except requests.exceptions.RequestException as exc:
            self._log.error("Error al obtener token de Cavali: %s", exc)
            error_response: Any = getattr(exc, "response", None)
            if error_response is not None:
                with contextlib.suppress(Exception):
                    self._log.error("Respuesta de error: %s", error_response.text)
            raise

        if not isinstance(token_data, dict) or not token_data.get("access_token"):
            raise RuntimeError("Respuesta inválida al obtener token de Cavali")

        try:
            expires_in = int(token_data.get("expires_in", 3600))
        except (TypeError, ValueError):
            expires_in = 3600

        expires_at = time.time() + max(expires_in, 0)
        return {
            "access_token": str(token_data["access_token"]),
            "expires_at": expires_at,
        }

    def _write_token(self, token: dict[str, Any]) -> None:
        payload = json.dumps(token).encode("utf-8")
        self._s3.upload_file(
            BytesIO(payload), key=TOKEN_S3_KEY, content_type="application/json"
        )

    def _access_token(self) -> str:
        token = self.get_cavali_token()
        if isinstance(token, dict):
            return str(token.get("access_token") or "")
        return str(token or "")

    def validar_estado_cavali(self, xmls_base64: list[str]) -> dict[str, Any]:
        token = self._access_token()

        headers: dict[str, str] = {
            "Authorization": f"Bearer {token}",
            "x-api-key": self._api_key,
            "Content-Type": "application/json",
        }

        invoice_xml_list: list[dict[str, str]] = [
            {"name": f"xml_{i + 1}.xml", "fileXml": xml_b64}
            for i, xml_b64 in enumerate(xmls_base64)
        ]
        payload_bloqueo: dict[str, Any] = {
            "invoiceXMLDetail": {"invoiceXML": invoice_xml_list}
        }

        response_bloqueo = requests.post(
            self._block_url, json=payload_bloqueo, headers=headers, timeout=300
        )

        if response_bloqueo.status_code != 200:
            print("ERROR DE CAVALI DETALLADO:", response_bloqueo.text)

        response_bloqueo.raise_for_status()
        bloqueo_data: dict[str, Any] = response_bloqueo.json()

        # Agregar tiempo de espera

        id_proceso = bloqueo_data.get("response", {}).get("idProceso")
        if not id_proceso:
            raise RuntimeError(
                f"Cavali no retornó idProceso. Respuesta: {bloqueo_data}"
            )

        payload_estado: dict[str, Any] = {"ProcessFilter": {"idProcess": id_proceso}}
        response_estado = requests.post(
            self._status_url, json=payload_estado, headers=headers, timeout=300
        )
        response_estado.raise_for_status()
        estado_data: dict[str, Any] = response_estado.json()

        return {
            "estado_response": estado_data,
        }
