import base64
from collections.abc import Iterable
from typing import Any, BinaryIO, Protocol

from src.infrastructure.cavali.cavali import CavaliService


class _HasFile(Protocol):
    file: BinaryIO


class CavaliOperacion:
    def __init__(self) -> None:
        self.cavali = CavaliService()

    def execute(self, xmls: Iterable[_HasFile]) -> dict[str, Any]:
        xmls_b64_group: list[str] = []

        for xml in xmls:
            content: bytes = xml.file.read()
            content_b64 = base64.b64encode(content).decode("utf-8")
            xmls_b64_group.append(content_b64)

        return self.cavali.validar_estado_cavali(xmls_b64_group)
