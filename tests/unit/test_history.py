"""Tests unitarios para pycommute_ai.core.history."""

from pycommute_ai.core.history import ConsultaHistory
from pycommute_ai.core.models import (
    CommuteResult,
    ConsultaEntry,
    RouteData,
    WeatherData,
)

ORIGIN_WEATHER = WeatherData(
    temperature=13.0, description="scattered clouds", city="Valencia"
)
DESTINATION_WEATHER = WeatherData(
    temperature=5.0, description="clear sky", city="Madrid"
)
ROUTE = RouteData(profile="cycling-regular", distance_km=2.0, duration_min=8.0)
RESULT = CommuteResult(
    origin_city="Valencia",
    destination_city="Madrid",
    origin_weather=ORIGIN_WEATHER,
    destination_weather=DESTINATION_WEATHER,
    routes=[ROUTE],
)


def _entry(city: str, profiles: list[str] | None = None) -> ConsultaEntry:
    return ConsultaEntry(
        city=city,
        profiles=profiles or ["cycling-regular"],
        result=RESULT,
    )


def test_history_add_and_retrieve() -> None:
    """Verifica que add() y get_recent() funcionan correctamente."""
    history = ConsultaHistory(maxlen=10)
    history.add(_entry("Valencia"))

    assert len(history) == 1
    entries = history.get_recent()
    assert entries[0].city == "Valencia"
    assert entries[0].profiles == ["cycling-regular"]


def test_history_respects_maxlen() -> None:
    """Verifica que maxlen descarta entradas antiguas automaticamente."""
    history = ConsultaHistory(maxlen=3)

    for city in ["Valencia", "Madrid", "Barcelona", "Sevilla"]:
        history.add(_entry(city))

    assert len(history) == 3
    cities = [e.city for e in history.get_recent()]
    assert "Valencia" not in cities
    assert "Sevilla" in cities


def test_history_get_recent_newest_first() -> None:
    """Verifica que get_recent() devuelve la mas reciente primero."""
    history = ConsultaHistory(maxlen=10)
    history.add(_entry("Valencia", ["cycling-regular"]))
    history.add(_entry("Madrid", ["driving-car"]))
    history.add(_entry("Barcelona", ["foot-walking"]))

    entries = history.get_recent()
    assert entries[0].city == "Barcelona"
    assert entries[1].city == "Madrid"
    assert entries[2].city == "Valencia"
