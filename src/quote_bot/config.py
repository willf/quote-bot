"""Load bot configuration from TOML."""

from __future__ import annotations

import tomllib
from pathlib import Path

import regex

from quote_bot.models import BotConfig


def load_config(path: Path) -> dict[str, BotConfig]:
    """Load and validate all ``[bots.<name>]`` tables in *path*."""
    path = path.resolve()
    with path.open("rb") as file:
        document = tomllib.load(file)

    raw_bots = document.get("bots")
    if not isinstance(raw_bots, dict) or not raw_bots:
        raise ValueError("configuration must contain at least one [bots.<name>] table")

    bots: dict[str, BotConfig] = {}
    for name, values in raw_bots.items():
        if not isinstance(values, dict):
            raise ValueError(f"bots.{name} must be a TOML table")
        try:
            quote_path = path.parent / values["quotes"]
            handle_env = values["handle_env"]
            password_env = values["password_env"]
        except KeyError as error:
            raise ValueError(f"bots.{name} is missing {error.args[0]!r}") from error

        bot = BotConfig(
            name=name,
            quotes=quote_path.resolve(),
            handle_env=str(handle_env),
            password_env=str(password_env),
            service_url=str(values.get("service_url", "https://bsky.social")).rstrip("/"),
            language=values.get("language", "en"),
            max_graphemes=int(values.get("max_graphemes", 300)),
            number_threads=bool(values.get("number_threads", True)),
            attribution_template=str(values.get("attribution_template", "— {attribution}")),
            hashtags=tuple(str(tag).removeprefix("#") for tag in values.get("hashtags", ())),
            interval_days=int(values.get("interval_days", 1)),
            offset=int(values.get("offset", 0)),
            epoch=str(values.get("epoch", "2025-01-01")),
        )
        if bot.max_graphemes < 20:
            raise ValueError(f"bots.{name}.max_graphemes must be at least 20")
        if bot.interval_days < 1:
            raise ValueError(f"bots.{name}.interval_days must be at least 1")
        if any(not regex.fullmatch(r"[\p{L}\p{N}_-]{1,64}", tag) for tag in bot.hashtags):
            raise ValueError(
                f"bots.{name}.hashtags must contain 1–64 letters, numbers, underscores, or hyphens"
            )
        bots[name] = bot
    return bots
