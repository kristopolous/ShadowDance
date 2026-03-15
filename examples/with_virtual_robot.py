"""
Example: Using ShadowDance with a Virtual Robot.

This example demonstrates testing ShadowDance with a simulated robot
that responds to commands just like a real Unitree robot.

Usage:
    source .venv/bin/activate
    python examples/with_virtual_robot.py
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from shadowdance import ShadowDance
from examples.virtual_robot import VirtualRobotServer, VirtualRobotClient

# Load .env file from project root
load_dotenv(Path(__file__).parent.parent / ".env")


def main():
    """Run ShadowDance with virtual robot and see traces in LangSmith."""
    # Enable LangSmith tracing
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "shadowdance"

    print("=== ShadowDance Virtual Robot Demo ===\n")
    print("Starting virtual robot server...")

    # Start virtual robot server
    server = VirtualRobotServer(verbose=True)
    server.start()

    # Create client and wrap with ShadowDance
    client = VirtualRobotClient(server)
    client.Init()

    print("\nWrapping with ShadowDance for LangSmith tracing...\n")
    client = ShadowDance(client)

    # Execute a sequence of robot commands
    # Each will be traced and sent to LangSmith
    print("--- Executing Robot Commands ---")

    client.Damp()
    time.sleep(0.1)

    client.StandUp()
    time.sleep(0.1)

    client.Move(0.3, 0, 0)
    time.sleep(0.1)

    client.Move(0, 0.2, 0.1)
    time.sleep(0.1)

    client.Euler(0.1, 0.05, 0)
    time.sleep(0.1)

    client.Hello()
    time.sleep(0.1)

    client.Stretch()
    time.sleep(0.1)

    client.Dance1()
    time.sleep(0.1)

    client.RecoveryStand()
    time.sleep(0.1)

    # Get final state
    state = client.GetState()
    print(f"\n--- Final Robot State ---")
    print(f"Position: {state['position']}")
    print(f"Velocity: {state['velocity']}")
    print(f"Mode: {state['mode']}")

    # Cleanup
    server.stop()

    print("\n=== Demo Complete ===")
    print("\nView your traces at: https://smith.langchain.com")
    print(f"Project: shadowdance")


if __name__ == "__main__":
    main()
