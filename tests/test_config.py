from pathlib import Path

import pytest

from quote_bot.config import load_config


def test_load_config_resolves_quote_path(tmp_path: Path) -> None:
    config = tmp_path / "bots.toml"
    config.write_text(
        '[bots.test]\nquotes="quotes.jsonl"\nhandle_env="HANDLE"\npassword_env="PASSWORD"\n'
        'hashtags=["#DailyQuote"]\n',
        encoding="utf-8",
    )

    bot = load_config(config)["test"]

    assert bot.quotes == tmp_path / "quotes.jsonl"
    assert bot.language == "en"
    assert bot.max_graphemes == 300
    assert bot.hashtags == ("DailyQuote",)


@pytest.mark.parametrize(
    "document, message",
    [
        ("", "at least one"),
        ("[bots.test]\nquotes='x'\npassword_env='P'", "handle_env"),
        (
            "[bots.test]\nquotes='x'\nhandle_env='H'\npassword_env='P'\ninterval_days=0",
            "interval_days",
        ),
        (
            "[bots.test]\nquotes='x'\nhandle_env='H'\npassword_env='P'\nhashtags=['bad tag']",
            "hashtags",
        ),
    ],
)
def test_invalid_config(tmp_path: Path, document: str, message: str) -> None:
    config = tmp_path / "bots.toml"
    config.write_text(document, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_config(config)
