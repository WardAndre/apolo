from fastapi import APIRouter

from app.services.orchestrator import radio_orchestrator

router = APIRouter(prefix="/radio", tags=["radio"])


@router.get("/status")
def get_radio_status():
    return radio_orchestrator.get_status()


@router.post("/generate-next")
def generate_next_track():
    track = radio_orchestrator.generate_next_track()
    return {
        "message": "Next track generated and added to buffer",
        "track": track.model_dump(),
        "radio_status": radio_orchestrator.get_status(),
    }