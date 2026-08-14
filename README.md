# Bluesky Quote Bots

A small Python system for running any number of JSONL-backed quote bots from
GitHub Actions. Long quotations become properly linked Bluesky threads, and the
same date always selects the same quote, so no database or cron host is needed.

The included Pascal and Julian of Norwich records are **mock data**. They are
only examples of the input format, not publication-ready transcriptions.

## How it works

1. GitHub Actions starts the command on a cron schedule.
2. Each configured bot selects an entry using the date, its epoch, interval,
   and offset: `(days since epoch / interval + offset) modulo quote count`.
3. A long `text` entry is split on paragraph, sentence, or word boundaries.
   An entry with `parts` preserves editorially chosen thread breaks.
4. Configured hashtags are appended to the final post and encoded as Bluesky
   rich-text facets, making them clickable and searchable.
5. The first post becomes the thread root. Every later post replies to the
   preceding post while retaining the same root reference.

Selection is deterministic and stateless. Reordering or inserting JSONL rows
changes future selections; append records when you want to preserve the cycle.
Running a live command twice on the same day will post twice—use the workflow's
concurrency guard and avoid retrying a successful job.

## Local setup

Python 3.11 or newer is required.

```shell
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
quote-bot --config bots.toml --all --dry-run --date 2026-01-01
```

The dry run reads no credentials and makes no network calls.

## JSONL format

Each nonblank line is one JSON object with a unique `id`. Use exactly one of
`text` or `parts`:

```json
{"id":"p-001","text":"One quotation...","source":"Lafuma 100"}
{"id":"p-002","parts":["Preferred first post.","Preferred reply."],"attribution":"fragment 101"}
```

Supported fields:

| Field | Required | Meaning |
|---|---:|---|
| `id` | yes | Stable identifier, unique within the file |
| `text` | one of | A quote that may be split automatically |
| `parts` | one of | Array of editorially chosen thread posts |
| `source` | no | Source label; also serves as attribution by default |
| `attribution` | no | Overrides `source` in the attribution template |
| `metadata` | no | Arbitrary provenance/import information, not posted |

Explicit parts are not allowed to be empty. If an explicit part exceeds the
configured post limit it is split further. Thread numbering and attribution
are included when calculating the 300-grapheme limit.

## Bot configuration

Bots live in `bots.toml`:

```toml
[bots.pascal]
quotes = "data/pascal.jsonl"
handle_env = "PASCAL_BSKY_HANDLE"
password_env = "PASCAL_BSKY_APP_PASSWORD"
service_url = "https://bsky.social"
language = "en"
max_graphemes = 300
number_threads = true
attribution_template = "— Pascal, Pensées ({attribution})"
hashtags = ["PascalsPensees"]
epoch = "2025-01-01"
interval_days = 1
offset = 0
```

Paths are relative to `bots.toml`. Template fields are `{attribution}`,
`{source}`, and `{id}`. Hashtags may be written with or without the leading
`#`; they are placed only on the final post of a thread. Set
`interval_days = 7` for a weekly bot while keeping
the workflow daily; on other days the command reports that the bot is not due.
The cron expression controls the time of day and can also be changed to run the
workflow less frequently.

To add a bot, add its table and JSONL file, then expose its two environment
variables in `.github/workflows/post-quotes.yml`.

## GitHub Actions deployment

1. Create a separate Bluesky account for each bot.
2. In each Bluesky account, create an app password. Do not use the account's
   main password.
3. Create the four repository Actions secrets named in `bots.toml` and the
   sample workflow: `PASCAL_BSKY_HANDLE`, `PASCAL_BSKY_APP_PASSWORD`,
   `JULIAN_BSKY_HANDLE`, and `JULIAN_BSKY_APP_PASSWORD`.
4. Push the repository. Tests run on pushes and pull requests. The posting job
   runs at 13:17 UTC daily.
5. Before the first scheduled run, use **Actions → Post scheduled quotes → Run
   workflow** with `dry_run` checked. Review the log, then run unchecked only if
   you intentionally want to publish immediately.

GitHub may delay scheduled workflows during busy periods. A schedule is best
understood as “once around this time,” not an exact timer.

## Commands

```shell
# Preview one bot for today
quote-bot --config bots.toml --bot pascal --dry-run

# Preview several named bots for a reproducible date
quote-bot --config bots.toml --bot pascal --bot julian --dry-run --date 2026-05-10

# Post every bot that is due today
quote-bot --config bots.toml --all

# Run quality checks
ruff check .
pytest --cov --cov-report=term-missing
```

## Operational notes

- App passwords and handles are read only from the configured environment
  variables. Never put them in TOML or JSONL.
- Thread creation is not transactional. If Bluesky accepts some replies and a
  later request fails, the partial thread remains. Inspect the account before
  retrying to avoid a duplicate.
- Configured hashtags and hashtag text appearing in quotations receive tag
  facets. URLs and mentions remain plain text in this minimal client.
- Source texts and editions may carry copyright or attribution requirements.
  Verify the edition you ingest before publication.

## License

[MIT](LICENSE)
