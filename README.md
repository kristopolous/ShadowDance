<p align="center">
<img width=250px src=https://9ol.es/tmp/shadow-logo.png>
<br/>
<a href=https://pypi.org/project/shadowdance><img src=https://badge.fury.io/py/shadowdance.svg/></a>
<br/><strong>One line. Multi-platform observability for LLM and robot SDKs.</strong>
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

Wrap each layer with ShadowDance → see the **full decision chain** in your observability platform.

### Adapter Pattern

ShadowDance uses an adapter pattern to support multiple observability backends:

```
┌─────────────────────────────────┐
│      ShadowDance Wrapper        │
│  (platform-agnostic interface)  │
└───────────────┬─────────────────┘
                │
    ┌───────────┴───────────┐
    │                       │
┌───▼──────────┐   ┌────────▼────────┐
│ LangSmith    │   │   Langfuse      │
│ Adapter      │   │   Adapter       │
└──────────────┘   └─────────────────┘
```

Select your platform via the `PLATFORM` environment variable:
- `PLATFORM=langsmith` (default)
- `PLATFORM=langfuse`

See [shadowdance/adapters/README.md](shadowdance/adapters/README.md) for detailed adapter documentation, including how to create custom adapters.

## Installation

```bash
pip install shadowdance
```

## Setup

```bash
# Load environment variables (create .env with your keys)
source .env
```

### Choose Your Observability Platform

ShadowDance supports multiple backends via the `PLATFORM` environment variable:

**LangSmith (default):**
```bash
PLATFORM=langsmith
LANGCHAIN_API_KEY=...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=shadowdance
```

**Langfuse:**
```bash
PLATFORM=langfuse
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional, for self-hosted
```

### LLM Configuration

```bash
# OpenRouter (OpenAI-compatible API)
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# Default model for vision and planning
DEFAULT_MODEL=openrouter/hunter-alpha
```

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

## Datasets & Experiments

Use ShadowDance with LangSmith datasets for **robot evaluation and regression testing**:

```python
from shadowdance import ShadowDance

# Log all executions to a dataset
robot = ShadowDance(
    SportClient(), 
    run_type="tool", 
    log_to_dataset="robot-tasks"  # Creates dataset automatically
)

# Every command is logged as an example
robot.StandUp()      # ✓ Logged with inputs, outputs, success
robot.Move(0.3, 0, 0)  # ✓ Logged with duration, result
```

**In LangSmith:**
1. Go to **Datasets & Experiments** tab
2. Find `robot-tasks` dataset with all executions
3. Create experiments to compare robot versions
4. Run regression tests on code changes

**Example: Evaluate robot configurations**
```bash
python examples/robot_evaluation.py
```

This creates datasets (`robot-eval-v1`, `robot-eval-v2`) and compares task success rates across configurations.

## Nested Tracing

Organize robot primitives under **task runs** for better visibility:

### Option 1: `@task` Decorator (Recommended)

```python
from shadowdance import ShadowDance, task

@task("pick_up_box")  # Creates parent run
def pick_up_box():
    robot = ShadowDance(SportClient())
    robot.StandUp()     # Nested under "pick_up_box"
    robot.Move(0.3, 0, 0)  # Nested
    robot.Damp()        # Nested

pick_up_box()
```

### Option 2: `task_context` Manager

```python
from shadowdance import ShadowDance, task_context

with task_context("move_to_kitchen"):
    robot = ShadowDance(SportClient())
    robot.StandUp()
    robot.Move(0.5, 0, 0)
```

### Option 3: Nested Tasks

```python
@task("complex_manipulation")
def complex_task():
    # Sub-task 1
    with task_context("grasp_object"):
        robot.Move(0.1, 0, 0)
        robot.close_gripper(0.08)
    
    # Sub-task 2
    with task_context("lift_object"):
        robot.Move(0, 0, 0.15)
```

**In LangSmith Runs dashboard:**
```
pick_up_box (chain)
├── StandUp (tool)
├── Move (tool)
└── Damp (tool)

move_to_kitchen (chain)
├── StandUp (tool)
└── Move (tool)
```

**Example:**
```bash
python examples/nested_tracing.py
```

## Demo

### Investor Demo

For a polished demonstration showing the full capabilities:

```bash
python examples/investor_demo.py
```

This creates **beautiful, organized traces** showing:
- 📦 **Warehouse Automation** - Pick and place with perception → planning → execution
- 🔍 **Quality Inspection** - Multi-point inspection with detailed tracking
- 🚨 **Safety Systems** - Emergency response with critical event logging

**Perfect for showing investors:**
1. Run the demo
2. Open https://smith.langchain.com
3. Project: `shadowdance-demo`
4. Watch traces appear in real-time

Each task shows clear hierarchy:
```
warehouse_pick_and_place (chain)
├── perception_phase (vision)
├── planning_phase (llm)
├── execution_phase (control)
│   ├── StandUp (tool)
│   ├── Move (tool) ×5
│   └── Damp (tool)
└── return_phase (control)
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
wrapped.Move(0.3, 0, 0)  # Traced in your observability platform
```

## File structure

```
./shadowdance/                # Main package
├── __init__.py               # ShadowDance wrapper + factory
└── adapters/
    ├── __init__.py           # Base interface + TraceEvent
    ├── langsmith.py          # LangSmith adapter
    ├── langfuse.py           # Langfuse adapter
    ├── example.py            # Template for custom adapters
    └── README.md             # Adapter documentation
./test_shadowdance.py         # Unit tests
./examples/
├── basic.py                  # Basic usage
├── error_handling.py         # Error handling demo
├── virtual_robot.py          # Virtual robot server
└── with_virtual_robot.py     # Virtual robot + observability demo
./pyproject.toml              # Package configuration
./requirements.txt            # Dependencies
./.env                        # Platform credentials (gitignored)
```

## Why

The Unitree SDK has no logging, no observability, no way to know why your robot did what it did. ShadowDance fixes that. This wrapper connects them with one line of code.

Choose your observability platform:
- **LangSmith**: Full-featured LLM observability with datasets, experiments, and evaluation
- **Langfuse**: Open-source alternative with tracing, metrics, and prompt management
- **Custom**: Build your own adapter (see [adapters/README.md](shadowdance/adapters/README.md))
