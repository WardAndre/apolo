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