# Usa la versión 3.10 para soportar la sintaxis moderna de tipos
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Actualiza pip
RUN pip install --upgrade pip

# Copia e instala requerimientos
COPY requirements/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia la carpeta src dentro del contenedor
COPY src/ src/

# Ejecuta el servidor uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]