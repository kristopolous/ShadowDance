# ShadowDance

One line. Full LangSmith observability for Unitree robot SDKs.

```python
from shadowdance import ShadowDance

client = LocoClient()
client = ShadowDance(client)  # <- add this
client.Move(0.3, 0, 0)        # <- everything else unchanged
```

Every method call is now a traced LangSmith event. See what your robot did, when, and why.

## What it does

`ShadowDance()` wraps any Unitree SDK client object. It intercepts every method call and logs it as a LangSmith run — command name, arguments, result, timestamp, duration. No code changes beyond the one-liner.

If the client is being called from inside a LangChain agent, the traces nest automatically under the agent's run tree.

## Setup

```bash
pip install langsmith
export LANGCHAIN_API_KEY=your_key
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT=unitree-demo
```

## Usage

```python
from shadowdance import ShadowDance

# Wrap any Unitree SDK client
client = SportClient()
client = ShadowDance(client)

# All method calls are now traced
client.Move(0.3, 0, 0)
client.StandUp()
client.Damp()
```

## Example Output in LangSmith

```
Run: robot_session
  └── Move(vx=0.3, vy=0, vyaw=0)        12ms  ✓
  └── StandUp()                          8ms  ✓
  └── Move(vx=0, vy=0.3, vyaw=0)        11ms  ✓
  └── Damp()                             9ms  ✓
```

## Files

- `shadowdance.py` - Main implementation
- `test_shadowdance.py` - Unit tests
- `example_usage.py` - Usage examples