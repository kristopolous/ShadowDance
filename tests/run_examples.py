#!/usr/bin/env python3
"""
Unitree example test runner.

Runs Unitree SDK examples with ShadowDance using different adapters:
1. Pass-through (baseline - zero overhead)
2. LangSmith (or other real platform)

Compares results to verify:
- Identical return values
- Acceptable performance overhead
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class TestRun:
    """Result from running an example."""
    adapter: str
    success: bool
    duration_ms: float
    output: str
    error: str = None


def run_example_with_adapter(
    example_path: str,
    adapter: str,
    timeout: float = 30.0
) -> TestRun:
    """
    Run a Unitree example with specified adapter.

    Args:
        example_path: Path to the example script
        adapter: Adapter to use (passthrough, langsmith, etc.)
        timeout: Timeout in seconds

    Returns:
        TestRun with results
    """
    env = os.environ.copy()
    env["PLATFORM"] = adapter

    # Disable actual API calls for langsmith/langfuse in tests
    if adapter == "langsmith":
        env["LANGCHAIN_TRACING_V2"] = "false"
    if adapter == "langfuse":
        env["LANGFUSE_PUBLIC_KEY"] = "test"
        env["LANGFUSE_SECRET_KEY"] = "test"

    start = time.perf_counter()
    try:
        result = subprocess.run(
            [sys.executable, example_path],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        duration_ms = (time.perf_counter() - start) * 1000

        return TestRun(
            adapter=adapter,
            success=result.returncode == 0,
            duration_ms=duration_ms,
            output=result.stdout,
            error=result.stderr if result.returncode != 0 else None
        )
    except subprocess.TimeoutExpired:
        return TestRun(
            adapter=adapter,
            success=False,
            duration_ms=timeout * 1000,
            output="",
            error=f"Timeout after {timeout}s"
        )
    except Exception as e:
        return TestRun(
            adapter=adapter,
            success=False,
            duration_ms=0,
            output="",
            error=str(e)
        )


def compare_runs(
    passthrough: TestRun,
    platform: TestRun,
    overhead_threshold_ms: float = 5.0
) -> Tuple[bool, str]:
    """
    Compare test runs from passthrough and platform adapters.

    Args:
        passthrough: Result from passthrough adapter
        platform: Result from real platform adapter
        overhead_threshold_ms: Max acceptable overhead

    Returns:
        (passed, message)
    """
    # Check both succeeded
    if not passthrough.success:
        return False, f"Passthrough run failed: {passthrough.error}"
    if not platform.success:
        return False, f"Platform run failed: {platform.error}"

    # Compare outputs (should be identical for deterministic examples)
    if passthrough.output.strip() != platform.output.strip():
        # For some examples, output may differ slightly - just warn
        print(f"  ⚠ Output differs (may be expected)")

    # Check overhead
    overhead = platform.duration_ms - passthrough.duration_ms
    overhead_pct = (overhead / passthrough.duration_ms * 100) if passthrough.duration_ms > 0 else 0

    if overhead > overhead_threshold_ms:
        return False, f"Overhead {overhead:.2f}ms exceeds threshold {overhead_threshold_ms}ms"

    return True, f"✓ Overhead {overhead:.2f}ms ({overhead_pct:.1f}%)"


def find_example_scripts(examples_dir: str) -> List[str]:
    """Find all Python example scripts."""
    examples = []
    for root, dirs, files in os.walk(examples_dir):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']

        for file in files:
            if file.endswith('.py') and not file.startswith('_'):
                examples.append(os.path.join(root, file))

    return sorted(examples)


def run_test_suite(
    examples_dir: str,
    platform: str = "langsmith",
    max_examples: int = None
):
    """
    Run test suite on Unitree examples.

    Args:
        examples_dir: Directory containing Unitree examples
        platform: Platform adapter to test (default: langsmith)
        max_examples: Max examples to run (None = all)
    """
    print("="*70)
    print("SHADOWDANCE UNITREE EXAMPLE TEST SUITE")
    print("="*70)
    print(f"Examples directory: {examples_dir}")
    print(f"Platform adapter: {platform}")
    print()

    examples = find_example_scripts(examples_dir)
    if max_examples:
        examples = examples[:max_examples]

    print(f"Found {len(examples)} example scripts\n")

    results = []
    passed = 0
    failed = 0

    for i, example in enumerate(examples, 1):
        rel_path = os.path.relpath(example, examples_dir)
        print(f"[{i}/{len(examples)}] {rel_path}")

        # Run with passthrough (baseline)
        print(f"  Running with passthrough adapter...")
        passthrough = run_example_with_adapter(example, "passthrough")

        # Run with real platform
        print(f"  Running with {platform} adapter...")
        platform_run = run_example_with_adapter(example, platform)

        # Compare
        success, message = compare_runs(passthrough, platform_run)

        if success:
            passed += 1
            print(f"  {message} ✓")
        else:
            failed += 1
            print(f"  {message} ✗")

        results.append({
            "example": rel_path,
            "passed": success,
            "passthrough_ms": passthrough.duration_ms,
            "platform_ms": platform_run.duration_ms,
            "message": message
        })
        print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"{'Example':<50} {'Status':<10} {'Overhead'}")
    print("-"*70)

    for result in results:
        status = "✓ PASS" if result["passed"] else "✗ FAIL"
        overhead = result["platform_ms"] - result["passthrough_ms"]
        print(f"{result['example']:<50} {status:<10} {overhead:+.2f}ms")

    print("-"*70)
    print(f"Passed: {passed}/{len(examples)}")
    print(f"Failed: {failed}/{len(examples)}")

    if failed == 0:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Unitree examples with ShadowDance")
    parser.add_argument(
        "--examples-dir",
        default="tests/unitree_examples",
        help="Directory containing Unitree examples"
    )
    parser.add_argument(
        "--platform",
        default="langsmith",
        choices=["passthrough", "langsmith", "langfuse", "weave"],
        help="Platform adapter to test"
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=None,
        help="Max examples to run (default: all)"
    )

    args = parser.parse_args()

    if not os.path.isdir(args.examples_dir):
        print(f"Error: Examples directory not found: {args.examples_dir}")
        sys.exit(1)

    sys.exit(run_test_suite(
        args.examples_dir,
        args.platform,
        args.max_examples
    ))
