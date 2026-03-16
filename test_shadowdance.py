"""
Unit tests for ShadowDance wrapper with adapter pattern.

Run with: python test_shadowdance.py
"""

import os
from unittest.mock import Mock, MagicMock, patch

from shadowdance import (
    ShadowDance,
    ObservabilityAdapter,
    LangSmithAdapter,
    LangfuseAdapter,
    TraceEvent,
    DatasetExample,
    _get_adapter,
    task,
    task_context,
)


class MockClient:
    """Mock Unitree SDK client for testing."""

    def __init__(self):
        self.value = "initial"

    def Move(self, vx: float, vy: float, vyaw: float) -> int:
        """Move method."""
        return 0

    def StandUp(self) -> int:
        """Stand up method."""
        return 1

    def Damp(self) -> int:
        """Damp method."""
        return 2

    def get_state(self) -> dict:
        """Get state method."""
        return {"battery": 100}

    def RaiseError(self) -> None:
        """Method that raises an error."""
        raise ValueError("Test error")


class MockAdapter(ObservabilityAdapter):
    """Mock adapter for testing."""

    def __init__(self):
        self.events = []
        self.examples = []
        self.current_event = None

    def capture_event(self, event: TraceEvent) -> str:
        event_id = str(len(self.events))
        self.events.append((event_id, event))
        self.current_event = event
        return event_id

    def complete_event(self, event_id: str, event: TraceEvent) -> None:
        # Update the stored event with completion data
        for i, (eid, e) in enumerate(self.events):
            if eid == event_id:
                self.events[i] = (event_id, event)
                break

    def update_event(self, event_id: str, metadata: dict) -> None:
        for i, (eid, e) in enumerate(self.events):
            if eid == event_id:
                e.metadata.update(metadata)
                break

    def log_example(self, example: DatasetExample) -> None:
        self.examples.append(example)

    def get_current_event(self) -> TraceEvent:
        return self.current_event

    def flush(self, timeout_ms: float = None) -> None:
        pass


def test_adapter_selection_langsmith():
    """Test that LangSmith adapter is selected by default."""
    os.environ["PLATFORM"] = "langsmith"
    # Reset cache
    import shadowdance
    shadowdance._adapter_cache = None
    adapter = _get_adapter()
    assert isinstance(adapter, LangSmithAdapter)
    print("✓ test_adapter_selection_langsmith")


def test_adapter_selection_langfuse():
    """Test that Langfuse adapter is selected when PLATFORM=langfuse."""
    os.environ["PLATFORM"] = "langfuse"
    # Reset cache
    import shadowdance
    shadowdance._adapter_cache = None
    adapter = _get_adapter()
    assert isinstance(adapter, LangfuseAdapter)
    print("✓ test_adapter_selection_langfuse")


def test_adapter_selection_default():
    """Test that LangSmith is default when PLATFORM not set."""
    if "PLATFORM" in os.environ:
        del os.environ["PLATFORM"]
    # Reset cache
    import shadowdance
    shadowdance._adapter_cache = None
    adapter = _get_adapter()
    assert isinstance(adapter, LangSmithAdapter)
    print("✓ test_adapter_selection_default")


def test_wrap_simple_client():
    """Test wrapping a simple client."""
    client = MockClient()
    wrapped = ShadowDance(client)
    assert wrapped._client is client
    print("✓ test_wrap_simple_client")


def test_intercept_method_call():
    """Test that method calls are intercepted and traced."""
    adapter = MockAdapter()
    client = MockClient()
    wrapped = ShadowDance(client)
    wrapped._adapter = adapter

    result = wrapped.Move(0.3, 0.0, 0.0)

    # Verify event was created with method name
    assert len(adapter.events) == 1
    event_id, event = adapter.events[0]
    assert event.name == "Move"
    assert event.run_type == "tool"
    # Verify result is returned
    assert result == 0
    print("✓ test_intercept_method_call")


def test_preserve_method_signature():
    """Test that method signatures are preserved."""
    client = MockClient()
    wrapped = ShadowDance(client)

    # Check that wrapped method has same name
    assert wrapped.Move.__name__ == "Move"
    print("✓ test_preserve_method_signature")


def test_no_args_method():
    """Test calling method with no arguments."""
    adapter = MockAdapter()
    client = MockClient()
    wrapped = ShadowDance(client)
    wrapped._adapter = adapter

    result = wrapped.Damp()
    assert result == 2
    assert adapter.events[0][1].name == "Damp"
    print("✓ test_no_args_method")


def test_get_attribute_not_method():
    """Test accessing non-callable attributes."""
    client = MockClient()
    wrapped = ShadowDance(client)

    # Should return the attribute directly without wrapping
    assert wrapped.value == "initial"
    print("✓ test_get_attribute_not_method")


def test_method_with_kwargs():
    """Test calling method with keyword arguments."""
    adapter = MockAdapter()
    client = MockClient()
    wrapped = ShadowDance(client)
    wrapped._adapter = adapter

    result = wrapped.Move(vx=0.5, vy=0.2, vyaw=0.1)
    assert result == 0
    # Verify kwargs were logged
    assert adapter.events[0][1].inputs["kwargs"]["vx"] == 0.5
    print("✓ test_method_with_kwargs")


def test_repr():
    """Test string representation."""
    client = MockClient()
    wrapped = ShadowDance(client)
    assert "ShadowDance" in repr(wrapped)
    assert "MockClient" in repr(wrapped)
    print("✓ test_repr")


def test_exception_handling():
    """Test that exceptions are properly propagated."""
    adapter = MockAdapter()
    client = MockClient()
    wrapped = ShadowDance(client)
    wrapped._adapter = adapter

    try:
        wrapped.RaiseError()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == "Test error"
        # Verify error was captured
        assert adapter.events[0][1].error is not None
    print("✓ test_exception_handling")


def test_captures_timestamps():
    """Test that timestamps are captured by ShadowDance."""
    adapter = MockAdapter()
    client = MockClient()
    wrapped = ShadowDance(client)
    wrapped._adapter = adapter

    wrapped.Move(0.3, 0.0, 0.0)

    event = adapter.events[0][1]
    assert event.start_time is not None
    assert event.end_time is not None
    assert event.duration_ms is not None
    assert event.duration_ms >= 0
    print("✓ test_captures_timestamps")


def test_run_type_preserved():
    """Test that run_type is preserved in events."""
    adapter = MockAdapter()
    client = MockClient()
    wrapped = ShadowDance(client, run_type="llm")
    wrapped._adapter = adapter

    wrapped.StandUp()

    assert adapter.events[0][1].run_type == "llm"
    print("✓ test_run_type_preserved")


def test_task_decorator_with_mock_adapter():
    """Test task decorator with mock adapter."""
    adapter = MockAdapter()
    client = MockClient()
    wrapped = ShadowDance(client)
    wrapped._adapter = adapter

    @task("test_task", run_type="chain")
    def my_task():
        wrapped.StandUp()
        return "done"

    # Patch _get_adapter to return our mock
    with patch("shadowdance._get_adapter", return_value=adapter):
        result = my_task()

    assert result == "done"
    # Should have events for task and StandUp
    assert len(adapter.events) >= 1
    print("✓ test_task_decorator_with_mock_adapter")


def test_task_context_with_mock_adapter():
    """Test task context manager with mock adapter."""
    adapter = MockAdapter()
    client = MockClient()
    wrapped = ShadowDance(client)
    wrapped._adapter = adapter

    with patch("shadowdance._get_adapter", return_value=adapter):
        with task_context("test_context"):
            wrapped.Damp()

    # Should have events
    assert len(adapter.events) >= 1
    print("✓ test_task_context_with_mock_adapter")


def test_trace_event_complete():
    """Test TraceEvent completion."""
    event = TraceEvent(name="test", run_type="tool", inputs={"x": 1})
    assert event.end_time is None
    assert event.duration_ms is None

    event.complete(outputs={"result": 42})

    assert event.end_time is not None
    assert event.duration_ms is not None
    assert event.outputs == {"result": 42}
    print("✓ test_trace_event_complete")


def test_trace_event_to_dict():
    """Test TraceEvent to_dict conversion."""
    event = TraceEvent(name="test", run_type="llm", inputs={"prompt": "hello"})
    event.complete(outputs={"response": "hi"})

    data = event.to_dict()
    assert data["name"] == "test"
    assert data["run_type"] == "llm"
    assert data["inputs"] == {"prompt": "hello"}
    assert data["outputs"] == {"response": "hi"}
    assert data["duration_ms"] is not None
    print("✓ test_trace_event_to_dict")


def run_all_tests():
    """Run all tests."""
    print("Running ShadowDance adapter pattern tests...\n")

    test_adapter_selection_langsmith()
    test_adapter_selection_langfuse()
    test_adapter_selection_default()
    test_wrap_simple_client()
    test_intercept_method_call()
    test_preserve_method_signature()
    test_no_args_method()
    test_get_attribute_not_method()
    test_method_with_kwargs()
    test_repr()
    test_exception_handling()
    test_captures_timestamps()
    test_run_type_preserved()
    test_task_decorator_with_mock_adapter()
    test_task_context_with_mock_adapter()
    test_trace_event_complete()
    test_trace_event_to_dict()

    print("\n✓ All tests passed!")


if __name__ == "__main__":
    run_all_tests()
