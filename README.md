# ML Service

FastAPI сервис для предсказаний с логированием запросов в PostgreSQL.

## Установка и запуск

### Через Docker Compose


```bash
docker-compose up --build
```

### Локально
```bash
pip install -r requirements.txt
python -m uvicorn app.app:app --reload
```


## Запуск готового Docker-образа из реестра

```bash
docker pull ghcr.io/avandrevv/ml-service:latest
docker run -p 8000:8000 ghcr.io/avandrevv/ml-service:latest
```

Для успешного поднятия образа из реестра требуется **запущенный PostgreSQL**. 
При локальном поднятии сервера FastAPI может рабоать без логирования (без БД).
При запуске docker-compose запуск БД не требуется.

## Переменные окружения
Необходим файл `.env` со следующим содержимым:
```env
PGPASSWORD=your_password
```

## Эндпоинты
| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | Проверка статуса сервиса |
| POST | `/predict` | Предсказание по признакам |
| POST | `/generate` | Генерация текста через сервис Ollama |
| GET | `/logs` | Последние 10 записей логов |

### Пример запроса `/predict`
```json
{
  "features": [5.1, 3.5, 1.4, 0.2]
}
```

### Пример ответа `/predict`
```json
{
  "prediction": 0,
  "confidence": 0.95,
  "processing_time_ms": 1.23
}
```


### Пример запроса `/generate`
```json
{
  "prompt": "Hi, im andrew and how is your name",
  "model": "tinyllama"
}
```


### Пример ответа `/generate`
```json
{
  "model": "tinyllama",
  "response": "Hello Andrew! I am an AI assistant.",
  "done": true
}
```

## Тесты
```bash
docker-compose exec app pytest my_tests/ -v
```

## CI/CD
GitHub Actions запускает тесты и сборку Docker при каждом пуше в ветку `master`.

## Структура проекта
```
.
├── app/
│   ├── app.py
│   └── schemas.py
├── my_tests/
├── model.joblib
├── scaler.joblib
├── requirements.txt
├── Dockerfile
├── Dockerfile.ollama
├── docker-compose.yml
└── README.md
```

## Упрощённая визуализация архитектуры сервиса
```mermaid
graph LR
    A[Клиент] --> B[FastAPI]
    B --> C["/health"]
    B --> D["/predict"]
    B --> E["/generate"]
    B --> F["/logs"]
    D --> G[(PostgreSQL)]
    F <--> G
    E --> H[Ollama API]
    I[pytest + Mocking] --> B
    J[GitHub Actions] --> I
    J --> K[Сборка Docker]
    K --> L[Образ ml-service]
```
