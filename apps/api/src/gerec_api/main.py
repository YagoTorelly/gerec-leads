"""Ponto de entrada da API HTTP."""

from typing import Any

from fastapi import FastAPI, Request

from gerec_api.auth.sessions import AuthService
from gerec_api.auth.permissions import DashboardService
from gerec_api.config import Settings
from gerec_api.domain.business_time import BusinessClock, MongoHolidayRepository
from gerec_api.domain.leads import LeadService
from gerec_api.domain.lead_notifications import LeadNotificationService
from gerec_api.domain.operations import OperationsService
from gerec_api.domain.queue import QueueService
from gerec_api.domain.user_administration import UserAdministrationService
from gerec_api.infrastructure.mongo.client import MongoClientFactory
from gerec_api.infrastructure.mongo import bootstrap
from gerec_api.infrastructure.mongo.clock import MongoClock
from gerec_api.infrastructure.mongo.collections import MongoCollections
from gerec_api.infrastructure.mongo.lead_repository import LeadRepository
from gerec_api.infrastructure.mongo.lead_notification_repository import MongoLeadNotificationRepository
from gerec_api.infrastructure.mongo.operations_repository import MongoOperationsRepository
from gerec_api.infrastructure.mongo.queue_repository import QueueRepository
from gerec_api.infrastructure.mongo.user_repository import UserRepository
from gerec_api.routes.auth import router as auth_router
from gerec_api.routes.leads import router as leads_router
from gerec_api.routes.operations import router as operations_router
from gerec_api.routes.queue import router as queue_router
from gerec_api.routes.dashboard import router as dashboard_router
from gerec_api.routes.admin import router as admin_router
from gerec_api.routes.lead_notifications import router as lead_notifications_router
from gerec_api.routes.reports import router as reports_router


API_CONTRACT_VERSION = "1"


def create_app(
    *,
    settings: Settings | None = None,
    database: Any | None = None,
    auth_service: AuthService | None = None,
) -> FastAPI:
    """Create the HTTP app with a lazily connected MongoDB handle and auth service."""
    settings = settings or Settings.from_env()
    owns_database = database is None
    if owns_database:
        database = MongoClientFactory.create(settings)
        bootstrap.ensure_schema(database)
    app = FastAPI(title="Gerenciador de Leads WTG API")
    app.state.settings = settings
    app.state.schema_ready = True
    app.state.database = database
    app.state.auth_service = auth_service if auth_service is not None else AuthService(database)
    app.state.dashboard_service = DashboardService(database)
    app.state.lead_service = LeadService(LeadRepository(database))
    database_clock = MongoClock(database)
    app.state.lead_notification_service = LeadNotificationService(
        MongoLeadNotificationRepository(database),
        signing_key=settings.app_secret.get_secret_value(),
        now=database_clock.now,
    )
    business_clock = BusinessClock(
        MongoHolidayRepository(database[MongoCollections.HOLIDAYS])
    )
    app.state.queue_service = QueueService(
        QueueRepository(database)
    )
    app.state.operations_service = OperationsService(
        MongoOperationsRepository(
            database,
            clock=database_clock,
        ),
        business_clock=business_clock,
        clock=database_clock,
    )
    app.state.user_administration_service = UserAdministrationService(
        UserRepository(database)
    )

    @app.middleware("http")
    async def add_contract_version(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Gerec-API-Contract-Version"] = API_CONTRACT_VERSION
        return response

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "database": settings.mongodb_database}

    app.include_router(auth_router)
    app.include_router(leads_router)
    app.include_router(queue_router)
    app.include_router(operations_router)
    app.include_router(dashboard_router)
    app.include_router(admin_router)
    app.include_router(lead_notifications_router)
    app.include_router(reports_router)
    return app
