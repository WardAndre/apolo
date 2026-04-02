from pydantic import BaseModel

from app.schemas.track import EnergyLevel, MoodType


class TrackGenerationRequest(BaseModel):
    sequence_number: int
    title: str
    style: str
    mode: str
    bpm: int
    energy: EnergyLevel
    mood: MoodType
    musical_key: str
    duration_seconds: int

class TrackGenerationResult(BaseModel):
    generator_name: str
    generation_status: str
    generation_time_ms: int
    prompt_text: str
    audio_asset_uri: str