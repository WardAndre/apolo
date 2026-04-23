from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.health import router as health_router
from app.api.routes.radio import router as radio_router
from app.core.database import init_db
from app.core.settings import get_settings
from app.services.storage.audio_asset_storage import AudioAssetStorage

settings = get_settings()

Path(settings.asset_storage_dir).mkdir(parents=True, exist_ok=True)

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    AudioAssetStorage().ensure_storage_dir()


app.mount(
    settings.asset_public_path,
    StaticFiles(directory=settings.asset_storage_dir),
    name="assets",
)

app.include_router(health_router)
app.include_router(radio_router)