# detecte (Python)

[![PyPI](https://img.shields.io/pypi/v/detecte.svg)](https://pypi.org/project/detecte/)
[![Python](https://img.shields.io/pypi/pyversions/detecte.svg)](https://pypi.org/project/detecte/)

Runtime security for AI agents. The Python SDK for [detecte.xyz](https://detecte.xyz) — a one-to-one
companion to [`@detecte/sdk`](https://www.npmjs.com/package/@detecte/sdk).

## Install

```bash
pip install detecte
```

## Quickstart

```python
import os
from detecte import Detecte

detecte = Detecte(api_key=os.environ["DETECTE_API_KEY"])

decision = detecte.verify(
    agent="support_bot",
    action="refund_order",
    params={"order_id": "ord_8821", "amount": 49.99},
)

if not decision.allowed:
    raise RuntimeError(f"Blocked: {decision.reason}")
```

## Async

```python
from detecte import AsyncDetecte

async def main():
    detecte = AsyncDetecte(api_key="sk_test_...")
    decision = await detecte.verify(agent="bot", action="x")
    print(decision.allowed)
```

## Resources

- `detecte.agents.list() / .get(id) / .create(...)`
- `detecte.policies.list() / .create(...) / .dry_run(policy=..., sample_size=1000)`
- `detecte.incidents.list() / .resolve(id)`
- `detecte.audit.list(...)`
- `detecte.approvals.get(decision_id) / .wait(decision_id)`
- `detecte.scans.run(agent=..., system_prompt=...)`

## Webhooks

```python
from detecte import verify_webhook, WebhookVerificationError

try:
    verify_webhook(
        payload=raw_body,
        signature=request.headers["Detecte-Signature"],
        secret=os.environ["DETECTE_WEBHOOK_SECRET"],
    )
except WebhookVerificationError:
    return Response(status=401)
```

## LangChain integration

```python
from detecte import Detecte
from detecte.integrations.langchain import DetecteCallbackHandler

detecte = Detecte()
handler = DetecteCallbackHandler(detecte=detecte, agent_id="agent_xxx")
executor = AgentExecutor.from_agent_and_tools(
    agent=...,
    tools=...,
    callbacks=[handler],
)
```

## License

MIT — copyright Detecte, Inc.
