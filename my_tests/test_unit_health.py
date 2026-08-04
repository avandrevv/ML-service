import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.app import app

client = TestClient(app, raise_server_exceptions=False)


def test_health_positive():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_health_invalid_method():
    response = client.post("/health")
    assert response.status_code == 405


if __name__ == "__main__":
    test_health_positive()
    test_health_invalid_method()
    print("Все тесты health успешно пройдены!")
