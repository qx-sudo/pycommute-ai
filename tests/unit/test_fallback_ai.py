"""Tests del FallbackAIAdapter — patron de resiliencia."""

from unittest.mock import AsyncMock

import pytest
from pycommute_ai.adapters.fallback_ai import FallbackAIAdapter
from pycommute_ai.core.models import AIRecommendation, RouteData, WeatherData

ORIGIN_WEATHER = WeatherData(
    temperature=13.0, description="scattered clouds", city="Valencia"
)
DESTINATION_WEATHER = WeatherData(
    temperature=5.0, description="light snow", city="Madrid"
)
ROUTES = [RouteData(distance_km=350.0, duration_min=180.0, profile="driving-car")]

VALID_RECOMMENDATION = AIRecommendation(
    recommendation="Toma el coche, las condiciones son adversas para la bici",
    suggested_profile="driving-car",
    confidence="alta",
    reasoning="Nieve en Madrid hace peligroso cualquier otro transporte",
    outfit_tips=["abrigo", "guantes"],
    departure_advice="Salir antes de las 14h",
)

_KWARGS = dict(
    origin_city="Valencia",
    destination_city="Madrid",
    origin_weather=ORIGIN_WEATHER,
    destination_weather=DESTINATION_WEATHER,
    routes=ROUTES,
)


def _make_adapter(
    primary_result=None, primary_error=None, secondary_result=None, secondary_error=None
):
    primary = AsyncMock()
    secondary = AsyncMock()
    if primary_error:
        primary.get_recommendation = AsyncMock(side_effect=primary_error)
    else:
        primary.get_recommendation = AsyncMock(
            return_value=primary_result or VALID_RECOMMENDATION
        )
    if secondary_error:
        secondary.get_recommendation = AsyncMock(side_effect=secondary_error)
    else:
        secondary.get_recommendation = AsyncMock(
            return_value=secondary_result or VALID_RECOMMENDATION
        )
    return FallbackAIAdapter(primary=primary, secondary=secondary), primary, secondary


@pytest.mark.anyio
async def test_fallback_uses_primary_when_available():
    fallback, primary, secondary = _make_adapter()

    result = await fallback.get_recommendation(**_KWARGS)

    assert result == VALID_RECOMMENDATION
    primary.get_recommendation.assert_awaited_once()
    secondary.get_recommendation.assert_not_awaited()


@pytest.mark.anyio
async def test_fallback_switches_to_secondary_on_error():
    secondary_rec = AIRecommendation(
        recommendation="Recomendacion desde Ollama local para el viaje",
        suggested_profile="driving-car",
        confidence="media",
        reasoning="Fallback local activo",
        outfit_tips=["abrigo"],
        departure_advice="Salir pronto",
    )
    fallback, primary, secondary = _make_adapter(
        primary_error=ConnectionError("429 RESOURCE_EXHAUSTED"),
        secondary_result=secondary_rec,
    )

    result = await fallback.get_recommendation(**_KWARGS)

    assert result == secondary_rec
    assert result.confidence == "media"
    primary.get_recommendation.assert_awaited_once()
    secondary.get_recommendation.assert_awaited_once()


@pytest.mark.anyio
async def test_fallback_raises_if_both_fail():
    fallback, primary, secondary = _make_adapter(
        primary_error=ConnectionError("Gemini no disponible"),
        secondary_error=ConnectionError("Ollama no disponible"),
    )

    with pytest.raises(ConnectionError, match="Ollama no disponible"):
        await fallback.get_recommendation(**_KWARGS)


@pytest.mark.anyio
async def test_fallback_secondary_not_called_if_primary_succeeds():
    fallback, primary, secondary = _make_adapter()

    await fallback.get_recommendation(**_KWARGS)

    secondary.get_recommendation.assert_not_awaited()
