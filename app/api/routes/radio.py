from fastapi import APIRouter, HTTPException, Query, Request, Response

from app.core.settings import get_settings
from app.services.orchestrator import radio_orchestrator

router = APIRouter(prefix="/radio", tags=["radio"])


def _absolute_asset_url(request: Request, asset_uri: str | None) -> str | None:
    if asset_uri is None:
        return None

    if asset_uri.startswith("http://") or asset_uri.startswith("https://"):
        return asset_uri

    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}{asset_uri}"


def _with_absolute_asset_url(request: Request, track: dict | None) -> dict | None:
    if track is None:
        return None

    payload = dict(track)
    payload["absolute_audio_asset_url"] = _absolute_asset_url(
        request,
        payload.get("audio_asset_uri"),
    )
    return payload


@router.get("/profile")
def get_radio_profile():
    return radio_orchestrator.get_profile()


@router.get("/settings")
def get_radio_settings():
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "app_env": settings.app_env,
        "generator_backend": settings.generator_backend,
        "ml_provider": settings.ml_provider,
        "database_url_configured": bool(settings.database_url),
        "asset_storage_dir": settings.asset_storage_dir,
        "asset_public_path": settings.asset_public_path,
        "placeholder_asset_seconds": settings.placeholder_asset_seconds,
    }


@router.get("/generator")
def get_generator_info():
    return radio_orchestrator.get_generator_info()


@router.get("/provider")
def get_provider_info():
    generator_info = radio_orchestrator.get_generator_info()
    provider = generator_info.get("provider")

    if provider is None:
        raise HTTPException(status_code=404, detail="Current generator has no provider")

    return provider


@router.get("/generation-jobs/{job_id}")
def get_generation_job(job_id: str):
    job = radio_orchestrator.get_generation_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Generation job not found")

    return job


@router.get("/history/generation-jobs")
def list_recent_generation_jobs(limit: int = Query(default=20, ge=1, le=100)):
    items = radio_orchestrator.list_recent_generation_jobs(limit)
    return {
        "items": items,
        "count": len(items),
    }


@router.get("/history/tracks")
def list_recent_tracks(limit: int = Query(default=20, ge=1, le=100)):
    items = radio_orchestrator.list_recent_tracks(limit)
    return {
        "items": items,
        "count": len(items),
    }


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


@router.get("/stream/now-playing")
def get_now_playing(request: Request):
    current_track = radio_orchestrator.get_now_playing()
    playback_state = radio_orchestrator.get_playback_state()

    return {
        "is_playing": playback_state["is_playing"],
        "current_track": _with_absolute_asset_url(request, current_track),
        "next_track": _with_absolute_asset_url(request, playback_state["next_track"]),
    }


@router.get("/stream/queue")
def get_stream_queue(request: Request):
    queue = radio_orchestrator.get_playout_queue()

    items = [_with_absolute_asset_url(request, track) for track in queue]

    return {
        "items": items,
        "count": len(items),
    }


@router.get("/stream/playlist.m3u")
def get_stream_playlist(request: Request):
    queue = radio_orchestrator.get_playout_queue()

    lines = ["#EXTM3U"]

    for track in queue:
        asset_url = _absolute_asset_url(request, track.get("audio_asset_uri"))

        if asset_url is None:
            continue

        title = track.get("title", "Untitled Track")
        duration_seconds = int(track.get("duration_seconds", 0))

        lines.append(f"#EXTINF:{duration_seconds},{title}")
        lines.append(asset_url)

    playlist_content = "\n".join(lines) + "\n"
    return Response(content=playlist_content, media_type="audio/x-mpegurl")


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