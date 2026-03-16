"""
Test that verifies ShadowDance behavior with different adapters.

Compares:
1. Pass-through adapter (zero overhead baseline)
2. Real platform adapter (langsmith, etc.)

Verifies identical functional behavior with acceptable overhead.
"""

import os
import time
from unittest.mock import MagicMock

# Set platform before importing ShadowDance
os.environ["PLATFORM"] = "passthrough"


def create_mock_sport_client():
    """Create mock SportClient for testing."""
    client = MagicMock()
    client.Damp.return_value = 0
    client.StandUp.return_value = 0
    client.Move.return_value = 0
    client.StopMove.return_value = 0
    client.RecoveryStand.return_value = 0
    return client


def test_passthrough_vs_langsmith():
    """Compare passthrough adapter with LangSmith adapter."""
    import shadowdance
    from shadowdance import ShadowDance

    # Reset adapter cache
    shadowdance._adapter_cache = None

    # Test with passthrough
    os.environ["PLATFORM"] = "passthrough"
    shadowdance._adapter_cache = None
    client_passthrough = ShadowDance(create_mock_sport_client(), run_type="tool")

    # Test with langsmith
    os.environ["PLATFORM"] = "langsmith"
    shadowdance._adapter_cache = None
    client_langsmith = ShadowDance(create_mock_sport_client(), run_type="tool")

    test_methods = [
        ("Damp", [], {}),
        ("StandUp", [], {}),
        ("Move", [0.3, 0, 0], {}),
        ("StopMove", [], {}),
    ]

    print("\n" + "="*70)
    print("PASSTHROUGH VS LANGSMITH COMPARISON")
    print("="*70)

    results_match = True
    overheads = []

    for method_name, args, kwargs in test_methods:
        # Run with passthrough
        start = time.perf_counter()
        result_pt = getattr(client_passthrough, method_name)(*args, **kwargs)
        time_pt = (time.perf_counter() - start) * 1000

        # Run with langsmith
        start = time.perf_counter()
        result_ls = getattr(client_langsmith, method_name)(*args, **kwargs)
        time_ls = (time.perf_counter() - start) * 1000

        overhead = time_ls - time_pt
        overheads.append(overhead)

        match = result_pt == result_ls
        status = "✓" if match else "✗"

        print(f"{method_name:<15} passthrough={time_pt:8.3f}ms  langsmith={time_ls:8.3f}ms  overhead={overhead:8.3f}ms  {status}")

        if not match:
            results_match = False

    avg_overhead = sum(overheads) / len(overheads)
    max_overhead = max(overheads)

    print("-"*70)
    print(f"Average overhead: {avg_overhead:.3f}ms")
    print(f"Max overhead: {max_overhead:.3f}ms")
    print(f"Acceptable threshold: <1.0ms per call")

    # Reset to default
    os.environ["PLATFORM"] = "langsmith"
    shadowdance._adapter_cache = None

    if results_match and max_overhead < 1.0:
        print("\n✓ TEST PASSED - Results match, overhead acceptable")
        return True
    else:
        print("\n✗ TEST FAILED")
        return False


def test_passthrough_zero_overhead():
    """Verify passthrough adapter has near-zero overhead."""
    import shadowdance
    from shadowdance import ShadowDance

    # Reset adapter cache
    shadowdance._adapter_cache = None
    os.environ["PLATFORM"] = "passthrough"
    shadowdance._adapter_cache = None

    # Create client without ShadowDance
    plain_client = create_mock_sport_client()

    # Create client with ShadowDance (passthrough)
    wrapped_client = ShadowDance(create_mock_sport_client(), run_type="tool")

    print("\n" + "="*70)
    print("PASSTHROUGH OVERHEAD TEST")
    print("="*70)

    overheads = []

    for _ in range(10):
        # Plain call
        start = time.perf_counter()
        plain_client.Damp()
        time_plain = (time.perf_counter() - start) * 1000

        # Wrapped call
        start = time.perf_counter()
        wrapped_client.Damp()
        time_wrapped = (time.perf_counter() - start) * 1000

        overhead = time_wrapped - time_plain
        overheads.append(overhead)

    avg_overhead = sum(overheads) / len(overheads)
    max_overhead = max(overheads)

    print(f"Average overhead: {avg_overhead:.3f}ms")
    print(f"Max overhead: {max_overhead:.3f}ms")
    print(f"Acceptable threshold: <0.5ms per call")

    # Reset to default
    os.environ["PLATFORM"] = "langsmith"
    shadowdance._adapter_cache = None

    if max_overhead < 0.5:
        print("\n✓ PASSTHROUGH TEST PASSED - Near-zero overhead confirmed")
        return True
    else:
        print("\n✗ PASSTHROUGH TEST FAILED - Overhead too high")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("SHADOWDANCE ADAPTER COMPARISON TESTS")
    print("="*70)

    test1 = test_passthrough_zero_overhead()
    test2 = test_passthrough_vs_langsmith()

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Passthrough overhead test: {'✓ PASS' if test1 else '✗ FAIL'}")
    print(f"Passthrough vs LangSmith:  {'✓ PASS' if test2 else '✗ FAIL'}")
    print("="*70)

    if test1 and test2:
        print("\n✓ ALL TESTS PASSED")
        exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        exit(1)
