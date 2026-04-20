"""Adaptador de Ollama — implementa AIPort con modelo local.

Ollama corre localmente en localhost:11434.
No requiere internet ni API key — ideal como fallback offline.

Usa ollama.AsyncClient para llamadas async identicas a GeminiAdapter.
El mismo prompt y schema que Gemini garantizan respuestas compatibles.
"""

import json

import ollama
from loguru import logger

from pycommute_ai.core.models import AIRecommendation, RouteData, WeatherData

_SYSTEM_PROMPT = """Eres un asistente de movilidad urbana experto.
Analiza las condiciones meteorologicas y las rutas disponibles
para dar recomendaciones practicas y utiles.
Responde SIEMPRE en espanol y en formato JSON valido."""

_RECOMMENDATION_SCHEMA = {
    "recommendation": "string — recomendacion principal (min 10 palabras)",
    "suggested_profile": "string — uno de: cycling-regular, driving-car, foot-walking",
    "confidence": "string — uno de: alta, media, baja",
    "reasoning": "string — razonamiento breve en una linea",
    "outfit_tips": "array de strings — ropa y accesorios recomendados",
    "departure_advice": "string — consejo sobre cuando/como salir",
}


class OllamaAdapter:
    """Adaptador para modelos locales via Ollama.

    Implementa AIPort via duck typing — intercambiable con GeminiAdapter
    sin modificar CommuteService.

    Args:
        model: Nombre del modelo en Ollama. Default: gemma3:1b.
        base_url: URL base del servidor Ollama.
    """

    def __init__(
        self,
        model: str = "gemma3:1b",
        base_url: str = "http://localhost:11434",
    ) -> None:
        self._model = model
        self._client = ollama.AsyncClient(host=base_url)
        logger.debug(
            "OllamaAdapter inicializado con modelo {model} en {url}",
            model=model,
            url=base_url,
        )

    async def get_recommendation(
        self,
        origin_city: str,
        destination_city: str,
        origin_weather: WeatherData,
        destination_weather: WeatherData,
        routes: list[RouteData],
    ) -> AIRecommendation:
        """Genera recomendacion usando modelo local de Ollama.

        Args:
            origin_city: Ciudad de origen.
            destination_city: Ciudad de destino.
            origin_weather: Clima en el origen.
            destination_weather: Clima en el destino.
            routes: Rutas disponibles rankeadas por tiempo.

        Returns:
            AIRecommendation validada con Pydantic.

        Raises:
            ollama.ResponseError: Si el modelo no existe en Ollama.
            ConnectionError: Si Ollama no esta corriendo.
            json.JSONDecodeError: Si la respuesta no es JSON valido.
        """
        prompt = self._build_prompt(
            origin_city,
            destination_city,
            origin_weather,
            destination_weather,
            routes,
        )

        logger.info(
            "Consultando Ollama ({model}) para viaje {origin} -> {dest}",
            model=self._model,
            origin=origin_city,
            dest=destination_city,
        )

        response = await self._client.chat(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        raw_text = response.message.content
        clean = self._clean_json(raw_text)
        data = json.loads(clean)
        recommendation = AIRecommendation(**data)

        logger.info(
            "Recomendacion Ollama: {profile} (confianza: {conf})",
            profile=recommendation.suggested_profile,
            conf=recommendation.confidence,
        )
        return recommendation

    def _build_prompt(
        self,
        origin_city: str,
        destination_city: str,
        origin_weather: WeatherData,
        destination_weather: WeatherData,
        routes: list[RouteData],
    ) -> str:
        """Construye el prompt con contexto estructurado de ambas ciudades y rutas.

        Args:
            origin_city: Ciudad de origen.
            destination_city: Ciudad de destino.
            origin_weather: Clima en el origen.
            destination_weather: Clima en el destino.
            routes: Rutas disponibles.

        Returns:
            Prompt listo para enviar a Ollama.
        """
        routes_text = "\n".join(
            [
                f"  - {r.profile}: {r.distance_km}km, {r.duration_min} min"
                for r in routes
            ]
        )

        return f"""Analiza este viaje y da una recomendacion practica:

ORIGEN: {origin_city}
  Temperatura: {origin_weather.temperature}C
  Condicion: {origin_weather.description}

DESTINO: {destination_city}
  Temperatura: {destination_weather.temperature}C
  Condicion: {destination_weather.description}

RUTAS DISPONIBLES:
{routes_text}

Responde UNICAMENTE con un JSON valido con esta estructura exacta:
{json.dumps(_RECOMMENDATION_SCHEMA, ensure_ascii=False, indent=2)}

No agregues explicaciones fuera del JSON."""

    @staticmethod
    def _clean_json(raw: str) -> str:
        """Elimina el markdown que Ollama agrega a veces (```json ... ```).

        Args:
            raw: Texto de respuesta de Ollama.

        Returns:
            JSON limpio listo para json.loads().
        """
        clean = raw.strip()
        if clean.startswith("```"):
            parts = clean.split("```")
            clean = parts[1] if len(parts) > 1 else clean
            if clean.startswith("json"):
                clean = clean[4:]
        return clean.strip()
