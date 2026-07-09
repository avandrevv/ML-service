## Архитектура ML-сервиса на основе FastAPI
* Выбранная модель: sklearn.linear_model, LogisticRegression (backlog: развернуть несколько моделей, в том числе LLM)
* Модели храняться в формате .joblib
* pydantic для автоматической валидации вводимых и выходных данных
* postgresql - выбранная БД
