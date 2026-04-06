import random
import time
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.generation import ProviderGenerationJob, TrackGenerationRequest
from app.services.generators.providers.base import BaseGenerationProvider


def _slugify(value: str) -> str:
    return value.lower().replace(" ", "-").replace("/", "-")


class SimulatedVertexProvider(BaseGenerationProvider):
    def __init__(self) -> None:
        self.name = "simulated_vertex_provider"
        self.version = "1.0"
        self._jobs: dict[str, ProviderGenerationJob] = {}

    def submit_generation_job(
        self,
        request: TrackGenerationRequest,
        prompt_text: str,
    ) -> ProviderGenerationJob:
        job = ProviderGenerationJob(
            job_id=str(uuid4()),
            provider_name=self.name,
            status="submitted",
            prompt_text=prompt_text,
        )
        self._jobs[job.job_id] = job
        return job

    def wait_for_job_completion(self, job_id: str) -> ProviderGenerationJob:
        job = self._jobs.get(job_id)

        if job is None:
            raise ValueError(f"Generation job not found: {job_id}")

        if job.status == "completed":
            return job

        processing_job = job.model_copy(update={"status": "processing"})
        self._jobs[job_id] = processing_job

        started_at = time.perf_counter()
        simulated_latency_ms = random.randint(1200, 2600)
        time.sleep(simulated_latency_ms / 1000)
        finished_at = time.perf_counter()

        generation_time_ms = int((finished_at - started_at) * 1000)

        completed_job = processing_job.model_copy(
            update={
                "status": "completed",
                "completed_at": datetime.now(timezone.utc),
                "generation_time_ms": generation_time_ms,
                "audio_asset_uri": (
                    f"simulated-vertex://apolo/jobs/{_slugify(job_id)}/audio.wav"
                ),
            }
        )

        self._jobs[job_id] = completed_job
        return completed_job

    def get_job(self, job_id: str) -> ProviderGenerationJob | None:
        return self._jobs.get(job_id)

    def get_info(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "type": "simulated_provider",
            "supports_async_jobs": True,
            "supports_real_audio_generation": False,
        }