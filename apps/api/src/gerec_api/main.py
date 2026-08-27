"""Ponto de entrada da API HTTP."""

from typing import Any

from fastapi import FastAPI

from gerec_api.auth.sessions import AuthService
from gerec_api.config import Settings
from gerec_api.infrastructure.mongo.client import MongoClientFactory
from gerec_api.routes.auth import router as auth_router


def create_app(
    *,
    settings: Settings | None = None,
    database: Any | None = None,
    auth_service: AuthService | None = None,
) -> FastAPI:
    """Create the HTTP app with a lazily connected MongoDB handle and auth service."""
    settings = settings or Settings.from_env()
    if database is None:
        database = MongoClientFactory.create(settings)
    app = FastAPI(title="Gerenciador de Leads WTG API")
    app.state.database = database
    app.state.auth_service = auth_service if auth_service is not None else AuthService(database)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "database": settings.mongodb_database}

    app.include_router(auth_router)
    return app
