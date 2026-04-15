"""Demo de la Clase 1 — Primera llamada real a OpenWeather.

Nota: demo actualizado en Clase 8 — OpenWeatherAdapter reemplaza get_current_weather standalone.
Nota: demo actualizado — get_current_weather() devuelve WeatherData (Pydantic) desde Clase 9.
Ver snapshots/clase_01/, clase_02/, clase_03/ para las versiones originales.
Ver snapshots/clase_01/ para la version original.

Nota: este script usa print() intencionalmente.
Loguru se introduce en la Clase 3 como mejora explícita.

Ejecutar:
    # Windows (PowerShell)
    uv run python scripts/demo_weather.py

    # Linux
    uv run python scripts/demo_weather.py
"""

import os

import anyio
from dotenv import load_dotenv

import pycommute_ai
from pycommute_ai.adapters.weather import OpenWeatherAdapter

# Carga las variables desde .env (Clase 3 reemplazará esto con pydantic-settings)
load_dotenv()

CITY = "Valencia"


async def main() -> None:
    """Ejecuta la demo de consulta de clima."""
    print(f"[INFO] PyCommute v{pycommute_ai.__version__} iniciado")

    api_key = os.getenv("OPENWEATHER_API_KEY")
    assert api_key, "OPENWEATHER_API_KEY no encontrada en .env"

    try:
        adapter = OpenWeatherAdapter()
        weather = await adapter.get_current_weather(CITY, api_key)
        temp = weather.temperature
        desc = weather.description
        print(f"[INFO] Clima en {CITY}: {temp:.0f}°C, {desc}")
    except Exception as e:
        print(f"[ERROR] No se pudo obtener el clima: {e}")
        raise


anyio.run(main)
