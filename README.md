# ShadowDance

One line. Full LangSmith observability for Unitree robot SDKs.

```python
client = LocoClient()
client = ShadowDance(client)  # <- add this
client.Move(0.3, 0, 0)        # <- everything else unchanged
```

Every method call is now a traced LangSmith event. See what your robot did, when, and why.

## What it does

`ShadowDance()` wraps any Unitree SDK client object. It intercepts every method call and logs it as a LangSmith run — command name, arguments, result, timestamp, duration. No code changes beyond the one-liner.

If the client is being called from inside a LangChain agent, the traces nest automatically under the agent's run tree. You get the full decision chain: agent reasoning → tool call → robot command.

## Setup

```bash
pip install langsmith
export LANGCHAIN_API_KEY=your_key
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT=unitree-demo
```

## Implementation target

Create `shadowdance.py` in the project root:

- `ShadowDance(client)` returns a proxy object
- The proxy intercepts all method calls via `__getattr__`
- Each intercepted call wraps execution in a `langsmith.trace()` context
- Log: method name, args, kwargs, return value, exception if any
- Preserve the original method signature and return value exactly
- Do not modify `unitree_sdk2_python` source

## File structure

```
./shadowdance.py          <- implement this
./README.md               <- this file
./unitree_sdk2_python/    <- do not modify
./langchain/              <- reference for LangSmith integration patterns
./langchain/AGENTS.md     <- agent instructions
```

## Example output in LangSmith

```
Run: robot_session
  └── Move(vx=0.3, vy=0, vyaw=0)        12ms  ✓
  └── HighStand()                         8ms  ✓
  └── Move(vx=0, vy=0.3, vyaw=0)        11ms  ✓
  └── Damp()                              9ms  ✓
```

## Why

The Unitree SDK has no logging, no observability, no way to know why your robot did what it did. LangSmith fixes that. This wrapper connects them with one line of code.
