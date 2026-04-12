from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RadioTrackModel(Base):
    __tablename__ = "radio_tracks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    generation_job_id: Mapped[int] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    generated_asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("generated_assets.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    bpm: Mapped[int] = mapped_column(Integer, nullable=False)
    energy: Mapped[str] = mapped_column(String(50), nullable=False)
    mood: Mapped[str] = mapped_column(String(50), nullable=False)
    musical_key: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    generator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    generation_job = relationship("GenerationJobModel", back_populates="radio_track")
    generated_asset = relationship("GeneratedAssetModel", back_populates="radio_track")