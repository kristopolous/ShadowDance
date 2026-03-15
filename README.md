<p align="center">
<img width=250px src=https://9ol.es/tmp/shadow-logo.png>
<br/>
<a href=https://pypi.org/project/shadowdanc><img src=https://badge.fury.io/py/shadowdance.svg/></a>
<br/><strong>One line. Full LangSmith observability for robot SDKs.</strong>
</p>

## Quick Start: Robot Tracing

```python
from unitree_sdk2py.go2.sport.sport_client import SportClient
from shadowdance import ShadowDance

# Your existing robot code
client = SportClient()
client.Init()

# ONE LINE - wrap with ShadowDance
client = ShadowDance(client)  # <- that's all you need!

# Everything else unchanged - now fully traced
client.StandUp()
client.Move(0.3, 0, 0)
client.Damp()
```

Every robot command is now a traced LangSmith event with full inputs, outputs, and timing.

## Connect to LLMs: Code-as-Policies

Add LLM decision-making and trace the full stack (vision → planning → execution):

```python
from shadowdance import ShadowDance
from openai import OpenAI

# Wrap your robot (as above)
robot = SportClient()
robot = ShadowDance(robot, run_type="tool")

# Wrap your LLM (ONE LINE)
llm = OpenAI()
llm = ShadowDance(llm, run_type="llm")

# Simple code-as-policies: LLM generates robot commands
task = "move forward and stop"
prompt = f"Generate robot commands for: {task}"

response = llm.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)

# Execute LLM-generated commands (traced!)
exec(response.choices[0].message.content)  # e.g., robot.Move(0.3, 0, 0)
```

Now in LangSmith you see the **full chain**: LLM reasoning → generated code → robot execution.

## Architecture

Modern LLM-powered robots use a **layered architecture**:

```
┌─────────────────────────────────────────┐
│  Your Agent Code                        │
│  ShadowDance(agent, run_type="chain")   │
├─────────────────────────────────────────┤
│  LLM (OpenAI, etc.)                     │
│  ShadowDance(llm, run_type="llm")       │
│  "pick up box" → [move, grasp, lift]    │
├─────────────────────────────────────────┤
│  Robot SDK (Unitree, etc.)              │
│  ShadowDance(robot, run_type="tool")    │
│  Move(0.3, 0, 0), StandUp(), etc.       │
└─────────────────────────────────────────┘
```

Wrap each layer with ShadowDance → see the **full decision chain** in LangSmith.

## Installation

```bash
pip install shadowdance
```

## Setup

```bash
# Load environment variables (create .env with your keys)
source .env
```

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

## Examples

### Full Demo: Code-as-Policies

```bash
python examples/code_as_policies.py
```

This demonstrates the complete **Code-as-Policies** approach:
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

### Run Types

LangSmith has different run types for better dashboard filtering:

| Run Type | Use Case | Example |
|----------|----------|---------|
| `"llm"` | LLM/VLM API calls | OpenAI, Anthropic, vision models |
| `"tool"` | Function/tool calls | Robot commands, API wrappers |
| `"chain"` | Orchestration logic | Agents, multi-step workflows |
| `"retriever"` | Document retrieval | RAG systems, vector stores |
| `"embedding"` | Embedding generation | Text embeddings |
| `"prompt"` | Prompt formatting | Custom prompt templates |

```python
# LLM calls
client = ShadowDance(OpenAI(), run_type="llm")

# Robot/tool calls
client = ShadowDance(SportClient(), run_type="tool")

# Agent orchestration
agent = ShadowDance(MyAgent(), run_type="chain")
```

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
