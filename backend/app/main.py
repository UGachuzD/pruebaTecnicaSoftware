import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import AsyncMongoClient

from app.api.errors import register_exception_handlers
from app.api.routes import realtime, tickets, webhooks
from app.core.config import get_settings
from app.realtime.manager import ConnectionManager
from app.repositories.tickets import ensure_indexes

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    client: AsyncMongoClient = AsyncMongoClient(settings.mongo_uri, tz_aware=True)
    database = client[settings.mongo_db]
    await ensure_indexes(database)
    app.state.database = database
    try:
        yield
    finally:
        await client.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Deskly API", version="0.1.0", lifespan=lifespan)
    app.state.connection_manager = ConnectionManager()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type"],
    )
    register_exception_handlers(app)
    app.include_router(tickets.router)
    app.include_router(webhooks.router)
    app.include_router(realtime.router)
    return app


app = create_app()
