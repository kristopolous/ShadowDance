"""
Unitree example test harness.

Runs Unitree SDK examples with and without ShadowDance to verify:
1. Identical functional results
2. Performance within acceptable jitter (<1ms overhead)
"""

import time
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass
from typing import Callable, Any, Dict, List


@dataclass
class TestResult:
    """Result from a single test run."""
    name: str
    success: bool
    duration_ms: float
    return_value: Any
    error: Exception = None


def run_with_timing(
    func: Callable,
    *args,
    mock_client: bool = True,
    shadowdance_wrapper: bool = False,
    **kwargs
) -> TestResult:
    """
    Run a function with optional ShadowDance wrapping and timing.

    Args:
        func: The function to run
        *args: Arguments to pass to func
        mock_client: If True, use mock Unitree client
        shadowdance_wrapper: If True, wrap with ShadowDance
        **kwargs: Keyword arguments to pass to func

    Returns:
        TestResult with timing and outcome
    """
    from shadowdance import ShadowDance

    # Create or mock the client
    if mock_client:
        client = create_mock_sport_client()
    else:
        from unitree_sdk2py.go2.sport.sport_client import SportClient
        client = SportClient()
        client.SetTimeout(10.0)
        client.Init()

    # Optionally wrap with ShadowDance
    if shadowdance_wrapper:
        client = ShadowDance(client, run_type="tool")

    # Time the execution
    start = time.perf_counter()
    try:
        result = func(client, *args, **kwargs)
        duration_ms = (time.perf_counter() - start) * 1000
        return TestResult(
            name=func.__name__,
            success=True,
            duration_ms=duration_ms,
            return_value=result
        )
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000
        return TestResult(
            name=func.__name__,
            success=False,
            duration_ms=duration_ms,
            return_value=None,
            error=e
        )


def create_mock_sport_client() -> MagicMock:
    """Create a mock SportClient for testing without hardware."""
    client = MagicMock()

    # Mock all SportClient methods with realistic return values
    client.Damp.return_value = 0
    client.StandUp.return_value = 0
    client.StandDown.return_value = 0
    client.Move.return_value = 0
    client.StopMove.return_value = 0
    client.HandStand.return_value = 0
    client.BalanceStand.return_value = 0
    client.RecoveryStand.return_value = 0
    client.LeftFlip.return_value = 0
    client.BackFlip.return_value = 0
    client.FreeWalk.return_value = 0
    client.FreeBound.return_value = 0
    client.FreeAvoid.return_value = 0
    client.WalkUpright.return_value = 0
    client.CrossStep.return_value = 0
    client.FreeJump.return_value = 0

    return client


def test_sport_client_methods():
    """
    Test all SportClient methods with and without ShadowDance.

    Verifies:
    1. Same return values
    2. Overhead < 1ms per call (acceptable jitter)
    """
    from shadowdance import ShadowDance

    print("Testing SportClient methods with/without ShadowDance...\n")

    # Define test methods and their arguments
    test_methods = [
        ("Damp", [], {}),
        ("StandUp", [], {}),
        ("StandDown", [], {}),
        ("Move", [0.3, 0, 0], {}),
        ("Move", [0, 0.3, 0], {}),
        ("Move", [0, 0, 0.5], {}),
        ("StopMove", [], {}),
        ("RecoveryStand", [], {}),
    ]

    results_without = []
    results_with = []

    # Run without ShadowDance
    print("Running WITHOUT ShadowDance...")
    client_plain = create_mock_sport_client()
    for method_name, args, kwargs in test_methods:
        method = getattr(client_plain, method_name)
        start = time.perf_counter()
        result = method(*args, **kwargs)
        duration = (time.perf_counter() - start) * 1000
        results_without.append({
            "method": method_name,
            "duration_ms": duration,
            "result": result
        })

    # Run with ShadowDance
    print("Running WITH ShadowDance...")
    client_wrapped = ShadowDance(create_mock_sport_client(), run_type="tool")
    for method_name, args, kwargs in test_methods:
        method = getattr(client_wrapped, method_name)
        start = time.perf_counter()
        result = method(*args, **kwargs)
        duration = (time.perf_counter() - start) * 1000
        results_with.append({
            "method": method_name,
            "duration_ms": duration,
            "result": result
        })

    # Compare results
    print("\n" + "="*70)
    print("RESULTS COMPARISON")
    print("="*70)
    print(f"{'Method':<20} {'Plain (ms)':<15} {'ShadowDance (ms)':<18} {'Overhead':<12} {'Match'}")
    print("-"*70)

    all_passed = True
    max_overhead = 0
    total_plain = 0
    total_with = 0

    for r_plain, r_with in zip(results_without, results_with):
        method = r_plain["method"]
        plain_time = r_plain["duration_ms"]
        sd_time = r_with["duration_ms"]
        overhead = sd_time - plain_time
        result_match = r_plain["result"] == r_with["result"]

        total_plain += plain_time
        total_with += sd_time
        max_overhead = max(max_overhead, overhead)

        status = "✓" if result_match and overhead < 1.0 else "✗"
        if not result_match or overhead >= 1.0:
            all_passed = False

        print(f"{method:<20} {plain_time:<15.3f} {sd_time:<18.3f} {overhead:<12.3f} {status}")

    print("-"*70)
    print(f"{'TOTAL':<20} {total_plain:<15.3f} {total_with:<18.3f} {total_with-total_plain:<12.3f}")
    print(f"\nMax overhead: {max_overhead:.3f}ms")
    print(f"Acceptable jitter threshold: <1.0ms per call")

    if all_passed:
        print("\n✓ ALL TESTS PASSED - ShadowDance adds negligible overhead")
    else:
        print("\n✗ SOME TESTS FAILED - See above for details")

    return all_passed


def test_return_values_match():
    """Verify ShadowDance returns identical values to plain client."""
    from shadowdance import ShadowDance

    print("\nTesting return value matching...\n")

    client_plain = create_mock_sport_client()
    client_wrapped = ShadowDance(create_mock_sport_client(), run_type="tool")

    test_cases = [
        ("Damp", [], {}),
        ("StandUp", [], {}),
        ("Move", [0.3, 0, 0], {}),
        ("Move", [0, 0.3, 0], {}),
        ("StopMove", [], {}),
    ]

    all_match = True
    for method_name, args, kwargs in test_cases:
        plain_result = getattr(client_plain, method_name)(*args, **kwargs)
        wrapped_result = getattr(client_wrapped, method_name)(*args, **kwargs)

        match = plain_result == wrapped_result
        status = "✓" if match else "✗"
        print(f"{method_name}: plain={plain_result}, wrapped={wrapped_result} {status}")

        if not match:
            all_match = False

    return all_match


def test_exception_propagation():
    """Verify exceptions are properly propagated through ShadowDance."""
    from shadowdance import ShadowDance

    print("\nTesting exception propagation...\n")

    # Create mock that raises exception
    mock_client = create_mock_sport_client()
    mock_client.Damp.side_effect = ValueError("Test error")

    wrapped = ShadowDance(mock_client, run_type="tool")

    # Test plain client raises
    plain_raised = False
    try:
        mock_client.Damp()
    except ValueError:
        plain_raised = True

    # Test wrapped client raises
    wrapped_raised = False
    try:
        wrapped.Damp()
    except ValueError:
        wrapped_raised = True

    print(f"Plain client raised: {plain_raised} ✓")
    print(f"Wrapped client raised: {wrapped_raised} ✓")

    return plain_raised and wrapped_raised


def run_all_tests():
    """Run all verification tests."""
    print("="*70)
    print("SHADOWDANCE VERIFICATION TEST SUITE")
    print("="*70)
    print()

    results = {
        "Return values match": test_return_values_match(),
        "Exception propagation": test_exception_propagation(),
        "Performance overhead": test_sport_client_methods(),
    }

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())
    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
