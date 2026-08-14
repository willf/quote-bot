"""Format a quote as one or more Bluesky-sized thread posts."""

from __future__ import annotations

import regex

from quote_bot.models import BotConfig, Quote


def grapheme_len(text: str) -> int:
    """Count Unicode extended grapheme clusters, as Bluesky does for limits."""
    return len(regex.findall(r"\X", text))


def _split_once(text: str, limit: int) -> list[str]:
    graphemes = regex.findall(r"\X", text.strip())
    chunks: list[str] = []
    while len(graphemes) > limit:
        window = graphemes[: limit + 1]
        break_at = 0
        # Prefer paragraph, sentence, then word boundaries in the latter half.
        for pattern in (r"\n\s*\n", r"(?<=[.!?;:])\s+", r"\s+"):
            matches = list(regex.finditer(pattern, "".join(window)))
            candidates = [
                match.end()
                for match in matches
                if grapheme_len("".join(window)[: match.end()]) <= limit
            ]
            if candidates:
                character_index = candidates[-1]
                break_at = grapheme_len("".join(window)[:character_index])
                if break_at >= limit // 2:
                    break
        if break_at < 1:
            break_at = limit
        chunks.append("".join(graphemes[:break_at]).strip())
        graphemes = graphemes[break_at:]
        while graphemes and graphemes[0].isspace():
            graphemes.pop(0)
    if graphemes:
        chunks.append("".join(graphemes).strip())
    return chunks


def _split_parts(parts: list[str], limit: int) -> list[str]:
    return [chunk for part in parts for chunk in _split_once(part, limit)]


def format_thread(quote: Quote, bot: BotConfig) -> list[str]:
    """Build post text, applying attribution and stable ``(n/N)`` labels."""
    parts = list(quote.parts) if quote.parts else [quote.text or ""]
    attribution = quote.attribution or quote.source
    if attribution:
        rendered = bot.attribution_template.format(
            attribution=attribution, source=quote.source or "", id=quote.id
        )
        parts[-1] = f"{parts[-1].rstrip()}\n\n{rendered}"
    if bot.hashtags:
        tags = " ".join(f"#{tag}" for tag in bot.hashtags)
        parts[-1] = f"{parts[-1].rstrip()}\n\n{tags}"

    total_guess = 1
    while True:
        suffix_size = grapheme_len(f" ({total_guess}/{total_guess})") if bot.number_threads else 0
        chunks = _split_parts(parts, bot.max_graphemes - suffix_size)
        total = len(chunks)
        if total == total_guess:
            break
        total_guess = total

    if bot.number_threads and total > 1:
        chunks = [f"{chunk} ({index}/{total})" for index, chunk in enumerate(chunks, 1)]
    if any(grapheme_len(chunk) > bot.max_graphemes for chunk in chunks):
        raise ValueError(f"quote {quote.id!r} could not be split within the post limit")
    return chunks
