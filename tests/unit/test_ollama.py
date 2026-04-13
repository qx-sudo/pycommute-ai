"""Tests del OllamaAdapter — mockean el cliente Ollama."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pycommute_ai.adapters.ollama_adapter import OllamaAdapter
from pycommute_ai.core.models import AIRecommendation, RouteData, WeatherData

FIXTURES = Path(__file__).parent.parent / "fixtures"

ORIGIN_WEATHER = WeatherData(
    temperature=13.0, description="scattered clouds", city="Valencia"
)
DESTINATION_WEATHER = WeatherData(
    temperature=5.0, description="light snow", city="Madrid"
)
ROUTES = [
    RouteData(distance_km=350.0, duration_min=180.0, profile="driving-car"),
    RouteData(distance_km=350.0, duration_min=1200.0, profile="cycling-regular"),
]

_VALID_RESPONSE = json.loads(
    (FIXTURES / "gemini_response.json").read_text(encoding="utf-8")
)


def _make_ollama_response(content: str) -> MagicMock:
    """Construye el objeto de respuesta que devuelve ollama.AsyncClient.chat()."""
    mock_response = MagicMock()
    mock_response.message.content = content
    return mock_response


@pytest.fixture
def adapter():
    with patch("ollama.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        yield OllamaAdapter(model="gemma3:1b"), mock_client


@pytest.mark.anyio
async def test_ollama_returns_valid_recommendation(adapter):
    ollama_adapter, mock_client = adapter
    mock_client.chat = AsyncMock(
        return_value=_make_ollama_response(json.dumps(_VALID_RESPONSE))
    )

    result = await ollama_adapter.get_recommendation(
        origin_city="Valencia",
        destination_city="Madrid",
        origin_weather=ORIGIN_WEATHER,
        destination_weather=DESTINATION_WEATHER,
        routes=ROUTES,
    )

    assert isinstance(result, AIRecommendation)
    assert result.suggested_profile == "driving-car"
    assert result.confidence == "alta"
    assert len(result.outfit_tips) > 0
    mock_client.chat.assert_awaited_once()


@pytest.mark.anyio
async def test_ollama_handles_markdown_in_response(adapter):
    ollama_adapter, mock_client = adapter
    raw_json = json.dumps(_VALID_RESPONSE)
    mock_client.chat = AsyncMock(
        return_value=_make_ollama_response(f"```json\n{raw_json}\n```")
    )

    result = await ollama_adapter.get_recommendation(
        origin_city="Valencia",
        destination_city="Madrid",
        origin_weather=ORIGIN_WEATHER,
        destination_weather=DESTINATION_WEATHER,
        routes=ROUTES,
    )

    assert isinstance(result, AIRecommendation)
    assert result.suggested_profile == "driving-car"


@pytest.mark.anyio
async def test_ollama_raises_on_connection_error(adapter):
    ollama_adapter, mock_client = adapter
    mock_client.chat = AsyncMock(
        side_effect=ConnectionError("Cannot connect to Ollama")
    )

    with pytest.raises(ConnectionError, match="Cannot connect to Ollama"):
        await ollama_adapter.get_recommendation(
            origin_city="Valencia",
            destination_city="Madrid",
            origin_weather=ORIGIN_WEATHER,
            destination_weather=DESTINATION_WEATHER,
            routes=ROUTES,
        )
