from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.contactos.add_contacto import AddContacto
from src.application.contactos.delete_contactos import DeleteContacto
from src.application.contactos.get_contacto import GetContacto
from src.infrastructure.postgresql.connection import get_db
from src.infrastructure.postgresql.repositories.contactos.contactos import (
    ContactoRepository,
)

DBSession = Annotated[Session, Depends(get_db)]


def dp_add_contactos(db: DBSession) -> AddContacto:
    return AddContacto(repository=ContactoRepository(db))


def dp_contactos(db: DBSession) -> GetContacto:
    return GetContacto(repository=ContactoRepository(db))


def dp_delete_contactos(db: DBSession) -> DeleteContacto:
    return DeleteContacto(repository=ContactoRepository(db))
