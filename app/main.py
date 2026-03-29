from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.radio import router as radio_router

app = FastAPI(title="Projeto Apolo")

app.include_router(health_router)
app.include_router(radio_router)