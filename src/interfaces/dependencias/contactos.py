from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.contactos.add_contacto import AddContacto
from src.application.contactos.delete_contactos import DeleteContacto
from src.application.contactos.get_contacto import GetContacto
from src.infrastructure.postgresql.connection import get_db
from src.infrastructure.postgresql.repositories.contactos.contactos import (
    ContactoRepository,
)


def dp_add_contactos(db: Session = Depends(get_db)) -> AddContacto:
    repository = ContactoRepository(db)
    return AddContacto(repository)


def dp_contactos(db: Session = Depends(get_db)) -> GetContacto:
    repository = ContactoRepository(db)
    return GetContacto(repository)


def dp_delete_contactos(db: Session = Depends(get_db)) -> DeleteContacto:
    repository = ContactoRepository(db)
    return DeleteContacto(repository)
