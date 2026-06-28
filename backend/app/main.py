from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import logger
from app.api.routers import auth, assets, honeypot, threat_intel, telemetry, alerts
from app.api.websockets import telemetry as ws_telemetry
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.db.redis_cache import connect_to_redis, close_redis_connection
from app.ml.loader import ModelRegistry
from app.correlation.router import router as correlation_router
from app.correlation.consumer import CorrelationEngine
from app.api.websockets.telemetry import manager as ws_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AegisNet API — initialising connections...")
    await connect_to_mongo()
    await connect_to_redis()
    logger.info("MongoDB and Redis ready.")

    # Pre-load ML models into memory
    logger.info("Loading ML models...")
    ModelRegistry.get()

    # Start the WebSocket alert broadcast background loop
    broadcast_task = asyncio.create_task(ws_telemetry.alert_broadcast_loop())
    logger.info("Alert broadcast loop started.")
    
    # Start Correlation Engine
    correlation_engine = CorrelationEngine(ws_manager)
    correlation_task = asyncio.create_task(correlation_engine.run())
    logger.info("Correlation Engine started.")

    yield

    logger.info("Shutting down AegisNet API...")
    broadcast_task.cancel()
    correlation_task.cancel()
    try:
        await asyncio.gather(broadcast_task, correlation_task, return_exceptions=True)
    except asyncio.CancelledError:
        pass
    await close_mongo_connection()
    await close_redis_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# REST Routers
app.include_router(auth.router,         prefix=f"{settings.API_V1_STR}/auth",          tags=["Auth"])
app.include_router(assets.router,       prefix=f"{settings.API_V1_STR}/assets",         tags=["Assets"])
app.include_router(honeypot.router,     prefix=f"{settings.API_V1_STR}/honeypot",       tags=["Honeypot"])
app.include_router(threat_intel.router, prefix=f"{settings.API_V1_STR}/threat-intel",   tags=["Threat Intel"])
app.include_router(telemetry.router,    prefix=f"{settings.API_V1_STR}/telemetry",      tags=["Telemetry"])
app.include_router(alerts.router,       prefix=f"{settings.API_V1_STR}/alerts",         tags=["Alerts"])
app.include_router(correlation_router,  prefix=f"{settings.API_V1_STR}/correlation",    tags=["Correlation"])

# WebSocket
app.include_router(ws_telemetry.router, tags=["WebSocket"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "AegisNet API operational", "version": "1.0.0"}
