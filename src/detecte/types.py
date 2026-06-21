"""Pydantic models mirroring @detecte/sdk's Zod schemas."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Tier = Literal["low", "medium", "high", "restricted"]
DecisionStatus = Literal["allowed", "blocked", "escalated", "pending_approval"]


class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class PolicyEvaluation(_Base):
    id: str
    name: str
    result: str


class DecisionMetadata(_Base):
    latency_ms: int = 0


class Decision(_Base):
    id: str
    allowed: bool
    status: DecisionStatus
    reason: Optional[str] = None
    policies_evaluated: list[PolicyEvaluation] = Field(default_factory=list)
    risk_delta: float = 0
    approval_url: Optional[str] = None
    expires_at: Optional[str] = None
    metadata: DecisionMetadata = Field(default_factory=DecisionMetadata)


class Agent(_Base):
    id: str
    name: str
    description: Optional[str] = None
    tier: Tier = "medium"
    declared_capabilities: list[str] = Field(default_factory=list)
    risk_score: int = 0
    created_at: Optional[str] = None


class Policy(_Base):
    id: str
    name: str
    agents: list[str] = Field(default_factory=list)
    when: dict[str, Any] = Field(default_factory=dict)
    then: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_at: Optional[str] = None


class Incident(_Base):
    id: str
    agent: Optional[str] = None
    decision_id: Optional[str] = None
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    status: Literal["open", "acknowledged", "resolved"] = "open"
    summary: str
    created_at: str
    resolved_at: Optional[str] = None


class AuditEntry(_Base):
    id: str
    ts: str
    agent: Optional[str] = None
    action: Optional[str] = None
    decision_id: Optional[str] = None
    status: Optional[DecisionStatus] = None
    actor: Optional[str] = None


class Approval(_Base):
    id: str
    decision_id: str
    approved: Optional[bool] = None
    reason: Optional[str] = None
    approver: Optional[str] = None
    approval_url: Optional[str] = None
