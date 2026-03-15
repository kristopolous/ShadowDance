"""
ShadowDance - LangSmith observability for LLM and robot SDKs.

Wraps any client object (OpenAI, Unitree, etc.) and intercepts method calls,
logging them as LangSmith runs with command name, arguments, result,
timestamp, and duration.

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
"""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, Literal, Optional, Dict
from contextlib import contextmanager

from langsmith import trace
from langsmith import Client as LangSmithClient
from langsmith.run_helpers import get_current_run_tree

RunType = Literal["tool", "chain", "llm", "retriever", "embedding", "prompt"]


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
        run_type: LangSmith run type (default: "chain")
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
            with trace(name=name, run_type=run_type, **kwargs) as rt:
                rt.metadata.update({
                    "function": func.__name__,
                    "args": args,
                    "kwargs": func_kwargs,
                })
                result = func(*args, **func_kwargs)
                rt.end(outputs={"result": result})
                return result
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
    with trace(name=name, run_type=run_type, **kwargs) as rt:
        rt.metadata.update({"context": "task_context"})
        yield rt
        rt.end()


def get_parent_run():
    """Get the current parent run tree if in a trace context."""
    try:
        return get_current_run_tree()
    except Exception:
        return None


class ShadowDance:
    """
    Proxy wrapper for client objects that adds LangSmith tracing.

    Works with any client: OpenAI, Unitree robot SDKs, or custom clients.
    Every method call becomes a traced LangSmith event with proper run type.
    
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
            run_type: LangSmith run type for better dashboard filtering.
            parent_run: Optional parent run name for nesting.
            log_to_dataset: Optional dataset name for experiment logging.
        """
        self._client = client
        self._run_type = run_type
        self._parent_run_name = parent_run
        self._log_to_dataset = log_to_dataset
        self._ls_client = None
        
        if log_to_dataset:
            try:
                self._ls_client = LangSmithClient()
                try:
                    self._ls_client.read_dataset(dataset_name=log_to_dataset)
                except Exception:
                    self._ls_client.create_dataset(
                        dataset_name=log_to_dataset,
                        description=f"Dataset for {client.__class__.__name__} executions",
                    )
            except Exception as e:
                print(f"[ShadowDance] Warning: Could not initialize dataset '{log_to_dataset}': {e}")
                self._log_to_dataset = None

    def _get_parent_run(self):
        """Get the parent run for nesting."""
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
        """Wrap a method with LangSmith tracing."""

        @wraps(method)
        def traced(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            result: Any = None
            
            parent = self._get_parent_run()

            with trace(name=name, run_type=self._run_type, parent=parent) as rt:
                try:
                    # Log inputs
                    input_data = {}
                    if args:
                        input_data["args"] = args
                    if kwargs:
                        input_data["kwargs"] = kwargs
                    rt.add_inputs(input_data)

                    # Execute method
                    result = method(*args, **kwargs)

                    # Log outputs
                    rt.add_outputs({"result": result})

                    # Extract and log token usage (if subclass provides it)
                    token_usage = self.get_token_count(kwargs, result)
                    if token_usage:
                        rt.add_metadata({"token_usage": token_usage})
                    
                    # Extract and log cost (if subclass provides it)
                    cost = self.get_cost(kwargs, result)
                    if cost:
                        rt.add_metadata({"cost": cost})

                    # Log to dataset if configured
                    if self._log_to_dataset and self._ls_client:
                        try:
                            self._ls_client.create_example(
                                inputs=input_data,
                                outputs={"result": result},
                                dataset_name=self._log_to_dataset,
                                metadata={"method": name, "run_type": self._run_type},
                            )
                        except Exception:
                            pass

                    return result

                except Exception as e:
                    rt.add_event({"name": "error", "data": {"error": str(e)}})
                    
                    if self._log_to_dataset and self._ls_client:
                        try:
                            self._ls_client.create_example(
                                inputs=input_data,
                                outputs={"error": str(e)},
                                dataset_name=self._log_to_dataset,
                                metadata={"method": name, "run_type": self._run_type},
                            )
                        except Exception:
                            pass
                    
                    raise

                finally:
                    rt.add_metadata({"duration_ms": (time.perf_counter() - start_time) * 1000})

        return traced

    def __repr__(self) -> str:
        return f"ShadowDance({self._client!r})"


__all__ = ["ShadowDance", "task", "task_context", "get_parent_run", "RunType"]
