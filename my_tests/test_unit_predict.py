import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.app import app 

client = TestClient(app)

def test_predict_positive():
    response = client.post(
        "/predict",
        json={"features": [5.1, 3.5, 1.4, 0.2]}
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "prediction" in data
    assert "confidence" in data
    assert "processing_time_ms" in data
    
    assert isinstance(data["prediction"], int)
    assert isinstance(data["confidence"], float)
    assert isinstance(data["processing_time_ms"], float)
    
    assert 0 <= data["confidence"] <= 1


def test_predict_wrong_length():
    response = client.post(
        "/predict",
        json={"features": [1, 2, 3]} 
    )
    
    assert response.status_code == 422


def test_predict_missing_field():
    response = client.post(
        "/predict",
        json={}  
    )
    
    assert response.status_code == 422


def test_predict_wrong_type():
    response = client.post(
        "/predict",
        json={"features": ["a", "b", "c", "d"]}
    )
    
    assert response.status_code == 422
    
if __name__ == "__main__":
    test_predict_positive()
    test_predict_wrong_length()
    test_predict_missing_field()
    test_predict_wrong_type()
    print("Тест пройдены успешно")