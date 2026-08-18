import math
import struct
import wave
from pathlib import Path
import shutil
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.core.settings import get_settings
from app.schemas.generation import ProviderAudioResult, StoredAudioAsset


class AudioAssetStorage:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_dir = Path(self.settings.asset_storage_dir)
        self.generated_dir = self.base_dir / "generated"

    def _normalize_audio_format(
            self,
            asset_format: str,
    ) -> str:
        normalized = asset_format.lower().strip().lstrip(".")

        aliases = {
            "mpeg": "mp3",
            "wave": "wav",
        }

        normalized = aliases.get(normalized, normalized)

        supported_formats = {
            "wav",
            "mp3",
            "flac",
            "aac",
            "m4a",
            "ogg",
        }

        if normalized not in supported_formats:
            raise ValueError(
                f"Unsupported provider audio format: {asset_format}"
            )

        return normalized

    def ensure_storage_dir(self) -> None:
        self.generated_dir.mkdir(parents=True, exist_ok=True)

    def persist_provider_asset(
            self,
            *,
            audio_result: ProviderAudioResult,
            sequence_number: int,
            provider_job_id: str,
            bpm: int,
            mood: str,
            duration_seconds: int,
    ) -> StoredAudioAsset:
        if audio_result.source_uri.startswith("simulated-vertex://"):
            asset_uri = self.create_placeholder_asset(
                sequence_number=sequence_number,
                provider_job_id=provider_job_id,
                bpm=bpm,
                mood=mood,
                duration_seconds=duration_seconds,
            )

            return StoredAudioAsset(
                asset_uri=asset_uri,
                format="wav",
            )

        source_scheme = urlparse(audio_result.source_uri).scheme.lower()

        if source_scheme in {"http", "https"}:
            return self._download_provider_asset(
                audio_result=audio_result,
                sequence_number=sequence_number,
                provider_job_id=provider_job_id,
            )

        raise ValueError(
            f"Unsupported provider audio source: {audio_result.source_uri}"
        )

    def _download_provider_asset(
            self,
            *,
            audio_result: ProviderAudioResult,
            sequence_number: int,
            provider_job_id: str,
    ) -> StoredAudioAsset:
        self.ensure_storage_dir()

        asset_format = self._normalize_audio_format(audio_result.format)

        safe_job_id = provider_job_id.replace("-", "")
        filename = (
            f"track_{sequence_number:04d}_"
            f"{safe_job_id}.{asset_format}"
        )

        output_path = self.generated_dir / filename
        temporary_path = output_path.with_suffix(
            output_path.suffix + ".part"
        )

        request = Request(
            audio_result.source_uri,
            headers={
                "User-Agent": "Projeto-Apolo/1.0",
            },
        )

        try:
            with urlopen(request, timeout=60) as response:
                with temporary_path.open("wb") as output_file:
                    shutil.copyfileobj(
                        response,
                        output_file,
                        length=1024 * 1024,
                    )

            temporary_path.replace(output_path)

        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

        return StoredAudioAsset(
            asset_uri=(
                f"{self.settings.asset_public_path}"
                f"/generated/{filename}"
            ),
            format=asset_format,
        )

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
