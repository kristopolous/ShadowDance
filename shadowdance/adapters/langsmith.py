"""LangSmith observability adapter."""

import logging
import threading
from typing import Any, Dict, Optional

from . import ObservabilityAdapter, TraceEvent, DatasetExample, RunType

logger = logging.getLogger(__name__)


class LangSmithAdapter(ObservabilityAdapter):
    """
    LangSmith observability backend.

    Fire-and-forget design:
    - Events are sent in background threads
    - Traces may be dropped under load (observability > reliability)
    - Never blocks user code
    """

    def __init__(self):
        from langsmith import Client as LangSmithClient
        from langsmith import run_trees

        self._client = LangSmithClient()
        self._run_trees: Dict[str, run_trees.RunTree] = {}
        self._lock = threading.Lock()
        self._initialized_datasets: set = set()

    def capture_event(self, event: TraceEvent) -> Optional[str]:
        """Capture event and send to LangSmith in background thread."""
        try:
            # Get parent run if nested
            parent_run = None
            if event.parent_event:
                with self._lock:
                    parent_run = self._run_trees.get(id(event.parent_event))

            # Create run tree
            run_tree = run_trees.RunTree(
                name=event.name,
                run_type=event.run_type,
                inputs=event.inputs or {},
                metadata=event.metadata,
                parent_run=parent_run,
                client=self._client,
            )

            # Store for later completion
            event_id = str(id(run_tree))
            with self._lock:
                self._run_trees[event_id] = run_tree

            # Post start event in background (fire-and-forget)
            def _post_start():
                try:
                    run_tree.post()
                except Exception as e:
                    logger.debug(f"LangSmith: Failed to post start event: {e}")

            threading.Thread(target=_post_start, daemon=True).start()
            return event_id

        except Exception as e:
            logger.debug(f"LangSmith: Failed to capture event: {e}")
            return None

    def complete_event(self, event_id: str, event: TraceEvent) -> None:
        """Complete event and send to LangSmith in background thread."""
        try:
            with self._lock:
                run_tree = self._run_trees.pop(event_id, None)

            if run_tree is None:
                return

            # Set outputs and end
            if event.outputs:
                run_tree.end(outputs=event.outputs)
            elif event.error:
                run_tree.end(error=str(event.error))

            # Add timing metadata
            run_tree.add_metadata({"duration_ms": event.duration_ms})

            # Post completion in background
            def _post_end():
                try:
                    run_tree.patch()
                except Exception as e:
                    logger.debug(f"LangSmith: Failed to patch end event: {e}")

            threading.Thread(target=_post_end, daemon=True).start()

        except Exception as e:
            logger.debug(f"LangSmith: Failed to complete event: {e}")

    def update_event(self, event_id: str, metadata: Dict[str, Any]) -> None:
        """Update event metadata."""
        try:
            with self._lock:
                run_tree = self._run_trees.get(event_id)

            if run_tree:
                run_tree.add_metadata(metadata)
        except Exception:
            pass  # Silently ignore metadata updates

    def log_example(
        self, example: DatasetExample
    ) -> None:
        """Log example to dataset in background thread."""
        try:
            # Create dataset if needed (synchronously, but cached)
            if example.dataset_name not in self._initialized_datasets:
                try:
                    self._client.read_dataset(dataset_name=example.dataset_name)
                except Exception:
                    self._client.create_dataset(
                        dataset_name=example.dataset_name,
                        description="Dataset for ShadowDance executions",
                    )
                self._initialized_datasets.add(example.dataset_name)

            # Create example in background
            def _create_example():
                try:
                    self._client.create_example(
                        inputs=example.inputs,
                        outputs=example.outputs,
                        dataset_name=example.dataset_name,
                        metadata=example.metadata,
                    )
                except Exception as e:
                    logger.debug(f"LangSmith: Failed to create example: {e}")

            threading.Thread(target=_create_example, daemon=True).start()

        except Exception as e:
            logger.debug(f"LangSmith: Failed to log example: {e}")

    def get_current_event(self) -> Optional[TraceEvent]:
        """Get current event from context (not supported in this simple impl)."""
        # LangSmith has get_current_run_tree() but we'd need to map it back
        # For now, nesting is handled via parent_event in TraceEvent
        return None

    def flush(self, timeout_ms: Optional[float] = None) -> None:
        """Best effort flush of queued events."""
        # LangSmith's background posts are fire-and-forget
        # We can't really flush, but we can wait a bit
        if timeout_ms:
            threading.Event().wait(timeout_ms / 1000.0)


__all__ = ["LangSmithAdapter"]
