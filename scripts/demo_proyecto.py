"""Demo de la Clase 2 — match/case sobre dos APIs reales.

Nota: demo actualizado en Clase 5 — get_current_weather y get_route son ahora async.
Nota: demo actualizado en Clase 8 — OpenWeatherAdapter y OpenRouteAdapter reemplazan
      las funciones standalone. Ver snapshots/clase_02/ para la version original.
Nota: demo actualizado — get_current_weather() devuelve WeatherData (Pydantic) desde Clase 9.
Nota: demo actualizado — get_route() devuelve RouteData (Pydantic) desde Clase 9.
Ver snapshots/clase_01/, clase_02/, clase_03/ para las versiones originales.

Nota: este script usa print() intencionalmente.
Loguru se introduce en la Clase 3 como mejora explícita.

Ejecutar:
    # Windows (PowerShell)
    uv run python scripts/demo_proyecto.py

    # Linux
    uv run python scripts/demo_proyecto.py
"""

import os

import anyio
from dotenv import load_dotenv

import pycommute_ai
from pycommute_ai.adapters.route import OpenRouteAdapter
from pycommute_ai.adapters.weather import OpenWeatherAdapter

load_dotenv()

CITY = "Valencia"
# Coordenadas (lat, lon): Valencia centro → barrio del Carmen
ORIGIN = (39.4697, -0.3763)
DESTINATION = (39.4756, -0.3884)

PROFILE_LABELS = {
    "cycling-regular": "bicicleta",
    "driving-car": "coche",
}


async def main() -> None:
    """Ejecuta la demo de clima y rutas."""
    print(f"[INFO] PyCommute v{pycommute_ai.__version__} iniciado")

    weather_key = os.getenv("OPENWEATHER_API_KEY")
    assert weather_key, "OPENWEATHER_API_KEY no encontrada en .env"

    route_key = os.getenv("OPENROUTESERVICE_API_KEY")
    assert route_key, "OPENROUTESERVICE_API_KEY no encontrada en .env"

    weather_adapter = OpenWeatherAdapter()
    route_adapter = OpenRouteAdapter()

    try:
        weather = await weather_adapter.get_current_weather(CITY, weather_key)
        temp = weather.temperature
        desc = weather.description
        print(f"[INFO] Clima en {CITY}: {temp:.0f}°C, {desc}")
    except Exception as e:
        print(f"[ERROR] No se pudo obtener el clima: {e}")
        raise

    for profile in ["cycling-regular", "driving-car"]:
        try:
            route = await route_adapter.get_route(
                ORIGIN, DESTINATION, profile, route_key
            )
            label = PROFILE_LABELS[profile]
            print(
                f"[INFO] Ruta encontrada: {route.distance_km} km, "
                f"{route.duration_min} min en {label}"
            )
        except Exception as e:
            print(f"[ERROR] No se pudo obtener la ruta ({profile}): {e}")
            raise


anyio.run(main)
