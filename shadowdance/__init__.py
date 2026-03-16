"""
ShadowDance - Observability for LLM and robot SDKs.

Wraps any client object (OpenAI, Unitree, etc.) and intercepts method calls,
logging them as traced events with command name, arguments, result,
timestamp, and duration.

Supports multiple observability backends via adapter pattern:
- LangSmith (default)
- Langfuse
- Weave (Weights & Biases)
- Custom adapters (see shadowdance.adapters.example)

Usage:
    from shadowdance import ShadowDance, task

    # OpenAI client (LLM runs)
    client = OpenAI()
    client = ShadowDance(client, run_type="llm")
    response = client.chat.completions.create(...)

    # Robot client (tool runs)
    client = SportClient()
    client = ShadowDance(client, run_type="tool")
    client.Move(0.3, 0, 0)

    # With task decorator for nesting
    @task("pick_up_box")
    def my_task():
        robot = ShadowDance(SportClient())
        robot.Move(0.3, 0, 0)  # Nested under "pick_up_box"

Environment Variables:
    PLATFORM: Observability backend ("langsmith", "langfuse", or "weave")
            Default: "langsmith"

Design:
    - Timestamps captured by ShadowDance (not adapters) for accurate latency
    - Fire-and-forget: adapters send in background, may drop under load
    - Observability never blocks user code
    - Lazy imports: only the selected adapter's dependencies are required
"""

from __future__ import annotations

import atexit
import os
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional
from contextlib import contextmanager

from .adapters import (
    ObservabilityAdapter,
    RunType,
    TraceEvent,
    DatasetExample,
)
from .adapters.langsmith import LangSmithAdapter
from .adapters.langfuse import LangfuseAdapter

# WeaveAdapter is imported lazily to avoid requiring weave unless PLATFORM=weave
# from .adapters.weave import WeaveAdapter


# ============================================================================
# Adapter Factory
# ============================================================================

_adapter_cache: Optional[ObservabilityAdapter] = None


def _get_adapter() -> ObservabilityAdapter:
    """Get the configured observability adapter based on PLATFORM env var."""
    global _adapter_cache

    if _adapter_cache is not None:
        return _adapter_cache

    platform = os.environ.get("PLATFORM", "langsmith").lower()

    if platform == "weave":
        from .adapters.weave import WeaveAdapter
        _adapter_cache = WeaveAdapter()
    elif platform == "langfuse":
        from .adapters.langfuse import LangfuseAdapter
        _adapter_cache = LangfuseAdapter()
    elif platform == "langsmith":
        from .adapters.langsmith import LangSmithAdapter
        _adapter_cache = LangSmithAdapter()
    else:
        raise ValueError(
            f"Unknown PLATFORM: {platform}. Must be 'langsmith', 'langfuse', or 'weave'"
        )

    return _adapter_cache


def _flush_on_exit():
    """Flush pending traces on program exit."""
    global _adapter_cache
    if _adapter_cache is not None:
        try:
            _adapter_cache.flush(timeout_ms=500)  # Best effort, 500ms max
        except Exception:
            pass  # Silently ignore flush errors during shutdown


atexit.register(_flush_on_exit)


# ============================================================================
# Task Decorator & Context Manager
# ============================================================================

def task(name: str, run_type: RunType = "chain", **kwargs):
    """
    Decorator to create a parent run for nested tracing.

    All ShadowDance-wrapped calls inside the function will be nested
    under this parent run.

    Args:
        name: Name of the task/run
        run_type: Run type (default: "chain")
        **kwargs: Additional metadata to log

    Usage:
        @task("pick_up_box")
        def pick_up_box():
            robot = ShadowDance(SportClient())
            robot.StandUp()
            robot.Move(0.3, 0, 0)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **func_kwargs):
            adapter = _get_adapter()

            # Create parent event
            event = TraceEvent(
                name=name,
                run_type=run_type,
                inputs={"args": args, "kwargs": func_kwargs},
                metadata={"function": func.__name__, **kwargs},
            )
            event_id = adapter.capture_event(event)

            try:
                result = func(*args, **func_kwargs)
                event.complete(outputs={"result": result})
                adapter.complete_event(event_id, event)
                return result
            except Exception as e:
                event.complete(error=e)
                adapter.complete_event(event_id, event)
                raise
        return wrapper
    return decorator


@contextmanager
def task_context(name: str, run_type: RunType = "chain", **kwargs):
    """
    Context manager for creating parent runs.

    Usage:
        with task_context("pick_up_box"):
            robot = ShadowDance(SportClient())
            robot.StandUp()
            robot.Move(0.3, 0, 0)
    """
    adapter = _get_adapter()
    event = TraceEvent(
        name=name,
        run_type=run_type,
        metadata={"context": "task_context", **kwargs},
    )
    event_id = adapter.capture_event(event)
    try:
        yield event
    finally:
        adapter.complete_event(event_id, event)


def get_parent_run() -> Optional[TraceEvent]:
    """Get the current parent event for nesting."""
    adapter = _get_adapter()
    return adapter.get_current_event()


# ============================================================================
# ShadowDance Wrapper
# ============================================================================

class ShadowDance:
    """
    Proxy wrapper for client objects that adds observability tracing.

    Works with any client: OpenAI, Unitree robot SDKs, or custom clients.
    Every method call becomes a traced event with proper run type.

    The backend is selected via the PLATFORM environment variable:
    - PLATFORM=langsmith (default)
    - PLATFORM=langfuse

    Subclasses can override get_token_count() and get_cost() for provider-specific
    usage tracking.

    Usage:
        from shadowdance import ShadowDance, task

        # Basic usage
        client = OpenAI()
        client = ShadowDance(client, run_type="llm")

        # With nesting
        @task("pick_up_box")
        def my_task():
            robot = ShadowDance(SportClient())
            robot.Move(0.3, 0, 0)
    """

    def __init__(
        self,
        client: Any,
        run_type: RunType = "tool",
        parent_run: Optional[str] = None,
        log_to_dataset: Optional[str] = None,
    ):
        """
        Initialize the ShadowDance wrapper.

        Args:
            client: The client object to wrap (OpenAI, Unitree, etc.).
            run_type: Run type for better dashboard filtering.
            parent_run: Optional parent run name for nesting.
            log_to_dataset: Optional dataset name for experiment logging.
        """
        self._client = client
        self._run_type = run_type
        self._parent_run_name = parent_run
        self._log_to_dataset = log_to_dataset
        self._adapter = _get_adapter()

    def _get_parent_event(self) -> Optional[TraceEvent]:
        """Get the parent event for nesting."""
        if self._parent_run_name:
            return None
        return get_parent_run()

    def get_token_count(self, request: Any, response: Any) -> Optional[Dict[str, int]]:
        """
        Extract token count from API request/response.

        Override in subclasses for provider-specific extraction.

        Args:
            request: The request arguments sent to the API
            response: The response object from the API

        Returns:
            Dict with token counts or None:
            {"input_tokens": int, "output_tokens": int, "total_tokens": int}
        """
        pass

    def get_cost(self, request: Any, response: Any) -> Optional[Dict[str, float]]:
        """
        Calculate cost for the API call.

        Override in subclasses for provider-specific pricing.

        Args:
            request: The request arguments sent to the API
            response: The response object from the API

        Returns:
            Dict with cost info or None:
            {"input_cost": float, "output_cost": float, "total_cost": float}
        """
        pass

    def __getattr__(self, name: str) -> Any:
        """Intercept attribute access on the wrapped client."""
        attr = getattr(self._client, name)

        if callable(attr):
            return self._wrap_method(attr, name)

        return attr

    def _wrap_method(self, method: Callable, name: str) -> Callable:
        """Wrap a method with observability tracing."""

        @wraps(method)
        def traced(*args: Any, **kwargs: Any) -> Any:
            result: Any = None
            error: Optional[Exception] = None

            # Build input data
            input_data = {}
            if args:
                input_data["args"] = args
            if kwargs:
                input_data["kwargs"] = kwargs

            # Create trace event (timestamp captured here)
            event = TraceEvent(
                name=name,
                run_type=self._run_type,
                inputs=input_data,
                parent_event=self._get_parent_event(),
            )

            # Add model metadata
            if hasattr(self, '_model') and self._model:
                event.metadata["ls_model_name"] = self._model
            if self._run_type == "llm":
                event.metadata["ls_provider"] = "openrouter"

            # Capture start and send to adapter
            event_id = self._adapter.capture_event(event)

            try:
                # Execute method
                result = method(*args, **kwargs)

                # Complete event with outputs
                event.complete(outputs={"result": result})

                # Extract token usage and cost (if subclass provides them)
                token_usage = self.get_token_count(kwargs, result)
                cost = self.get_cost(kwargs, result)

                # Update event with usage data
                if token_usage or cost:
                    usage_metadata = {}
                    if token_usage:
                        usage_metadata.update(token_usage)
                    if cost:
                        usage_metadata.update(cost)
                    self._adapter.update_event(event_id, usage_metadata)

                # Complete the event
                self._adapter.complete_event(event_id, event)

                # Log to dataset if configured
                if self._log_to_dataset:
                    example_metadata = {
                        "method": name,
                        "run_type": self._run_type,
                        "duration_ms": event.duration_ms,
                    }
                    if token_usage:
                        example_metadata["token_usage"] = token_usage
                    if cost:
                        example_metadata["cost"] = cost

                    self._adapter.log_example(
                        DatasetExample(
                            dataset_name=self._log_to_dataset,
                            inputs=input_data,
                            outputs={"result": result},
                            metadata=example_metadata,
                        )
                    )

                return result

            except Exception as e:
                error = e
                event.complete(error=e)
                self._adapter.complete_event(event_id, event)

                # Log to dataset if configured
                if self._log_to_dataset:
                    self._adapter.log_example(
                        DatasetExample(
                            dataset_name=self._log_to_dataset,
                            inputs=input_data,
                            outputs={"error": str(error)},
                            metadata={
                                "method": name,
                                "run_type": self._run_type,
                                "duration_ms": event.duration_ms,
                            },
                        )
                    )

                raise

        return traced

    def __repr__(self) -> str:
        return f"ShadowDance({self._client!r})"


__all__ = [
    "ShadowDance",
    "task",
    "task_context",
    "get_parent_run",
    "RunType",
    "ObservabilityAdapter",
    "LangSmithAdapter",
    "LangfuseAdapter",
    "WeaveAdapter",
    "TraceEvent",
    "DatasetExample",
]
