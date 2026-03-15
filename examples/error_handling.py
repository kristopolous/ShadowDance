"""
Error handling example for ShadowDance.

This example demonstrates how exceptions are traced and logged
by ShadowDance, making debugging robot issues easier.

Usage:
    export LANGCHAIN_API_KEY=your_key
    export LANGCHAIN_TRACING_V2=true
    export LANGCHAIN_PROJECT=unitree-demo
    python examples/error_handling.py
"""

import os

from shadowdance import ShadowDance


class MockRobotClient:
    """Mock robot client that can simulate errors."""

    def __init__(self, fail_rate: float = 0.0):
        self._fail_rate = fail_rate
        self._call_count = 0

    def Init(self) -> None:
        """Initialize the client."""
        print("Client initialized")

    def Move(self, vx: float, vy: float, vyaw: float) -> int:
        """
        Move the robot. May fail if velocity is too high.

        Raises:
            ValueError: If velocity exceeds safe limits.
        """
        self._call_count += 1

        # Simulate error conditions
        if abs(vx) > 1.0:
            raise ValueError(f"Velocity too high: vx={vx} (max: 1.0)")
        if abs(vy) > 1.0:
            raise ValueError(f"Velocity too high: vy={vy} (max: 1.0)")
        if abs(vyaw) > 1.0:
            raise ValueError(f"Velocity too high: vyaw={vyaw} (max: 1.0)")

        print(f"Moved successfully: ({vx}, {vy}, {vyaw})")
        return 0

    def Connect(self) -> int:
        """
        Connect to the robot. May fail randomly.

        Raises:
            ConnectionError: If connection fails.
        """
        self._call_count += 1
        raise ConnectionError("Failed to connect to robot at 192.168.1.100")


def safe_robot_operation(client: ShadowDance, operation: str, **kwargs) -> tuple[bool, str]:
    """
    Execute a robot operation with error handling.

    Args:
        client: The ShadowDance-wrapped client.
        operation: Name of the operation to perform.
        **kwargs: Arguments to pass to the operation.

    Returns:
        Tuple of (success, message).
    """
    try:
        method = getattr(client, operation)
        result = method(**kwargs)
        return True, f"Operation '{operation}' succeeded with result: {result}"
    except ValueError as e:
        return False, f"Invalid argument: {e}"
    except ConnectionError as e:
        return False, f"Connection failed: {e}"
    except Exception as e:
        return False, f"Unexpected error: {type(e).__name__}: {e}"


def main():
    """Demonstrate ShadowDance error handling."""
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

    print("=== ShadowDance Error Handling Demo ===\n")

    # Create and wrap client
    client = MockRobotClient()
    client = ShadowDance(client)
    client.Init()

    # Demo 1: Successful operation
    print("--- Test 1: Valid Move Command ---")
    success, msg = safe_robot_operation(client, "Move", vx=0.3, vy=0, vyaw=0)
    print(f"Success: {success}")
    print(f"Message: {msg}\n")

    # Demo 2: Invalid argument (will be traced with error)
    print("--- Test 2: Invalid Velocity (Error Expected) ---")
    success, msg = safe_robot_operation(client, "Move", vx=1.5, vy=0, vyaw=0)
    print(f"Success: {success}")
    print(f"Message: {msg}\n")

    # Demo 3: Connection error (will be traced with error)
    print("--- Test 3: Connection Error (Error Expected) ---")
    success, msg = safe_robot_operation(client, "Connect")
    print(f"Success: {success}")
    print(f"Message: {msg}\n")

    # Demo 4: Multiple operations with mixed results
    print("--- Test 4: Batch Operations ---")
    operations = [
        {"op": "Move", "args": {"vx": 0.2, "vy": 0, "vyaw": 0}},
        {"op": "Move", "args": {"vx": 0, "vy": 0.3, "vyaw": 0}},
        {"op": "Move", "args": {"vx": 2.0, "vy": 0, "vyaw": 0}},  # Will fail
        {"op": "Move", "args": {"vx": 0, "vy": 0, "vyaw": 0.1}},
    ]

    results = []
    for op in operations:
        success, msg = safe_robot_operation(client, op["op"], **op["args"])
        results.append((success, msg))
        status = "✓" if success else "✗"
        print(f"  {status} {op['op']}: {msg}")

    print(f"\nBatch complete: {sum(1 for s, _ in results if s)}/{len(results)} succeeded")

    print("\n=== Demo Complete ===")
    print(
        "\nWith LANGCHAIN_TRACING_V2=true, all errors would be visible in LangSmith "
        "with full stack traces and input/output data for debugging."
    )


if __name__ == "__main__":
    main()
