from src.domain.interfaces import AuthInterface


class SyncFirebase:
    def __init__(self, repository: AuthInterface):
        self.repository = repository

    def execute(self, firebase_token, nombre: str = None):
        """
        Sincroniza un usuario de Firebase con la base de datos.
        Si el usuario no existe, lo crea.
        """
        # Verificar el token de Firebase y obtener el AuthToken
        auth_token = self.repository.verify_token(firebase_token)

        # Buscar el usuario en la base de datos
        user = self.repository.find_by_email(auth_token.email)
        is_new = False

        # Si no existe, crear el usuario
        if not user:
            user = self.repository.create(auth_token.email, nombre)
            is_new = True

        return {"is_new": is_new, "user": user}
