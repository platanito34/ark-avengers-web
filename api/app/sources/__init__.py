"""Registro de fuentes de estado disponibles."""
from app.config import Settings
from app.sources.ark_rcon import ArkRconSource
from app.sources.base import SourceError, SourceReport, StatusSource
from app.sources.mock import MockSource
from app.sources.pterodactyl import PterodactylSource

__all__ = ["build_sources", "SourceError", "SourceReport", "StatusSource"]


def build_sources(settings: Settings) -> dict[str, StatusSource]:
    sources: list[StatusSource] = [
        MockSource(settings.mock_dir),
        PterodactylSource(
            mode=settings.pterodactyl_mode,
            mock_dir=settings.mock_dir,
            url=settings.pterodactyl_url,
            api_key=settings.pterodactyl_api_key,
            timeout=settings.source_timeout_seconds,
        ),
        ArkRconSource(),
    ]
    return {s.type: s for s in sources}
