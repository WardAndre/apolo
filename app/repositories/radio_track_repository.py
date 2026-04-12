from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models.radio_track import RadioTrackModel
from app.schemas.track import Track


class RadioTrackRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_track(
        self,
        generation_job_id: int,
        generated_asset_id: int | None,
        track: Track,
    ) -> RadioTrackModel:
        db_track = RadioTrackModel(
            generation_job_id=generation_job_id,
            generated_asset_id=generated_asset_id,
            sequence_number=track.sequence_number,
            title=track.title,
            bpm=track.bpm,
            energy=track.energy,
            mood=track.mood,
            musical_key=track.musical_key,
            duration_seconds=track.duration_seconds,
            generator_name=track.generator_name,
            provider_name=track.provider_name,
        )
        self.db.add(db_track)
        self.db.flush()
        return db_track

    def list_recent(self, limit: int = 20) -> list[RadioTrackModel]:
        stmt = (
            select(RadioTrackModel)
            .order_by(desc(RadioTrackModel.id))
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())