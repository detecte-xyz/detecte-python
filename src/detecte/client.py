"""Top-level Detecte client (sync + async)."""

from __future__ import annotations

import os
from typing import Any, Literal, Optional

from .http import SyncHttp, AsyncHttp, DEFAULT_BASE_URL
from .errors import DetecteApiError, DetecteNetworkError
from .types import Decision, Agent, Policy, Incident, AuditEntry, Approval

Failsafe = Literal["fail_open", "fail_closed", "fail_silent"]


def _resolve_key(api_key: Optional[str]) -> str:
    k = api_key or os.environ.get("DETECTE_API_KEY")
    if not k:
        raise ValueError("api_key not provided and DETECTE_API_KEY not set")
    return k


def _fallback_decision(reason: str) -> Decision:
    return Decision.model_validate(
        {
            "id": "dec_fallback",
            "allowed": True,
            "status": "allowed",
            "reason": reason,
            "policies_evaluated": [],
            "risk_delta": 0,
            "approval_url": None,
            "metadata": {"latency_ms": 0},
        }
    )


class Detecte:
    """Synchronous Detecte client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 5.0,
        retries: int = 2,
        failsafe: Failsafe = "fail_open",
    ):
        self._http = SyncHttp(_resolve_key(api_key), base_url, timeout, retries)
        self._failsafe = failsafe
        self.agents = _AgentsResource(self._http)
        self.policies = _PoliciesResource(self._http)
        self.incidents = _IncidentsResource(self._http)
        self.audit = _AuditResource(self._http)
        self.approvals = _ApprovalsResource(self._http)
        self.scans = _ScansResource(self._http)

    def verify(
        self,
        *,
        agent: str,
        action: str,
        params: Optional[dict[str, Any]] = None,
        context: Optional[dict[str, Any]] = None,
        sensitive: Optional[list[str]] = None,
        session_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Decision:
        body = {
            "agent": agent,
            "action": action,
            "params": params or {},
            "context": context or {},
        }
        if sensitive:
            body["sensitive"] = sensitive
        if session_id:
            body["sessionId"] = session_id
        if idempotency_key:
            body["idempotencyKey"] = idempotency_key
        try:
            data = self._http.request("POST", "/v1/verify", json=body)
            return Decision.model_validate(data)
        except DetecteNetworkError:
            if self._failsafe == "fail_open":
                return _fallback_decision("Detecte unreachable; fail_open")
            if self._failsafe == "fail_closed":
                return Decision.model_validate(
                    {
                        "id": "dec_fallback",
                        "allowed": False,
                        "status": "blocked",
                        "reason": "Detecte unreachable; fail_closed",
                        "policies_evaluated": [],
                        "risk_delta": 0,
                        "approval_url": None,
                        "metadata": {"latency_ms": 0},
                    }
                )
            raise


class AsyncDetecte:
    """Asynchronous Detecte client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 5.0,
        retries: int = 2,
        failsafe: Failsafe = "fail_open",
    ):
        self._http = AsyncHttp(_resolve_key(api_key), base_url, timeout, retries)
        self._failsafe = failsafe
        self.agents = _AsyncAgentsResource(self._http)
        self.policies = _AsyncPoliciesResource(self._http)
        self.incidents = _AsyncIncidentsResource(self._http)
        self.audit = _AsyncAuditResource(self._http)
        self.approvals = _AsyncApprovalsResource(self._http)
        self.scans = _AsyncScansResource(self._http)

    async def verify(
        self,
        *,
        agent: str,
        action: str,
        params: Optional[dict[str, Any]] = None,
        context: Optional[dict[str, Any]] = None,
        sensitive: Optional[list[str]] = None,
        session_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Decision:
        body = {
            "agent": agent,
            "action": action,
            "params": params or {},
            "context": context or {},
        }
        if sensitive:
            body["sensitive"] = sensitive
        if session_id:
            body["sessionId"] = session_id
        if idempotency_key:
            body["idempotencyKey"] = idempotency_key
        try:
            data = await self._http.request("POST", "/v1/verify", json=body)
            return Decision.model_validate(data)
        except DetecteNetworkError:
            if self._failsafe == "fail_open":
                return _fallback_decision("Detecte unreachable; fail_open")
            if self._failsafe == "fail_closed":
                return Decision.model_validate(
                    {
                        "id": "dec_fallback",
                        "allowed": False,
                        "status": "blocked",
                        "reason": "Detecte unreachable; fail_closed",
                        "policies_evaluated": [],
                        "risk_delta": 0,
                        "approval_url": None,
                        "metadata": {"latency_ms": 0},
                    }
                )
            raise


# ── Sync resources ──

class _AgentsResource:
    def __init__(self, http: SyncHttp):
        self._h = http

    def list(self, limit: int = 50) -> list[Agent]:
        data = self._h.request("GET", f"/v1/agents?limit={limit}") or {}
        return [Agent.model_validate(a) for a in data.get("data", [])]

    def get(self, agent_id: str) -> Agent:
        return Agent.model_validate(self._h.request("GET", f"/v1/agents/{agent_id}"))

    def create(self, **fields: Any) -> Agent:
        return Agent.model_validate(self._h.request("POST", "/v1/agents", json=fields))

    def update(self, agent_id: str, **fields: Any) -> Agent:
        return Agent.model_validate(self._h.request("PATCH", f"/v1/agents/{agent_id}", json=fields))


class _PoliciesResource:
    def __init__(self, http: SyncHttp):
        self._h = http

    def list(self, limit: int = 100) -> list[Policy]:
        data = self._h.request("GET", f"/v1/policies?limit={limit}") or {}
        return [Policy.model_validate(p) for p in data.get("data", [])]

    def create(self, **fields: Any) -> Policy:
        return Policy.model_validate(self._h.request("POST", "/v1/policies", json=fields))

    def dry_run(self, *, policy: dict[str, Any], sample_size: int = 1000) -> dict[str, Any]:
        return self._h.request(
            "POST",
            "/v1/policies/dry-run",
            json={"policy": policy, "sample_size": sample_size},
        )

    def update(self, policy_id: str, **fields: Any) -> Policy:
        return Policy.model_validate(self._h.request("PATCH", f"/v1/policies/{policy_id}", json=fields))

    def delete(self, policy_id: str) -> None:
        self._h.request("DELETE", f"/v1/policies/{policy_id}")


class _IncidentsResource:
    def __init__(self, http: SyncHttp):
        self._h = http

    def list(self, limit: int = 50) -> list[Incident]:
        data = self._h.request("GET", f"/v1/incidents?limit={limit}") or {}
        return [Incident.model_validate(i) for i in data.get("data", [])]

    def resolve(self, incident_id: str) -> Incident:
        return Incident.model_validate(self._h.request("POST", f"/v1/incidents/{incident_id}/resolve"))


class _AuditResource:
    def __init__(self, http: SyncHttp):
        self._h = http

    def list(self, **params: Any) -> list[AuditEntry]:
        from urllib.parse import urlencode
        qs = urlencode({k: v for k, v in params.items() if v is not None})
        data = self._h.request("GET", f"/v1/audit?{qs}" if qs else "/v1/audit") or {}
        return [AuditEntry.model_validate(a) for a in data.get("data", [])]


class _ApprovalsResource:
    def __init__(self, http: SyncHttp):
        self._h = http

    def get(self, decision_id: str) -> Approval:
        return Approval.model_validate(self._h.request("GET", f"/v1/approvals/{decision_id}"))

    def wait(self, decision_id: str, *, timeout_ms: int = 5 * 60_000, poll_ms: int = 2000) -> Approval:
        import time as _time
        deadline = _time.time() + timeout_ms / 1000
        while True:
            a = self.get(decision_id)
            if a.approved is not None:
                return a
            if _time.time() >= deadline:
                return a
            _time.sleep(poll_ms / 1000)


class _ScansResource:
    def __init__(self, http: SyncHttp):
        self._h = http

    def run(self, agent: str, *, system_prompt: Optional[str] = None) -> dict[str, Any]:
        body: dict[str, Any] = {"agent": agent}
        if system_prompt is not None:
            body["system_prompt"] = system_prompt
        return self._h.request("POST", "/v1/scans", json=body)


# ── Async resources (wrappers) ──

class _AsyncAgentsResource:
    def __init__(self, http: AsyncHttp):
        self._h = http

    async def list(self, limit: int = 50) -> list[Agent]:
        data = (await self._h.request("GET", f"/v1/agents?limit={limit}")) or {}
        return [Agent.model_validate(a) for a in data.get("data", [])]

    async def get(self, agent_id: str) -> Agent:
        return Agent.model_validate(await self._h.request("GET", f"/v1/agents/{agent_id}"))

    async def create(self, **fields: Any) -> Agent:
        return Agent.model_validate(await self._h.request("POST", "/v1/agents", json=fields))


class _AsyncPoliciesResource:
    def __init__(self, http: AsyncHttp):
        self._h = http

    async def list(self, limit: int = 100) -> list[Policy]:
        data = (await self._h.request("GET", f"/v1/policies?limit={limit}")) or {}
        return [Policy.model_validate(p) for p in data.get("data", [])]

    async def create(self, **fields: Any) -> Policy:
        return Policy.model_validate(await self._h.request("POST", "/v1/policies", json=fields))


class _AsyncIncidentsResource:
    def __init__(self, http: AsyncHttp):
        self._h = http

    async def list(self, limit: int = 50) -> list[Incident]:
        data = (await self._h.request("GET", f"/v1/incidents?limit={limit}")) or {}
        return [Incident.model_validate(i) for i in data.get("data", [])]


class _AsyncAuditResource:
    def __init__(self, http: AsyncHttp):
        self._h = http

    async def list(self, **params: Any) -> list[AuditEntry]:
        from urllib.parse import urlencode
        qs = urlencode({k: v for k, v in params.items() if v is not None})
        data = (await self._h.request("GET", f"/v1/audit?{qs}" if qs else "/v1/audit")) or {}
        return [AuditEntry.model_validate(a) for a in data.get("data", [])]


class _AsyncApprovalsResource:
    def __init__(self, http: AsyncHttp):
        self._h = http

    async def get(self, decision_id: str) -> Approval:
        return Approval.model_validate(await self._h.request("GET", f"/v1/approvals/{decision_id}"))


class _AsyncScansResource:
    def __init__(self, http: AsyncHttp):
        self._h = http

    async def run(self, agent: str, *, system_prompt: Optional[str] = None) -> dict[str, Any]:
        body: dict[str, Any] = {"agent": agent}
        if system_prompt is not None:
            body["system_prompt"] = system_prompt
        return await self._h.request("POST", "/v1/scans", json=body)
