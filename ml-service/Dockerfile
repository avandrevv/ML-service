FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN mkdir -p src/ml_service && touch src/ml_service/__init__.py

RUN --mount=type=cache,target=/root/.cache/uv \
    pip install uv && \
    uv sync --frozen --no-dev

COPY . .


FROM python:3.11-slim AS final
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "ml_service.main:app", "--host", "0.0.0.0", "--port", "8000"]