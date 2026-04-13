"""Tests unitarios para pycommute_ai.core.ranking."""

import pytest
from pycommute_ai.core.models import RouteData
from pycommute_ai.core.ranking import (
    get_best_route,
    rank_routes_by_distance,
    rank_routes_by_time,
)

ROUTES = [
    RouteData(profile="foot-walking", distance_km=1.8, duration_min=22),
    RouteData(profile="driving-car", distance_km=2.1, duration_min=5),
    RouteData(profile="cycling-regular", distance_km=2.0, duration_min=8),
]


def test_rank_routes_by_time_orders_ascending() -> None:
    """Verifica que rank_routes_by_time ordena de menor a mayor tiempo."""
    ranked = rank_routes_by_time(ROUTES)

    assert ranked[0].duration_min <= ranked[1].duration_min
    assert ranked[1].duration_min <= ranked[2].duration_min
    assert ranked[0].profile == "driving-car"


def test_get_best_route_by_time_returns_fastest() -> None:
    """Verifica que get_best_route(by='time') devuelve la ruta mas rapida."""
    best = get_best_route(ROUTES, by="time")

    assert best.profile == "driving-car"
    assert best.duration_min == 5


def test_get_best_route_by_distance_returns_shortest() -> None:
    """Verifica que get_best_route(by='distance') devuelve la ruta mas corta."""
    best = get_best_route(ROUTES, by="distance")

    assert best.profile == "foot-walking"
    assert best.distance_km == 1.8


def test_rank_routes_empty_list_returns_empty() -> None:
    """Verifica que una lista vacia retorna lista vacia sin error."""
    assert rank_routes_by_time([]) == []
    assert rank_routes_by_distance([]) == []


def test_get_best_route_raises_on_empty() -> None:
    """Verifica que get_best_route lanza ValueError con lista vacia."""
    with pytest.raises(ValueError, match="No hay rutas"):
        get_best_route([])


def test_get_best_route_raises_on_invalid_criterion() -> None:
    """Verifica que get_best_route lanza ValueError con criterio invalido."""
    with pytest.raises(ValueError, match="Criterio invalido"):
        get_best_route(ROUTES, by="speed")
