from app.schemas.generation import TrackGenerationRequest
from app.schemas.track import Track
from app.services.generators.base import BaseTrackGenerator
from app.services.generators.prompt_builder import build_music_prompt
from app.services.generators.providers.base import BaseGenerationProvider
from app.services.generators.providers.factory import get_generation_provider


class MLTrackGenerator(BaseTrackGenerator):
    def __init__(self, provider: BaseGenerationProvider | None = None) -> None:
        self.name = "ml_pipeline_generator"
        self.version = "1.0"
        self.provider = provider or get_generation_provider()

    def generate_track(self, request: TrackGenerationRequest) -> Track:
        prompt_text = build_music_prompt(request)

        submitted_job = self.provider.submit_generation_job(request, prompt_text)
        completed_job = self.provider.wait_for_job_completion(submitted_job.job_id)

        return Track(
            sequence_number=request.sequence_number,
            title=request.title,
            bpm=request.bpm,
            energy=request.energy,
            mood=request.mood,
            musical_key=request.musical_key,
            duration_seconds=request.duration_seconds,
            generator_name=self.name,
            provider_name=completed_job.provider_name,
            generation_job_id=completed_job.job_id,
            generation_status=completed_job.status,
            generation_time_ms=completed_job.generation_time_ms,
            prompt_text=completed_job.prompt_text,
            audio_asset_uri=completed_job.audio_asset_uri,
        )

    def get_info(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "type": "ml_pipeline",
            "supports_real_audio_generation": False,
            "supports_provider_jobs": True,
            "provider": self.provider.get_info(),
        }

    def get_generation_job(self, job_id: str) -> dict | None:
        job = self.provider.get_job(job_id)
        return job.model_dump() if job else None