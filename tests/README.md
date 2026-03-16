# ShadowDance Test Suite

## Verification Tests

These tests verify that ShadowDance provides observability **without changing behavior or adding significant overhead**.

### Run the Test Suite

```bash
python tests/test_unitree_examples.py
```

### What We Test

1. **Return Value Matching**: ShadowDance-wrapped clients return identical values to plain clients
2. **Exception Propagation**: Exceptions are properly passed through ShadowDance
3. **Performance Overhead**: Added latency < 1ms per call (acceptable jitter)

### Example Output

```
======================================================================
SHADOWDANCE VERIFICATION TEST SUITE
======================================================================

Testing return value matching...
Damp: plain=0, wrapped=0 ✓
StandUp: plain=0, wrapped=0 ✓
Move: plain=0, wrapped=0 ✓

Testing exception propagation...
Plain client raised: True ✓
Wrapped client raised: True ✓

RESULTS COMPARISON
======================================================================
Method               Plain (ms)      ShadowDance (ms)   Overhead     Match
----------------------------------------------------------------------
Damp                 0.030           0.166              0.135        ✓
StandUp              0.021           0.057              0.037        ✓
Move                 0.019           0.052              0.032        ✓
----------------------------------------------------------------------
TOTAL                0.144           0.554              0.409

Max overhead: 0.135ms
Acceptable jitter threshold: <1.0ms per call

✓ ALL TESTS PASSED - ShadowDance adds negligible overhead
```

## Unitree Examples

The `unitree_examples/` directory contains copied examples from the Unitree SDK for testing.

These are **not** included in the git repo (Unitree SDK is external), but are copied here for test execution.

### Running Examples with ShadowDance

To run any Unitree example with ShadowDance tracing:

```python
from unitree_sdk2py.go2.sport.sport_client import SportClient
from shadowdance import ShadowDance

# Your existing code
client = SportClient()
client.Init()

# Add ONE LINE
client = ShadowDance(client)  # <- Now fully traced

# Everything below works exactly as before
client.StandUp()
client.Move(0.3, 0, 0)
```

## Performance Guarantees

ShadowDance guarantees:
- **< 1ms overhead** per method call (typically < 0.2ms)
- **Identical return values** to unwrapped client
- **Proper exception propagation** - no swallowed errors
- **Zero code changes** required in your existing logic
