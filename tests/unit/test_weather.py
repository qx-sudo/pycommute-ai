"""Tests unitarios para pycommute_ai.adapters.weather."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from pycommute_ai.adapters.weather import OpenWeatherAdapter
from pycommute_ai.core.models import WeatherData


@pytest.mark.anyio
async def test_get_weather_returns_weather_data(mock_httpx_weather: AsyncMock) -> None:
    """Verifica que get_current_weather devuelve una instancia de WeatherData."""
    adapter = OpenWeatherAdapter()
    result = await adapter.get_current_weather("Valencia", "fake-key")

    assert isinstance(result, WeatherData)


@pytest.mark.anyio
async def test_get_weather_returns_correct_types(mock_httpx_weather: AsyncMock) -> None:
    """Verifica que temperature es float, description y city son str."""
    adapter = OpenWeatherAdapter()
    result = await adapter.get_current_weather("Valencia", "fake-key")

    assert isinstance(result.temperature, float)
    assert isinstance(result.description, str)
    assert isinstance(result.city, str)


@pytest.mark.anyio
async def test_get_weather_raises_on_bad_key(mocker) -> None:
    """Verifica que HTTPStatusError se propaga con una API key invalida (401).

    Con @retry configurado para ConnectError/TimeoutException unicamente,
    un HTTPStatusError no se reintenta — falla en el primer intento.
    """
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401 Unauthorized",
        request=MagicMock(),
        response=MagicMock(status_code=401),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)
    mocker.patch(
        "pycommute_ai.adapters.weather.httpx.AsyncClient", return_value=mock_client
    )

    with pytest.raises(httpx.HTTPStatusError):
        adapter = OpenWeatherAdapter()
        await adapter.get_current_weather("Valencia", "key-invalida")


@pytest.mark.anyio
async def test_get_weather_raises_on_malformed_response(mocker) -> None:
    """Verifica que una respuesta sin las claves esperadas lanza ValueError."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"status": "ok"}  # sin 'main' ni 'weather'
    mock_response.raise_for_status.return_value = None
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)
    mocker.patch(
        "pycommute_ai.adapters.weather.httpx.AsyncClient", return_value=mock_client
    )

    with pytest.raises(ValueError, match="Respuesta inesperada"):
        adapter = OpenWeatherAdapter()
        await adapter.get_current_weather("Valencia", "fake-key")


@pytest.mark.parametrize("city", ["Valencia", "Madrid", "Barcelona"])
@pytest.mark.anyio
async def test_get_weather_accepts_any_city(
    mock_httpx_weather: AsyncMock, city: str
) -> None:
    """Verifica que el campo city del resultado refleja el argumento de entrada."""
    adapter = OpenWeatherAdapter()
    result = await adapter.get_current_weather(city, "fake-key")

    assert result.city == city
