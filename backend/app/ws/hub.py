"""WebSocket hub — multiplexes ingestion + AI milestones per reviewing session."""

from __future__ import annotations

import asyncio
import json
import uuid

from starlette.websockets import WebSocket

from app.core.logging_setup import get_logger

log = get_logger(__name__)


class ProgressHub:
    """In-memory fan-out broker; horizontally scaling requires Redis pub/sub in production."""

    def __init__(self) -> None:
        self._channels: dict[uuid.UUID, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def register(self, document_id: uuid.UUID, websocket: WebSocket) -> None:
        async with self._lock:
            self._channels.setdefault(document_id, set()).add(websocket)

    async def unregister(self, document_id: uuid.UUID, websocket: WebSocket) -> None:
        async with self._lock:
            bucket = self._channels.get(document_id)
            if not bucket:
                return
            bucket.discard(websocket)
            if not bucket:
                self._channels.pop(document_id, None)

    async def publish(self, document_id: uuid.UUID, message: dict) -> None:
        payload = json.dumps(message, default=str)
        async with self._lock:
            sockets = list(self._channels.get(document_id, ()))
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception as exc:  # noqa: BLE001 - fan-out must stay resilient
                log.warning("websocket_send_failed", error=str(exc))
                dead.append(ws)
        for ws in dead:
            await self.unregister(document_id, ws)


progress_hub = ProgressHub()
