from collections import deque
import random

from app.core.radio_profile import RADIO_PROFILE
from app.schemas.generation import TrackGenerationRequest
from app.schemas.track import Track
from app.services.generators.factory import get_track_generator


class RadioOrchestrator:
    def __init__(self) -> None:
        self.channel_name = RADIO_PROFILE["channel_name"]
        self.style = RADIO_PROFILE["style"]
        self.mode = RADIO_PROFILE["mode"]
        self.description = RADIO_PROFILE["description"]

        self.target_buffer_minutes = RADIO_PROFILE["target_buffer_minutes"]
        self.minimum_buffer_minutes = RADIO_PROFILE["minimum_buffer_minutes"]
        self.auto_refill_enabled = RADIO_PROFILE["auto_refill_enabled"]

        self._bpm_min = RADIO_PROFILE["bpm_min"]
        self._bpm_max = RADIO_PROFILE["bpm_max"]
        self._target_bpm = RADIO_PROFILE["target_bpm"]
        self._available_moods = RADIO_PROFILE["moods"]
        self._duration_options = RADIO_PROFILE["duration_options_seconds"]
        self._available_keys = RADIO_PROFILE["musical_keys"]

        self._track_generator = get_track_generator()

        self._buffer: deque[Track] = deque()
        self._current_track: Track | None = None
        self._sequence_number = 0
        self._is_playing = False

    def get_buffer_minutes(self) -> float:
        total_buffer_seconds = sum(track.duration_seconds for track in self._buffer)
        return round(total_buffer_seconds / 60, 2)

    def get_profile(self) -> dict:
        return RADIO_PROFILE

    def get_generator_info(self) -> dict:
        return self._track_generator.get_info()

    def get_status(self) -> dict:
        buffer_list = list(self._buffer)
        next_track = buffer_list[0] if buffer_list else None
        upcoming_tracks_preview = [track.model_dump() for track in buffer_list[:3]]

        return {
            "channel_name": self.channel_name,
            "style": self.style,
            "mode": self.mode,
            "description": self.description,
            "generator": self.get_generator_info(),
            "is_playing": self._is_playing,
            "current_track": self._current_track.model_dump() if self._current_track else None,
            "next_track": next_track.model_dump() if next_track else None,
            "buffer_minutes": self.get_buffer_minutes(),
            "minimum_buffer_minutes": self.minimum_buffer_minutes,
            "target_buffer_minutes": self.target_buffer_minutes,
            "auto_refill_enabled": self.auto_refill_enabled,
            "queued_tracks": len(self._buffer),
            "upcoming_tracks_preview": upcoming_tracks_preview,
            "constraints": {
                "allow_vocals": RADIO_PROFILE["allow_vocals"],
                "allow_speech": RADIO_PROFILE["allow_speech"],
                "allow_jingles": RADIO_PROFILE["allow_jingles"],
            },
        }

    def get_buffer(self) -> list[dict]:
        return [track.model_dump() for track in self._buffer]

    def get_playback_state(self) -> dict:
        next_track = self._buffer[0] if self._buffer else None

        return {
            "is_playing": self._is_playing,
            "current_track": self._current_track.model_dump() if self._current_track else None,
            "next_track": next_track.model_dump() if next_track else None,
            "queued_tracks": len(self._buffer),
            "buffer_minutes": self.get_buffer_minutes(),
            "minimum_buffer_minutes": self.minimum_buffer_minutes,
            "target_buffer_minutes": self.target_buffer_minutes,
            "auto_refill_enabled": self.auto_refill_enabled,
            "generator": self.get_generator_info(),
        }

    def generate_next_track(self) -> Track:
        track = self._create_track()

        if self._current_track is None:
            self.start_playback()

        return track

    def fill_buffer_to_target(self, auto_start_playback: bool = True) -> list[Track]:
        generated_tracks: list[Track] = []

        while self.get_buffer_minutes() < self.target_buffer_minutes:
            generated_tracks.append(self._create_track())

        if auto_start_playback and self._current_track is None and self._buffer:
            self.start_playback()

        return generated_tracks

    def ensure_minimum_buffer(self) -> dict:
        if not self.auto_refill_enabled:
            return {
                "auto_refill_enabled": False,
                "auto_refill_triggered": False,
                "generated_tracks_count": 0,
                "generated_tracks": [],
                "buffer_minutes": self.get_buffer_minutes(),
            }

        if self.get_buffer_minutes() >= self.minimum_buffer_minutes:
            return {
                "auto_refill_enabled": True,
                "auto_refill_triggered": False,
                "generated_tracks_count": 0,
                "generated_tracks": [],
                "buffer_minutes": self.get_buffer_minutes(),
            }

        generated_tracks = self.fill_buffer_to_target(auto_start_playback=False)

        return {
            "auto_refill_enabled": True,
            "auto_refill_triggered": True,
            "generated_tracks_count": len(generated_tracks),
            "generated_tracks": [track.model_dump() for track in generated_tracks],
            "buffer_minutes": self.get_buffer_minutes(),
        }

    def start_playback(self) -> dict:
        if self._current_track is None and not self._buffer and self.auto_refill_enabled:
            self.ensure_minimum_buffer()

        if self._current_track is None and self._buffer:
            self._current_track = self._buffer.popleft()

        self._is_playing = self._current_track is not None
        auto_refill_result = self.ensure_minimum_buffer()

        return {
            "message": "Playback started",
            "auto_refill": auto_refill_result,
            "playback_state": self.get_playback_state(),
        }

    def advance_to_next_track(self) -> dict:
        finished_track = self._current_track

        if self._buffer:
            self._current_track = self._buffer.popleft()
            self._is_playing = True
        else:
            self._current_track = None
            self._is_playing = False

        auto_refill_result = self.ensure_minimum_buffer()

        if self._current_track is None and self._buffer:
            self._current_track = self._buffer.popleft()
            self._is_playing = True

        return {
            "message": "Playback advanced to next track",
            "finished_track": finished_track.model_dump() if finished_track else None,
            "auto_refill": auto_refill_result,
            "playback_state": self.get_playback_state(),
        }

    def _create_track(self) -> Track:
        profile = self._build_next_profile()

        self._sequence_number += 1
        request = TrackGenerationRequest(
            sequence_number=self._sequence_number,
            title=f"Apolo Sequence {self._sequence_number}",
            style=self.style,
            mode=self.mode,
            bpm=profile["bpm"],
            energy=profile["energy"],
            mood=profile["mood"],
            musical_key=profile["musical_key"],
            duration_seconds=profile["duration_seconds"],
        )

        track = self._track_generator.generate_track(request)
        self._buffer.append(track)
        return track

    def _build_next_profile(self) -> dict:
        reference_track = self._get_reference_track()

        if reference_track is None:
            return {
                "bpm": self._target_bpm,
                "energy": "medium",
                "mood": random.choice(["hypnotic", "deep"]),
                "musical_key": random.choice(self._available_keys),
                "duration_seconds": random.choice(self._duration_options),
            }

        recent_tracks = list(self._buffer)[-2:]
        recent_moods = {track.mood for track in recent_tracks}
        recent_keys = {track.musical_key for track in recent_tracks}

        next_energy = self._choose_next_energy(reference_track.energy)
        next_bpm = self._choose_next_bpm(reference_track.bpm, next_energy)
        next_mood = self._choose_next_mood(recent_moods)
        next_key = self._choose_next_key(recent_keys)
        next_duration = self._choose_next_duration()

        return {
            "bpm": next_bpm,
            "energy": next_energy,
            "mood": next_mood,
            "musical_key": next_key,
            "duration_seconds": next_duration,
        }

    def _get_reference_track(self) -> Track | None:
        if self._buffer:
            return self._buffer[-1]
        if self._current_track:
            return self._current_track
        return None

    def _choose_next_energy(self, current_energy: str) -> str:
        transitions = {
            "medium": ["medium", "medium_high"],
            "medium_high": ["medium", "medium_high"],
        }
        return random.choice(transitions[current_energy])

    def _choose_next_bpm(self, current_bpm: int, next_energy: str) -> int:
        delta = random.choice([-1, 0, 1])

        if next_energy == "medium_high":
            delta = max(delta, 0)

        next_bpm = current_bpm + delta
        return max(self._bpm_min, min(self._bpm_max, next_bpm))

    def _choose_next_mood(self, recent_moods: set[str]) -> str:
        available_options = [mood for mood in self._available_moods if mood not in recent_moods]

        if not available_options:
            available_options = self._available_moods

        return random.choice(available_options)

    def _choose_next_key(self, recent_keys: set[str]) -> str:
        available_options = [key for key in self._available_keys if key not in recent_keys]

        if not available_options:
            available_options = self._available_keys

        return random.choice(available_options)

    def _choose_next_duration(self) -> int:
        return random.choice(self._duration_options)

    def get_generation_job(self, job_id: str) -> dict | None:
        return self._track_generator.get_generation_job(job_id)

radio_orchestrator = RadioOrchestrator()