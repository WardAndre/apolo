from app.core.settings import get_settings
from app.services.generators.providers.base import BaseGenerationProvider
from app.services.generators.providers.simulated_vertex_provider import (
    SimulatedVertexProvider,
)

_provider: BaseGenerationProvider | None = None


def get_generation_provider() -> BaseGenerationProvider:
    global _provider

    if _provider is not None:
        return _provider

    settings = get_settings()

    if settings.ml_provider == "simulated_vertex":
        _provider = SimulatedVertexProvider()
    else:
        raise ValueError(f"Unsupported ML provider: {settings.ml_provider}")

    return _provider