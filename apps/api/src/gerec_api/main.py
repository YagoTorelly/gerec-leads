"""Ponto de entrada da API HTTP."""

from typing import Any

from fastapi import FastAPI

from gerec_api.auth.sessions import AuthService
from gerec_api.config import Settings
from gerec_api.domain.business_time import BusinessClock, MongoHolidayRepository
from gerec_api.domain.leads import LeadService
from gerec_api.domain.operations import OperationsService, SystemClock
from gerec_api.domain.queue import QueueService
from gerec_api.infrastructure.mongo.client import MongoClientFactory
from gerec_api.infrastructure.mongo.collections import MongoCollections
from gerec_api.infrastructure.mongo.lead_repository import LeadRepository
from gerec_api.infrastructure.mongo.operations_repository import MongoOperationsRepository
from gerec_api.infrastructure.mongo.queue_repository import QueueRepository
from gerec_api.routes.auth import router as auth_router
from gerec_api.routes.leads import router as leads_router
from gerec_api.routes.operations import router as operations_router
from gerec_api.routes.queue import router as queue_router


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
    app.state.settings = settings
    app.state.database = database
    app.state.auth_service = auth_service if auth_service is not None else AuthService(database)
    app.state.lead_service = LeadService(LeadRepository(database))
    business_clock = BusinessClock(
        MongoHolidayRepository(database[MongoCollections.HOLIDAYS])
    )
    app.state.queue_service = QueueService(
        QueueRepository(database, business_clock=business_clock)
    )
    app.state.operations_service = OperationsService(
        MongoOperationsRepository(database),
        business_clock=business_clock,
        clock=SystemClock(),
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "database": settings.mongodb_database}

    app.include_router(auth_router)
    app.include_router(leads_router)
    app.include_router(queue_router)
    app.include_router(operations_router)
    return app
