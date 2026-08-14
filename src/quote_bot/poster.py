"""Post fully linked Bluesky threads."""

from __future__ import annotations

from typing import Protocol

from quote_bot.models import BotConfig, PostRef, Quote
from quote_bot.threading import format_thread


class PostingClient(Protocol):
    def create_post(
        self,
        text: str,
        *,
        root: PostRef | None = None,
        parent: PostRef | None = None,
        language: str | None = "en",
    ) -> PostRef: ...


def post_quote(client: PostingClient, quote: Quote, bot: BotConfig) -> list[PostRef]:
    """Post a quote and return each created record reference in thread order."""
    posts = format_thread(quote, bot)
    references: list[PostRef] = []
    root: PostRef | None = None
    parent: PostRef | None = None
    for text in posts:
        reference = client.create_post(text, root=root, parent=parent, language=bot.language)
        references.append(reference)
        root = root or reference
        parent = reference
    return references

