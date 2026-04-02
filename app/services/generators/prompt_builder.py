from app.schemas.generation import TrackGenerationRequest


def build_music_prompt(request: TrackGenerationRequest) -> str:
    return (
        f"Generate an instrumental electronic track in the style of {request.style}. "
        f"Mode: {request.mode}. "
        f"BPM: {request.bpm}. "
        f"Energy: {request.energy}. "
        f"Mood: {request.mood}. "
        f"Key: {request.musical_key}. "
        f"Duration: {request.duration_seconds} seconds. "
        f"No vocals. No speech. No jingles. "
        f"Progressive, hypnotic, immersive flow suitable for continuous radio playback."
    )