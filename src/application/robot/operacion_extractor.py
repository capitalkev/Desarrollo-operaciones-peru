from __future__ import annotations

from typing import Any

from fastapi import UploadFile

from src.application.robot.xml_robot import XmlOperacion


class RobotOperacionExtractor:
    def __init__(self) -> None:
        self.xml_parser = XmlOperacion()

    async def execute(self, xml_files: list[UploadFile]) -> list[dict[str, Any]]:
        return await self.xml_parser.execute(xml_files)
