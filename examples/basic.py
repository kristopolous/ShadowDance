"""
Basic usage example for ShadowDance.

This example demonstrates how to wrap a Unitree SDK client
with ShadowDance for LangSmith tracing.

Usage:
    export LANGCHAIN_API_KEY=your_key
    export LANGCHAIN_TRACING_V2=true
    export LANGCHAIN_PROJECT=unitree-demo
    python examples/basic.py
"""

import os

from shadowdance import ShadowDance


class MockSportClient:
    """Mock SportClient simulating Unitree SDK behavior."""

    def __init__(self):
        self._initialized = False

    def Init(self) -> None:
        """Initialize the client."""
        self._initialized = True
        print("Client initialized")

    def Damp(self) -> int:
        """Set robot to damp mode."""
        print("Damp mode activated")
        return 0

    def StandUp(self) -> int:
        """Make the robot stand up."""
        print("Robot standing up")
        return 0

    def Move(self, vx: float, vy: float, vyaw: float) -> int:
        """
        Move the robot with velocity commands.

        Args:
            vx: Forward/backward velocity (m/s)
            vy: Left/right velocity (m/s)
            vyaw: Rotation velocity (rad/s)
        """
        print(f"Moving: vx={vx}, vy={vy}, vyaw={vyaw}")
        return 0

    def RecoveryStand(self) -> int:
        """Recover to standing position."""
        print("Recovering to stand position")
        return 0


def main():
    """Demonstrate ShadowDance basic usage."""

    # Create the client
    client = MockSportClient()
    client.Init()

    # Wrap with ShadowDance - this is the only line you need to add!
    client = ShadowDance(client)

    # All method calls are now traced
    print("\n--- Executing robot commands ---")
    client.Damp()
    client.StandUp()
    client.Move(0.3, 0, 0)
    client.Move(0, 0.2, 0.1)
    client.RecoveryStand()
    print("--- Commands complete ---\n")

    # The wrapped client preserves the original interface
    print(f"Client type: {type(client)}")
    print(f"Wrapped client: {client._client}")


if __name__ == "__main__":
    main()
