FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /venv
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt
COPY . .

FROM python:3.11-slim AS final
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /app /app
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]