<p align="center">
<img width=250px src=https://9ol.es/tmp/shadow-logo.png>
<br/>
<a href=https://pypi.org/project/shadowdanc><img src=https://badge.fury.io/py/shadowdance.svg/></a>
<br/><strong>One line. Full LangSmith observability for LLM and robot SDKs.</strong>
</p>


```python
from shadowdance import ShadowDance

# OpenAI client
client = OpenAI()
client = ShadowDance(client)  # <- ONE LINE
response = client.chat.completions.create(...)  # <- traced!
```

```python
# Robot client
client = SportClient()
client = ShadowDance(client)  # <- ONE LINE
client.Move(0.3, 0, 0)  # <- traced!
```

Every call is now a traced LangSmith event.

## What it does

`ShadowDance()` wraps any client object (OpenAI, Unitree, etc.). It intercepts every method call and logs it as a LangSmith run — command name, arguments, result, timestamp, duration. No code changes beyond the one-liner.

If the client is being called from inside a LangChain agent, the traces nest automatically under the agent's run tree.

## How LLM Robot Systems Work

Modern LLM-powered robots use a **layered architecture**:

```
┌─────────────────────────────────────────┐
│  High-Level Agent (ShadowDance here!)   │
│  "pick up the box" → coordinates layers │
├─────────────────────────────────────────┤
│  Task Planning (LLM)                    │
│  Natural language → symbolic plan       │
├─────────────────────────────────────────┤
│  Perception (VLM)                       │
│  Camera image → object positions        │
├─────────────────────────────────────────┤
│  Low-Level Control                      │
│  Trajectories → motor commands          │
└─────────────────────────────────────────┘
```

ShadowDance traces the **full stack** so you can debug:
- What did the LLM plan?
- What did the VLM see?
- What commands were sent?
- Where did it fail?

## Installation

```bash
pip install -e .
# or
pip install langsmith
```

## Setup

```bash
# Install dependencies
pip install -e .

# Load environment variables
source .env
```

## Configuration

The `.env` file contains:

```bash
# LangSmith tracing
LANGCHAIN_API_KEY=...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=shadowdance

# OpenRouter (OpenAI-compatible API)
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# Default model for vision and planning
DEFAULT_MODEL=openrouter/hunter-alpha
```

### Using Different Models

Change `DEFAULT_MODEL` in `.env` to use different models:

- **Vision + Text**: `openrouter/hunter-alpha` (multimodal)
- **Free models**: See [OpenRouter's model list](https://openrouter.ai/models)

### Test Connection

```bash
python examples/test_openrouter.py
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

### Quick Start: OpenAI Client

```python
from openai import OpenAI
from shadowdance import ShadowDance

client = OpenAI()
client = ShadowDance(client)  # ONE LINE

response = client.chat.completions.create(
    model="openrouter/hunter-alpha",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

Run: `python examples/openai_client.py`

### Code-as-Policies (Full Demo)

Modern LLM robot architecture: VLM → LLM → Code → Robot

```bash
python examples/code_as_policies.py
```

This demonstrates the **Code-as-Policies** approach:
1. **VLM** analyzes image → detects white box at [0.0, 0.1, 0.72]
2. **LLM** generates Python code → `robot.move_to(...)`, `robot.close_gripper(...)`
3. **Safe executor** runs code → robot picks up box
4. **ShadowDance** traces everything → debug in LangSmith

```
Task: "Pick up the white box"
  ↓
Vision: white_box detected at [0.0, 0.1, 0.72]
  ↓  
LLM: Generates 4-line Python program
  ↓
Robot: move_to → close_gripper → move_to (SUCCESS)
```

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
