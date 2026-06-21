import httpx
import pytest
import respx

from detecte import Detecte, AsyncDetecte


@respx.mock
def test_verify_allowed():
    respx.post("https://api.detecte.xyz/v1/verify").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "dec_1",
                "allowed": True,
                "status": "allowed",
                "reason": None,
                "policies_evaluated": [],
                "risk_delta": 1,
                "metadata": {"latency_ms": 12},
            },
        )
    )
    d = Detecte(api_key="sk_test_x")
    decision = d.verify(agent="bot", action="x")
    assert decision.allowed
    assert decision.id == "dec_1"


@respx.mock
def test_verify_blocked():
    respx.post("https://api.detecte.xyz/v1/verify").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "dec_2",
                "allowed": False,
                "status": "blocked",
                "reason": "policy violation",
                "policies_evaluated": [{"id": "pol_1", "name": "amount_cap", "result": "blocked"}],
                "risk_delta": 0,
                "metadata": {"latency_ms": 8},
            },
        )
    )
    d = Detecte(api_key="sk_test_x")
    decision = d.verify(agent="bot", action="refund", params={"amount": 9999})
    assert not decision.allowed
    assert decision.policies_evaluated[0].name == "amount_cap"


@respx.mock
def test_failsafe_open_on_network_error():
    respx.post("https://api.detecte.xyz/v1/verify").mock(side_effect=httpx.ConnectError("boom"))
    d = Detecte(api_key="sk_test_x", retries=0, failsafe="fail_open")
    decision = d.verify(agent="bot", action="x")
    assert decision.allowed is True
    assert "fail_open" in (decision.reason or "")


@pytest.mark.asyncio
@respx.mock
async def test_async_client_verify():
    respx.post("https://api.detecte.xyz/v1/verify").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "dec_3",
                "allowed": True,
                "status": "allowed",
                "reason": None,
                "policies_evaluated": [],
                "risk_delta": 0,
                "metadata": {"latency_ms": 5},
            },
        )
    )
    d = AsyncDetecte(api_key="sk_test_x")
    decision = await d.verify(agent="bot", action="x")
    assert decision.allowed
