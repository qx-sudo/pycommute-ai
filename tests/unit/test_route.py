"""Tests unitarios para pycommute_ai.adapters.route."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from pycommute_ai.adapters.route import OpenRouteAdapter
from pycommute_ai.core.models import RouteData

VALENCIA = (39.4697, -0.3763)
DESTINATION = (39.4870, -0.3560)


@pytest.mark.anyio
async def test_get_route_returns_route_data(mock_httpx_route: AsyncMock) -> None:
    """Verifica que get_route devuelve una instancia de RouteData."""
    adapter = OpenRouteAdapter()
    result = await adapter.get_route(
        VALENCIA, DESTINATION, "cycling-regular", "fake-key"
    )

    assert isinstance(result, RouteData)


@pytest.mark.anyio
async def test_get_route_converts_units_correctly(mock_httpx_route: AsyncMock) -> None:
    """Verifica la conversion de unidades: metros a km, segundos a minutos.

    El fixture route_valencia.json tiene distance=3200.5m y duration=720.3s,
    que deben convertirse a 3.2 km y 12 min.
    """
    adapter = OpenRouteAdapter()
    result = await adapter.get_route(
        VALENCIA, DESTINATION, "cycling-regular", "fake-key"
    )

    assert result.distance_km == 3.2
    assert result.duration_min == 12


@pytest.mark.anyio
async def test_get_route_preserves_profile(mock_httpx_route: AsyncMock) -> None:
    """Verifica que el perfil de ruta se preserva en el resultado."""
    adapter = OpenRouteAdapter()
    result = await adapter.get_route(VALENCIA, DESTINATION, "driving-car", "fake-key")

    assert result.profile == "driving-car"


@pytest.mark.anyio
async def test_get_route_raises_on_bad_key(mocker) -> None:
    """Verifica que HTTPStatusError se propaga con una API key invalida (403)."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "403 Forbidden",
        request=MagicMock(),
        response=MagicMock(status_code=403),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)
    mocker.patch(
        "pycommute_ai.adapters.route.httpx.AsyncClient", return_value=mock_client
    )

    with pytest.raises(httpx.HTTPStatusError):
        adapter = OpenRouteAdapter()
        await adapter.get_route(
            VALENCIA, DESTINATION, "cycling-regular", "key-invalida"
        )


@pytest.mark.parametrize(
    "profile",
    [
        "cycling-regular",
        "driving-car",
        "foot-walking",
    ],
)
@pytest.mark.anyio
async def test_get_route_accepts_valid_profiles(
    mock_httpx_route: AsyncMock, profile: str
) -> None:
    """Verifica que get_route acepta distintos perfiles y los preserva."""
    adapter = OpenRouteAdapter()
    result = await adapter.get_route(VALENCIA, DESTINATION, profile, "fake-key")

    assert result.profile == profile
