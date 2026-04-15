"""Aplicacion FastAPI de PyCommute."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from loguru import logger

from pycommute_ai import __version__
from pycommute_ai.api.routers import cities, commute, health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup y shutdown del servidor."""
    logger.info("PyCommute API v{version} iniciando...", version=__version__)
    yield
    logger.info("PyCommute API cerrando...")


app = FastAPI(
    title="PyCommute API",
    description="Asesor de movilidad inteligente con IA hibrida (Gemini + Ollama fallback)",
    version=__version__,
    lifespan=lifespan,
)

app.include_router(health.router, tags=["health"])
app.include_router(cities.router, tags=["cities"])
app.include_router(commute.router, tags=["commute"])
