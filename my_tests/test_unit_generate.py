import sys
import os
from unittest.mock import patch
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.app import app 

client = TestClient(app)

@patch("app.app.httpx.AsyncClient.post")
def test_generate_positive(mock_post):
    fake_request = httpx.Request("POST", "http://ollama:11434/api/generate")
    fake_response = httpx.Response(
        status_code=200,
        json={
            "model": "tinyllama",
            "response": "Hello Andrew! I am an AI assistant.",
            "done": True
        },
        request=fake_request
    )
    mock_post.return_value = fake_response

    response = client.post(
        "/generate",
        json={"prompt": "Hi, im andrew and how is your name", "model": "tinyllama"}
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
        json={"prompt": 12345, "model": "tinyllama"}
    )
    assert response.status_code == 422


@patch("app.app.httpx.AsyncClient.post")
def test_generate_ollama_error(mock_post):
    async def mock_network_error(*args, **kwargs):
        raise httpx.ConnectError("Connection failed")
        
    mock_post.side_effect = mock_network_error

    try:
        response = client.post(
            "/generate",
            json={"prompt": "Hello", "model": "tinyllama"}
        )
        assert response.status_code == 500
        assert "Не удалось связаться с сервисом Ollama" in response.json()["detail"]
    except httpx.ConnectError:
        pass


if __name__ == "__main__":
    test_generate_positive() 
    test_generate_missing_field()
    test_generate_wrong_type()
    test_generate_ollama_error()
    
    print("Все тесты Ollama пройдены успешно через __main__!")