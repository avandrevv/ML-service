from fastapi import FastAPI
from joblib import load
import numpy as np
import time

from app.schemas import PredictRequest, PredictResponse

app = FastAPI()

model = load('model.joblib')
scaler = load('scaler.joblib')

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    start = time.time()
    
    X = np.array(request.features).reshape(1, -1)
    X_scaled = scaler.transform(X)
    
    pred = int(model.predict(X_scaled)[0])
    conf = float(model.predict_proba(X_scaled).max())
    elapsed = (time.time() - start) * 1000
    
    return PredictResponse(
        prediction=pred,
        confidence=conf,
        processing_time_ms=round(elapsed, 2)
    )