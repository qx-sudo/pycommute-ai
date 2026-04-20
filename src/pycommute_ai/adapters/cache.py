"""Adaptador de cache en memoria — implementa CachePort."""

from functools import lru_cache

from loguru import logger

from pycommute_ai.core.ports import CachePort  # noqa: F401 — cumple el protocolo

_COORDENADAS: dict[str, tuple[float, float]] = {
    # Ciudades principales de España
    "Valencia": (39.4699, -0.3763),
    "Madrid": (40.4168, -3.7038),
    "Barcelona": (41.3851, 2.1734),
    "Sevilla": (37.3891, -5.9845),
    "Bilbao": (43.2630, -2.9350),
    "Zaragoza": (41.6488, -0.8891),
    "Málaga": (36.7213, -4.4214),
    "Alicante": (38.3452, -0.4810),
    "Córdoba": (37.8882, -4.7794),
    "Vigo": (42.2328, -8.7226),
    # Rutas cortas desde Valencia (ciclismo)
    "Sagunto": (39.6794, -0.2722),
    "Gandía": (38.9667, -0.1833),
    # Rutas cortas desde Madrid
    "Alcalá De Henares": (40.4818, -3.3635),
    "Toledo": (39.8628, -4.0273),
    # Europa
    "París": (48.8566, 2.3522),
}


@lru_cache(maxsize=128)
def get_coordinates(city: str) -> tuple[float, float]:
    """Obtiene las coordenadas de una ciudad con cache en memoria.

    Función de módulo con lru_cache — el adaptador delega a esta función
    para que cache_info() y cache_clear() sean accesibles sin estado de instancia.

    Args:
        city: Nombre de la ciudad.

    Returns:
        Tupla (latitud, longitud).

    Raises:
        ValueError: Si la ciudad no está en el registro.
    """
    city_normalized = city.strip().title()

    if city_normalized not in _COORDENADAS:
        logger.warning("Cache miss — ciudad desconocida: {city}", city=city_normalized)
        raise ValueError(f"Ciudad no encontrada: {city_normalized}")

    coords = _COORDENADAS[city_normalized]
    logger.debug(
        "Cache miss — coordenadas {city}: {coords}",
        city=city_normalized,
        coords=coords,
    )
    return coords


def cache_info() -> str:
    """Devuelve estadísticas del cache de coordenadas."""
    info = get_coordinates.cache_info()
    return (
        f"hits={info.hits}, misses={info.misses}, "
        f"maxsize={info.maxsize}, currsize={info.currsize}"
    )


class MemoryCacheAdapter:
    """Adaptador de cache en memoria con lru_cache.

    Implementa CachePort — si mañana usamos Redis,
    solo cambia este adaptador sin tocar CommuteService.
    """

    def get_coordinates(self, city: str) -> tuple[float, float]:
        """Obtiene las coordenadas de una ciudad.

        Delega a la función get_coordinates() del módulo para
        mantener el cache compartido entre instancias del adaptador.

        Args:
            city: Nombre de la ciudad.

        Returns:
            Tupla (latitud, longitud).

        Raises:
            ValueError: Si la ciudad no está en el registro.
        """
        return get_coordinates(city)
