import hashlib
import hmac
import time

import pytest

from detecte.webhooks import (
    WebhookVerificationError,
    is_valid_webhook,
    verify_webhook,
)


def _sign(payload: str, secret: str, ts: int) -> str:
    signed = f"{ts}.{payload}".encode("utf-8")
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def test_valid_signature_passes():
    ts = int(time.time())
    payload = '{"hi":1}'
    secret = "whsec_test"
    verify_webhook(payload=payload, signature=_sign(payload, secret, ts), secret=secret)


def test_tampered_payload_fails():
    ts = int(time.time())
    secret = "whsec_test"
    sig = _sign('{"hi":1}', secret, ts)
    with pytest.raises(WebhookVerificationError):
        verify_webhook(payload='{"hi":2}', signature=sig, secret=secret)


def test_old_timestamp_fails():
    secret = "whsec_test"
    payload = '{"hi":1}'
    ts = int(time.time()) - 1000
    with pytest.raises(WebhookVerificationError, match="tolerance"):
        verify_webhook(payload=payload, signature=_sign(payload, secret, ts), secret=secret)


def test_is_valid_webhook_returns_bool():
    ts = int(time.time())
    payload = "abc"
    secret = "whsec_test"
    assert is_valid_webhook(payload=payload, signature=_sign(payload, secret, ts), secret=secret)
    assert not is_valid_webhook(payload="abd", signature=_sign(payload, secret, ts), secret=secret)


def test_malformed_header_fails():
    with pytest.raises(WebhookVerificationError):
        verify_webhook(payload="x", signature="not-a-valid-header", secret="s")
