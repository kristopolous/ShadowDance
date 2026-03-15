"""
ShadowDance - LangSmith observability for Unitree robot SDKs.

Wraps any Unitree SDK client object and intercepts method calls,
logging them as LangSmith runs with command name, arguments, result,
timestamp, and duration.
"""

from __future__ import annotations

from typing import Any, Callable

from langsmith import trace


class ShadowDance:
    """
    Proxy wrapper for Unitree SDK clients that adds LangSmith tracing.

    Usage:
        client = LocoClient()
        client = ShadowDance(client)  # <- add this
        client.Move(0.3, 0, 0)        # <- everything else unchanged

    Every method call is now a traced LangSmith event.
    """

    def __init__(self, client: Any):
        self._client = client

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._client, name)

        if callable(attr):
            return self._wrap_method(attr, name)

        return attr

    def _wrap_method(self, method: Callable, name: str) -> Callable:
        def traced(*args: Any, **kwargs: Any) -> Any:
            with trace(name=name, inputs={"args": args, "kwargs": kwargs}) as run:
                result = method(*args, **kwargs)
                run.set_output({"result": result})
                return result

        return traced

    def __repr__(self) -> str:
        return f"ShadowDance({self._client!r})"