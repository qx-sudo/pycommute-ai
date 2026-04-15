"""Schemas de entrada y salida de la API.

Separados de los modelos de dominio (core/models.py) porque
los contratos HTTP pueden evolucionar independientemente
de los contratos internos del sistema.

CommuteRequest/CommuteResponse definen lo que la API acepta y devuelve.
WeatherData/RouteData/AIRecommendation se reutilizan directamente —
sus contratos ya son estables y coinciden con lo que la API expone.
"""

from pydantic import BaseModel, Field

from pycommute_ai.core.models import AIRecommendation, RouteData, WeatherData


class CommuteRequest(BaseModel):
    """Cuerpo del POST /commute."""

    origin_city: str = Field(min_length=1, examples=["Valencia"])
    destination_city: str = Field(min_length=1, examples=["Madrid"])
    profiles: list[str] = Field(
        default=["driving-car", "cycling-regular"],
        examples=[["driving-car", "cycling-regular", "foot-walking"]],
    )
    include_ai: bool = Field(
        default=True,
        description="Incluir recomendacion de IA en la respuesta",
    )


class CommuteResponse(BaseModel):
    """Respuesta del POST /commute."""

    origin_city: str
    destination_city: str
    origin_weather: WeatherData
    destination_weather: WeatherData
    routes: list[RouteData]
    best_route: RouteData | None
    ai_recommendation: AIRecommendation | None = None


class HistoryEntry(BaseModel):
    """Entrada resumida del historial para GET /commute/history."""

    timestamp: str
    origin_city: str
    profiles: list[str]
    best_profile: str | None


class HealthResponse(BaseModel):
    """Respuesta del GET /health."""

    status: str
    version: str
    adapters: dict[str, str]


class CitiesResponse(BaseModel):
    """Respuesta del GET /cities."""

    cities: list[str]
    total: int
