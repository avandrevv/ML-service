import sys
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.app import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=False)


@patch("app.app.httpx.AsyncClient.post")
def test_generate_positive(mock_post):
    async def mock_post_async(*args, **kwargs):
        fake_request = httpx.Request(
            "POST", "http://ollama:11434/api/generate"
        )
        return httpx.Response(
            status_code=200,
            json={
                "model": "tinyllama",
                "response": "Hello Andrew! I am an AI assistant.",
                "done": True,
            },
            request=fake_request,
        )

    mock_post.side_effect = mock_post_async

    response = client.post(
        "/generate",
        json={
            "prompt": "Hi, im andrew and how is your name",
            "model": "tinyllama",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "model" in data
    assert data["model"] == "tinyllama"
    assert isinstance(data["response"], str)


def test_generate_missing_field():
    response = client.post("/generate", json={})
    assert response.status_code == 422


def test_generate_wrong_type():
    response = client.post(
        "/generate",
        json={"prompt": 12345, "model": "tinyllama"},
    )
    assert response.status_code == 422


@patch("app.app.httpx.AsyncClient.post")
def test_generate_ollama_error(mock_post):
    async def mock_network_error(*args, **kwargs):
        raise httpx.ConnectError("Connection failed")

    mock_post.side_effect = mock_network_error

    response = client.post(
        "/generate",
        json={"prompt": "Hello", "model": "tinyllama"},
    )

    assert response.status_code == 500

    if "application/json" in response.headers.get("content-type", ""):
        data = response.json()
        if "detail" in data:
            assert "Не удалось связаться с сервисом Ollama" in data["detail"]


if __name__ == "__main__":
    test_generate_positive()
    test_generate_missing_field()
    test_generate_wrong_type()
    test_generate_ollama_error()
    print("Все тесты generate успешно пройдены!")
