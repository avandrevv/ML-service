import os
import time
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
import httpx
from joblib import load
import numpy as np
import psycopg2
from psycopg2.extras import Json

from app.schemas import GenerateRequest, PredictRequest, PredictResponse

load_dotenv()

app = FastAPI()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost:11434")
OLLAMA_GENERATE_URL = f"http://{OLLAMA_HOST}/api/generate"
OLLAMA_PULL_URL = f"http://{OLLAMA_HOST}/api/pull"

model = load("model.joblib")
scaler = load("scaler.joblib")


def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "predict_logs_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("PGPASSWORD"),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
            connect_timeout=3
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"DB Connection Error: {e}")
        return None


def init_db():
    """Создает таблицу при первом запуске."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS predict_logs (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT NOW(),
                        features JSONB,
                        prediction INTEGER,
                        confidence FLOAT,
                        processing_time_ms FLOAT,
                        ip VARCHAR(45),
                        user_agent TEXT
                    );
                """)
        except Exception as e:
            print(f"Failed to create table: {e}")
        finally:
            conn.close()


init_db()


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest, req: Request):
    start = time.time()
    X = np.array(request.features).reshape(1, -1)
    X_scaled = scaler.transform(X)
    pred = int(model.predict(X_scaled)[0])
    conf = float(model.predict_proba(X_scaled).max())
    elapsed = (time.time() - start) * 1000

    client_ip = req.client.host if req.client else "127.0.0.1"

    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO predict_logs (features, prediction, confidence,
                    processing_time_ms, ip, user_agent)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        Json(request.features),
                        pred,
                        conf,
                        round(elapsed, 2),
                        client_ip,
                        req.headers.get("user-agent", "unknown")
                    )
                )
        except Exception as e:
            print(f"Logging failed: {e}")
        finally:
            conn.close()

    return PredictResponse(
        prediction=pred,
        confidence=conf,
        processing_time_ms=round(elapsed, 2)
    )


@app.get("/logs")
def get_logs():
    conn = get_db_connection()
    if not conn:
        return {"error": "Database connection failed"}

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, timestamp, features, prediction, confidence, "
                "processing_time_ms, ip, user_agent "
                "FROM predict_logs ORDER BY id DESC LIMIT 10"
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "timestamp": r[1].isoformat(),
                    "features": r[2],
                    "prediction": r[3],
                    "confidence": r[4],
                    "processing_time_ms": r[5],
                    "ip": r[6],
                    "user_agent": r[7]
                }
                for r in rows
            ]
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


@app.post("/generate")
async def generate_text(request: GenerateRequest):
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            payload = {
                "model": request.model,
                "prompt": request.prompt,
                "stream": False,
            }
            response = await client.post(
                OLLAMA_GENERATE_URL,
                json=payload
            )

            if response.status_code == 404:
                pull_response = await client.post(
                    OLLAMA_PULL_URL,
                    json={"name": request.model, "stream": False}
                )
                pull_response.raise_for_status()

                response = await client.post(
                    OLLAMA_GENERATE_URL,
                    json=payload
                )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Ollama API Error: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Не удалось связаться с сервисом Ollama: {str(e)}"
            )
