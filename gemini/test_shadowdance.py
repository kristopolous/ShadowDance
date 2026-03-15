"""
Unit tests for the improved ShadowDance wrapper in gemini/shadowdance.py.
Uses unittest for compatibility.
Ensures it imports the local shadowdance.py.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# ENSURE we import the shadowdance.py from THIS directory (gemini/)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import shadowdance
# Reload if it was already imported from elsewhere
import importlib
importlib.reload(shadowdance)
from shadowdance import ShadowDance

class MockRobotClient:
    """A mock robot client to test ShadowDance."""
    
    def Move(self, vx: float, vy: float, vyaw: float) -> int:
        """Original Move method."""
        return 0
        
    def StandUp(self) -> int:
        """Original StandUp method."""
        return 1
        
    def Damp(self) -> int:
        """Original Damp method."""
        return 2

    def ErrorMethod(self):
        """Method that raises an error."""
        raise ValueError("Simulated error")

class TestShadowDance(unittest.TestCase):
    def test_delegation(self):
        client = MockRobotClient()
        proxy = ShadowDance(client)
        self.assertEqual(proxy.Move.__name__, "Move")
        self.assertEqual(proxy.Move.__doc__, "Original Move method.")
        
    def test_trace_call(self):
        client = MockRobotClient()
        proxy = ShadowDance(client)
        
        with patch("shadowdance.trace") as mock_trace:
            # Set up mock context
            mock_rt = MagicMock()
            mock_trace.return_value.__enter__.return_value = mock_rt
            
            # Call method
            result = proxy.Move(0.3, 0.1, 0.0)
            
            # Verify trace was started with correct name and inputs
            # inspect.signature should map the args to vx, vy, vyaw
            mock_trace.assert_called_once()
            args, kwargs = mock_trace.call_args
            self.assertEqual(kwargs["name"], "Move")
            self.assertEqual(kwargs["inputs"], {"vx": 0.3, "vy": 0.1, "vyaw": 0.0})
            
            # Verify output was added
            # Note: My implementation uses add_outputs or set_output
            if mock_rt.add_outputs.called:
                mock_rt.add_outputs.assert_called_with({"result": 0})
            else:
                mock_rt.set_output.assert_called_with({"result": 0})
            self.assertEqual(result, 0)

    def test_error_handling(self):
        client = MockRobotClient()
        proxy = ShadowDance(client)
        
        with patch("shadowdance.trace") as mock_trace:
            mock_rt = MagicMock()
            mock_trace.return_value.__enter__.return_value = mock_rt
            
            with self.assertRaisesRegex(ValueError, "Simulated error"):
                proxy.ErrorMethod()
                
            # Trace should have been called with inputs={} because ErrorMethod has no args
            mock_trace.assert_called_with(name="ErrorMethod", run_type="tool", inputs={})

    def test_attribute_delegation(self):
        client = MockRobotClient()
        client.battery = 85
        proxy = ShadowDance(client)
        
        # Test getattr
        self.assertEqual(proxy.battery, 85)
        
        # Test setattr
        proxy.battery = 90
        self.assertEqual(client.battery, 90)
        
        # Test dir
        self.assertIn("Move", dir(proxy))
        self.assertIn("battery", dir(proxy))

if __name__ == "__main__":
    unittest.main()
