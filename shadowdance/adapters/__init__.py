"""
ShadowDance adapters - Observability backend implementations.

Each adapter implements the ObservabilityAdapter interface for a specific
observability platform.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional
import time

RunType = Literal["tool", "chain", "llm", "retriever", "embedding", "prompt"]


@dataclass
class TraceEvent:
    """
    A timestamped trace event captured by ShadowDance.

    All timestamps are captured by ShadowDance (not adapters) to ensure
    accurate latency measurement regardless of adapter implementation.
    """

    name: str
    run_type: RunType
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timestamps captured by ShadowDance
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None

    # Parent tracking for nested traces
    parent_event: Optional["TraceEvent"] = None

    def complete(
        self,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """Mark the event as complete with outputs or error."""
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        if outputs:
            self.outputs = outputs
        if error:
            self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for adapter consumption."""
        return {
            "name": self.name,
            "run_type": self.run_type,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error": self.error,
            "metadata": self.metadata,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
        }


@dataclass
class DatasetExample:
    """A dataset example for evaluation."""

    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    dataset_name: str = ""


class ObservabilityAdapter(ABC):
    """
    Base interface for observability backends.

    ShadowDance captures all timestamps and manages trace lifecycle.
    Adapters receive fully-formed events and handle transmission.

    Adapters should:
    - Be fire-and-forget (never block user code)
    - Drop traces gracefully under load
    - Never raise exceptions to user code
    """

    @abstractmethod
    def capture_event(self, event: TraceEvent) -> Optional[str]:
        """
        Capture a trace event for sending to the observability backend.

        This is called when a traced method starts. The adapter should
        queue or send the event asynchronously.

        Args:
            event: The TraceEvent with all data and timestamps

        Returns:
            An event ID for later updates, or None if event was dropped
        """
        pass

    @abstractmethod
    def complete_event(self, event_id: str, event: TraceEvent) -> None:
        """
        Mark a previously captured event as complete.

        This is called when a traced method finishes. The event already
        contains outputs/error and timing data.

        Args:
            event_id: The ID from capture_event()
            event: The updated TraceEvent with completion data
        """
        pass

    @abstractmethod
    def update_event(self, event_id: str, metadata: Dict[str, Any]) -> None:
        """
        Update metadata on an in-flight event.

        Used for adding token usage, cost, duration, etc.

        Args:
            event_id: The ID from capture_event()
            metadata: Additional metadata to merge
        """
        pass

    @abstractmethod
    def log_example(self, example: DatasetExample) -> None:
        """
        Log an example to a dataset for evaluation.

        Args:
            example: The dataset example to log
        """
        pass

    @abstractmethod
    def get_current_event(self) -> Optional[TraceEvent]:
        """
        Get the current active event for nesting.

        Returns:
            Current TraceEvent or None if not in a trace
        """
        pass

    @abstractmethod
    def flush(self, timeout_ms: Optional[float] = None) -> None:
        """
        Flush any queued events to the backend.

        Called on shutdown for graceful cleanup.

        Args:
            timeout_ms: Maximum time to wait (None = best effort)
        """
        pass


__all__ = [
    "ObservabilityAdapter",
    "RunType",
    "TraceEvent",
    "DatasetExample",
]
