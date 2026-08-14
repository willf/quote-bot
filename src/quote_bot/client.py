"""Small standard-library client for the AT Protocol endpoints we need."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from quote_bot.models import PostRef


class BlueskyError(RuntimeError):
    """An AT Protocol request failed."""


@dataclass
class BlueskyClient:
    """Authenticate and create Bluesky post records."""

    service_url: str = "https://bsky.social"
    timeout: float = 30.0
    _access_jwt: str | None = None
    _did: str | None = None

    def _request(self, method: str, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode()
        headers = {"Content-Type": "application/json", "User-Agent": "bluesky-quote-bots/0.1"}
        if self._access_jwt:
            headers["Authorization"] = f"Bearer {self._access_jwt}"
        request = urllib.request.Request(
            f"{self.service_url.rstrip('/')}/xrpc/{endpoint}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")
            raise BlueskyError(f"{endpoint} failed with HTTP {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise BlueskyError(f"{endpoint} failed: {error.reason}") from error

    def login(self, identifier: str, password: str) -> None:
        session = self._request(
            "POST",
            "com.atproto.server.createSession",
            {"identifier": identifier, "password": password},
        )
        self._access_jwt = session["accessJwt"]
        self._did = session["did"]

    def create_post(
        self,
        text: str,
        *,
        root: PostRef | None = None,
        parent: PostRef | None = None,
        language: str | None = "en",
    ) -> PostRef:
        if not self._access_jwt or not self._did:
            raise BlueskyError("login must be called before create_post")
        record: dict[str, Any] = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": datetime.now(UTC).isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            ),
        }
        if language:
            record["langs"] = [language]
        if root and parent:
            record["reply"] = {
                "root": {"uri": root.uri, "cid": root.cid},
                "parent": {"uri": parent.uri, "cid": parent.cid},
            }
        response = self._request(
            "POST",
            "com.atproto.repo.createRecord",
            {"repo": self._did, "collection": "app.bsky.feed.post", "record": record},
        )
        return PostRef(uri=response["uri"], cid=response["cid"])
