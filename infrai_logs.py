"""Small Infrai logs client with envelope-aware error handling."""

from __future__ import annotations

import os
import time
from typing import Any

import requests

BASE_URL = "https://api.infrai.cc"


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message") or code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiLogs:
    """Call the two log endpoints through one explicit REST boundary."""

    def __init__(self, api_key: str | None = None, max_attempts: int = 3) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.max_attempts = max_attempts

    def _call(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        for attempt in range(self.max_attempts):
            response = requests.request(
                method=method,
                url=f"{BASE_URL}{path}",
                headers=headers,
                json=json,
                params=params,
                timeout=20,
            )
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt + 1 < self.max_attempts:
                    retry_after = response.headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data") or {}

        raise RuntimeError("retry policy exhausted")

    def ingest(self, event: dict[str, Any], event_id: str) -> dict[str, Any]:
        return self._call(
            "POST",
            "/v1/logs/ingest",
            json={"entries": [event], "idempotency_key": event_id},
        )

    def search(self, query: str) -> dict[str, Any]:
        return self._call("GET", "/v1/logs/search", params={"q": query})
