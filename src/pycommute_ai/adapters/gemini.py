"""Adaptador de Gemini API — implementa AIPort.

Recibe contexto estructurado (clima de origen, clima de destino, rutas)
y devuelve AIRecommendation validada por Pydantic.

Usa google-genai (SDK actual). La variable de entorno GOOGLE_API_KEY
se inyecta via GeminiAdapter(api_key=settings.google_api_key).
"""

import json

from google import genai
from google.genai import types
from loguru import logger

from pycommute_ai.core.models import AIRecommendation, RouteData, WeatherData

_DEFAULT_MODEL = "gemini-2.5-flash"

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


class GeminiAdapter:
    """Adaptador para Gemini API que genera recomendaciones estructuradas.

    Implementa AIPort via duck typing — no hereda de Protocol.
    Usa system_instruction para establecer el rol del modelo
    y pide respuesta JSON estructurada via schema en el prompt.
    """

    def __init__(self, api_key: str, model: str | None = None) -> None:
        """Inicializa el adaptador con la API key y el modelo.

        Args:
            api_key: Clave de autenticacion de Google AI Studio.
            model: Nombre del modelo Gemini. Si None, usa settings.gemini_model.
        """
        self._client = genai.Client(api_key=api_key)
        self._model = model or _DEFAULT_MODEL
        self._config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
        )
        logger.debug("GeminiAdapter inicializado con modelo {model}", model=model)

    async def get_recommendation(
        self,
        origin_city: str,
        destination_city: str,
        origin_weather: WeatherData,
        destination_weather: WeatherData,
        routes: list[RouteData],
    ) -> AIRecommendation:
        """Genera recomendacion usando Gemini con respuesta JSON estructurada.

        Args:
            origin_city: Ciudad de origen.
            destination_city: Ciudad de destino.
            origin_weather: Clima en el origen.
            destination_weather: Clima en el destino.
            routes: Rutas disponibles rankeadas por tiempo.

        Returns:
            AIRecommendation validada con Pydantic.

        Raises:
            ValidationError: Si Gemini devuelve un campo con valor inesperado.
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
            "Consultando Gemini para viaje {origin} -> {dest}",
            origin=origin_city,
            dest=destination_city,
        )

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=self._config,
        )
        raw_text = response.text

        clean = self._clean_json(raw_text)
        data = json.loads(clean)
        recommendation = AIRecommendation(**data)

        logger.info(
            "Recomendacion IA: {profile} (confianza: {conf})",
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
            Prompt listo para enviar a Gemini.
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
        """Elimina el markdown que Gemini agrega a veces (```json ... ```).

        Args:
            raw: Texto de respuesta de Gemini.

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
