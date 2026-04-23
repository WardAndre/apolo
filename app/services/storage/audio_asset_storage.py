import math
import struct
import wave
from pathlib import Path

from app.core.settings import get_settings


class AudioAssetStorage:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_dir = Path(self.settings.asset_storage_dir)
        self.generated_dir = self.base_dir / "generated"

    def ensure_storage_dir(self) -> None:
        self.generated_dir.mkdir(parents=True, exist_ok=True)

    def create_placeholder_asset(
        self,
        *,
        sequence_number: int,
        provider_job_id: str,
        bpm: int,
        mood: str,
        duration_seconds: int,
    ) -> str:
        self.ensure_storage_dir()

        preview_seconds = max(
            5,
            min(duration_seconds, self.settings.placeholder_asset_seconds),
        )

        safe_job_id = provider_job_id.replace("-", "")
        filename = f"track_{sequence_number:04d}_{safe_job_id}.wav"
        output_path = self.generated_dir / filename

        if not output_path.exists():
            self._render_placeholder_wav(
                output_path=output_path,
                seconds=preview_seconds,
                bpm=bpm,
                mood=mood,
            )

        return f"{self.settings.asset_public_path}/generated/{filename}"

    def _render_placeholder_wav(
        self,
        *,
        output_path: Path,
        seconds: int,
        bpm: int,
        mood: str,
    ) -> None:
        sample_rate = 8000
        channels = 1
        sample_width = 2
        amplitude = 9000

        base_frequency_by_mood = {
            "hypnotic": 110.0,
            "deep": 98.0,
            "spatial": 146.0,
            "nocturnal": 82.0,
        }
        base_freq = base_frequency_by_mood.get(mood, 110.0)
        beat_hz = bpm / 60.0
        total_samples = sample_rate * seconds
        chunk_size = 2048

        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)

            for start in range(0, total_samples, chunk_size):
                current_chunk_size = min(chunk_size, total_samples - start)
                frames = bytearray()

                for offset in range(current_chunk_size):
                    sample_index = start + offset
                    t = sample_index / sample_rate

                    pulse = 0.55 + 0.45 * math.sin(2 * math.pi * beat_hz * t)
                    tone = (
                        math.sin(2 * math.pi * base_freq * t)
                        + 0.35 * math.sin(2 * math.pi * base_freq * 2 * t)
                        + 0.15 * math.sin(2 * math.pi * base_freq * 4 * t)
                    )

                    sample_value = int(amplitude * pulse * tone)
                    sample_value = max(-32767, min(32767, sample_value))

                    frames.extend(struct.pack("<h", sample_value))

                wav_file.writeframes(frames)