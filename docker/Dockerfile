FROM node:24.0.0-bookworm-slim AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12.3-slim-bookworm AS runtime

ENV PYTHONPATH=/app/backend \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements-dev.lock ./
RUN pip install --no-cache-dir --requirement requirements-dev.lock
COPY alembic.ini ./
COPY migrations/ ./migrations/
COPY backend/ ./backend/
COPY docker/entrypoints/ ./docker/entrypoints/
COPY --from=frontend-build /frontend/dist/varys-frontend/browser ./backend/varys/frontend/
RUN adduser --disabled-password --gecos '' varys \
    && mkdir /data \
    && chown -R varys:varys /app /data \
    && chmod +x docker/entrypoints/*.sh

USER varys
CMD ["python", "-m", "varys.api"]
