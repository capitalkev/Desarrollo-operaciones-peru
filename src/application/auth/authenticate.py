from dataclasses import dataclass

from src.domain.interfaces import AuthInterface
from src.domain.models import AuthToken, User


@dataclass
class AuthenticateUserCommand:
    """
    Comando para autenticar un usuario
    """

    token: str
    require_db_user: bool = True


@dataclass
class AuthenticateUserResult:
    """
    Resultado de la autenticación
    """

    auth_token: AuthToken
    user: User | None = None


class AuthenticateUserUseCase:
    """
    Caso de uso: Autenticar usuario

    Flujo:
    1. Verificar token con Firebase
    2. Consultar usuario en BD si es necesario

    Este caso de uso centraliza toda la lógica de autenticación,
    evitando duplicación entre /sync y /me.
    """

    def __init__(self, repository: AuthInterface):
        self.repository = repository

    def execute(self, command: AuthenticateUserCommand) -> AuthenticateUserResult:
        """
        Ejecuta la autenticación

        Args:
            command: Comando con el token a verificar

        Returns:
            Resultado con el token verificado y usuario (si se consultó)

        Raises:
            ValueError: Si el token es inválido o el usuario no existe (cuando se requiere)
        """
        # 1. Verificar token con Firebase
        auth_token = self.repository.verify_token(command.token)

        # 2. Consultar usuario en BD solo si es necesario
        user = None
        if command.require_db_user:
            user_dict = self.repository.find_by_email(auth_token.email)

            if not user_dict:
                raise ValueError(
                    f"Usuario {auth_token.email} no existe en el sistema. "
                    "Debe sincronizarse primero."
                )

            # Convertir dict a User dataclass
            user = User(
                email=user_dict["email"],
                nombre=user_dict["nombre"],
                rol=user_dict["rol"],
                created_at=user_dict.get("created_at"),
            )

        return AuthenticateUserResult(auth_token=auth_token, user=user)
