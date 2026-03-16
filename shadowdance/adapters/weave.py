"""Weights & Biases Weave observability adapter."""

import logging
import threading
from typing import Any, Dict, Optional

from . import ObservabilityAdapter, TraceEvent, DatasetExample, RunType

logger = logging.getLogger(__name__)


class WeaveAdapter(ObservabilityAdapter):
    """
    Weights & Biases Weave observability backend.

    Fire-and-forget design:
    - Events are sent in background threads
    - Traces may be dropped under load (observability > reliability)
    - Never blocks user code
    """

    def __init__(self, project_name: Optional[str] = None):
        import weave

        # Initialize Weave client
        self._project_name = project_name or "shadowdance"
        self._client = weave.init(self._project_name)
        self._calls: Dict[str, Any] = {}  # event_id -> call object
        self._lock = threading.Lock()

    def capture_event(self, event: TraceEvent) -> Optional[str]:
        """Capture event and send to Weave in background thread."""
        try:
            # Map run_type to Weave op type
            op_type_map = {
                "tool": "Tool",
                "chain": "Chain",
                "llm": "LLM",
                "retriever": "Retriever",
                "embedding": "Embedding",
                "prompt": "Prompt",
            }

            # Get parent call if nested
            parent_call = None
            if event.parent_event:
                with self._lock:
                    parent_call = self._calls.get(id(event.parent_event))

            # Create call in background thread
            call_id = None

            def _create_call():
                nonlocal call_id
                try:
                    call = self._client.create_call(
                        op=op_type_map.get(event.run_type, "Tool"),
                        inputs=event.inputs or {},
                        parent=parent_call,
                        display_name=event.name,
                        attributes=event.metadata,
                    )
                    with self._lock:
                        self._calls[str(id(call))] = call
                        call_id = str(id(call))
                except Exception as e:
                    logger.debug(f"Weave: Failed to create call: {e}")

            # Start in background thread
            thread = threading.Thread(target=_create_call, daemon=True)
            thread.start()
            thread.join(timeout=0.1)  # Brief wait to get call_id

            # Return a temporary ID based on event if call_id not ready
            if call_id is None:
                call_id = f"temp_{id(event)}"
                with self._lock:
                    self._calls[call_id] = None  # Placeholder

            return call_id

        except Exception as e:
            logger.debug(f"Weave: Failed to capture event: {e}")
            return None

    def complete_event(self, event_id: str, event: TraceEvent) -> None:
        """Complete event and send to Weave in background thread."""
        try:
            with self._lock:
                call = self._calls.pop(event_id, None)

            if call is None:
                return

            # Build output data
            output_data = event.outputs.get("result") if event.outputs else None
            if event.error:
                output_data = {"error": str(event.error)}

            # Add metadata
            metadata = {
                "duration_ms": event.duration_ms,
                "start_time": event.start_time,
                "end_time": event.end_time,
            }

            # Complete call in background
            def _finish_call():
                try:
                    # Weave calls are finished by returning from the decorated function
                    # For manual calls, we need to use the internal API
                    # The call object has a _finish method internally
                    if hasattr(call, "_finish"):
                        call._finish(output=output_data, exception=event.error)
                    elif hasattr(call, "finish"):
                        call.finish(output=output_data)
                except Exception as e:
                    logger.debug(f"Weave: Failed to finish call: {e}")

            threading.Thread(target=_finish_call, daemon=True).start()

        except Exception as e:
            logger.debug(f"Weave: Failed to complete event: {e}")

    def update_event(self, event_id: str, metadata: Dict[str, Any]) -> None:
        """Update event metadata."""
        try:
            with self._lock:
                call = self._calls.get(event_id)

            if call and hasattr(call, "attributes"):
                # Weave attributes are typically set at creation time
                # We can't modify them after, but we could track separately
                pass
        except Exception:
            pass

    def log_example(self, example: DatasetExample) -> None:
        """Log example to dataset in background thread."""
        try:
            def _create_example():
                try:
                    import weave

                    # Weave doesn't have a direct "dataset" concept like LangSmith
                    # Instead, we log as a trace with special metadata
                    call = self._client.create_call(
                        op="DatasetExample",
                        inputs=example.inputs,
                        parent=None,
                        display_name=f"example:{example.dataset_name}",
                        attributes={
                            **example.metadata,
                            "dataset": example.dataset_name,
                            "type": "example",
                        },
                    )

                    # Finish with output
                    if hasattr(call, "_finish"):
                        call._finish(output=example.outputs)
                    elif hasattr(call, "finish"):
                        call.finish(output=example.outputs)

                except Exception as e:
                    logger.debug(f"Weave: Failed to create example: {e}")

            threading.Thread(target=_create_example, daemon=True).start()

        except Exception as e:
            logger.debug(f"Weave: Failed to log example: {e}")

    def get_current_event(self) -> Optional[TraceEvent]:
        """Get current event from context (not directly supported)."""
        # Weave has a call stack but it's not directly accessible
        # Nesting is handled via parent_event in TraceEvent
        return None

    def flush(self, timeout_ms: Optional[float] = None) -> None:
        """Flush queued events to Weave."""
        try:
            # Weave has a finish method to flush background tasks
            if hasattr(self._client, "finish"):
                if timeout_ms:
                    # Weave doesn't support timeout, just call it
                    self._client.finish(use_progress_bar=False)
                else:
                    self._client.finish(use_progress_bar=False)
        except Exception:
            pass


__all__ = ["WeaveAdapter"]
