from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.health import router as health_router
from app.api.routes.radio import router as radio_router
from app.core.database import init_db
from app.core.settings import get_settings
from app.services.storage.audio_asset_storage import AudioAssetStorage
from app.services.orchestrator import radio_orchestrator

settings = get_settings()

Path(settings.asset_storage_dir).mkdir(parents=True, exist_ok=True)
Path(settings.hls_output_dir).mkdir(parents=True, exist_ok=True)
Path(settings.playout_manifest_path).parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    AudioAssetStorage().ensure_storage_dir()
    radio_orchestrator.restore_persistent_state()


app.mount(
    settings.asset_public_path,
    StaticFiles(directory=settings.asset_storage_dir),
    name="assets",
)

app.mount(
    settings.hls_public_path,
    StaticFiles(directory=settings.hls_output_dir),
    name="hls",
)

app.include_router(health_router)
app.include_router(radio_router)