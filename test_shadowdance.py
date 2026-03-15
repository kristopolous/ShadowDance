"""
Unit tests for ShadowDance wrapper.

Run with: python test_shadowdance.py
"""

import os
from unittest.mock import Mock, MagicMock, patch

from shadowdance import ShadowDance


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


def test_wrap_simple_client():
    """Test wrapping a simple client."""
    client = MockClient()
    wrapped = ShadowDance(client)
    assert wrapped._client is client
    print("✓ test_wrap_simple_client")


def test_intercept_method_call():
    """Test that method calls are intercepted and traced."""
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    client = MockClient()
    wrapped = ShadowDance(client)

    with patch("shadowdance.trace") as mock_trace:
        mock_context = MagicMock()
        mock_trace.return_value.__enter__ = Mock(return_value=mock_context)
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        result = wrapped.Move(0.3, 0.0, 0.0)

        # Verify trace was called with method name
        mock_trace.assert_called_once_with(name="Move", run_type="tool")
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
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    client = MockClient()
    wrapped = ShadowDance(client)

    with patch("shadowdance.trace") as mock_trace:
        mock_context = MagicMock()
        mock_trace.return_value.__enter__ = Mock(return_value=mock_context)
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        result = wrapped.Damp()
        assert result == 2
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
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    client = MockClient()
    wrapped = ShadowDance(client)

    with patch("shadowdance.trace") as mock_trace:
        mock_context = MagicMock()
        mock_trace.return_value.__enter__ = Mock(return_value=mock_context)
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        result = wrapped.Move(vx=0.5, vy=0.2, vyaw=0.1)
        assert result == 0
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
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    client = MockClient()
    wrapped = ShadowDance(client)

    try:
        wrapped.RaiseError()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == "Test error"
    print("✓ test_exception_handling")


def test_logs_inputs_outputs():
    """Test that inputs and outputs are logged."""
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    client = MockClient()
    wrapped = ShadowDance(client)

    with patch("shadowdance.trace") as mock_trace:
        mock_context = MagicMock()
        mock_trace.return_value.__enter__ = Mock(return_value=mock_context)
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        wrapped.Move(0.3, 0.0, 0.0)

        # Verify add_inputs and add_outputs were called
        mock_context.add_inputs.assert_called()
        mock_context.add_outputs.assert_called()
    print("✓ test_logs_inputs_outputs")


def run_all_tests():
    """Run all tests."""
    print("Running ShadowDance tests...\n")

    test_wrap_simple_client()
    test_intercept_method_call()
    test_preserve_method_signature()
    test_no_args_method()
    test_get_attribute_not_method()
    test_method_with_kwargs()
    test_repr()
    test_exception_handling()
    test_logs_inputs_outputs()

    print("\n✓ All tests passed!")


if __name__ == "__main__":
    run_all_tests()
