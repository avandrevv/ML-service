from fastapi import APIRouter, HTTPException, Request
from dotenv import load_dotenv
import httpx
from joblib import load
import numpy as np
from psycopg2.extras import Json
import time
import os

from src.database import get_db_connection
from src.schemas import GenerateRequest, PredictRequest, PredictResponse

load_dotenv()

prompt_router = APIRouter()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost:11434")
OLLAMA_GENERATE_URL = f"http://{OLLAMA_HOST}/api/generate"
OLLAMA_PULL_URL = f"http://{OLLAMA_HOST}/api/pull"

model = load("model.joblib")
scaler = load("scaler.joblib")


@prompt_router.post("/predict", response_model=PredictResponse)
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


@prompt_router.post("/generate")
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