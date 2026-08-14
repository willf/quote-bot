"""Domain models for quote bots."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Quote:
    """A quote loaded from one JSONL record."""

    id: str
    text: str | None = None
    parts: tuple[str, ...] = ()
    source: str | None = None
    attribution: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if bool(self.text) == bool(self.parts):
            raise ValueError(f"quote {self.id!r} must have exactly one of 'text' or 'parts'")
        if self.parts and any(not part.strip() for part in self.parts):
            raise ValueError(f"quote {self.id!r} contains an empty thread part")


@dataclass(frozen=True)
class BotConfig:
    """Configuration for one Bluesky account and quote collection."""

    name: str
    quotes: Path
    handle_env: str
    password_env: str
    service_url: str = "https://bsky.social"
    language: str | None = "en"
    max_graphemes: int = 300
    number_threads: bool = True
    attribution_template: str = "— {attribution}"
    hashtags: tuple[str, ...] = ()
    interval_days: int = 1
    offset: int = 0
    epoch: str = "2025-01-01"


@dataclass(frozen=True)
class PostRef:
    """The strong reference returned after creating a Bluesky post."""

    uri: str
    cid: str
