"""Command-line entry point."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from quote_bot.client import BlueskyClient
from quote_bot.config import load_config
from quote_bot.quotes import select_quote
from quote_bot.threading import format_thread


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quote-bot", description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("bots.toml"))
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--bot", action="append", help="bot name (repeatable)")
    selection.add_argument("--all", action="store_true", help="run every configured bot")
    parser.add_argument("--dry-run", action="store_true", help="print posts without logging in")
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bots = load_config(args.config)
    names = list(bots) if args.all else args.bot
    unknown = [name for name in names if name not in bots]
    if unknown:
        raise ValueError(f"unknown bot(s): {', '.join(unknown)}")

    for name in names:
        bot = bots[name]
        quote = select_quote(bot, args.date)
        if quote is None:
            print(f"[{name}] not scheduled for {args.date.isoformat()}")
            continue
        posts = format_thread(quote, bot)
        if args.dry_run:
            print(f"[{name}] quote={quote.id} posts={len(posts)}")
            for index, post in enumerate(posts, 1):
                print(f"--- {index}/{len(posts)} ---\n{post}")
            continue

        try:
            handle = os.environ[bot.handle_env]
            password = os.environ[bot.password_env]
        except KeyError as error:
            message = f"bot {name!r} requires environment variable {error.args[0]}"
            raise ValueError(message) from error
        client = BlueskyClient(bot.service_url)
        client.login(handle, password)
        from quote_bot.poster import post_quote

        references = post_quote(client, quote, bot)
        print(f"[{name}] posted quote={quote.id} root={references[0].uri}")
    return 0


def main() -> None:
    try:
        raise SystemExit(run())
    except (OSError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
