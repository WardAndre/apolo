from abc import ABC, abstractmethod

from app.schemas.generation import TrackGenerationRequest
from app.schemas.track import Track


class BaseTrackGenerator(ABC):
    @abstractmethod
    def generate_track(self, request: TrackGenerationRequest) -> Track:
        pass

    @abstractmethod
    def get_info(self) -> dict:
        pass

    def get_generation_job(self, job_id: str) -> dict | None:
        return None

    def list_recent_generation_jobs(self, limit: int = 20) -> list[dict]:
        return []

    def list_recent_tracks(self, limit: int = 20) -> list[dict]:
        return []