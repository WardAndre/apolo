from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.radio import router as radio_router
from app.core.database import init_db

app = FastAPI(title="Projeto Apolo")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(health_router)
app.include_router(radio_router)