from __future__ import annotations

from typing import Any

from fastapi import UploadFile

from src.application.robot.xml_robot import XmlOperacion
from src.domain.interfaces import OperacionesInterface


class RobotOperacionExtractor:
    def __init__(self, operaciones_repo: OperacionesInterface) -> None:
        self.xml_parser = XmlOperacion(operaciones_repo)

    async def execute(self, xml_files: list[UploadFile]) -> list[dict[str, Any]]:
        return await self.xml_parser.execute(xml_files)
