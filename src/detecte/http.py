"""Sync + async HTTP client with retries, timeouts, and Detecte-specific error mapping."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Optional

import httpx

from .errors import (
    DetecteApiError,
    DetecteAuthError,
    DetecteNetworkError,
    DetecteRateLimitError,
    DetecteTimeoutError,
    DetecteValidationError,
)

__VERSION__ = "0.1.1"
USER_AGENT = f"detecte-python/{__VERSION__}"
DEFAULT_BASE_URL = "https://api.detecte.xyz"


def _map_status(status: int, body: Any) -> type[DetecteApiError]:
    if status == 401 or status == 403:
        return DetecteAuthError
    if status == 422:
        return DetecteValidationError
    if status == 429:
        return DetecteRateLimitError
    return DetecteApiError


def _retry_after_ms(response: httpx.Response) -> Optional[int]:
    ra = response.headers.get("retry-after")
    if not ra:
        return None
    try:
        return int(float(ra) * 1000)
    except (TypeError, ValueError):
        return None


def _backoff(attempt: int) -> float:
    return min(0.25 * (2 ** attempt) + 0.05 * attempt, 5.0)


class _BaseHttp:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout_s: float = 5.0,
        retries: int = 2,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.retries = retries

    def _headers(self, extra: Optional[dict[str, str]] = None) -> dict[str, str]:
        h = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }
        if extra:
            h.update(extra)
        return h

    def _raise_for_status(self, response: httpx.Response) -> None:
        if 200 <= response.status_code < 300:
            return
        try:
            body = response.json()
        except Exception:
            body = response.text
        message = (
            (body.get("message") if isinstance(body, dict) else None)
            or (body if isinstance(body, str) else f"HTTP {response.status_code}")
        )
        cls = _map_status(response.status_code, body)
        if cls is DetecteRateLimitError:
            raise DetecteRateLimitError(
                message,
                status=response.status_code,
                retry_after_ms=_retry_after_ms(response),
                body=body,
            )
        raise cls(message, status=response.status_code, body=body)


class SyncHttp(_BaseHttp):
    def request(self, method: str, path: str, *, json: Any = None, headers: Optional[dict[str, str]] = None) -> Any:
        url = f"{self.base_url}{path}"
        last_err: Optional[BaseException] = None
        for attempt in range(self.retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_s) as client:
                    response = client.request(method, url, json=json, headers=self._headers(headers))
                if response.status_code == 429 and attempt < self.retries:
                    time.sleep((_retry_after_ms(response) or 1000) / 1000)
                    continue
                if 500 <= response.status_code < 600 and attempt < self.retries:
                    time.sleep(_backoff(attempt))
                    continue
                self._raise_for_status(response)
                return response.json() if response.content else None
            except httpx.TimeoutException as e:
                last_err = e
                if attempt < self.retries:
                    time.sleep(_backoff(attempt))
                    continue
                raise DetecteTimeoutError(f"Timed out after {self.timeout_s}s")
            except httpx.HTTPError as e:
                last_err = e
                if attempt < self.retries:
                    time.sleep(_backoff(attempt))
                    continue
                raise DetecteNetworkError(str(e))
        if last_err:
            raise DetecteNetworkError(str(last_err))


class AsyncHttp(_BaseHttp):
    async def request(self, method: str, path: str, *, json: Any = None, headers: Optional[dict[str, str]] = None) -> Any:
        url = f"{self.base_url}{path}"
        last_err: Optional[BaseException] = None
        for attempt in range(self.retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                    response = await client.request(method, url, json=json, headers=self._headers(headers))
                if response.status_code == 429 and attempt < self.retries:
                    await asyncio.sleep((_retry_after_ms(response) or 1000) / 1000)
                    continue
                if 500 <= response.status_code < 600 and attempt < self.retries:
                    await asyncio.sleep(_backoff(attempt))
                    continue
                self._raise_for_status(response)
                return response.json() if response.content else None
            except httpx.TimeoutException as e:
                last_err = e
                if attempt < self.retries:
                    await asyncio.sleep(_backoff(attempt))
                    continue
                raise DetecteTimeoutError(f"Timed out after {self.timeout_s}s")
            except httpx.HTTPError as e:
                last_err = e
                if attempt < self.retries:
                    await asyncio.sleep(_backoff(attempt))
                    continue
                raise DetecteNetworkError(str(e))
        if last_err:
            raise DetecteNetworkError(str(last_err))
