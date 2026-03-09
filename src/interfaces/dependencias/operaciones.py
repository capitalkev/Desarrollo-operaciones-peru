from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.operaciones.create_id import CreateIdOperacion
from src.application.operaciones.create_op import CreateOperacion
from src.application.operaciones.find import FindFacturas
from src.application.operaciones.get_all import GetAllOperaciones
from src.application.robot.operacion_robot import RobotOperacion
from src.infrastructure.postgresql.connection import get_db
from src.infrastructure.postgresql.repositories.operaciones.operaciones import (
    OperacionesRepository,
)


def dp_robot_operacion(db: Session = Depends(get_db)) -> RobotOperacion:
    repository = OperacionesRepository(db)
    create_id_op = CreateIdOperacion(repository)
    guardar_op = CreateOperacion(repository)
    return RobotOperacion(create_id_op=create_id_op, guardar_op=guardar_op)


def dp_operaciones(db: Session = Depends(get_db)) -> GetAllOperaciones:
    repository = OperacionesRepository(db)
    return GetAllOperaciones(repository)


def dp_facturas(db: Session = Depends(get_db)) -> FindFacturas:
    repository = OperacionesRepository(db)
    return FindFacturas(repository)
