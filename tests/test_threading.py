from pathlib import Path

import pytest

from quote_bot.models import BotConfig, Quote
from quote_bot.threading import format_thread, grapheme_len


def bot(**changes: object) -> BotConfig:
    values = {
        "name": "test",
        "quotes": Path("quotes.jsonl"),
        "handle_env": "HANDLE",
        "password_env": "PASSWORD",
        "max_graphemes": 50,
    }
    values.update(changes)
    return BotConfig(**values)  # type: ignore[arg-type]


def test_short_quote_with_attribution_is_one_post() -> None:
    quote = Quote(id="one", text="A short thought.", source="Book 1")

    assert format_thread(quote, bot()) == ["A short thought.\n\n— Book 1"]


def test_long_quote_splits_and_numbers_within_limit() -> None:
    quote = Quote(
        id="long",
        text=(
            "First sentence has several words. Second sentence also has several words. "
            "Third sentence finishes the quotation."
        ),
    )

    posts = format_thread(quote, bot(max_graphemes=45))

    assert len(posts) > 1
    assert posts[0].endswith(f"(1/{len(posts)})")
    assert posts[-1].endswith(f"({len(posts)}/{len(posts)})")
    assert all(grapheme_len(post) <= 45 for post in posts)


def test_explicit_parts_are_preserved_when_they_fit() -> None:
    quote = Quote(id="parts", parts=("Editorial break one.", "Editorial break two."))

    assert format_thread(quote, bot()) == [
        "Editorial break one. (1/2)",
        "Editorial break two. (2/2)",
    ]


def test_graphemes_keep_emoji_sequences_together() -> None:
    family = "👨‍👩‍👧‍👦"
    assert grapheme_len(family) == 1
    posts = format_thread(Quote(id="emoji", text=family * 40), bot(max_graphemes=20))
    assert all(grapheme_len(post) <= 20 for post in posts)


def test_quote_requires_exactly_one_content_form() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        Quote(id="empty")
