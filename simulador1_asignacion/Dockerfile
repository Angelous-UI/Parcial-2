# ============================================================= #
#  Dockerfile - Simulador 1: Asignacion de Memoria
# ============================================================= #
# Empaqueta el simulador en una imagen reproducible. El proyecto
# usa SOLO la libreria estandar de Python, asi que no hace falta
# instalar dependencias (no hay requirements.txt).
# ------------------------------------------------------------- #

# 1) Imagen base: Python 3.13 en su variante "slim" (ligera).
FROM python:3.13-slim

# 2) Evita que Python genere archivos .pyc y fuerza que la salida
#    (print) se muestre inmediatamente, sin buffer. Esencial para
#    ver el menu de la CLI en tiempo real dentro del contenedor.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3) Directorio de trabajo dentro del contenedor.
WORKDIR /app

# 4) Copiamos TODO el proyecto al contenedor.
#    (.dockerignore excluye cache y archivos innecesarios.)
COPY . /app

# 5) Comando por defecto: modo INTERACTIVO (menu de consola).
#    Para el modo por lotes se sobreescribe al ejecutar, p. ej.:
#      docker run --rm sim1 python main.py --entrada datos/entrada.txt
CMD ["python", "main.py"]
