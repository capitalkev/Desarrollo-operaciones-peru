from __future__ import annotations

from typing import Any

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, Field


class OperacionDeudorRequest(BaseModel):
    """DTO interno (aplicación) por deudor.

    Nota: FastAPI no puede parsear UploadFile dentro de un JSON automáticamente.
    Este modelo se instancia en el router luego de mapear filenames -> UploadFile.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    xml_data: dict[str, Any]
    xml_file: UploadFile
    pdf_files: list[UploadFile] = Field(default_factory=list)
    mails_verificacion: list[str] = Field(default_factory=list)
