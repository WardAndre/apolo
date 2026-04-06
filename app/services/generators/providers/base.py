from abc import ABC, abstractmethod

from app.schemas.generation import ProviderGenerationJob, TrackGenerationRequest


class BaseGenerationProvider(ABC):
    @abstractmethod
    def submit_generation_job(
        self,
        request: TrackGenerationRequest,
        prompt_text: str,
    ) -> ProviderGenerationJob:
        pass

    @abstractmethod
    def wait_for_job_completion(self, job_id: str) -> ProviderGenerationJob:
        pass

    @abstractmethod
    def get_job(self, job_id: str) -> ProviderGenerationJob | None:
        pass

    @abstractmethod
    def get_info(self) -> dict:
        pass