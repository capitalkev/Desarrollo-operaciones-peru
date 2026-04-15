from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.operaciones.create_id import CreateIdOperacion
from src.application.operaciones.create_op import CreateOperacion
from src.application.operaciones.find import FindFacturas
from src.application.operaciones.get_all import GetAllOperaciones
from src.application.robot.operacion_extractor import RobotOperacionExtractor
from src.application.robot.operacion_robot import RobotOperacion
from src.infrastructure.postgresql.connection import get_db
from src.infrastructure.postgresql.repositories.operaciones.operaciones import (
    OperacionesRepository,
)

DBSession = Annotated[Session, Depends(get_db)]


def dp_robot_operacion(db: DBSession) -> RobotOperacion:
    create_id_op = CreateIdOperacion(repository=OperacionesRepository(db))
    guardar_op = CreateOperacion(repository=OperacionesRepository(db))
    return RobotOperacion(create_id_op=create_id_op, guardar_op=guardar_op)


def dp_operaciones(db: DBSession) -> GetAllOperaciones:
    return GetAllOperaciones(repository=OperacionesRepository(db))


def dp_facturas(db: DBSession) -> FindFacturas:
    return FindFacturas(repository=OperacionesRepository(db))


def dp_robot_extractor(db: DBSession) -> RobotOperacionExtractor:
    return RobotOperacionExtractor(repository=OperacionesRepository(db))
