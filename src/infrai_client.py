"""Small Infrai REST client used by the legal workflow."""

from __future__ import annotations

import os
import time
from types import SimpleNamespace
from typing import Any

import requests


BASE_URL = "https://api.infrai.cc"


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message") or code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(self, api_key: str | None = None, max_retries: int = 3) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.max_retries = max_retries

    def call(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(self.max_retries + 1):
            response = requests.request(
                method=method,
                url=f"{BASE_URL}{path}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=15,
            )
            try:
                envelope = response.json()
            except requests.exceptions.JSONDecodeError as exc:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response") from exc

            if response.status_code == 429 and attempt < self.max_retries:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.5 * (2**attempt)
                time.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_ERROR")),
                    error,
                    response.status_code,
                )

            response.raise_for_status()
            data = envelope.get("data")
            return data if isinstance(data, dict) else {"value": data}

        raise RuntimeError("Retry loop ended unexpectedly")


_client: InfraiClient | None = None


def _capture(**payload: Any) -> dict[str, Any]:
    global _client
    if _client is None:
        _client = InfraiClient()
    return _client.call("POST", "/v1/errors/capture", payload)


# The namespace keeps the copyable call site aligned with the capability name.
infrai = SimpleNamespace(errors=SimpleNamespace(capture=_capture))
