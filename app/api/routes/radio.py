from fastapi import APIRouter

from app.services.orchestrator import radio_orchestrator

router = APIRouter(prefix="/radio", tags=["radio"])


@router.get("/profile")
def get_radio_profile():
    return radio_orchestrator.get_profile()


@router.get("/status")
def get_radio_status():
    return radio_orchestrator.get_status()


@router.get("/buffer")
def get_radio_buffer():
    return {
        "buffer": radio_orchestrator.get_buffer(),
        "buffer_minutes": radio_orchestrator.get_buffer_minutes(),
    }


@router.get("/playback")
def get_playback_state():
    return radio_orchestrator.get_playback_state()


@router.post("/generate-next")
def generate_next_track():
    track = radio_orchestrator.generate_next_track()
    return {
        "message": "Next track generated and added to buffer",
        "track": track.model_dump(),
        "radio_status": radio_orchestrator.get_status(),
    }


@router.post("/fill-buffer")
def fill_buffer():
    generated_tracks = radio_orchestrator.fill_buffer_to_target()
    return {
        "message": "Buffer filled to target",
        "generated_tracks_count": len(generated_tracks),
        "generated_tracks": [track.model_dump() for track in generated_tracks],
        "radio_status": radio_orchestrator.get_status(),
    }


@router.post("/auto-refill/check")
def check_auto_refill():
    result = radio_orchestrator.ensure_minimum_buffer()
    return {
        "message": "Auto-refill check executed",
        "result": result,
        "radio_status": radio_orchestrator.get_status(),
    }


@router.post("/playback/start")
def start_playback():
    return radio_orchestrator.start_playback()


@router.post("/playback/next")
def advance_playback():
    return radio_orchestrator.advance_to_next_track()