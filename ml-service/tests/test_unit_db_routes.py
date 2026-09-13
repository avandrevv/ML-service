import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parent.parent))

from ml_service.main import app

client = TestClient(app, raise_server_exceptions=False)


def _mock_conn(rows=None, one=None):
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    if rows is not None:
        cur.fetchall.return_value = rows
    if one is not None:
        cur.fetchone.return_value = one
    return conn


@patch("ml_service.routers.db_routes.get_db_connection")
def test_get_logs_success(mock_get_conn):
    rows = [
        (1, datetime(2025, 1, 1, 12, 0), [1.0, 2.0, 3.0, 4.0], 1, 0.95, 12.5,
         "127.0.0.1", "pytest"),
    ]
    conn = _mock_conn(rows=rows)
    mock_get_conn.return_value = conn

    resp = client.get("/logs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["prediction"] == 1
    assert data[0]["ip"] == "127.0.0.1"
    assert data[0]["timestamp"] == "2025-01-01T12:00:00"
    conn.close.assert_called_once()


@patch("ml_service.routers.db_routes.get_db_connection")
def test_get_logs_empty(mock_get_conn):
    mock_get_conn.return_value = _mock_conn(rows=[])
    resp = client.get("/logs")
    assert resp.status_code == 200
    assert resp.json() == []


@patch("ml_service.routers.db_routes.get_db_connection")
def test_get_logs_no_connection(mock_get_conn):
    mock_get_conn.return_value = None
    resp = client.get("/logs")
    assert resp.status_code == 200
    assert resp.json() == {"error": "Database connection failed"}


@patch("ml_service.routers.db_routes.get_db_connection")
def test_get_logs_exception(mock_get_conn):
    conn = _mock_conn()
    conn.cursor.return_value.__enter__.return_value.execute.side_effect = \
        Exception("boom")
    mock_get_conn.return_value = conn

    resp = client.get("/logs")
    assert resp.status_code == 200
    assert "boom" in resp.json()["error"]
    conn.close.assert_called_once()


@patch("ml_service.routers.db_routes.get_db_connection")
def test_get_prompts_success(mock_get_conn):
    rows = [
        (1, datetime(2025, 1, 1, 12, 0), "tinyllama", "hi", "127.0.0.1", "pytest"),
    ]
    conn = _mock_conn(rows=rows)
    mock_get_conn.return_value = conn

    resp = client.get("/prompts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["model"] == "tinyllama"
    assert data[0]["prompt"] == "hi"
    conn.close.assert_called_once()


@patch("ml_service.routers.db_routes.get_db_connection")
def test_get_prompts_empty(mock_get_conn):
    mock_get_conn.return_value = _mock_conn(rows=[])
    resp = client.get("/prompts")
    assert resp.status_code == 200
    assert resp.json() == []


@patch("ml_service.routers.db_routes.get_db_connection")
def test_get_prompts_no_connection(mock_get_conn):
    mock_get_conn.return_value = None
    resp = client.get("/prompts")
    assert resp.json() == {"error": "Database connection failed"}


@patch("ml_service.routers.db_routes.get_db_connection")
def test_get_prompts_exception(mock_get_conn):
    conn = _mock_conn()
    conn.cursor.return_value.__enter__.return_value.execute.side_effect = \
        Exception("fail")
    mock_get_conn.return_value = conn

    resp = client.get("/prompts")
    assert "fail" in resp.json()["error"]
    conn.close.assert_called_once()


@patch("ml_service.routers.db_routes.get_db_connection")
def test_get_stats_success(mock_get_conn):
    conn = _mock_conn()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.side_effect = [
        (10, 100, 0.85, 12.5),   # overall
        (5, 3),                   # prompts
    ]
    cur.fetchall.return_value = [
        (datetime(2025, 1, 1), 50, 0.9, 10.0, 5),
        (datetime(2025, 1, 2), 50, 0.8, 15.0, 4),
    ]
    mock_get_conn.return_value = conn

    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_predictions"] == 100
    assert data["avg_confidence"] == 0.85
    assert data["avg_processing_time_ms"] == 12.5
    assert len(data["last_7_days"]) == 2
    assert data["last_7_days"][0]["date"] == "2025-01-01T00:00:00"
    assert data["prompts_last_24h"] == 5
    assert data["unique_models_24h"] == 3
    conn.close.assert_called_once()


@patch("ml_service.routers.db_routes.get_db_connection")
def test_get_stats_none_values(mock_get_conn):
    """Проверяем ветки с None -> 0."""
    conn = _mock_conn()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchone.side_effect = [
        (0, None, None, None),
        None,
    ]
    cur.fetchall.return_value = [
        (datetime(2025, 1, 1), None, None, None, None),
    ]
    mock_get_conn.return_value = conn

    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_predictions"] == 0
    assert data["avg_confidence"] == 0
    assert data["avg_processing_time_ms"] == 0
    assert data["last_7_days"][0]["predictions"] == 0
    assert data["last_7_days"][0]["confidence"] == 0
    assert data["prompts_last_24h"] == 0
    assert data["unique_models_24h"] == 0


@patch("ml_service.routers.db_routes.get_db_connection")
def test_get_stats_no_connection(mock_get_conn):
    mock_get_conn.return_value = None
    resp = client.get("/stats")
    assert resp.json() == {"error": "Database connection failed"}


@patch("ml_service.routers.db_routes.get_db_connection")
def test_get_stats_exception(mock_get_conn):
    conn = _mock_conn()
    conn.cursor.return_value.__enter__.return_value.execute.side_effect = \
        Exception("stats fail")
    mock_get_conn.return_value = conn

    resp = client.get("/stats")
    assert "stats fail" in resp.json()["error"]
    conn.close.assert_called_once()
