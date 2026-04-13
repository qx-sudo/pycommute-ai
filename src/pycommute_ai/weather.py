"""Cliente de clima — primera llamada real a OpenWeather API."""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(city: str) -> dict:
    """Obtiene el clima actual de una ciudad.

    Args:
        city: Nombre de la ciudad.

    Returns:
        Dict con temperature, description y city.

    Raises:
        ValueError: Si la API key no esta configurada.
        httpx.HTTPError: Si la API devuelve un error.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise ValueError("OPENWEATHER_API_KEY no esta configurada en .env")

    response = httpx.get(
        BASE_URL,
        params={"q": city, "appid": api_key, "units": "metric"},
    )
    response.raise_for_status()
    data = response.json()

    return {
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"],
        "city": data["name"],
    }
