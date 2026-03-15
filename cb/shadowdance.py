"""
ShadowDance - LangSmith observability for Unitree robot SDKs.

Wraps any Unitree SDK client object and intercepts method calls,
logging them as LangSmith runs with command name, arguments, result,
timestamp, and duration.
"""

from __future__ import annotations

from functools import wraps
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
        """
        Initialize the ShadowDance wrapper.

        Args:
            client: The Unitree SDK client object to wrap.
        """
        self._client = client

    def __getattr__(self, name: str) -> Any:
        """
        Intercept attribute access on the wrapped client.

        If the attribute is a callable method, wrap it with LangSmith tracing.
        Otherwise, return the attribute directly.

        Args:
            name: The name of the attribute to access.

        Returns:
            The wrapped method or the original attribute.
        """
        attr = getattr(self._client, name)

        if callable(attr):
            return self._wrap_method(attr, name)

        return attr

    def _wrap_method(self, method: Callable, name: str) -> Callable:
        """
        Wrap a method with LangSmith tracing.

        Args:
            method: The method to wrap.
            name: The name of the method.

        Returns:
            A wrapped version of the method that logs to LangSmith.
        """

        @wraps(method)
        def traced(*args: Any, **kwargs: Any) -> Any:
            with trace(name=name, run_type="tool") as rt:
                input_data = {}
                if args:
                    input_data["args"] = args
                if kwargs:
                    input_data["kwargs"] = kwargs
                rt.add_inputs(input_data)

                result = method(*args, **kwargs)
                rt.add_outputs({"result": result})

                return result

        return traced

    def __repr__(self) -> str:
        """Return a string representation of the ShadowDance wrapper."""
        return f"ShadowDance({self._client!r})"