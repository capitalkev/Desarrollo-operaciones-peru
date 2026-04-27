import io


class InMemoryFile:
    """Clase auxiliar para imitar la estructura de un UploadFile de FastAPI en memoria."""

    def __init__(
        self,
        filename: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ):
        self.filename = filename
        self.file = io.BytesIO(content)
        self.content_type = content_type
