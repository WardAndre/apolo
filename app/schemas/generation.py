from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

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


class ProviderGenerationJob(BaseModel):
    job_id: str
    provider_name: str
    status: Literal["submitted", "processing", "completed", "failed"]
    prompt_text: str
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    generation_time_ms: int | None = None
    audio_asset_uri: str | None = None
    error_message: str | None = None