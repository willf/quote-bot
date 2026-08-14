from pathlib import Path

from quote_bot.models import BotConfig, PostRef, Quote
from quote_bot.poster import post_quote


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, PostRef | None, PostRef | None, str | None]] = []

    def create_post(
        self,
        text: str,
        *,
        root: PostRef | None = None,
        parent: PostRef | None = None,
        language: str | None = "en",
    ) -> PostRef:
        self.calls.append((text, root, parent, language))
        number = len(self.calls)
        return PostRef(uri=f"at://post/{number}", cid=f"cid-{number}")


def test_post_quote_builds_reply_chain_with_constant_root() -> None:
    config = BotConfig(
        name="test",
        quotes=Path("quotes.jsonl"),
        handle_env="HANDLE",
        password_env="PASSWORD",
        language="en-GB",
    )
    quote = Quote(id="thread", parts=("one", "two", "three"))
    client = FakeClient()

    refs = post_quote(client, quote, config)

    assert len(refs) == 3
    assert client.calls[0][1:3] == (None, None)
    assert client.calls[1][1:3] == (refs[0], refs[0])
    assert client.calls[2][1:3] == (refs[0], refs[1])
    assert all(call[3] == "en-GB" for call in client.calls)

