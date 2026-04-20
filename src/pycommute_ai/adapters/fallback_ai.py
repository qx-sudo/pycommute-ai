"""Adaptador de fallback — intenta primary, conmuta a secondary si falla.

Patron de resiliencia de IA hibrida:
1. Intentar con el adaptador primario (cloud — mejor calidad)
2. Si falla por cualquier motivo, conmutar al secundario (local — siempre disponible)
3. CommuteService no sabe cual de los dos respondio

FallbackAIAdapter implementa AIPort — es un adaptador que orquesta otros.
El patron se llama Composite: un objeto que implementa una interfaz
usando otros objetos que implementan la misma interfaz.
"""

from loguru import logger

from pycommute_ai.core.models import AIRecommendation, RouteData, WeatherData
from pycommute_ai.core.ports import AIPort


class FallbackAIAdapter:
    """Adaptador de IA con fallback automatico.

    Implementa AIPort — el CommuteService lo usa exactamente igual
    que GeminiAdapter u OllamaAdapter.

    El patron:
        primary (Gemini) → falla → secondary (Ollama)

    La logica de fallback esta encapsulada aqui —
    CommuteService no sabe nada del fallback.

    Args:
        primary: Adaptador preferido (ej: GeminiAdapter).
        secondary: Adaptador de respaldo (ej: OllamaAdapter).
    """

    def __init__(self, primary: AIPort, secondary: AIPort) -> None:
        self._primary = primary
        self._secondary = secondary
        logger.debug(
            "FallbackAIAdapter: {primary} -> {secondary}",
            primary=type(primary).__name__,
            secondary=type(secondary).__name__,
        )

    async def get_recommendation(
        self,
        origin_city: str,
        destination_city: str,
        origin_weather: WeatherData,
        destination_weather: WeatherData,
        routes: list[RouteData],
    ) -> AIRecommendation:
        """Intenta con primario, conmuta a secundario si falla.

        Args:
            origin_city: Ciudad de origen.
            destination_city: Ciudad de destino.
            origin_weather: Clima en el origen.
            destination_weather: Clima en el destino.
            routes: Rutas disponibles rankeadas por tiempo.

        Returns:
            AIRecommendation del primer adaptador que responda.

        Raises:
            Exception: Solo si ambos adaptadores fallan.
        """
        primary_name = type(self._primary).__name__
        secondary_name = type(self._secondary).__name__

        try:
            logger.info("Intentando con {adapter}...", adapter=primary_name)
            result = await self._primary.get_recommendation(
                origin_city,
                destination_city,
                origin_weather,
                destination_weather,
                routes,
            )
            logger.info("{adapter} respondio correctamente", adapter=primary_name)
            return result

        except Exception as e:
            logger.warning(
                "{primary} fallo: {error} — conmutando a {secondary}",
                primary=primary_name,
                error=str(e)[:120],
                secondary=secondary_name,
            )
            result = await self._secondary.get_recommendation(
                origin_city,
                destination_city,
                origin_weather,
                destination_weather,
                routes,
            )
            logger.info("{adapter} respondio correctamente", adapter=secondary_name)
            return result
