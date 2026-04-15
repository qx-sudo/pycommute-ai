"""Router de los endpoints /commute."""

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from pycommute_ai.api.dependencies import get_commute_service, get_settings
from pycommute_ai.api.schemas import CommuteRequest, CommuteResponse, HistoryEntry
from pycommute_ai.services.commute import CommuteService

router = APIRouter(prefix="/commute")


@router.post("/", response_model=CommuteResponse)
async def get_commute(
    request: CommuteRequest,
    service: CommuteService = Depends(get_commute_service),
    cfg=Depends(get_settings),
) -> CommuteResponse:
    """Consulta clima, rutas y recomendacion IA para un viaje.

    Lanza 3 tareas en paralelo (clima origen, clima destino, rutas).
    La recomendacion IA es opcional via include_ai.
    """
    try:
        result = await service.get_commute_info(
            city=request.origin_city,
            destination_city=request.destination_city,
            profiles=request.profiles,
            weather_key=cfg.openweather_api_key,
            route_key=cfg.openrouteservice_api_key,
            google_key=cfg.google_api_key if request.include_ai else None,
        )
        return CommuteResponse(**result.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Error en POST /commute: {error}", error=str(e))
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/history", response_model=list[HistoryEntry])
async def get_history(
    n: int = 10,
    service: CommuteService = Depends(get_commute_service),
) -> list[HistoryEntry]:
    """Devuelve las ultimas N consultas del historial."""
    entries = service.history.get_recent(n)
    return [
        HistoryEntry(
            timestamp=e.timestamp.isoformat(),
            origin_city=e.city,
            profiles=e.profiles,
            best_profile=e.result.best_route.profile if e.result.best_route else None,
        )
        for e in entries
    ]
