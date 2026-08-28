from collections import defaultdict

import pytest
from fastapi.testclient import TestClient

from gerec_api.config import Settings
from gerec_api.infrastructure.mongo.client import MongoClientFactory
from gerec_api.infrastructure.mongo import bootstrap
from gerec_api.main import create_app


def test_health_reports_the_configured_mongodb_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """Breaks if the health endpoint stops exposing the configured database."""
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017/?replicaSet=rs0")
    monkeypatch.setenv("MONGODB_DATABASE", "gerec_leads")
    monkeypatch.setenv("APP_SECRET", "test-only-secret")

    response = TestClient(
        create_app(settings=Settings.from_env(), database=defaultdict(object))
    ).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "gerec_leads"}


@pytest.mark.parametrize("missing_variable", ["MONGODB_URI", "MONGODB_DATABASE"])
def test_settings_reject_missing_mongodb_configuration_without_defaults(
    monkeypatch: pytest.MonkeyPatch, missing_variable: str
) -> None:
    """Breaks if MongoDB configuration starts accepting an implicit fallback."""
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017/?replicaSet=rs0")
    monkeypatch.setenv("MONGODB_DATABASE", "gerec_leads")
    monkeypatch.setenv("APP_SECRET", "test-only-secret")
    monkeypatch.delenv(missing_variable)

    with pytest.raises(ValueError, match=missing_variable):
        Settings.from_env()


def test_mongo_client_factory_selects_the_configured_database() -> None:
    """Breaks if the Mongo factory points server code at another database."""
    settings = Settings(
        MONGODB_URI="mongodb://localhost:27017/?replicaSet=rs0",
        MONGODB_DATABASE="gerec_leads",
        APP_SECRET="test-only-secret",
    )

    database = MongoClientFactory.create(settings)

    assert database.name == "gerec_leads"


def test_app_factory_ensures_schema_before_health_can_be_served(monkeypatch: pytest.MonkeyPatch) -> None:
    """Breaks if Railway starts listening before validators and indexes are installed."""
    database = defaultdict(object)
    calls: list[object] = []
    settings = Settings(
        MONGODB_URI="mongodb://localhost:27017/?replicaSet=rs0",
        MONGODB_DATABASE="gerec_leads",
        APP_SECRET="test-only-secret",
    )
    monkeypatch.setattr(MongoClientFactory, "create", lambda _settings: database)
    monkeypatch.setattr(bootstrap, "ensure_schema", lambda value: calls.append(value))

    app = create_app(settings=settings)

    assert calls == [database]
    assert app.state.schema_ready is True
