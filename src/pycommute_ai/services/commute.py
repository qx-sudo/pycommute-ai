"""Servicio de movilidad — orquesta usando puertos inyectados."""

from typing import Any, AsyncGenerator

import anyio
from loguru import logger

from pycommute_ai.core.history import ConsultaHistory
from pycommute_ai.core.models import CommuteResult, ConsultaEntry, RouteData
from pycommute_ai.core.ports import AIPort, CachePort, RoutePort, WeatherPort
from pycommute_ai.core.ranking import rank_routes_by_time


class CommuteService:
    """Servicio principal de PyCommute.

    Recibe los adaptadores por inyeccion de dependencias —
    no sabe si consulta OpenWeather, un mock o cualquier otra fuente.
    La logica de negocio esta aqui; las implementaciones concretas,
    en los adaptadores.
    """

    def __init__(
        self,
        weather: WeatherPort,
        route: RoutePort,
        cache: CachePort,
        history: ConsultaHistory | None = None,
        ai: AIPort | None = None,
    ) -> None:
        """Inicializa el servicio con sus dependencias.

        Args:
            weather: Adaptador de clima (implementa WeatherPort).
            route: Adaptador de rutas (implementa RoutePort).
            cache: Adaptador de coordenadas (implementa CachePort).
            history: Historial de consultas. Si None, crea uno nuevo.
            ai: Adaptador de IA para recomendaciones. Opcional.
        """
        self._weather = weather
        self._route = route
        self._cache = cache
        self._history = history or ConsultaHistory()
        self._ai = ai

    async def get_commute_info(
        self,
        city: str,
        destination_city: str,
        profiles: list[str],
        weather_key: str,
        route_key: str,
        google_key: str | None = None,
    ) -> CommuteResult:
        """Obtiene clima de ambas ciudades y rutas en paralelo, devuelve CommuteResult.

        Lanza 3 tareas en paralelo con anyio: clima de origen, clima de destino
        y rutas. Si hay adaptador de IA y google_key, genera recomendacion
        despues de obtener los datos base.

        Args:
            city: Ciudad de origen (nombre, ej. "Valencia").
            destination_city: Ciudad de destino (nombre, ej. "Madrid").
            profiles: Perfiles de ruta a consultar.
            weather_key: API key de OpenWeather.
            route_key: API key de OpenRouteService.
            google_key: API key de Google AI. Si None, omite la recomendacion IA.

        Returns:
            CommuteResult validado con ambos climas, routes, best_route
            y ai_recommendation (si hay adaptador de IA y google_key).
        """
        origin = self._cache.get_coordinates(city)
        destination = self._cache.get_coordinates(destination_city)

        results: dict[str, Any] = {}

        async def fetch_origin_weather() -> None:
            results["origin_weather"] = await self._weather.get_current_weather(
                city, weather_key
            )

        async def fetch_destination_weather() -> None:
            results["destination_weather"] = await self._weather.get_current_weather(
                destination_city, weather_key
            )

        async def fetch_routes() -> None:
            routes: list[RouteData] = []
            async for route in self._iter_routes(
                origin, destination, profiles, route_key
            ):
                routes.append(route)
            results["routes"] = rank_routes_by_time(routes)

        logger.info(
            "Consultando {origin} -> {dest} en paralelo",
            origin=city,
            dest=destination_city,
        )
        async with anyio.create_task_group() as tg:
            tg.start_soon(fetch_origin_weather)
            tg.start_soon(fetch_destination_weather)
            tg.start_soon(fetch_routes)

        commute_result = CommuteResult(
            origin_city=city,
            destination_city=destination_city,
            origin_weather=results["origin_weather"],
            destination_weather=results["destination_weather"],
            routes=results["routes"],
        )

        if self._ai and google_key:
            commute_result.ai_recommendation = await self._ai.get_recommendation(
                origin_city=city,
                destination_city=destination_city,
                origin_weather=commute_result.origin_weather,
                destination_weather=commute_result.destination_weather,
                routes=commute_result.routes,
            )

        self._history.add(
            ConsultaEntry(city=city, profiles=profiles, result=commute_result)
        )

        return commute_result

    async def _iter_routes(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        profiles: list[str],
        api_key: str,
    ) -> AsyncGenerator[RouteData, None]:
        """Genera rutas de forma lazy — una por perfil."""
        for profile in profiles:
            yield await self._route.get_route(origin, destination, profile, api_key)

    @property
    def history(self) -> ConsultaHistory:
        """Acceso al historial de consultas."""
        return self._history
