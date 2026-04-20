"""Router del endpoint GET /health."""

from fastapi import APIRouter

from pycommute_ai import __version__
from pycommute_ai.adapters.cache import MemoryCacheAdapter
from pycommute_ai.adapters.route import OpenRouteAdapter
from pycommute_ai.adapters.weather import OpenWeatherAdapter
from pycommute_ai.api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Estado del servicio y adaptadores configurados."""
    return HealthResponse(
        status="OK",
        version=__version__,
        adapters={
            "weather": OpenWeatherAdapter.__name__,
            "route": OpenRouteAdapter.__name__,
            "cache": MemoryCacheAdapter.__name__,
        },
    )
