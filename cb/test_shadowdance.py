"""
Unit tests for ShadowDance wrapper.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
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


class TestShadowDance:
    """Test cases for ShadowDance wrapper."""

    def test_wrap_simple_client(self):
        """Test wrapping a simple client."""
        client = MockClient()
        wrapped = ShadowDance(client)
        assert wrapped._client is client

    def test_intercept_method_call(self):
        """Test that method calls are intercepted and traced."""
        client = MockClient()
        wrapped = ShadowDance(client)

        with patch("shadowdance.trace") as mock_trace:
            mock_context = MagicMock()
            mock_trace.return_value.__enter__ = Mock(return_value=mock_context)
            mock_trace.return_value.__exit__ = Mock(return_value=False)

            result = wrapped.Move(0.3, 0.0, 0.0)

            mock_trace.assert_called_once_with(name="Move", run_type="tool")
            assert result == 0

    def test_preserve_method_signature(self):
        """Test that method signatures are preserved."""
        client = MockClient()
        wrapped = ShadowDance(client)

        assert wrapped.Move.__name__ == "Move"
        assert "Move method" in (wrapped.Move.__doc__ or "")

    def test_no_args_method(self):
        """Test calling method with no arguments."""
        client = MockClient()
        wrapped = ShadowDance(client)

        with patch("shadowdance.trace") as mock_trace:
            mock_context = MagicMock()
            mock_trace.return_value.__enter__ = Mock(return_value=mock_context)
            mock_trace.return_value.__exit__ = Mock(return_value=False)

            result = wrapped.Damp()
            assert result == 2

    def test_get_attribute_not_method(self):
        """Test accessing non-callable attributes."""
        client = MockClient()
        wrapped = ShadowDance(client)

        assert wrapped.value == "initial"

    def test_method_with_kwargs(self):
        """Test calling method with keyword arguments."""
        client = MockClient()
        wrapped = ShadowDance(client)

        with patch("shadowdance.trace") as mock_trace:
            mock_context = MagicMock()
            mock_trace.return_value.__enter__ = Mock(return_value=mock_context)
            mock_trace.return_value.__exit__ = Mock(return_value=False)

            result = wrapped.Move(vx=0.5, vy=0.2, vyaw=0.1)
            assert result == 0

    def test_repr(self):
        """Test string representation."""
        client = MockClient()
        wrapped = ShadowDance(client)
        assert "ShadowDance" in repr(wrapped)
        assert "MockClient" in repr(wrapped)


class TestShadowDanceWithLangSmith:
    """Test integration with LangSmith trace context."""

    @patch("shadowdance.trace")
    def test_logs_inputs(self, mock_trace):
        """Test that inputs are logged to LangSmith."""
        client = MockClient()
        wrapped = ShadowDance(client)

        mock_context = MagicMock()
        mock_trace.return_value.__enter__ = Mock(return_value=mock_context)
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        wrapped.Move(0.3, 0.0, 0.0)

        mock_context.add_inputs.assert_called()

    @patch("shadowdance.trace")
    def test_logs_outputs(self, mock_trace):
        """Test that outputs are logged to LangSmith."""
        client = MockClient()
        wrapped = ShadowDance(client)

        mock_context = MagicMock()
        mock_trace.return_value.__enter__ = Mock(return_value=mock_context)
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        wrapped.StandUp()

        mock_context.add_outputs.assert_called()

    @patch("shadowdance.trace")
    def test_handles_exception(self, mock_trace):
        """Test that exceptions are handled and logged."""
        client = MockClient()
        client.Move = Mock(side_effect=Exception("Test error"))
        wrapped = ShadowDance(client)

        mock_context = MagicMock()
        mock_trace.return_value.__enter__ = Mock(return_value=mock_context)
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        with pytest.raises(Exception):
            wrapped.Move(0.3, 0.0, 0.0)

        mock_context.add_event.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])