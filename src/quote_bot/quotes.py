"""JSONL quote loading and deterministic selection."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from quote_bot.models import BotConfig, Quote


def load_quotes(path: Path) -> list[Quote]:
    """Load quote objects from *path*, reporting useful line-level errors."""
    quotes: list[Quote] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                quote_id = str(record["id"])
                parts = tuple(str(part) for part in record.get("parts", ()))
                text = record.get("text")
                quote = Quote(
                    id=quote_id,
                    text=str(text) if text is not None else None,
                    parts=parts,
                    source=record.get("source"),
                    attribution=record.get("attribution"),
                    metadata=dict(record.get("metadata", {})),
                )
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                raise ValueError(f"{path}:{line_number}: {error}") from error
            if quote.id in seen:
                raise ValueError(f"{path}:{line_number}: duplicate quote id {quote.id!r}")
            seen.add(quote.id)
            quotes.append(quote)
    if not quotes:
        raise ValueError(f"{path}: no quotes found")
    return quotes


def selection_index(bot: BotConfig, on_date: date, quote_count: int) -> int | None:
    """Return the scheduled quote index, or ``None`` when the bot is not due."""
    epoch = date.fromisoformat(bot.epoch)
    elapsed = (on_date - epoch).days
    if elapsed < 0 or elapsed % bot.interval_days:
        return None
    return (elapsed // bot.interval_days + bot.offset) % quote_count


def select_quote(bot: BotConfig, on_date: date) -> Quote | None:
    """Select a stable quote for a date without requiring persistent state."""
    quotes = load_quotes(bot.quotes)
    index = selection_index(bot, on_date, len(quotes))
    return None if index is None else quotes[index]

