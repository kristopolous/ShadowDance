"""
Example usage of ShadowDance with Unitree SDK clients.
"""

import os
from shadowdance import ShadowDance


def example_basic_sport_client():
    """Basic example with a mock SportClient."""

    class MockSportClient:
        def Move(self, vx: float, vy: float, vyaw: float) -> int:
            print(f"Moving: vx={vx}, vy={vy}, vyaw={vyaw}")
            return 0

        def StandUp(self) -> int:
            print("Standing up...")
            return 0

        def StandDown(self) -> int:
            print("Standing down...")
            return 0

        def Damp(self) -> int:
            print("Damping...")
            return 0

    client = MockSportClient()
    client = ShadowDance(client)

    client.Move(0.3, 0.0, 0.0)
    client.StandUp()
    client.Move(0.0, 0.3, 0.0)
    client.Damp()


def example_with_loco_client():
    """Example with LocoClient."""

    class MockLocoClient:
        def __init__(self):
            self.connected = True

        def Move(self, x: float, y: float, yaw: float) -> int:
            return 0

        def HighStand(self) -> int:
            return 0

        def Stop(self) -> int:
            return 0

    client = ShadowDance(MockLocoClient())
    client.Move(0.5, 0.0, 0.0)
    client.HighStand()
    client.Stop()


def setup_environment():
    """Set up environment variables."""
    os.environ["LANGCHAIN_API_KEY"] = "your_api_key"
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "unitree-robot-demo"


if __name__ == "__main__":
    print("=" * 60)
    print("ShadowDance Example Usage")
    print("=" * 60)

    print("\n--- Example 1: Basic SportClient ---")
    example_basic_sport_client()

    print("\n--- Example 2: LocoClient ---")
    example_with_loco_client()

    print("\n--- Setup ---")
    setup_environment()

    print("\n" + "=" * 60)
    print("Note: Set LANGCHAIN_API_KEY to see traces in LangSmith")
    print("=" * 60)