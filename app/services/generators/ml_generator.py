from app.core.database import SessionLocal
from app.repositories.generated_asset_repository import GeneratedAssetRepository
from app.repositories.generation_job_repository import GenerationJobRepository
from app.repositories.radio_track_repository import RadioTrackRepository
from app.schemas.generation import TrackGenerationRequest
from app.schemas.track import Track
from app.services.generators.base import BaseTrackGenerator
from app.services.generators.prompt_builder import build_music_prompt
from app.services.generators.providers.base import BaseGenerationProvider
from app.services.generators.providers.factory import get_generation_provider
from app.services.storage.audio_asset_storage import AudioAssetStorage


class MLTrackGenerator(BaseTrackGenerator):
    def __init__(self, provider: BaseGenerationProvider | None = None) -> None:
        self.name = "ml_pipeline_generator"
        self.version = "3.0"
        self.provider = provider or get_generation_provider()
        self.asset_storage = AudioAssetStorage()

    def generate_track(self, request: TrackGenerationRequest) -> Track:
        prompt_text = build_music_prompt(request)
        submitted_job = self.provider.submit_generation_job(request, prompt_text)

        with SessionLocal() as db:
            job_repo = GenerationJobRepository(db)
            asset_repo = GeneratedAssetRepository(db)
            track_repo = RadioTrackRepository(db)

            db_job = job_repo.create_submitted_job(
                request=request,
                generator_name=self.name,
                provider_name=submitted_job.provider_name,
                provider_job_id=submitted_job.job_id,
                prompt_text=prompt_text,
            )

            try:
                completed_job = self.provider.wait_for_job_completion(submitted_job.job_id)
                job_repo.mark_completed(db_job, completed_job)

                public_asset_uri = self.asset_storage.create_placeholder_asset(
                    sequence_number=request.sequence_number,
                    provider_job_id=submitted_job.job_id,
                    bpm=request.bpm,
                    mood=request.mood,
                    duration_seconds=request.duration_seconds,
                )

                db_asset = asset_repo.create_asset(
                    generation_job_id=db_job.id,
                    asset_uri=public_asset_uri,
                    duration_seconds=request.duration_seconds,
                    asset_format="wav",
                )

                track = Track(
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
                    audio_asset_uri=public_asset_uri,
                )

                track_repo.create_track(
                    generation_job_id=db_job.id,
                    generated_asset_id=db_asset.id,
                    track=track,
                )

                db.commit()
                return track

            except Exception as exc:
                db.rollback()

                db_job = job_repo.get_by_provider_job_id(submitted_job.job_id)
                if db_job is not None:
                    job_repo.mark_failed(db_job, str(exc))
                    db.commit()

                raise

    def get_info(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "type": "ml_pipeline",
            "supports_real_audio_generation": False,
            "supports_provider_jobs": True,
            "supports_persistence": True,
            "supports_playout_assets": True,
            "provider": self.provider.get_info(),
        }

    def get_generation_job(self, job_id: str) -> dict | None:
        provider_job = self.provider.get_job(job_id)
        provider_job_dict = provider_job.model_dump() if provider_job is not None else None

        with SessionLocal() as db:
            job_repo = GenerationJobRepository(db)
            db_job = job_repo.get_by_provider_job_id(job_id)

            if db_job is None:
                return provider_job_dict

            return {
                "job_id": db_job.provider_job_id,
                "provider_name": db_job.provider_name,
                "status": db_job.status,
                "prompt_text": db_job.prompt_text,
                "submitted_at": db_job.submitted_at,
                "completed_at": db_job.completed_at,
                "generation_time_ms": db_job.generation_time_ms,
                "audio_asset_uri": (
                    db_job.generated_asset.asset_uri if db_job.generated_asset else None
                ),
                "error_message": db_job.error_message,
            }

    def list_recent_generation_jobs(self, limit: int = 20) -> list[dict]:
        with SessionLocal() as db:
            job_repo = GenerationJobRepository(db)
            jobs = job_repo.list_recent(limit=limit)

            return [
                {
                    "id": job.id,
                    "provider_job_id": job.provider_job_id,
                    "sequence_number": job.sequence_number,
                    "title": job.title,
                    "status": job.status,
                    "provider_name": job.provider_name,
                    "generator_name": job.generator_name,
                    "generation_time_ms": job.generation_time_ms,
                    "submitted_at": job.submitted_at,
                    "completed_at": job.completed_at,
                    "audio_asset_uri": (
                        job.generated_asset.asset_uri if job.generated_asset else None
                    ),
                }
                for job in jobs
            ]

    def list_recent_tracks(self, limit: int = 20) -> list[dict]:
        with SessionLocal() as db:
            track_repo = RadioTrackRepository(db)
            tracks = track_repo.list_recent(limit=limit)

            return [
                {
                    "id": track.id,
                    "sequence_number": track.sequence_number,
                    "title": track.title,
                    "bpm": track.bpm,
                    "energy": track.energy,
                    "mood": track.mood,
                    "musical_key": track.musical_key,
                    "duration_seconds": track.duration_seconds,
                    "generator_name": track.generator_name,
                    "provider_name": track.provider_name,
                    "audio_asset_uri": (
                        track.generated_asset.asset_uri if track.generated_asset else None
                    ),
                    "created_at": track.created_at,
                }
                for track in tracks
            ]