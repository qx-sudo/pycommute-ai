"""Tests unitarios para pycommute_ai.core.models."""

import pytest
from pycommute_ai.core.models import (
    AIRecommendation,
    CommuteResult,
    ConsultaEntry,
    RouteData,
    WeatherData,
)
from pydantic import ValidationError

ORIGIN_WEATHER = WeatherData(
    temperature=13.0, description="scattered clouds", city="Valencia"
)
DESTINATION_WEATHER = WeatherData(
    temperature=5.0, description="light snow", city="Madrid"
)
ROUTE_CYCLING = RouteData(distance_km=5.0, duration_min=22.0, profile="cycling-regular")
ROUTE_DRIVING = RouteData(distance_km=4.8, duration_min=5.0, profile="driving-car")


def _make_result(**kwargs) -> CommuteResult:
    defaults = dict(
        origin_city="Valencia",
        destination_city="Madrid",
        origin_weather=ORIGIN_WEATHER,
        destination_weather=DESTINATION_WEATHER,
        routes=[ROUTE_CYCLING],
    )
    defaults.update(kwargs)
    return CommuteResult(**defaults)


def test_weather_data_valid() -> None:
    """Verifica que WeatherData acepta datos validos y normaliza description."""
    w = WeatherData(temperature=13.5, description="Clear Sky", city="Valencia")

    assert w.temperature == 13.5
    assert w.description == "clear sky"  # normalizado a lowercase


def test_weather_data_invalid_temperature() -> None:
    """Verifica que temperatura fuera de rango lanza ValidationError."""
    with pytest.raises(ValidationError, match="Temperatura irrealista"):
        WeatherData(temperature=999.0, description="hot", city="Venus")


def test_route_data_invalid_profile() -> None:
    """Verifica que perfil no soportado lanza ValidationError."""
    with pytest.raises(ValidationError, match="Perfil invalido"):
        RouteData(distance_km=2.0, duration_min=8.0, profile="flying-car")


def test_commute_result_sets_best_route_automatically() -> None:
    """Verifica que CommuteResult calcula best_route en el model_validator."""
    result = _make_result(routes=[ROUTE_CYCLING, ROUTE_DRIVING])

    assert result.best_route is not None
    assert result.best_route.profile == "driving-car"  # menor duration_min (5 < 22)


def test_commute_result_has_origin_and_destination() -> None:
    """Verifica que CommuteResult tiene clima de origen y destino."""
    result = _make_result()

    assert result.origin_city == "Valencia"
    assert result.destination_city == "Madrid"
    assert result.origin_weather.city == "Valencia"
    assert result.destination_weather.city == "Madrid"


def test_consulta_entry_serializable() -> None:
    """Verifica que ConsultaEntry es serializable a dict con model_dump()."""
    result = _make_result()
    entry = ConsultaEntry(city="Valencia", profiles=["cycling-regular"], result=result)

    data = entry.model_dump()

    assert "timestamp" in data
    assert data["city"] == "Valencia"
    assert "result" in data


def test_ai_recommendation_valid() -> None:
    """Verifica que AIRecommendation acepta datos validos."""
    rec = AIRecommendation(
        recommendation="Toma el coche, hay nieve en Madrid y es lo mas seguro",
        suggested_profile="driving-car",
        confidence="Alta",  # mayuscula — debe normalizarse a lowercase
        reasoning="Nieve en destino hace inviable la bici",
        outfit_tips=["abrigo", "bufanda"],
        departure_advice="Salir antes de las 14h",
    )

    assert rec.confidence == "alta"  # normalizado a lowercase
    assert rec.suggested_profile == "driving-car"
    assert len(rec.outfit_tips) == 2


def test_ai_recommendation_invalid_confidence() -> None:
    """Verifica que confianza invalida lanza ValidationError."""
    with pytest.raises(ValidationError, match="Confianza invalida"):
        AIRecommendation(
            recommendation="Recomendacion valida con suficientes palabras",
            suggested_profile="driving-car",
            confidence="muy-alta",
            reasoning="Razonamiento",
        )


def test_ai_recommendation_invalid_profile() -> None:
    """Verifica que perfil sugerido invalido lanza ValidationError."""
    with pytest.raises(ValidationError, match="Perfil invalido"):
        AIRecommendation(
            recommendation="Recomendacion valida con suficientes palabras",
            suggested_profile="helicopter",
            confidence="alta",
            reasoning="Razonamiento",
        )
