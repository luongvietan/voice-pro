FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --no-create-home --no-log-init --shell /usr/sbin/nologin appuser

COPY pyproject.toml README.md main.py alembic.ini ./
COPY app ./app
COPY alembic ./alembic

RUN pip install --no-cache-dir pip setuptools wheel hatchling \
    && pip install --no-cache-dir . \
    && chown -R appuser:appgroup /app

ENV PYTHONPATH=/app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
