"""Langfuse observability adapter."""

import logging
import threading
from typing import Any, Dict, Optional

from . import ObservabilityAdapter, TraceEvent, DatasetExample, RunType

logger = logging.getLogger(__name__)


class LangfuseAdapter(ObservabilityAdapter):
    """
    Langfuse observability backend.

    Fire-and-forget design:
    - Langfuse SDK has built-in async flushing
    - Events are sent in background
    - Never blocks user code
    """

    def __init__(self):
        from langfuse import Langfuse

        self._client = Langfuse()
        self._traces: Dict[str, Any] = {}  # event_id -> (trace, span)
        self._lock = threading.Lock()

    def capture_event(self, event: TraceEvent) -> Optional[str]:
        """Capture event and send to Langfuse in background thread."""
        try:
            # Map run_type to Langfuse type
            type_map = {
                "tool": "TOOL",
                "chain": "CHAIN",
                "llm": "LLM",
                "retriever": "RETRIEVER",
                "embedding": "EMBEDDING",
                "prompt": "PROMPT",
            }

            # Get parent span if nested
            parent_span = None
            if event.parent_event:
                with self._lock:
                    parent_data = self._traces.get(id(event.parent_event))
                    if parent_data:
                        parent_span = parent_data[1]

            # Create trace and span
            if parent_span is None:
                trace = self._client.trace(
                    name=event.name,
                    metadata=event.metadata,
                    input=event.inputs,
                )
                span = trace.span(
                    name=event.name,
                    type=type_map.get(event.run_type, "TOOL"),
                    metadata=event.metadata,
                    input=event.inputs,
                )
            else:
                span = parent_span.span(
                    name=event.name,
                    type=type_map.get(event.run_type, "TOOL"),
                    metadata=event.metadata,
                    input=event.inputs,
                )

            # Store for later completion
            event_id = str(id(span))
            with self._lock:
                self._traces[event_id] = (span, span)

            return event_id

        except Exception as e:
            logger.debug(f"Langfuse: Failed to capture event: {e}")
            return None

    def complete_event(self, event_id: str, event: TraceEvent) -> None:
        """Complete event and send to Langfuse in background thread."""
        try:
            with self._lock:
                span_data = self._traces.pop(event_id, None)

            if span_data is None:
                return

            span = span_data[1]

            # Build end data
            end_data = {}
            if event.outputs:
                end_data["output"] = event.outputs.get("result")
            if event.error:
                end_data["level"] = "ERROR"
                end_data["status_message"] = str(event.error)

            # End span in background
            def _end_span():
                try:
                    span.end(**end_data)
                except Exception as e:
                    logger.debug(f"Langfuse: Failed to end span: {e}")

            threading.Thread(target=_end_span, daemon=True).start()

        except Exception as e:
            logger.debug(f"Langfuse: Failed to complete event: {e}")

    def update_event(self, event_id: str, metadata: Dict[str, Any]) -> None:
        """Update event metadata."""
        try:
            with self._lock:
                span_data = self._traces.get(event_id)

            if span_data:
                span = span_data[1]
                # Langfuse doesn't support metadata update after creation
                # We'd need to track it separately if needed
        except Exception:
            pass

    def log_example(self, example: DatasetExample) -> None:
        """Log example to dataset in background thread."""
        try:
            def _create_example():
                try:
                    dataset = self._client.get_dataset(name=example.dataset_name)
                    if dataset is None:
                        dataset = self._client.create_dataset(
                            name=example.dataset_name,
                            description="Dataset for ShadowDance executions",
                        )

                    dataset.create_example(
                        input=example.inputs,
                        output=example.outputs.get("result"),
                        metadata=example.metadata,
                    )
                except Exception as e:
                    logger.debug(f"Langfuse: Failed to create example: {e}")

            threading.Thread(target=_create_example, daemon=True).start()

        except Exception as e:
            logger.debug(f"Langfuse: Failed to log example: {e}")

    def get_current_event(self) -> Optional[TraceEvent]:
        """Get current event from context (not directly supported)."""
        # Langfuse doesn't have thread-local context like LangSmith
        # Nesting is handled via parent_event in TraceEvent
        return None

    def flush(self, timeout_ms: Optional[float] = None) -> None:
        """Flush queued events to Langfuse."""
        try:
            # Langfuse SDK has built-in flush
            self._client.flush()
        except Exception:
            pass


__all__ = ["LangfuseAdapter"]
