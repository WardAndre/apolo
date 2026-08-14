from pathlib import Path

from app.core.settings import get_settings
from app.schemas.track import Track


class PlayoutManifestWriter:
    def __init__(self) -> None:
        self.settings = get_settings()

        self.manifest_path = Path(self.settings.playout_manifest_path)
        self.playout_asset_root = Path(self.settings.playout_asset_root)

        self.asset_public_path = self.settings.asset_public_path.rstrip("/")

    def ensure_dirs(self) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

    def write_queue(self, tracks: list[Track]) -> str:
        self.ensure_dirs()

        lines = ["#EXTM3U"]

        for track in tracks:
            asset_path = self._asset_uri_to_playout_path(track.audio_asset_uri)

            if asset_path is not None:
                lines.append(str(asset_path))

        self.manifest_path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

        return str(self.manifest_path.resolve())

    def _asset_uri_to_playout_path(
        self,
        asset_uri: str | None,
    ) -> Path | None:
        if not asset_uri:
            return None

        prefix = f"{self.asset_public_path}/"

        if not asset_uri.startswith(prefix):
            return None

        relative_path = asset_uri[len(prefix):]

        return self.playout_asset_root / relative_path