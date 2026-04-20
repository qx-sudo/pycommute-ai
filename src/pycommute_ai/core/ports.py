"""Puertos de PyCommute AI — contratos definidos con typing.Protocol.

Un puerto define QUE hace un componente, no COMO lo hace.
Cualquier clase que implemente estos metodos cumple el contrato
sin necesidad de heredar — eso es duck typing estructural.
"""

from typing import Protocol, runtime_checkable

from pycommute_ai.core.models import AIRecommendation, RouteData, WeatherData


@runtime_checkable
class WeatherPort(Protocol):
    """Puerto para consultar datos de clima."""

    async def get_current_weather(self, city: str, api_key: str) -> WeatherData:
        """Obtiene el clima actual para una ciudad.

        Args:
            city: Nombre de la ciudad.
            api_key: Clave de autenticacion.

        Returns:
            WeatherData validado con temperature, description, city.
        """
        ...


@runtime_checkable
class RoutePort(Protocol):
    """Puerto para consultar rutas entre dos puntos."""

    async def get_route(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        profile: str,
        api_key: str,
    ) -> RouteData:
        """Obtiene una ruta entre dos coordenadas.

        Args:
            origin: Coordenadas de origen (lat, lon).
            destination: Coordenadas de destino (lat, lon).
            profile: Perfil de transporte.
            api_key: Clave de autenticacion.

        Returns:
            RouteData validado con distance_km, duration_min, profile.
        """
        ...


@runtime_checkable
class AIPort(Protocol):
    """Puerto para generar recomendaciones de movilidad con IA."""

    async def get_recommendation(
        self,
        origin_city: str,
        destination_city: str,
        origin_weather: WeatherData,
        destination_weather: WeatherData,
        routes: list[RouteData],
    ) -> AIRecommendation:
        """Genera una recomendacion de movilidad contextualizada.

        Args:
            origin_city: Ciudad de origen.
            destination_city: Ciudad de destino.
            origin_weather: Clima en el origen.
            destination_weather: Clima en el destino.
            routes: Rutas disponibles rankeadas.

        Returns:
            AIRecommendation con recomendacion, vestimenta y consejos.
        """
        ...


@runtime_checkable
class CachePort(Protocol):
    """Puerto para obtener coordenadas de ciudades."""

    def get_coordinates(self, city: str) -> tuple[float, float]:
        """Obtiene las coordenadas de una ciudad.

        Args:
            city: Nombre de la ciudad.

        Returns:
            Tupla (latitud, longitud).

        Raises:
            ValueError: Si la ciudad no esta disponible.
        """
        ...
