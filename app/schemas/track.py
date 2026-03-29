from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class Track(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    bpm: int
    energy: Literal["low", "medium", "high"]
    mood: str
    duration_seconds: int
    created_at: datetime = Field(default_factory=datetime.utcnow)