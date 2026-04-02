from app.schemas.generation import TrackGenerationRequest
from app.schemas.track import Track
from app.services.generators.base import BaseTrackGenerator
from app.services.generators.prompt_builder import build_music_prompt


class MockTrackGenerator(BaseTrackGenerator):
    def __init__(self) -> None:
        self.name = "mock_track_generator"
        self.version = "1.1"

    def generate_track(self, request: TrackGenerationRequest) -> Track:
        prompt_text = build_music_prompt(request)

        return Track(
            sequence_number=request.sequence_number,
            title=request.title,
            bpm=request.bpm,
            energy=request.energy,
            mood=request.mood,
            musical_key=request.musical_key,
            duration_seconds=request.duration_seconds,
            generator_name=self.name,
            generation_status="completed",
            generation_time_ms=50,
            prompt_text=prompt_text,
            audio_asset_uri=f"mock://apolo/tracks/{request.sequence_number}",
        )

    def get_info(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "type": "mock",
            "supports_real_audio_generation": False,
            "supports_metadata_generation": True,
        }