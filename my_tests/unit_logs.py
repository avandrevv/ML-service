import sys
import os
import psycopg2

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.app import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_predict_positive():
    payload = {"features": [5.1, 3.5, 1.4, 0.2]}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "confidence" in data
    assert "processing_time_ms" in data
    assert isinstance(data["prediction"], int)
    assert 0 <= data["prediction"] <= 2

def test_predict_negative():
    payload = {"features": [10.0, -5.0, 100.0, -10.0]}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data

def test_predict_invalid():
    payload = {"features": [5.1, 3.5, 1.4]}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422

def test_db_integration():
    conn = psycopg2.connect(
        dbname="predict_logs_db",
        user="postgres",
        password=os.getenv("PGPASSWORD", "1234"),
        host=os.getenv("DB_HOST", "localhost"),
        port=5432
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO predict_logs (features, prediction, confidence, processing_time_ms, ip, user_agent) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        ('[1.0, 2.0, 3.0, 4.0]', 1, 0.95, 1.23, '127.0.0.1', 'test')
    )
    new_id = cur.fetchone()[0]
    cur.close()

    cur = conn.cursor()
    cur.execute("SELECT * FROM predict_logs WHERE id = %s", (new_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    assert row is not None
    assert row[2] == [1.0, 2.0, 3.0, 4.0]
    assert row[3] == 1

if __name__ == "__main__":
    test_health()
    test_predict_positive()
    test_predict_negative()
    test_predict_invalid()
    test_db_integration()
    print("All tests passed")