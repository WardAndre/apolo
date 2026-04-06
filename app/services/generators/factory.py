from app.core.settings import get_settings
from app.services.generators.base import BaseTrackGenerator
from app.services.generators.ml_generator import MLTrackGenerator
from app.services.generators.mock_generator import MockTrackGenerator
from app.services.generators.simulated_ml_generator import SimulatedMLTrackGenerator

_track_generator: BaseTrackGenerator | None = None


def get_track_generator() -> BaseTrackGenerator:
    global _track_generator

    if _track_generator is not None:
        return _track_generator

    settings = get_settings()

    if settings.generator_backend == "ml_pipeline":
        _track_generator = MLTrackGenerator()
    elif settings.generator_backend == "simulated_ml":
        _track_generator = SimulatedMLTrackGenerator()
    else:
        _track_generator = MockTrackGenerator()

    return _track_generator