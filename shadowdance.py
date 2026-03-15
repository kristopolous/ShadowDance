"""
ShadowDance - LangSmith observability for LLM and robot SDKs.

Wraps any client object (OpenAI, Unitree, etc.) and intercepts method calls,
logging them as LangSmith runs with command name, arguments, result,
timestamp, and duration.

Usage:
    from shadowdance import ShadowDance
    
    client = OpenAI()
    client = ShadowDance(client)  # ONE LINE
    response = client.chat.completions.create(...)  # Now traced!
"""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, Optional

from langsmith import trace


class ShadowDance:
    """
    Proxy wrapper for client objects that adds LangSmith tracing.

    Works with any client: OpenAI, Unitree robot SDKs, or custom clients.
    Every method call becomes a traced LangSmith event.

    Usage:
        from shadowdance import ShadowDance
        
        # OpenAI client
        client = OpenAI()
        client = ShadowDance(client)
        response = client.chat.completions.create(...)

        # Robot client
        client = SportClient()
        client = ShadowDance(client)
        client.Move(0.3, 0, 0)
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
            start_time = time.perf_counter()
            result: Any = None

            with trace(name=name, run_type="tool") as rt:
                try:
                    # Log inputs
                    input_data = {}
                    if args:
                        input_data["args"] = args
                    if kwargs:
                        input_data["kwargs"] = kwargs
                    rt.add_inputs(input_data)

                    # Execute the method
                    result = method(*args, **kwargs)

                    # Log outputs
                    rt.add_outputs({"result": result})

                    return result

                except Exception as e:
                    # Log exception
                    rt.add_event({"name": "error", "data": {"error": str(e)}})
                    raise

                finally:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    # Duration is automatically tracked by LangSmith via latency property
                    rt.add_metadata({"duration_ms": elapsed_ms})

        return traced

    def __repr__(self) -> str:
        """Return a string representation of the ShadowDance wrapper."""
        return f"ShadowDance({self._client!r})"
