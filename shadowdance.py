"""
ShadowDance - LangSmith observability for LLM and robot SDKs.

Wraps any client object (OpenAI, Unitree, etc.) and intercepts method calls,
logging them as LangSmith runs with command name, arguments, result,
timestamp, and duration.

Usage:
    from shadowdance import ShadowDance
    
    # OpenAI client (LLM runs)
    client = OpenAI()
    client = ShadowDance(client, run_type="llm")
    response = client.chat.completions.create(...)  # Traced as LLM

    # Robot client (tool runs)
    client = SportClient()
    client = ShadowDance(client, run_type="tool")
    client.Move(0.3, 0, 0)  # Traced as tool

    # With dataset logging for experiments
    client = ShadowDance(client, run_type="tool", log_to_dataset="robot-tasks")
"""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, Literal, Optional

from langsmith import trace
from langsmith import Client as LangSmithClient

RunType = Literal["tool", "chain", "llm", "retriever", "embedding", "prompt"]


class ShadowDance:
    """
    Proxy wrapper for client objects that adds LangSmith tracing.

    Works with any client: OpenAI, Unitree robot SDKs, or custom clients.
    Every method call becomes a traced LangSmith event with proper run type.

    Usage:
        from shadowdance import ShadowDance

        # OpenAI client - traced as LLM
        client = OpenAI()
        client = ShadowDance(client, run_type="llm")
        response = client.chat.completions.create(...)

        # Robot client - traced as tool
        client = SportClient()
        client = ShadowDance(client, run_type="tool")
        client.Move(0.3, 0, 0)

        # Custom client - traced as chain
        client = CustomClient()
        client = ShadowDance(client, run_type="chain")
    """

    def __init__(self, client: Any, run_type: RunType = "tool"):
        """
        Initialize the ShadowDance wrapper.

        Args:
            client: The client object to wrap (OpenAI, Unitree, etc.).
            run_type: LangSmith run type for better dashboard filtering.
                      Options: "tool", "chain", "llm", "retriever", "embedding", "prompt"
                      Default: "tool"
        """
        self._client = client
        self._run_type = run_type

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

            with trace(name=name, run_type=self._run_type) as rt:
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
