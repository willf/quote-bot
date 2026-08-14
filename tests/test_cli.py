from pathlib import Path
from unittest.mock import patch

import pytest

from quote_bot.cli import run
from quote_bot.models import PostRef


def test_dry_run_needs_no_secrets(tmp_path: Path, capsys: object) -> None:
    (tmp_path / "quotes.jsonl").write_text('{"id":"one","text":"Hello"}\n', encoding="utf-8")
    (tmp_path / "bots.toml").write_text(
        '[bots.test]\nquotes="quotes.jsonl"\nhandle_env="MISSING_H"\npassword_env="MISSING_P"\n',
        encoding="utf-8",
    )

    result = run(
        [
            "--config",
            str(tmp_path / "bots.toml"),
            "--bot",
            "test",
            "--dry-run",
            "--date",
            "2026-01-01",
        ]
    )

    assert result == 0
    assert "quote=one posts=1" in capsys.readouterr().out  # type: ignore[attr-defined]


def _files(tmp_path: Path, *, interval_days: int = 1) -> Path:
    (tmp_path / "quotes.jsonl").write_text('{"id":"one","text":"Hello"}\n', encoding="utf-8")
    config = tmp_path / "bots.toml"
    config.write_text(
        "[bots.test]\n"
        'quotes="quotes.jsonl"\nhandle_env="BOT_H"\npassword_env="BOT_P"\n'
        f"interval_days={interval_days}\nepoch=\"2026-01-01\"\n",
        encoding="utf-8",
    )
    return config


def test_live_run_logs_in_and_posts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _files(tmp_path)
    monkeypatch.setenv("BOT_H", "bot.example")
    monkeypatch.setenv("BOT_P", "secret")

    class FakeBlueskyClient:
        def __init__(self, service_url: str) -> None:
            assert service_url == "https://bsky.social"

        def login(self, handle: str, password: str) -> None:
            assert (handle, password) == ("bot.example", "secret")

        def create_post(self, text: str, **kwargs: object) -> PostRef:
            assert text == "Hello"
            return PostRef("at://posted", "cid")

    with patch("quote_bot.cli.BlueskyClient", FakeBlueskyClient):
        assert run(["--config", str(config), "--all", "--date", "2026-01-01"]) == 0


def test_not_due_and_unknown_bot(tmp_path: Path, capsys: object) -> None:
    config = _files(tmp_path, interval_days=2)
    assert run(["--config", str(config), "--all", "--date", "2026-01-02"]) == 0
    assert "not scheduled" in capsys.readouterr().out  # type: ignore[attr-defined]

    with pytest.raises(ValueError, match="unknown bot"):
        run(["--config", str(config), "--bot", "missing", "--dry-run"])


def test_live_run_requires_secrets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _files(tmp_path)
    monkeypatch.delenv("BOT_H", raising=False)
    with pytest.raises(ValueError, match="BOT_H"):
        run(["--config", str(config), "--all", "--date", "2026-01-01"])
