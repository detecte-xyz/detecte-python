"""LangChain integration: a callback handler that verifies every tool call.

Usage::

    from langchain.agents import AgentExecutor
    from detecte import Detecte
    from detecte.integrations.langchain import DetecteCallbackHandler

    detecte = Detecte(api_key=...)
    executor = AgentExecutor.from_agent_and_tools(
        agent=...,
        tools=...,
        callbacks=[DetecteCallbackHandler(detecte=detecte, agent_id="agent_xxx")],
    )

When a blocked decision is encountered the handler raises a
``DetecteToolBlocked`` so the executor's standard error path will surface the
refusal back into the agent loop.
"""

from __future__ import annotations

from typing import Any, Optional


class DetecteToolBlocked(RuntimeError):
    """Raised by the callback when Detecte blocks a tool call."""


def _import_base_callback_handler() -> type:
    try:
        from langchain_core.callbacks.base import BaseCallbackHandler  # type: ignore
    except ImportError:
        try:
            from langchain.callbacks.base import BaseCallbackHandler  # type: ignore
        except ImportError as e:
            raise ImportError(
                "langchain (>=0.1) is required for DetecteCallbackHandler"
            ) from e
    return BaseCallbackHandler


def DetecteCallbackHandler(detecte: Any, agent_id: str) -> Any:  # noqa: N802 — public name
    """Construct a LangChain callback handler tied to a Detecte client + agent_id."""
    Base = _import_base_callback_handler()

    class _Handler(Base):  # type: ignore[misc, valid-type]
        def on_tool_start(
            self,
            serialized: dict[str, Any],
            input_str: str,
            *,
            run_id: Optional[str] = None,
            **kwargs: Any,
        ) -> None:
            tool_name = serialized.get("name") or "unknown"
            decision = detecte.verify(
                agent=agent_id,
                action=tool_name,
                params={"input": input_str},
                context={"run_id": str(run_id) if run_id else None},
            )
            if not decision.allowed:
                raise DetecteToolBlocked(
                    decision.reason or f"Detecte blocked tool {tool_name}"
                )

    return _Handler()
