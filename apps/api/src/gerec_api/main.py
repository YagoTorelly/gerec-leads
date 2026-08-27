"""Ponto de entrada da API HTTP."""

from fastapi import FastAPI

from gerec_api.config import Settings


def create_app() -> FastAPI:
    """Cria a aplica\u00e7\u00e3o sem abrir conex\u00e3o impl\u00edcita ao MongoDB."""
    settings = Settings.from_env()
    app = FastAPI(title="Gerenciador de Leads WTG API")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "database": settings.mongodb_database}

    return app
