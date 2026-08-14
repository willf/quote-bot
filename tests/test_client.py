import json
from unittest.mock import patch

import pytest

from quote_bot.client import BlueskyClient, BlueskyError, tag_facets
from quote_bot.models import PostRef


class Response:
    def __init__(self, payload: dict[str, str]) -> None:
        self.payload = payload

    def __enter__(self) -> "Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def test_login_and_create_reply_record() -> None:
    responses = [
        Response({"accessJwt": "token", "did": "did:example:me"}),
        Response({"uri": "at://new", "cid": "new-cid"}),
    ]
    with patch("urllib.request.urlopen", side_effect=responses) as urlopen:
        client = BlueskyClient()
        client.login("bot.example", "app-password")
        result = client.create_post(
            "réponse #Pensées",
            root=PostRef("at://root", "root-cid"),
            parent=PostRef("at://parent", "parent-cid"),
        )

    assert result == PostRef("at://new", "new-cid")
    request = urlopen.call_args_list[1].args[0]
    payload = json.loads(request.data)
    assert payload["repo"] == "did:example:me"
    assert payload["record"]["reply"]["root"]["uri"] == "at://root"
    assert payload["record"]["facets"] == [
        {
            "index": {"byteStart": 9, "byteEnd": 18},
            "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": "Pensées"}],
        }
    ]
    assert request.headers["Authorization"] == "Bearer token"


def test_create_post_requires_login() -> None:
    with pytest.raises(BlueskyError, match="login"):
        BlueskyClient().create_post("hello")


def test_tag_facets_support_unicode_and_ignore_embedded_hashes() -> None:
    facets = tag_facets("é #Pensées email#fragment #two")

    assert [facet["features"][0]["tag"] for facet in facets] == ["Pensées", "two"]
    assert facets[0]["index"] == {"byteStart": 3, "byteEnd": 12}
