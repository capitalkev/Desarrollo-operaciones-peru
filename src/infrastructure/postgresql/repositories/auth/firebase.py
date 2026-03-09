from firebase_admin import auth  # type: ignore
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.domain.interfaces import AuthInterface
from src.domain.models import AuthToken


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
            raise ValueError(f"Token inválido o expirado: {e!s}")

    def find_by_email(self, email: str):
        """Busca un usuario por su email"""
        sql = """
            SELECT id, email, nombre, rol, created_at
            FROM usuarios
            WHERE email = :email
        """
        params = {"email": email}
        result = self.db.execute(text(sql), params)
        row = result.fetchone()

        if row:
            return dict(row._mapping)
        return None

    def create(self, email: str, nombre: str = None):
        """Crea un nuevo usuario en la base de datos"""
        # Si no se proporciona nombre, usar la parte antes del @ del email
        if not nombre:
            nombre = email.split("@")[0]

        sql = """
            INSERT INTO usuarios (email, nombre, rol)
            VALUES (:email, :nombre, 'rol2')
            RETURNING id, email, nombre, rol, created_at
        """
        params = {"email": email, "nombre": nombre}

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
