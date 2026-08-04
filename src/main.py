from fastapi import FastAPI

from src.database import init_db
from src.routers.db_routes import db_router
from src.routers.prompt_routes import prompt_router

app = FastAPI()
app.include_router(db_router)
app.include_router(prompt_router)


init_db()


@app.get("/health")
def health():
    return {"status": "healthy"}
