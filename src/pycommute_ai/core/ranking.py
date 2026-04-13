"""Ranking de rutas por prioridad usando heapq.

heapq mantiene una lista ordenada con insercion O(log n)
en lugar de ordenar toda la lista en cada operacion O(n log n).
"""

import heapq

from loguru import logger

from pycommute_ai.core.models import RouteData


def rank_routes_by_time(routes: list[RouteData]) -> list[RouteData]:
    """Rankea rutas de menor a mayor tiempo usando un min-heap.

    Args:
        routes: Lista de RouteData con duration_min, distance_km y profile.

    Returns:
        Lista ordenada de rutas — la mas rapida primero.
    """
    if not routes:
        return []

    # heapq trabaja con tuplas — el primer elemento es la clave de ordenamiento.
    # El indice original rompe empates de forma determinista.
    heap: list[tuple[float, int, RouteData]] = []
    for i, route in enumerate(routes):
        heapq.heappush(heap, (route.duration_min, i, route))

    ranked = []
    while heap:
        _, _, route = heapq.heappop(heap)
        ranked.append(route)

    logger.debug(
        "Rutas rankeadas: {n} rutas, mejor tiempo: {best} min",
        n=len(ranked),
        best=ranked[0].duration_min if ranked else 0,
    )
    return ranked


def rank_routes_by_distance(routes: list[RouteData]) -> list[RouteData]:
    """Rankea rutas de menor a mayor distancia usando un min-heap.

    Args:
        routes: Lista de RouteData con duration_min, distance_km y profile.

    Returns:
        Lista ordenada de rutas — la mas corta primero.
    """
    if not routes:
        return []

    heap: list[tuple[float, int, RouteData]] = []
    for i, route in enumerate(routes):
        heapq.heappush(heap, (route.distance_km, i, route))

    ranked = []
    while heap:
        _, _, route = heapq.heappop(heap)
        ranked.append(route)

    return ranked


def get_best_route(routes: list[RouteData], by: str = "time") -> RouteData:
    """Obtiene la mejor ruta segun criterio sin ordenar toda la lista.

    Usa heapq.nsmallest — O(n) en lugar de O(n log n) para obtener solo 1.

    Args:
        routes: Lista de rutas.
        by: Criterio — "time" o "distance".

    Returns:
        La ruta con menor tiempo o distancia.

    Raises:
        ValueError: Si routes esta vacia o by es invalido.
    """
    if not routes:
        raise ValueError("No hay rutas para rankear")

    key_map = {"time": "duration_min", "distance": "distance_km"}
    if by not in key_map:
        raise ValueError(f"Criterio invalido: {by}. Usar 'time' o 'distance'")

    key = key_map[by]
    best = heapq.nsmallest(1, routes, key=lambda r: getattr(r, key))[0]
    logger.info(
        "Mejor ruta ({by}): {profile} — {val}",
        by=by,
        profile=best.profile,
        val=getattr(best, key),
    )
    return best
