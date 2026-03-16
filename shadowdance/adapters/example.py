"""
Example adapter template.

Copy this file and implement the methods to create a custom observability adapter.
"""

import logging
from typing import Any, Dict, Optional

from . import ObservabilityAdapter, TraceEvent, DatasetExample

logger = logging.getLogger(__name__)


class ExampleAdapter(ObservabilityAdapter):
    """
    Example observability adapter.

    Copy this file and implement the methods to create a custom adapter
    for your own observability backend.

    Key design principles:
    - Fire-and-forget: Never block user code
    - Drop gracefully: Observability failures shouldn't affect main code
    - Timestamps are captured by ShadowDance, not adapters
    """

    def __init__(self):
        """Initialize your adapter with any required configuration."""
        # Initialize your observability client here
        # self._client = YourObservabilityClient()
        self._events: Dict[str, Any] = {}

    def capture_event(self, event: TraceEvent) -> Optional[str]:
        """
        Capture a trace event for sending to the observability backend.

        Called when a traced method starts. Should queue or send
        asynchronously.

        Returns:
            An event ID for later updates, or None if dropped
        """
        try:
            # Example: Create trace in your backend
            # trace = self._client.create_trace(
            #     name=event.name,
            #     run_type=event.run_type,
            #     inputs=event.inputs,
            #     metadata=event.metadata,
            #     timestamp=event.start_time,  # Use ShadowDance's timestamp
            # )
            # event_id = str(id(trace))
            # self._events[event_id] = trace
            # return event_id

            raise NotImplementedError("Implement capture_event for your backend")

        except Exception as e:
            logger.debug(f"ExampleAdapter: Failed to capture event: {e}")
            return None

    def complete_event(self, event_id: str, event: TraceEvent) -> None:
        """
        Mark a previously captured event as complete.

        Called when a traced method finishes. Event already contains
        outputs/error and timing data.
        """
        try:
            # Example: Complete trace in your backend
            # trace = self._events.pop(event_id, None)
            # if trace:
            #     trace.complete(
            #         outputs=event.outputs,
            #         error=event.error,
            #         duration_ms=event.duration_ms,
            #     )
            pass

        except Exception as e:
            logger.debug(f"ExampleAdapter: Failed to complete event: {e}")

    def update_event(self, event_id: str, metadata: Dict[str, Any]) -> None:
        """
        Update metadata on an in-flight event.

        Used for adding token usage, cost, duration, etc.
        """
        try:
            # Example: Update metadata
            # trace = self._events.get(event_id)
            # if trace:
            #     trace.metadata.update(metadata)
            pass

        except Exception as e:
            logger.debug(f"ExampleAdapter: Failed to update event: {e}")

    def log_example(self, example: DatasetExample) -> None:
        """
        Log an example to a dataset for evaluation.
        """
        try:
            # Example: Create dataset example
            # dataset = self._client.get_or_create_dataset(example.dataset_name)
            # dataset.add_example(
            #     input=example.inputs,
            #     output=example.outputs,
            #     metadata=example.metadata,
            # )
            pass

        except Exception as e:
            logger.debug(f"ExampleAdapter: Failed to log example: {e}")

    def get_current_event(self) -> Optional[TraceEvent]:
        """
        Get the current active event for nesting.

        Return None if your backend doesn't support thread-local context.
        ShadowDance will handle nesting via parent_event in TraceEvent.
        """
        return None

    def flush(self, timeout_ms: Optional[float] = None) -> None:
        """
        Flush any queued events to the backend.

        Called on shutdown for graceful cleanup.
        """
        try:
            # Example: Flush queued events
            # self._client.flush(timeout=timeout_ms)
            pass

        except Exception as e:
            logger.debug(f"ExampleAdapter: Failed to flush: {e}")


__all__ = ["ExampleAdapter"]
