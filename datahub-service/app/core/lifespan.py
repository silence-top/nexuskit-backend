# app/core/lifespan.py — Application startup / shutdown hooks
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.db import engine

logger = logging.getLogger("datahub-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Datahub Service starting up...")
    yield
    logger.info("Datahub Service shutting down...")
    await engine.dispose()
