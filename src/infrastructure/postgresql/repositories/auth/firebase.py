from firebase_admin import auth
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.domain.interfaces import AuthInterface
from src.domain.models import AuthToken, Rol


class AuthRepository(AuthInterface):
    def __init__(self, db: Session):
        self.db = db

    def verify_token(self, token: str) -> AuthToken:
        """Verifica el token de Firebase y retorna un AuthToken con el email"""
        try:
            decoded_token = auth.verify_id_token(token)
            email = decoded_token.get("email")
            if not email:
                raise ValueError("Token no contiene email")
            return AuthToken(email=email)
        except Exception as e:
            raise ValueError(f"Token inválido o expirado: {e!s}") from None

    def find_by_email(self, email: str):
        """Busca un usuario por su email"""
        sql = """
            SELECT email, nombre, rol, ultimo_ingreso
            FROM usuarios
            WHERE email = :email
        """
        params = {"email": email}
        result = self.db.execute(text(sql), params)
        row = result.fetchone()

        if row:
            return dict(row._mapping)
        return None

    def create(self, email: str, nombre: str):
        if not nombre:
            nombre = email.split("@")[0]

        sql = """
            INSERT INTO usuarios (email, nombre, rol)
            VALUES (:email, :nombre, :rol)
            RETURNING email, nombre, rol
        """
        params = {"email": email, "nombre": nombre, "rol": Rol.VENTAS.value}

        try:
            result = self.db.execute(text(sql), params)
            self.db.commit()
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None
        except Exception as e:
            self.db.rollback()
            print(f"Error en la base de datos: {e}")
            raise
