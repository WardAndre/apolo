from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

EnergyLevel = Literal["medium", "medium_high"]
MoodType = Literal["hypnotic", "deep", "spatial", "nocturnal"]


class Track(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    sequence_number: int
    title: str
    bpm: int
    energy: EnergyLevel
    mood: MoodType
    musical_key: str
    duration_seconds: int
    generator_name: str
    provider_name: str | None = None
    generation_job_id: str | None = None
    generation_status: Literal["queued", "processing", "completed", "failed"] = "completed"
    generation_time_ms: int | None = None
    prompt_text: str | None = None
    audio_asset_uri: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))