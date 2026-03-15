# ShadowDance

One line. Full LangSmith observability for Unitree robot SDKs.

```python
from qwen import ShadowDance

client = LocoClient()
client = ShadowDance(client)  # <- add this
client.Move(0.3, 0, 0)        # <- everything else unchanged
```

Every method call is now a traced LangSmith event. See what your robot did, when, and why.

## What it does

`ShadowDance()` wraps any Unitree SDK client object. It intercepts every method call and logs it as a LangSmith run — command name, arguments, result, timestamp, duration. No code changes beyond the one-liner.

If the client is being called from inside a LangChain agent, the traces nest automatically under the agent's run tree. You get the full decision chain: agent reasoning → tool call → robot command.

## Installation

```bash
pip install langsmith
```

## Setup

Set the following environment variables:

```bash
export LANGCHAIN_API_KEY=your_key
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT=unitree-demo
```

## Quick Start

### Basic Usage

```python
from unitree_sdk2py.go2.sport.sport_client import SportClient
from qwen import ShadowDance

# Create the client
client = SportClient()
client.Init()

# Wrap with ShadowDance
client = ShadowDance(client)

# All method calls are now traced
client.Damp()
client.StandUp()
client.Move(0.3, 0, 0)
```

### With LangChain Agent

```python
from langchain.agents import tool
from qwen import ShadowDance

@tool
def robot_move(vx: float, vy: float, vyaw: float) -> str:
    """Move the robot with velocity commands."""
    client = SportClient()
    client = ShadowDance(client)
    client.Init()
    client.Move(vx, vy, vyaw)
    return "Moved successfully"
```

## Examples

See the `examples/` directory for complete working examples:

- `examples/basic.py` - Basic usage with mock client
- `examples/agent_integration.py` - Integration with LangChain agents
- `examples/error_handling.py` - How exceptions are traced

## Features

- **Automatic tracing**: Every method call is logged automatically
- **Nested traces**: Integrates seamlessly with LangChain run trees
- **Exception tracking**: Errors are captured and logged
- **Duration tracking**: Each call's execution time is recorded
- **Input/output logging**: Arguments and return values are captured
- **Zero code changes**: Only one line to add, everything else unchanged

## API

### `ShadowDance(client)`

Wraps a client object with LangSmith tracing.

**Args:**
- `client`: The Unitree SDK client object to wrap (e.g., `SportClient`, `RobotStateClient`)

**Returns:**
- A proxy object that intercepts all method calls

**Example:**
```python
wrapped = ShadowDance(client)
wrapped.Move(0.3, 0, 0)  # Traced as "Move" in LangSmith
```

## Viewing Traces

Once configured, view your traces at [smith.langchain.com](https://smith.langchain.com):

```
Run: robot_session
  └── Move(vx=0.3, vy=0, vyaw=0)        12ms  ✓
  └── StandUp()                          8ms  ✓
  └── Damp()                            11ms  ✓
  └── RecoveryStand()                    9ms  ✓
```

## Why

The Unitree SDK has no logging, no observability, no way to know why your robot did what it did. LangSmith fixes that. This wrapper connects them with one line of code.

## License

MIT
