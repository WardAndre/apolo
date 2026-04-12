from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GeneratedAssetModel(Base):
    __tablename__ = "generated_assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    generation_job_id: Mapped[int] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    asset_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    format: Mapped[str] = mapped_column(String(50), nullable=False, default="wav")
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    generation_job = relationship("GenerationJobModel", back_populates="generated_asset")
    radio_track = relationship(
        "RadioTrackModel",
        back_populates="generated_asset",
        uselist=False,
    )