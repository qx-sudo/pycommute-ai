"""Tests unitarios para pycommute_ai.adapters.cache."""

import pytest
from pycommute_ai.adapters.cache import MemoryCacheAdapter, get_coordinates


def test_get_coordinates_returns_correct_values() -> None:
    """Verifica que las coordenadas de Valencia son correctas."""
    adapter = MemoryCacheAdapter()
    lat, lon = adapter.get_coordinates("Valencia")

    assert abs(lat - 39.4699) < 0.001
    assert abs(lon - (-0.3763)) < 0.001


def test_get_coordinates_uses_cache() -> None:
    """Verifica que la segunda llamada es un cache hit."""
    get_coordinates.cache_clear()

    adapter = MemoryCacheAdapter()
    adapter.get_coordinates("Madrid")
    adapter.get_coordinates("Madrid")

    info = get_coordinates.cache_info()
    assert info.hits >= 1
    assert info.misses == 1


def test_get_coordinates_raises_for_unknown_city() -> None:
    """Verifica que una ciudad desconocida lanza ValueError."""
    adapter = MemoryCacheAdapter()
    with pytest.raises(ValueError, match="Ciudad no encontrada"):
        adapter.get_coordinates("CiudadInventada")
