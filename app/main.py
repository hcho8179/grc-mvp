from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes import knowledge, questionnaires, answers

app = FastAPI(title="GRC MVP", version="0.1.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
app.include_router(questionnaires.router, prefix="/questionnaires", tags=["questionnaires"])
app.include_router(answers.router, prefix="/answers", tags=["answers"])


@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/questionnaires")
