"""Tests unitarios para pycommute_ai.config."""

import pytest
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    """Settings aislada sin carga desde .env — solo para tests.

    Hereda la misma estructura que Settings pero con env_file=None
    para evitar que el archivo .env del desarrollador interfiera en los tests.
    """

    model_config = SettingsConfigDict(env_file=None)

    openweather_api_key: str
    openrouteservice_api_key: str
    app_env: str = "development"
    log_level: str = "DEBUG"


def test_settings_loads_from_env(monkeypatch) -> None:
    """Verifica que Settings lee las variables de entorno correctamente."""
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-weather-key")
    monkeypatch.setenv("OPENROUTESERVICE_API_KEY", "test-route-key")

    s = _Settings()

    assert s.openweather_api_key == "test-weather-key"
    assert s.openrouteservice_api_key == "test-route-key"


def test_settings_raises_if_key_missing(monkeypatch) -> None:
    """Verifica que Settings lanza ValidationError si falta una key requerida.

    Esta es la propiedad de fail-fast: la app falla al arrancar,
    no en medio de una ejecucion cuando intenta usar la key inexistente.
    """
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTESERVICE_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        _Settings()


def test_settings_default_values(monkeypatch) -> None:
    """Verifica que app_env y log_level tienen los valores por defecto correctos."""
    monkeypatch.setenv("OPENWEATHER_API_KEY", "key1")
    monkeypatch.setenv("OPENROUTESERVICE_API_KEY", "key2")

    s = _Settings()

    assert s.app_env == "development"
    assert s.log_level == "DEBUG"
