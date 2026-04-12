from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models.generation_job import GenerationJobModel
from app.schemas.generation import ProviderGenerationJob, TrackGenerationRequest


class GenerationJobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_submitted_job(
        self,
        request: TrackGenerationRequest,
        generator_name: str,
        provider_name: str,
        provider_job_id: str,
        prompt_text: str,
    ) -> GenerationJobModel:
        db_job = GenerationJobModel(
            sequence_number=request.sequence_number,
            title=request.title,
            style=request.style,
            mode=request.mode,
            generator_name=generator_name,
            provider_name=provider_name,
            provider_job_id=provider_job_id,
            status="submitted",
            prompt_text=prompt_text,
        )
        self.db.add(db_job)
        self.db.flush()
        return db_job

    def mark_completed(
        self,
        db_job: GenerationJobModel,
        completed_job: ProviderGenerationJob,
    ) -> GenerationJobModel:
        db_job.status = completed_job.status
        db_job.generation_time_ms = completed_job.generation_time_ms
        db_job.completed_at = completed_job.completed_at
        db_job.error_message = completed_job.error_message
        self.db.flush()
        return db_job

    def mark_failed(
        self,
        db_job: GenerationJobModel,
        error_message: str,
    ) -> GenerationJobModel:
        db_job.status = "failed"
        db_job.error_message = error_message
        self.db.flush()
        return db_job

    def get_by_provider_job_id(self, provider_job_id: str) -> GenerationJobModel | None:
        stmt = select(GenerationJobModel).where(
            GenerationJobModel.provider_job_id == provider_job_id
        )
        return self.db.scalar(stmt)

    def list_recent(self, limit: int = 20) -> list[GenerationJobModel]:
        stmt = (
            select(GenerationJobModel)
            .order_by(desc(GenerationJobModel.id))
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())