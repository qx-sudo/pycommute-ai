"""Tests unitarios para pycommute_ai.services.commute."""

from unittest.mock import AsyncMock

import pytest
from pycommute_ai.adapters.cache import MemoryCacheAdapter
from pycommute_ai.core.models import (
    AIRecommendation,
    CommuteResult,
    RouteData,
    WeatherData,
)
from pycommute_ai.services.commute import CommuteService

ORIGIN_WEATHER = WeatherData(
    temperature=13.0, description="scattered clouds", city="Valencia"
)
DESTINATION_WEATHER = WeatherData(
    temperature=5.0, description="light snow", city="Madrid"
)
ROUTE_RESULT = RouteData(distance_km=3.2, duration_min=12.0, profile="cycling-regular")

AI_RESULT = AIRecommendation(
    recommendation="Toma el coche, hay nieve en Madrid y las condiciones son adversas",
    suggested_profile="driving-car",
    confidence="alta",
    reasoning="Nieve en destino hace inviable la bici",
    outfit_tips=["abrigo", "bufanda"],
    departure_advice="Salir antes de las 14h",
)


def _make_service(
    route_result: RouteData | None = None,
    ai_result: AIRecommendation | None = None,
) -> CommuteService:
    """Crea un CommuteService con adaptadores mockeados."""
    mock_weather = AsyncMock()
    mock_weather.get_current_weather = AsyncMock(
        side_effect=lambda city, key: (
            ORIGIN_WEATHER if city == "Valencia" else DESTINATION_WEATHER
        )
    )
    mock_route = AsyncMock()
    mock_route.get_route = AsyncMock(return_value=route_result or ROUTE_RESULT)

    mock_ai = None
    if ai_result is not None:
        mock_ai = AsyncMock()
        mock_ai.get_recommendation = AsyncMock(return_value=ai_result)

    return CommuteService(
        weather=mock_weather,
        route=mock_route,
        cache=MemoryCacheAdapter(),
        ai=mock_ai,
    )


@pytest.mark.anyio
async def test_get_commute_info_returns_commute_result() -> None:
    """Verifica que get_commute_info devuelve CommuteResult con ambos climas."""
    service = _make_service()

    result = await service.get_commute_info(
        city="Valencia",
        destination_city="Madrid",
        profiles=["cycling-regular"],
        weather_key="fake-key",
        route_key="fake-key",
    )

    assert isinstance(result, CommuteResult)
    assert result.origin_city == "Valencia"
    assert result.destination_city == "Madrid"
    assert result.origin_weather is not None
    assert result.destination_weather is not None
    assert len(result.routes) == 1


@pytest.mark.anyio
async def test_get_commute_info_parallel_execution() -> None:
    """Verifica que se obtiene una ruta por cada perfil solicitado."""
    service = _make_service()

    result = await service.get_commute_info(
        city="Valencia",
        destination_city="Madrid",
        profiles=["cycling-regular", "driving-car"],
        weather_key="fake-key",
        route_key="fake-key",
    )

    assert len(result.routes) == 2


@pytest.mark.anyio
async def test_get_commute_info_with_ai_recommendation() -> None:
    """Verifica que la recomendacion IA se adjunta al resultado si hay adaptador."""
    service = _make_service(ai_result=AI_RESULT)

    result = await service.get_commute_info(
        city="Valencia",
        destination_city="Madrid",
        profiles=["cycling-regular"],
        weather_key="fake-key",
        route_key="fake-key",
        google_key="fake-google-key",
    )

    assert result.ai_recommendation is not None
    assert result.ai_recommendation.suggested_profile == "driving-car"
    assert result.ai_recommendation.confidence == "alta"


@pytest.mark.anyio
async def test_get_commute_info_without_ai_omits_recommendation() -> None:
    """Verifica que sin adaptador IA la recomendacion es None."""
    service = _make_service()

    result = await service.get_commute_info(
        city="Valencia",
        destination_city="Madrid",
        profiles=["cycling-regular"],
        weather_key="fake-key",
        route_key="fake-key",
    )

    assert result.ai_recommendation is None
