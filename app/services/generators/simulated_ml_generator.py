import random
import time

from app.schemas.generation import TrackGenerationRequest
from app.schemas.track import Track
from app.services.generators.base import BaseTrackGenerator
from app.services.generators.prompt_builder import build_music_prompt


class SimulatedMLTrackGenerator(BaseTrackGenerator):
    def __init__(self) -> None:
        self.name = "simulated_ml_track_generator"
        self.version = "2.0"

    def generate_track(self, request: TrackGenerationRequest) -> Track:
        prompt_text = build_music_prompt(request)

        started_at = time.perf_counter()
        simulated_latency_ms = random.randint(800, 2200)
        time.sleep(simulated_latency_ms / 1000)
        finished_at = time.perf_counter()

        generation_time_ms = int((finished_at - started_at) * 1000)

        safe_style = request.style.lower().replace(" ", "-").replace("/", "-")
        safe_mood = request.mood.lower().replace(" ", "-")

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
            generation_time_ms=generation_time_ms,
            prompt_text=prompt_text,
            audio_asset_uri=(
                f"simulated-ml://apolo/{safe_style}/{safe_mood}/track-{request.sequence_number}"
            ),
        )

    def get_info(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "type": "simulated_ml",
            "supports_real_audio_generation": False,
            "supports_metadata_generation": True,
            "simulates_generation_latency": True,
            "notes": "Placeholder for future ML integration.",
        }