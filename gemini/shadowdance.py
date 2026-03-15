"""
ShadowDance - LangSmith observability for Unitree robot SDKs.

Wraps any Unitree SDK client object and intercepts method calls,
logging them as LangSmith runs with command name, arguments, result,
timestamp, and duration.
"""

from __future__ import annotations

import functools
import inspect
import time
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
        # Use super().__setattr__ to avoid recursion in __setattr__
        super().__setattr__("_client", client)

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

        @functools.wraps(method)
        def traced(*args: Any, **kwargs: Any) -> Any:
            # Map arguments to their names for the trace if possible
            try:
                sig = inspect.signature(method)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                inputs = dict(bound.arguments)
                # Remove 'self' if it's present (usually not for bound methods)
                if "self" in inputs:
                    inputs.pop("self")
            except Exception:
                # Fallback if signature binding fails
                inputs = {"args": args, "kwargs": kwargs} if args or kwargs else {}

            start_time = time.perf_counter()
            # Wrap execution in a LangSmith trace context
            with trace(name=name, run_type="tool", inputs=inputs) as rt:
                try:
                    # Execute the original method
                    result = method(*args, **kwargs)
                    
                    # Log outputs
                    if hasattr(rt, "add_outputs"):
                        rt.add_outputs({"result": result})
                    elif hasattr(rt, "set_output"):
                        rt.set_output({"result": result})
                        
                    # Add duration metadata
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    if hasattr(rt, "add_metadata"):
                        rt.add_metadata({"duration_ms": duration_ms})
                        
                    return result
                except Exception:
                    # The trace context manager automatically logs exceptions 
                    # and marks the run as failed.
                    raise

        return traced

    def __setattr__(self, name: str, value: Any) -> None:
        """Delegate attribute setting to the wrapped client."""
        if name == "_client":
            super().__setattr__(name, value)
        else:
            setattr(self._client, name, value)

    def __delattr__(self, name: str) -> None:
        """Delegate attribute deletion to the wrapped client."""
        delattr(self._client, name)

    def __dir__(self) -> list[str]:
        """Delegate dir() to the wrapped client."""
        return dir(self._client)

    def __repr__(self) -> str:
        """Return a string representation of the ShadowDance wrapper."""
        return f"ShadowDance({self._client!r})"
