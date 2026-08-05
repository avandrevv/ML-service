from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    features: list[float] = Field(..., min_length=4, max_length=4)


class PredictResponse(BaseModel):
    prediction: int
    confidence: float
    processing_time_ms: float


class GenerateRequest(BaseModel):
    prompt: str
    model: str = "tinyllama"
