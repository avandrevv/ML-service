import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.app import app 

client = TestClient(app)

def test_health_positive():
    response = client.get(
        "/health"
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"


    
if __name__ == "__main__":
    test_health_positive()
    print("Тест пройден успешно")