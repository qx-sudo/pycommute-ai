# Dockerfile — PyCommute AI
# Construye la imagen de la API FastAPI de PyCommute.
#
# Uso:
#   docker build -t pycommute_ai. .
#   docker run -p 8000:8000 pycommute_ai.
#
# O con Docker Compose (recomendado):
#   docker compose up --build

# ── Imagen base ──────────────────────────────────────────────────────────────
# python:3.12-slim = imagen oficial de Python 3.12, version "slim"
# "slim" significa: solo lo minimo para correr Python, sin herramientas de
# compilacion ni extras. Resultado: imagen mas pequena y mas segura.
FROM python:3.12-slim

# ── Directorio de trabajo ─────────────────────────────────────────────────────
# WORKDIR crea el directorio si no existe y hace cd a el.
# Todos los comandos siguientes (COPY, RUN, CMD) se ejecutan desde /app.
WORKDIR /app

# ── Instalar UV ───────────────────────────────────────────────────────────────
# UV es nuestro gestor de dependencias (el mismo que usamos en desarrollo).
# En lugar de instalarlo con pip, copiamos el binario directamente desde
# la imagen oficial de UV — mas rapido y sin dependencias adicionales.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# ── Copiar archivos de dependencias (primero, para aprovechar el cache) ───────
# Regla de oro de Docker: poner lo que cambia MENOS primero.
# pyproject.toml y uv.lock cambian solo cuando agregamos dependencias.
# El codigo fuente (src/) cambia en cada commit.
#
# Si copiamos las deps primero, Docker reutiliza esta capa en builds siguientes
# aunque el codigo haya cambiado — ahorramos tiempo en cada rebuild.
COPY pyproject.toml uv.lock ./

# ── Instalar dependencias ─────────────────────────────────────────────────────
# uv sync --frozen: instala exactamente lo que dice uv.lock (sin actualizar)
# --no-install-project: instala solo las dependencias, no el proyecto en si
# (lo instalaremos despues de copiar el codigo fuente)
RUN uv sync --frozen --no-install-project

# ── Copiar el codigo fuente ───────────────────────────────────────────────────
# Copiamos src/ DESPUES de instalar las deps.
# Asi, cambiar el codigo no invalida el cache de la capa de dependencias.
# Solo copiamos lo necesario para correr la app — sin tests, docs ni scripts.
#
# El build context es curso/ — src/ esta aqui directamente.
COPY src ./src

# ── Puerto ────────────────────────────────────────────────────────────────────
# EXPOSE es documentacion — le dice a Docker que la app usa el puerto 8000.
# No abre el puerto por si solo: eso lo hace -p en docker run o ports: en Compose.
EXPOSE 8000

# ── Comando de inicio ─────────────────────────────────────────────────────────
# CMD define el comando que se ejecuta cuando arranca el contenedor.
# Usamos la forma de lista (no string) para evitar que el shell interprete args.
#
# --host 0.0.0.0: acepta conexiones desde fuera del contenedor
#   (sin esto, solo escucharia en localhost dentro del contenedor)
# --port 8000: puerto en el que escucha uvicorn
CMD ["uv", "run", "uvicorn", "pycommute_ai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
