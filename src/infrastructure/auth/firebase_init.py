"""
Firebase Admin SDK Initialization
"""

import firebase_admin  # type: ignore
from firebase_admin import credentials  # type: ignore

from src.infrastructure.config import settings


def initialize_firebase():
    """Inicializa Firebase Admin SDK si no está inicializado"""
    if not firebase_admin._apps:
        cred_dict = settings.get_firebase_credentials()
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK inicializado correctamente")
