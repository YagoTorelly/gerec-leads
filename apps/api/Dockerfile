FROM python:3.12-slim

WORKDIR /app

COPY apps/api/pyproject.toml ./apps/api/pyproject.toml
COPY apps/api/src ./apps/api/src

RUN pip install --no-cache-dir ./apps/api

EXPOSE 8000

CMD ["sh", "-c", "uvicorn gerec_api.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
