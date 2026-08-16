import random
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from app.core.radio_profile import RADIO_PROFILE
from app.schemas.generation import TrackGenerationRequest
from app.schemas.track import Track
from app.services.generators.factory import get_track_generator
from app.services.playout.manifest_writer import PlayoutManifestWriter


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
        self._playout_manifest_writer = PlayoutManifestWriter()

        self._buffer: deque[Track] = deque()
        self._pending_playout: deque[Track] = deque()
        self._current_track: Track | None = None

        self._track_generation_lock = Lock()
        self._playout_request_lock = Lock()

        self._sequence_number = 0
        self._is_playing = False
        self._liquidsoap_track_started_at: datetime | None = None
        self._liquidsoap_metadata: dict = {}
        self._playout_manifest_path = self._sync_playout_manifest()

    def get_buffer_minutes(self) -> float:
        future_tracks = [
            *self._pending_playout,
            *self._buffer,
        ]

        total_buffer_seconds = sum(
            track.duration_seconds for track in future_tracks
        )

        return round(total_buffer_seconds / 60, 2)

    def get_profile(self) -> dict:
        return RADIO_PROFILE

    def get_generator_info(self) -> dict:
        return self._track_generator.get_info()

    def get_status(self) -> dict:
        pending_list = list(self._pending_playout)
        buffer_list = list(self._buffer)

        future_tracks = pending_list + buffer_list

        next_track = future_tracks[0] if future_tracks else None
        upcoming_tracks_preview = [
            track.model_dump()
            for track in future_tracks[:3]
        ]

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
            "queued_tracks": len(future_tracks),
            "pending_playout_tracks": len(pending_list),
            "buffer_tracks": len(buffer_list),
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
        pending_list = list(self._pending_playout)
        buffer_list = list(self._buffer)

        future_tracks = pending_list + buffer_list
        next_track = future_tracks[0] if future_tracks else None

        return {
            "is_playing": self._is_playing,
            "current_track": (
                self._current_track.model_dump()
                if self._current_track
                else None
            ),
            "next_track": (
                next_track.model_dump()
                if next_track
                else None
            ),
            "queued_tracks": len(future_tracks),
            "pending_playout_tracks": len(pending_list),
            "buffer_tracks": len(buffer_list),
            "buffer_minutes": self.get_buffer_minutes(),
            "minimum_buffer_minutes": self.minimum_buffer_minutes,
            "target_buffer_minutes": self.target_buffer_minutes,
            "auto_refill_enabled": self.auto_refill_enabled,
            "generator": self.get_generator_info(),
        }

    def get_playout_queue(self) -> list[dict]:
        return [track.model_dump() for track in self._get_playout_tracks()]

    def get_now_playing(self) -> dict | None:
        if self._current_track is None:
            return None

        payload = self._current_track.model_dump()

        payload["playback_source"] = (
            "liquidsoap"
            if self._liquidsoap_track_started_at is not None
            else "orchestrator"
        )

        payload["started_at"] = self._liquidsoap_track_started_at
        payload["liquidsoap_metadata"] = self._liquidsoap_metadata

        return payload

    def get_playout_manifest_info(self) -> dict:
        return {
            "manifest_path": self._playout_manifest_path,
            "queued_entries": len(self._get_playout_tracks()),
        }

    def get_generation_job(self, job_id: str) -> dict | None:
        return self._track_generator.get_generation_job(job_id)

    def list_recent_generation_jobs(self, limit: int = 20) -> list[dict]:
        return self._track_generator.list_recent_generation_jobs(limit)

    def list_recent_tracks(self, limit: int = 20) -> list[dict]:
        return self._track_generator.list_recent_tracks(limit)

    def generate_next_track(self) -> Track:
        track = self._create_track()
        self._sync_playout_manifest()

        return track

    def fill_buffer_to_target(self, auto_start_playback: bool = False) -> list[Track]:
        generated_tracks: list[Track] = []

        while self.get_buffer_minutes() < self.target_buffer_minutes:
            generated_tracks.append(self._create_track())

        if auto_start_playback and self._current_track is None and self._buffer:
            self.start_playback()
        else:
            self._sync_playout_manifest()

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
        auto_refill_result = self.ensure_minimum_buffer()

        self._sync_playout_manifest()

        return {
            "message": "Playback prepared; waiting for Liquidsoap",
            "auto_refill": auto_refill_result,
            "playback_state": self.get_playback_state(),
        }

    def advance_to_next_track(self) -> dict:
        auto_refill_result = self.ensure_minimum_buffer()

        return {
            "message": "Playback advancement is controlled by Liquidsoap",
            "auto_refill": auto_refill_result,
            "playback_state": self.get_playback_state(),
        }

    def _create_track(self) -> Track:
        with self._track_generation_lock:
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

        recent_tracks = self._get_playout_tracks()[-2:]

        recent_moods = {
            track.mood
            for track in recent_tracks
        }

        recent_keys = {
            track.musical_key
            for track in recent_tracks
        }

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

        if self._pending_playout:
            return self._pending_playout[-1]

        if self._current_track:
            return self._current_track

        return None

    def _get_playout_tracks(self) -> list[Track]:
        tracks: list[Track] = []

        if self._current_track is not None:
            tracks.append(self._current_track)

        tracks.extend(list(self._pending_playout))
        tracks.extend(list(self._buffer))

        return tracks

    def _sync_playout_manifest(self) -> str:
        return self._playout_manifest_writer.write_queue(self._get_playout_tracks())

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

    def sync_playback_from_liquidsoap(self, metadata: dict) -> dict:
        apolo_track_id = metadata.get("apolo_track_id")
        filename = metadata.get("filename") or metadata.get("initial_uri")

        pending_tracks = list(self._pending_playout)
        matching_index = None

        # Estratégia principal: UUID explícito.
        if apolo_track_id:
            for index, track in enumerate(pending_tracks):
                if str(track.id) == apolo_track_id:
                    matching_index = index
                    break

        # Fallback: nome do arquivo.
        if matching_index is None and filename:
            filename = Path(filename).name

            for index, track in enumerate(pending_tracks):
                if not track.audio_asset_uri:
                    continue

                track_filename = Path(track.audio_asset_uri).name

                if track_filename == filename:
                    matching_index = index
                    break

        # Callback repetido da faixa que já está no ar.
        if matching_index is None and self._current_track is not None:
            current_matches_id = (
                    apolo_track_id
                    and str(self._current_track.id) == apolo_track_id
            )

            current_matches_filename = False

            if filename and self._current_track.audio_asset_uri:
                current_matches_filename = (
                        Path(self._current_track.audio_asset_uri).name
                        == Path(filename).name
                )

            if current_matches_id or current_matches_filename:
                return {
                    "synced": True,
                    "already_current": True,
                    "current_track": self._current_track.model_dump(),
                    "started_at": self._liquidsoap_track_started_at,
                    "pending_playout_count": len(self._pending_playout),
                    "buffer_tracks_count": len(self._buffer),
                }

        if matching_index is None:
            return {
                "synced": False,
                "reason": (
                    "Track reported by Liquidsoap was not found "
                    "in pending playout"
                ),
                "apolo_track_id": apolo_track_id,
                "filename": filename,
                "pending_playout_count": len(self._pending_playout),
            }

        stale_pending_tracks: list[Track] = []

        # Tudo que estava reservado antes da faixa que realmente começou
        # é considerado abandonado pelo playout.
        for _ in range(matching_index):
            stale_pending_tracks.append(
                self._pending_playout.popleft()
            )

        playing_track = self._pending_playout.popleft()

        self._current_track = playing_track
        self._is_playing = True
        self._liquidsoap_track_started_at = datetime.now(timezone.utc)
        self._liquidsoap_metadata = metadata

        auto_refill_result = self.ensure_minimum_buffer()

        return {
            "synced": True,
            "current_track": playing_track.model_dump(),
            "started_at": self._liquidsoap_track_started_at,
            "stale_pending_tracks_count": len(stale_pending_tracks),
            "stale_pending_sequence_numbers": [
                track.sequence_number
                for track in stale_pending_tracks
            ],
            "pending_playout_count": len(self._pending_playout),
            "buffer_tracks_count": len(self._buffer),
            "buffer_minutes": self.get_buffer_minutes(),
            "auto_refill": auto_refill_result,
        }

    def get_next_playout_request(self) -> dict:
        with self._playout_request_lock:
            if not self._buffer:
                self.fill_buffer_to_target(auto_start_playback=False)

            if not self._buffer:
                return {
                    "available": False,
                    "reason": "No track available for playout",
                }

            next_track = self._buffer.popleft()
            self._pending_playout.append(next_track)

            if not next_track.audio_asset_uri:
                self._pending_playout.remove(next_track)

                return {
                    "available": False,
                    "reason": "Next track has no audio asset",
                }

            asset_filename = Path(next_track.audio_asset_uri).name

            liquidsoap_path = (
                f"/app/storage/assets/generated/{asset_filename}"
            )

            uri = (
                f'annotate:apolo_track_id="{next_track.id}":'
                f"{liquidsoap_path}"
            )

            auto_refill_result = self.ensure_minimum_buffer()

            return {
                "available": True,
                "track_id": str(next_track.id),
                "sequence_number": next_track.sequence_number,
                "uri": uri,
                "pending_playout_count": len(self._pending_playout),
                "buffer_tracks_count": len(self._buffer),
                "auto_refill": auto_refill_result,
            }


radio_orchestrator = RadioOrchestrator()
