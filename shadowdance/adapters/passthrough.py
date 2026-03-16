"""
Pass-through adapter for testing baseline performance.

This adapter does NOTHING - no tracing, no overhead.
Used to establish baseline performance for comparison.
"""

from typing import Any, Dict, Optional

from shadowdance.adapters import ObservabilityAdapter, TraceEvent, DatasetExample


class PassThroughAdapter(ObservabilityAdapter):
    """
    Pass-through adapter that does nothing.
    
    Used for testing to establish baseline performance.
    This adapter has ZERO overhead - it just returns immediately.
    """

    def capture_event(self, event: TraceEvent) -> Optional[str]:
        """Do nothing, return dummy ID."""
        return "passthrough"

    def complete_event(self, event_id: str, event: TraceEvent) -> None:
        """Do nothing."""
        pass

    def update_event(self, event_id: str, metadata: Dict[str, Any]) -> None:
        """Do nothing."""
        pass

    def log_example(self, example: DatasetExample) -> None:
        """Do nothing."""
        pass

    def get_current_event(self) -> Optional[TraceEvent]:
        """Return None."""
        return None

    def flush(self, timeout_ms: Optional[float] = None) -> None:
        """Do nothing."""
        pass


__all__ = ["PassThroughAdapter"]
