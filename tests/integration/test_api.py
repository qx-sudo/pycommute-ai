"""Tests de integracion de la API con TestClient.

Usa dependency_overrides para reemplazar get_commute_service() con un mock
sin patchear modulos. El router, la serializacion Pydantic y el manejo
de errores HTTP se prueban con llamadas HTTP reales al servidor de test.
"""

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from pycommute_ai.api.dependencies import get_commute_service, get_settings
from pycommute_ai.api.main import app
from pycommute_ai.core.models import CommuteResult, RouteData, WeatherData

_ORIGIN_WEATHER = WeatherData(
    temperature=13.0, description="clear sky", city="Valencia"
)
_DEST_WEATHER = WeatherData(temperature=5.0, description="clear sky", city="Madrid")
_ROUTES = [RouteData(distance_km=356.0, duration_min=218.0, profile="driving-car")]

_MOCK_RESULT = CommuteResult(
    origin_city="Valencia",
    destination_city="Madrid",
    origin_weather=_ORIGIN_WEATHER,
    destination_weather=_DEST_WEATHER,
    routes=_ROUTES,
)


def _mock_service() -> MagicMock:
    """Factory que devuelve un CommuteService mockeado."""
    service = MagicMock()
    service.history.get_recent.return_value = []
    service.get_commute_info = AsyncMock(return_value=_MOCK_RESULT)
    return service


def _mock_settings() -> MagicMock:
    """Settings minimos para tests — sin .env real."""
    cfg = MagicMock()
    cfg.openweather_api_key = "test-weather-key"
    cfg.openrouteservice_api_key = "test-route-key"
    cfg.google_api_key = "test-google-key"
    return cfg


app.dependency_overrides[get_commute_service] = _mock_service
app.dependency_overrides[get_settings] = _mock_settings
client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "adapters" in data


def test_cities_returns_list():
    response = client.get("/cities")
    assert response.status_code == 200
    data = response.json()
    assert "cities" in data
    assert len(data["cities"]) > 0
    assert data["total"] == len(data["cities"])
    assert "Valencia" in data["cities"]


def test_commute_returns_result():
    response = client.post(
        "/commute/",
        json={
            "origin_city": "Valencia",
            "destination_city": "Madrid",
            "profiles": ["driving-car"],
            "include_ai": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["origin_city"] == "Valencia"
    assert data["destination_city"] == "Madrid"
    assert "origin_weather" in data
    assert "destination_weather" in data
    assert len(data["routes"]) > 0


def test_commute_invalid_origin_city():
    response = client.post(
        "/commute/",
        json={
            "origin_city": "",
            "destination_city": "Madrid",
            "profiles": ["driving-car"],
        },
    )
    assert response.status_code == 422


def test_history_returns_list():
    response = client.get("/commute/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
