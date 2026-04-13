"""Tests del GeminiAdapter — mockean la API de Gemini."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pycommute_ai.adapters.gemini import GeminiAdapter
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


def _load_fixture() -> str:
    return (FIXTURES / "gemini_response.json").read_text(encoding="utf-8")


@pytest.fixture
def adapter():
    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        yield GeminiAdapter(api_key="test-key"), mock_client


@pytest.mark.anyio
async def test_get_recommendation_returns_ai_recommendation(adapter):
    gemini, mock_client = adapter
    mock_response = MagicMock()
    mock_response.text = _load_fixture()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    result = await gemini.get_recommendation(
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


@pytest.mark.anyio
async def test_get_recommendation_cleans_markdown_json(adapter):
    gemini, mock_client = adapter
    raw_json = _load_fixture()
    mock_response = MagicMock()
    mock_response.text = f"```json\n{raw_json}\n```"
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    result = await gemini.get_recommendation(
        origin_city="Valencia",
        destination_city="Madrid",
        origin_weather=ORIGIN_WEATHER,
        destination_weather=DESTINATION_WEATHER,
        routes=ROUTES,
    )

    assert isinstance(result, AIRecommendation)
    assert result.suggested_profile == "driving-car"


@pytest.mark.anyio
async def test_build_prompt_includes_both_cities(adapter):
    gemini, _ = adapter

    prompt = gemini._build_prompt(
        origin_city="Valencia",
        destination_city="Madrid",
        origin_weather=ORIGIN_WEATHER,
        destination_weather=DESTINATION_WEATHER,
        routes=ROUTES,
    )

    assert "Valencia" in prompt
    assert "Madrid" in prompt
    assert "13.0" in prompt
    assert "5.0" in prompt
    assert "driving-car" in prompt
    assert "cycling-regular" in prompt
