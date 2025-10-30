# syntax=docker/dockerfile:1.7

# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/app/.venv/bin:$PATH

WORKDIR /app

RUN python -m venv .venv

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Copy React build from frontend-builder stage
COPY --from=frontend-builder /frontend/dist /app/frontend/dist

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
