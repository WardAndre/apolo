from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models.generated_asset import GeneratedAssetModel


class GeneratedAssetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_asset(
        self,
        generation_job_id: int,
        asset_uri: str,
        duration_seconds: int,
        asset_format: str = "wav",
    ) -> GeneratedAssetModel:
        db_asset = GeneratedAssetModel(
            generation_job_id=generation_job_id,
            asset_uri=asset_uri,
            format=asset_format,
            duration_seconds=duration_seconds,
        )
        self.db.add(db_asset)
        self.db.flush()
        return db_asset

    def list_recent(self, limit: int = 20) -> list[GeneratedAssetModel]:
        stmt = (
            select(GeneratedAssetModel)
            .order_by(desc(GeneratedAssetModel.id))
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())