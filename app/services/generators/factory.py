from app.services.generators.base import BaseTrackGenerator
from app.services.generators.mock_generator import MockTrackGenerator

_track_generator: BaseTrackGenerator | None = None


def get_track_generator() -> BaseTrackGenerator:
    global _track_generator

    if _track_generator is None:
        _track_generator = MockTrackGenerator()

    return _track_generator