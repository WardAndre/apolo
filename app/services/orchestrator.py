import random

from app.core.radio_profile import RADIO_PROFILE
from app.schemas.track import Track


class RadioOrchestrator:
    def __init__(self) -> None:
        self.channel_name = RADIO_PROFILE["channel_name"]
        self.style = RADIO_PROFILE["style"]
        self.mode = RADIO_PROFILE["mode"]
        self.description = RADIO_PROFILE["description"]
        self.target_buffer_minutes = RADIO_PROFILE["target_buffer_minutes"]

        self._bpm_min = RADIO_PROFILE["bpm_min"]
        self._bpm_max = RADIO_PROFILE["bpm_max"]
        self._target_bpm = RADIO_PROFILE["target_bpm"]
        self._available_moods = RADIO_PROFILE["moods"]
        self._available_energy_levels = RADIO_PROFILE["energy_levels"]
        self._duration_options = RADIO_PROFILE["duration_options_seconds"]
        self._available_keys = RADIO_PROFILE["musical_keys"]

        self._buffer: list[Track] = []
        self._current_track: Track | None = None
        self._sequence_number = 0

    def get_buffer_minutes(self) -> float:
        total_buffer_seconds = sum(track.duration_seconds for track in self._buffer)
        return round(total_buffer_seconds / 60, 2)

    def get_profile(self) -> dict:
        return RADIO_PROFILE

    def get_status(self) -> dict:
        recent_tracks = [track.model_dump() for track in self._buffer[-3:]]

        return {
            "channel_name": self.channel_name,
            "style": self.style,
            "mode": self.mode,
            "description": self.description,
            "current_track": self._current_track.model_dump() if self._current_track else None,
            "buffer_minutes": self.get_buffer_minutes(),
            "target_buffer_minutes": self.target_buffer_minutes,
            "queued_tracks": len(self._buffer),
            "recent_tracks": recent_tracks,
            "constraints": {
                "allow_vocals": RADIO_PROFILE["allow_vocals"],
                "allow_speech": RADIO_PROFILE["allow_speech"],
                "allow_jingles": RADIO_PROFILE["allow_jingles"],
            },
        }

    def get_buffer(self) -> list[dict]:
        return [track.model_dump() for track in self._buffer]

    def generate_next_track(self) -> Track:
        profile = self._build_next_profile()

        self._sequence_number += 1
        track = Track(
            sequence_number=self._sequence_number,
            title=f"Apolo Sequence {self._sequence_number}",
            bpm=profile["bpm"],
            energy=profile["energy"],
            mood=profile["mood"],
            musical_key=profile["musical_key"],
            duration_seconds=profile["duration_seconds"],
        )

        self._buffer.append(track)

        if self._current_track is None:
            self._current_track = track

        return track

    def fill_buffer_to_target(self) -> list[Track]:
        generated_tracks: list[Track] = []

        while self.get_buffer_minutes() < self.target_buffer_minutes:
            generated_tracks.append(self.generate_next_track())

        return generated_tracks

    def _build_next_profile(self) -> dict:
        if not self._buffer and self._current_track is None:
            return {
                "bpm": self._target_bpm,
                "energy": "medium",
                "mood": random.choice(["hypnotic", "deep"]),
                "musical_key": random.choice(self._available_keys),
                "duration_seconds": random.choice(self._duration_options),
            }

        reference_track = self._buffer[-1] if self._buffer else self._current_track
        recent_moods = {track.mood for track in self._buffer[-2:]}
        recent_keys = {track.musical_key for track in self._buffer[-2:]}

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


radio_orchestrator = RadioOrchestrator()