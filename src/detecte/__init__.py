"""Detecte — runtime security for AI agents.

Quickstart::

    from detecte import Detecte

    detecte = Detecte(api_key=os.environ["DETECTE_API_KEY"])

    decision = detecte.verify(
        agent="support_bot",
        action="refund_order",
        params={"order_id": "ord_8821", "amount": 49.99},
    )

    if not decision.allowed:
        raise RuntimeError(f"Blocked: {decision.reason}")
"""

from .client import Detecte, AsyncDetecte
from .errors import (
    DetecteError,
    DetecteApiError,
    DetecteAuthError,
    DetecteValidationError,
    DetecteRateLimitError,
    DetecteNetworkError,
    DetecteTimeoutError,
)
from .types import (
    Decision,
    Agent,
    Policy,
    Incident,
    AuditEntry,
    Approval,
    PolicyEvaluation,
)
from .webhooks import verify_webhook, WebhookVerificationError

__version__ = "0.1.1"

__all__ = [
    "Detecte",
    "AsyncDetecte",
    "DetecteError",
    "DetecteApiError",
    "DetecteAuthError",
    "DetecteValidationError",
    "DetecteRateLimitError",
    "DetecteNetworkError",
    "DetecteTimeoutError",
    "Decision",
    "Agent",
    "Policy",
    "Incident",
    "AuditEntry",
    "Approval",
    "PolicyEvaluation",
    "verify_webhook",
    "WebhookVerificationError",
    "__version__",
]
