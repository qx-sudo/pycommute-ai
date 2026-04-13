"""Historial de consultas usando collections.deque.

deque con maxlen descarta automaticamente las entradas mas antiguas
cuando se supera la capacidad — O(1) para append y popleft.
"""

from collections import deque

from loguru import logger

from pycommute_ai.core.models import ConsultaEntry


class ConsultaHistory:
    """Historial de consultas con capacidad maxima configurable.

    Usa deque(maxlen=N) para descartar automaticamente
    las consultas mas antiguas cuando se supera la capacidad.
    """

    def __init__(self, maxlen: int = 10) -> None:
        """Inicializa el historial con capacidad maxima.

        Args:
            maxlen: Numero maximo de entradas a mantener.
        """
        self._history: deque[ConsultaEntry] = deque(maxlen=maxlen)

    def add(self, entry: ConsultaEntry) -> None:
        """Agrega una entrada al historial.

        Args:
            entry: ConsultaEntry Pydantic con ciudad, perfiles y resultado.
        """
        self._history.append(entry)
        logger.debug(
            "Historial actualizado: {n}/{max} entradas",
            n=len(self._history),
            max=self._history.maxlen,
        )

    def get_recent(self, n: int | None = None) -> list[ConsultaEntry]:
        """Obtiene las consultas mas recientes.

        Args:
            n: Numero de entradas. None devuelve todas.

        Returns:
            Lista de entradas — la mas reciente primero.
        """
        entries = list(self._history)
        entries.reverse()
        return entries[:n] if n else entries

    def __len__(self) -> int:
        return len(self._history)

    def clear(self) -> None:
        """Limpia el historial."""
        self._history.clear()
