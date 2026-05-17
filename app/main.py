from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import admin, answers, dashboard, knowledge, questionnaires

app = FastAPI(title="Sentinel GRC", version="0.1.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(dashboard.router, tags=["dashboard"])
app.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
app.include_router(questionnaires.router, prefix="/questionnaires", tags=["questionnaires"])
app.include_router(answers.router, prefix="/answers", tags=["answers"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
