import asyncio
import json
import logging
import os
from typing import List

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("aegisnet.ws.telemetry")

router = APIRouter()

REDIS_URL    = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ALERT_STREAM = "stream:ml:alerts"
CONSUMER_GROUP = "ws-broadcast"
CONSUMER_NAME  = "ws-server"
POLL_INTERVAL  = 0.5   # seconds between XREADGROUP calls


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"[ws] Client connected. Total: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"[ws] Client disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        dead = []
        async with self._lock:
            connections = list(self.active_connections)
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)


manager = ConnectionManager()


async def _ensure_ws_consumer_group(redis_client: aioredis.Redis) -> None:
    try:
        await redis_client.xgroup_create(
            ALERT_STREAM, CONSUMER_GROUP, id="$", mkstream=True
        )
    except Exception as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def alert_broadcast_loop():
    """
    Background task: reads new alerts from stream:ml:alerts
    and broadcasts them as JSON to all connected WebSocket clients.
    """
    redis_client = await aioredis.from_url(REDIS_URL, decode_responses=True)
    await _ensure_ws_consumer_group(redis_client)
    logger.info("[ws] Alert broadcast loop started.")

    try:
        while True:
            response = await redis_client.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={ALERT_STREAM: ">"},
                count=20,
                block=int(POLL_INTERVAL * 1000),
            )
            if not response:
                continue

            ack_ids = []
            for _stream, messages in response:
                for msg_id, record in messages:
                    ack_ids.append(msg_id)
                    payload = json.dumps({
                        "type": "alert",
                        "data": record,
                    })
                    if manager.active_connections:
                        await manager.broadcast(payload)

            if ack_ids:
                await redis_client.xack(ALERT_STREAM, CONSUMER_GROUP, *ack_ids)

    except asyncio.CancelledError:
        logger.info("[ws] Broadcast loop cancelled.")
    finally:
        await redis_client.close()


@router.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive — client pings are ignored gracefully
            await asyncio.wait_for(websocket.receive_text(), timeout=30)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        await manager.disconnect(websocket)
