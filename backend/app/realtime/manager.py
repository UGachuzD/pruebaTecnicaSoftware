import asyncio
import logging
from enum import StrEnum
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class TicketEvent(StrEnum):
    CREADO = "ticket.creado"
    ACTUALIZADO = "ticket.actualizado"
    COMENTADO = "ticket.comentado"


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("Cliente WebSocket conectado (activos: %d)", self.active_connections)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.discard(websocket)
            logger.info("Cliente WebSocket desconectado (activos: %d)", self.active_connections)

    async def broadcast(self, event: TicketEvent, data: dict[str, Any]) -> None:
        message = {"tipo": event.value, "datos": data}
        connections = list(self._connections)
        results = await asyncio.gather(
            *(connection.send_json(message) for connection in connections),
            return_exceptions=True,
        )
        for connection, result in zip(connections, results, strict=True):
            if isinstance(result, Exception):
                logger.warning(
                    "Fallo al enviar evento %s, se descarta el cliente: %r", event, result
                )
                self.disconnect(connection)
