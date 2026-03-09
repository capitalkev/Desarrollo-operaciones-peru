from firebase_admin import auth

from src.domain.interfaces import AuthInterface


class FirebaseTokenVerifier(AuthInterface):
    """
    Implementación de TokenVerifier usando Firebase Admin SDK
    """

    def __init__(self):
        pass

    def verify_token(self, token: str):
        try:
            decoded_token = auth.verify_id_token(token)

            return decoded_token.get("email")

        except Exception as e:
            raise ValueError(f"Token inválido o expirado: {e!s}")
