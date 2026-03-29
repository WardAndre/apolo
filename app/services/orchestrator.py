from app.schemas.track import Track


class RadioOrchestrator:
    def __init__(self) -> None:
        self.channel_name = "Apolo Radio"
        self.mode = "instrumental"
        self.target_buffer_minutes = 30
        self._buffer: list[Track] = []
        self._current_track: Track | None = None

    def get_status(self) -> dict:
        total_buffer_seconds = sum(track.duration_seconds for track in self._buffer)
        buffer_minutes = round(total_buffer_seconds / 60, 2)

        return {
            "channel_name": self.channel_name,
            "mode": self.mode,
            "current_track": self._current_track.model_dump() if self._current_track else None,
            "buffer_minutes": buffer_minutes,
            "target_buffer_minutes": self.target_buffer_minutes,
            "queued_tracks": len(self._buffer),
        }

    def generate_next_track(self) -> Track:
        track_number = len(self._buffer) + 1

        track = Track(
            title=f"Apolo Sequence {track_number}",
            bpm=120,
            energy="medium",
            mood="hypnotic",
            duration_seconds=300,
        )

        self._buffer.append(track)

        if self._current_track is None:
            self._current_track = track

        return track


radio_orchestrator = RadioOrchestrator()