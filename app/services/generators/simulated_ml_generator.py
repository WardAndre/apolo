from app.schemas.generation import TrackGenerationRequest
from app.schemas.track import Track
from app.services.generators.base import BaseTrackGenerator


class SimulatedMLTrackGenerator(BaseTrackGenerator):
    def __init__(self) -> None:
        self.name = "simulated_ml_track_generator"
        self.version = "1.0"

    def generate_track(self, request: TrackGenerationRequest) -> Track:
        return Track(
            sequence_number=request.sequence_number,
            title=request.title,
            bpm=request.bpm,
            energy=request.energy,
            mood=request.mood,
            musical_key=request.musical_key,
            duration_seconds=request.duration_seconds,
            generator_name=self.name,
            audio_asset_uri=(
                f"simulated-ml://apolo/"
                f"{request.style.lower().replace(' ', '-')}/"
                f"track-{request.sequence_number}"
            ),
        )

    def get_info(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "type": "simulated_ml",
            "supports_real_audio_generation": False,
            "supports_metadata_generation": True,
            "notes": "Placeholder for future ML integration.",
        }