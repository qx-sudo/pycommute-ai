"""Tests del cliente de clima."""

import pytest
from hola_pycommute.weather import get_weather


def test_get_weather_raises_without_key(monkeypatch):
    """Verifica el manejo de API key faltante — no requiere internet."""
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENWEATHER_API_KEY"):
        get_weather("Valencia")
