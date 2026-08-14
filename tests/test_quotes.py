from datetime import date
from pathlib import Path

import pytest

from quote_bot.models import BotConfig, Quote
from quote_bot.quotes import load_quotes, selection_index


def bot(tmp_path: Path, **changes: object) -> BotConfig:
    values = {
        "name": "test",
        "quotes": tmp_path / "quotes.jsonl",
        "handle_env": "HANDLE",
        "password_env": "PASSWORD",
    }
    values.update(changes)
    return BotConfig(**values)  # type: ignore[arg-type]


def test_load_quotes_supports_text_and_parts(tmp_path: Path) -> None:
    path = tmp_path / "quotes.jsonl"
    path.write_text(
        '{"id":"one","text":"Hello","metadata":{"chapter":1}}\n'
        '{"id":"two","parts":["A","B"],"source":"Book"}\n',
        encoding="utf-8",
    )

    quotes = load_quotes(path)

    assert quotes[0] == Quote(id="one", text="Hello", metadata={"chapter": 1})
    assert quotes[1].parts == ("A", "B")


@pytest.mark.parametrize(
    "contents, message",
    [
        ("", "no quotes"),
        ('{"id":"x","text":"A"}\n{"id":"x","text":"B"}\n', "duplicate"),
        ('{"id":"x","text":"A","parts":["B"]}\n', "exactly one"),
        ("not json\n", "Expecting value"),
    ],
)
def test_load_quotes_rejects_bad_data(tmp_path: Path, contents: str, message: str) -> None:
    path = tmp_path / "quotes.jsonl"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_quotes(path)


def test_selection_is_deterministic_and_honors_interval(tmp_path: Path) -> None:
    weekly = bot(tmp_path, epoch="2026-01-01", interval_days=7, offset=2)

    assert selection_index(weekly, date(2025, 12, 31), 10) is None
    assert selection_index(weekly, date(2026, 1, 1), 10) == 2
    assert selection_index(weekly, date(2026, 1, 2), 10) is None
    assert selection_index(weekly, date(2026, 1, 8), 10) == 3

