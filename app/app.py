import psycopg2
from psycopg2.extras import Json
from fastapi import FastAPI, Request
from app.schemas import PredictRequest, PredictResponse
import numpy as np
import time
from joblib import load
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
model = load('model.joblib')
scaler = load('scaler.joblib')

conn = None

def get_db_connection():
    return psycopg2.connect(
        dbname="predict_logs_db",
        user="postgres",
        password=os.getenv("PGPASSWORD"),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=5432
    )

@app.on_event("startup")
def startup():
    global conn
    conn = get_db_connection()
    conn.autocommit = True
    cur = conn.cursor()
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
    cur.close()

@app.on_event("shutdown")
def shutdown():
    if conn:
        conn.close()

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

    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO predict_logs (features, prediction, confidence, processing_time_ms, ip, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (Json(request.features), pred, conf, round(elapsed, 2),
             req.client.host, req.headers.get("user-agent"))
        )
        cur.close()
    except Exception as e:
        print(f"Logging failed: {e}") 

    return PredictResponse(
        prediction=pred,
        confidence=conf,
        processing_time_ms=round(elapsed, 2)
    )

@app.get("/logs")
def get_logs():
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, timestamp, features, prediction, confidence, processing_time_ms, ip, user_agent "
            "FROM predict_logs ORDER BY id DESC LIMIT 10"
        )
        rows = cur.fetchall()
        cur.close()
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