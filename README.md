<p align="center">
<img width=250px src=https://9ol.es/tmp/shadow-logo.png>
<br/>
<a href=https://pypi.org/project/shadowdance><img src=https://badge.fury.io/py/shadowdance.svg/></a>
<br/><strong>The first observability tool for LLM-powered robots.</strong>
</p>

## The Problem

When your robot does something unexpected, you have no idea why.

Was it the vision model? The planner? A bad command? The network? **There's no way to know.** Robot SDKs have no logging, no observability, no debugging. You're flying blind.

## The Solution

**One line of code.** Wrap your robot client and see everything:

```python
from unitree_sdk2py.go2.sport.sport_client import SportClient
from shadowdance import ShadowDance

# Your existing robot code
client = SportClient()
client.Init()

# ONE LINE - wrap with ShadowDance
client = ShadowDance(client)  # <- THAT'S IT. Everything below is traced.

# All robot commands now traced with inputs, outputs, timing
client.StandUp()
client.Move(0.3, 0, 0)
client.Damp()
```

**No refactoring. No code changes.** Just wrap and go.

## End-to-End ML Pipeline Observability

Modern LLM-powered robots span multiple systems:

```
┌─────────────────────────────────────────┐
│  Cloud LLM (OpenAI, Anthropic)          │
│  "pick up the white box" → commands     │
├─────────────────────────────────────────┤
│  Your Agent Code                        │
│  Vision → Planning → Execution          │
├─────────────────────────────────────────┤
│  Robot (Unitree Go2, H1, etc.)          │
│  Move, StandUp, Damp, gripper control   │
└─────────────────────────────────────────┘
```

**ShadowDance traces the entire pipeline:**

```python
from shadowdance import ShadowDance
from openai import OpenAI

# Wrap your LLM (ONE LINE)
llm = OpenAI()
llm = ShadowDance(llm, run_type="llm")

# Wrap your robot (ONE LINE)
robot = SportClient()
robot = ShadowDance(robot, run_type="tool")

# Now you see the FULL chain in your dashboard:
# LLM prompt → generated commands → robot execution → timing → errors
```

## Choose Your Observability Platform

**LangSmith (default):**
```bash
export PLATFORM=langsmith
export LANGCHAIN_API_KEY=...
```

**Langfuse:**
```bash
export PLATFORM=langfuse
export LANGFUSE_PUBLIC_KEY=...
export LANGFUSE_SECRET_KEY=...
```

**Weave (Weights & Biases):**
```bash
export PLATFORM=weave
export WANDB_API_KEY=...
```

## What You Get

### Full Trace Visibility

```
Run: robot_session
  ├── StandUp()                          8ms  ✓
  ├── Move(vx=0.3, vy=0, vyaw=0)        12ms  ✓
  ├── Move(vx=0, vy=0.3, vyaw=0)        11ms  ✓
  └── Damp()                             9ms  ✓
```

### Nested Task Organization

```python
from shadowdance import task

@task("pick_up_box")
def pick_up_box():
    robot = ShadowDance(SportClient())
    robot.StandUp()
    robot.Move(0.3, 0, 0)
    robot.Damp()
```

**In your dashboard:**
```
pick_up_box (chain)
├── StandUp (tool)
├── Move (tool)
└── Damp (tool)
```

### LLM + Robot Correlation

See how LLM decisions affect robot behavior:

```
code_as_policies_task (chain)
├── vision_analysis (llm)
│   └── "white_box at [0.0, 0.1, 0.72]"
├── code_generation (llm)
│   └── "robot.move_to(0.0, 0.1, 0.72)"
└── code_execution (tool)
    ├── move_to (tool)  ✓
    └── close_gripper (tool)  ✓
```

### Datasets & Regression Testing

```python
# Log all robot commands to a dataset
robot = ShadowDance(
    SportClient(),
    run_type="tool",
    log_to_dataset="robot-tasks"
)

# Every command logged for evaluation
robot.StandUp()      # ✓ Logged
robot.Move(0.3, 0, 0)  # ✓ Logged
```

**In your dashboard:**
1. Go to **Datasets & Experiments**
2. Find `robot-tasks` with all executions
3. Compare robot versions
4. Run regression tests

## Installation

```bash
pip install shadowdance
```

Then install your chosen platform:

```bash
# For LangSmith (default)
pip install langsmith

# For Langfuse
pip install langfuse

# For Weave
pip install wandb
```

## Quick Start

```bash
# Set your platform
export PLATFORM=langsmith
export LANGCHAIN_API_KEY=your-key

# Run your robot code
python your_robot_script.py
```

View traces at:
- **LangSmith**: [smith.langchain.com](https://smith.langchain.com)
- **Langfuse**: Your Langfuse dashboard
- **Weave**: Your Weave project in W&B

## API

### `ShadowDance(client, run_type="tool", log_to_dataset=None)`

Wraps any client object with observability tracing.

**Args:**
- `client`: The client object to wrap (Unitree SDK, OpenAI, etc.)
- `run_type`: Type for filtering ("tool", "llm", "chain", etc.)
- `log_to_dataset`: Optional dataset name for evaluation

**Example:**
```python
# Robot
robot = ShadowDance(SportClient(), run_type="tool")

# LLM
llm = ShadowDance(OpenAI(), run_type="llm")

# Agent
agent = ShadowDance(MyAgent(), run_type="chain")
```

### `@task(name, run_type="chain")`

Decorator to create parent runs for nested tracing.

**Example:**
```python
@task("pick_up_box")
def pick_up_box():
    robot = ShadowDance(SportClient())
    robot.StandUp()  # Nested under "pick_up_box"
```

### `task_context(name, run_type="chain")`

Context manager for creating parent runs.

**Example:**
```python
with task_context("move_to_kitchen"):
    robot = ShadowDance(SportClient())
    robot.Move(0.5, 0, 0)
```

## Run Types

| Run Type | Use Case | Example |
|----------|----------|---------|
| `"llm"` | LLM/VLM API calls | OpenAI, Anthropic, vision models |
| `"tool"` | Robot commands, API calls | Move, StandUp, gripper control |
| `"chain"` | Orchestration logic | Agents, multi-step workflows |
| `"retriever"` | Document retrieval | RAG systems, vector stores |
| `"embedding"` | Embedding generation | Text embeddings |

## Why ShadowDance?

**Before ShadowDance:**
- Robot SDKs have zero observability
- No way to debug why robot did X instead of Y
- Can't correlate LLM decisions with robot actions
- No regression testing for robot behavior
- Flying blind in production

**After ShadowDance:**
- Every robot command traced with timing and results
- Full LLM → robot pipeline visibility
- Organized traces by task
- Datasets for evaluation and regression
- Debug production issues from your dashboard

**One line of code.** That's all it takes to go from blind to full visibility.

## File Structure

```
./shadowdance/                # Main package
├── __init__.py               # ShadowDance wrapper + factory
└── adapters/
    ├── __init__.py           # Base interface + TraceEvent
    ├── langsmith.py          # LangSmith adapter
    ├── langfuse.py           # Langfuse adapter
    ├── weave.py              # Weave adapter (W&B)
    ├── passthrough.py        # Pass-through adapter (testing)
    ├── example.py            # Template for custom adapters
    └── README.md             # Adapter documentation
./tests/                      # Test suite
├── test_adapter_comparison.py   # Adapter overhead tests
├── test_unitree_examples.py   # Unitree SDK verification
└── unitree_examples/          # Copied Unitree SDK examples
./examples/                   # Example code
./pyproject.toml              # Package configuration
./requirements.txt            # Dependencies
```

## Testing

```bash
# Run adapter comparison tests (verifies <1ms overhead)
python tests/test_adapter_comparison.py

# Run Unitree example verification tests
python tests/test_unitree_examples.py

# Run Unitree examples with different adapters
python tests/run_examples.py --examples-dir tests/unitree_examples
```

## License

MIT
