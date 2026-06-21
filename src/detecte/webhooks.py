"""Webhook signature verification (Stripe-style HMAC-SHA256)."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional


class WebhookVerificationError(Exception):
    """Raised when a webhook signature can't be verified."""


def verify_webhook(
    *,
    payload: str | bytes,
    signature: str,
    secret: str,
    tolerance_s: int = 5 * 60,
) -> None:
    """Raise WebhookVerificationError unless the signature is valid.

    `signature` is the `Detecte-Signature` header value, formatted as
    ``t=<unix>,v1=<hex>``.
    """

    parts = dict(p.split("=", 1) for p in signature.split(",") if "=" in p)
    ts = parts.get("t")
    v1 = parts.get("v1")
    if not ts or not v1:
        raise WebhookVerificationError("malformed signature header")

    try:
        ts_int = int(ts)
    except ValueError:
        raise WebhookVerificationError("invalid timestamp")

    if abs(time.time() - ts_int) > tolerance_s:
        raise WebhookVerificationError("timestamp outside tolerance")

    if isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    else:
        payload_bytes = payload
    signed = f"{ts}.".encode("utf-8") + payload_bytes
    expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, v1):
        raise WebhookVerificationError("bad signature")


def is_valid_webhook(
    *,
    payload: str | bytes,
    signature: str,
    secret: str,
    tolerance_s: int = 5 * 60,
) -> bool:
    """Convenience wrapper that returns a bool instead of raising."""
    try:
        verify_webhook(payload=payload, signature=signature, secret=secret, tolerance_s=tolerance_s)
        return True
    except WebhookVerificationError:
        return False
