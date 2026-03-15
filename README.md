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

If the client is being called from inside a LangChain agent, the traces nest automatically under the agent's run tree. You get the full decision chain: agent reasoning → tool call → robot command.

## Installation

```bash
pip install -e .
# or
pip install langsmith
```

## Setup

```bash
# Load environment variables
source .env

# Or set manually
export LANGCHAIN_API_KEY=your_key
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT=unitree-demo
```

## Quick Start

### With a Real Robot

```python
from unitree_sdk2py.go2.sport.sport_client import SportClient
from shadowdance import ShadowDance

client = SportClient()
client.Init()

# Wrap with ShadowDance
client = ShadowDance(client)

# All calls are now traced
client.Move(0.3, 0, 0)
```

### With Virtual Robot (No Hardware Required)

Test LangSmith tracing without a physical robot:

```bash
source .env
python examples/with_virtual_robot.py
```

This runs a simulated robot that responds to commands just like a real Unitree robot. Perfect for development and testing!

## Examples

| Example | Description |
|---------|-------------|
| `examples/basic.py` | Basic usage with mock client |
| `examples/error_handling.py` | How exceptions are traced |
| `examples/with_virtual_robot.py` | Full demo with virtual robot + LangSmith |
| `examples/pick_up_box.py` | **Full stack**: Vision → Planning → Robot control |

### Full Stack Demo: Pick Up Box

The `pick_up_box.py` demo shows complete observability across your robot stack:

```
Vision (detect box)
   ↓
Planning (LLM generates plan)
   ↓  
Execution (robot control)
```

All traced in LangSmith with nested runs showing the full decision chain.

## Example output in LangSmith

```
Run: robot_session
  └── Move(vx=0.3, vy=0, vyaw=0)        12ms  ✓
  └── StandUp()                          8ms  ✓
  └── Move(vx=0, vy=0.3, vyaw=0)        11ms  ✓
  └── Damp()                             9ms  ✓
```

View your traces at [smith.langchain.com](https://smith.langchain.com)

## Testing

```bash
# Run unit tests
python test_shadowdance.py

# Run with virtual robot
python examples/with_virtual_robot.py
```

## API

### `ShadowDance(client)`

Wraps a client object with LangSmith tracing.

**Args:**
- `client`: The Unitree SDK client object to wrap

**Returns:**
- A proxy object that intercepts all method calls

**Example:**
```python
wrapped = ShadowDance(client)
wrapped.Move(0.3, 0, 0)  # Traced as "Move" in LangSmith
```

## File structure

```
./shadowdance.py              # Main implementation
./test_shadowdance.py         # Unit tests
./examples/
├── basic.py                  # Basic usage
├── error_handling.py         # Error handling demo
├── virtual_robot.py          # Virtual robot server
└── with_virtual_robot.py     # Virtual robot + LangSmith demo
./pyproject.toml              # Package configuration
./requirements.txt            # Dependencies
./.env                        # LangSmith credentials (gitignored)
```

## Why

The Unitree SDK has no logging, no observability, no way to know why your robot did what it did. LangSmith fixes that. This wrapper connects them with one line of code.
