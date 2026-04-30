FROM python:3.13.6-slim AS base

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen

COPY . /app


CMD ["uv", "run", "fastapi", "run", "main.py", "--port", "80", "--host", "0.0.0.0"]
