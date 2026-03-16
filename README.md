<p align="center">
<img width=250px src=https://9ol.es/tmp/shadow-logo.png>
<br/>
<a href=https://pypi.org/project/shadowdance><img src=https://badge.fury.io/py/shadowdance.svg/></a>
<br/><strong>Zero-code-change observability for Python.</strong>
</p>

## The Promise

**Your existing code needs exactly ONE line of change.**

No refactoring. No decorators. No rewriting. Just wrap your existing client/object and everything is traced.

```python
# Your existing code - unchanged
from some_library import SomeClient

client = SomeClient()
client.do_something(arg1, arg2)
client.do_another_thing()
```

Becomes:

```python
# Your existing code - ONE LINE CHANGE
from some_library import SomeClient
from shadowdance import ShadowDance

client = SomeClient()
client = ShadowDance(client)  # <- THAT'S IT. Everything below is traced.
client.do_something(arg1, arg2)
client.do_another_thing()
```

Every method call is now traced with inputs, outputs, timing, and errors. **You don't touch any of your existing logic.**

## Quick Start

```python
from shadowdance import ShadowDance

# Wrap any existing client or object
existing_client = SomeLibrary.Client()
existing_client = ShadowDance(existing_client)  # One line

# Everything below works exactly as before - now fully traced
existing_client.method1(arg1, arg2)
existing_client.method2()
result = existing_client.method3(key="value")
```

That's it. Your code doesn't change. ShadowDance intercepts all method calls automatically.

## Use Cases

### LLM Observability

```python
from openai import OpenAI
from shadowdance import ShadowDance

# Your existing OpenAI code
client = OpenAI()
client = ShadowDance(client, run_type="llm")  # One line

# Everything traced: prompts, completions, timing, tokens
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### API Clients

```python
import requests
from shadowdance import ShadowDance

# Wrap any HTTP client
api_client = SomeAPIClient()
api_client = ShadowDance(api_client, run_type="tool")  # One line

# All API calls traced
data = api_client.fetch_data()
api_client.post_update(item)
```

### Database Clients

```python
import redis
from shadowdance import ShadowDance

# Wrap your database client
db = redis.Redis()
db = ShadowDance(db, run_type="tool")  # One line

# All queries traced
db.set("key", "value")
result = db.get("key")
```

### Robot SDKs (Original Use Case)

```python
from unitree_sdk2py.go2.sport.sport_client import SportClient
from shadowdance import ShadowDance

# Your existing robot code
client = SportClient()
client.Init()
client = ShadowDance(client)  # One line

# All robot commands traced
client.StandUp()
client.Move(0.3, 0, 0)
client.Damp()
```

## Choose Your Observability Platform

ShadowDance supports multiple backends via the `PLATFORM` environment variable:

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

**Note:** You only need to install the platform you use. ShadowDance uses lazy imports.

## Run Types

Run types help you filter and organize traces in your dashboard:

| Run Type | Use Case | Example |
|----------|----------|---------|
| `"llm"` | LLM/VLM API calls | OpenAI, Anthropic, vision models |
| `"tool"` | Function/tool calls | API wrappers, database queries |
| `"chain"` | Orchestration logic | Agents, multi-step workflows |
| `"retriever"` | Document retrieval | RAG systems, vector stores |
| `"embedding"` | Embedding generation | Text embeddings |
| `"prompt"` | Prompt formatting | Custom prompt templates |

```python
# LLM calls
client = ShadowDance(OpenAI(), run_type="llm")

# API/tool calls
client = ShadowDance(APIClient(), run_type="tool")

# Agent orchestration
agent = ShadowDance(MyAgent(), run_type="chain")
```

## Nested Tracing (Optional)

If you want to organize traces under parent tasks, use the `@task` decorator:

```python
from shadowdance import ShadowDance, task

@task("process_request")  # Creates parent run
def process_request():
    # All ShadowDance-wrapped calls inside are nested
    client = ShadowDance(APIClient())
    client.fetch_data()    # Nested under "process_request"
    client.transform()     # Nested
    client.save()          # Nested

process_request()
```

**In your dashboard:**
```
process_request (chain)
├── fetch_data (tool)
├── transform (tool)
└── save (tool)
```

## Datasets & Experiments

Log executions to datasets for evaluation and regression testing:

```python
from shadowdance import ShadowDance

# Log all executions to a dataset
client = ShadowDance(
    APIClient(),
    run_type="tool",
    log_to_dataset="api-calls"  # Creates dataset automatically
)

# Every call is logged as an example
client.do_something(arg1)  # ✓ Logged with inputs, outputs, timing
client.do_another(arg2)    # ✓ Logged with duration, result
```

**In your dashboard:**
1. Go to **Datasets & Experiments** tab
2. Find your dataset with all executions
3. Create experiments to compare versions
4. Run regression tests on code changes

## Example Output

**Your observability dashboard:**
```
Run: api_session
  └── fetch_data(query="users")     45ms  ✓
  └── transform(data)               12ms  ✓
  └── save(result)                  23ms  ✓
  └── get("key")                     8ms  ✓
```

View traces at:
- **LangSmith**: [smith.langchain.com](https://smith.langchain.com)
- **Langfuse**: Your Langfuse dashboard
- **Weave**: Your Weave project in W&B

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

## API

### `ShadowDance(client, run_type="tool", log_to_dataset=None)`

Wraps any client object with observability tracing.

**Args:**
- `client`: Any Python object with methods (API client, database client, LLM client, etc.)
- `run_type`: Type for filtering in dashboard ("tool", "llm", "chain", etc.)
- `log_to_dataset`: Optional dataset name for evaluation logging

**Returns:**
- A proxy object that intercepts all method calls

**Example:**
```python
wrapped = ShadowDance(client)
wrapped.method(arg1, arg2)  # Automatically traced
```

### `@task(name, run_type="chain")`

Optional decorator to create parent runs for nested tracing.

**Example:**
```python
@task("my_workflow")
def my_function():
    client = ShadowDance(APIClient())
    client.do_something()  # Nested under "my_workflow"
```

### `task_context(name, run_type="chain")`

Optional context manager for creating parent runs.

**Example:**
```python
with task_context("batch_process"):
    client = ShadowDance(APIClient())
    client.process_batch(items)
```

## File Structure

```
./shadowdance/                # Main package
├── __init__.py               # ShadowDance wrapper + factory
└── adapters/
    ├── __init__.py           # Base interface + TraceEvent
    ├── langsmith.py          # LangSmith adapter
    ├── langfuse.py           # Langfuse adapter
    ├── weave.py              # Weave adapter (W&B)
    ├── example.py            # Template for custom adapters
    └── README.md             # Adapter documentation
./test_shadowdance.py         # Unit tests
./examples/                   # Example code
./pyproject.toml              # Package configuration
./requirements.txt            # Dependencies
```

## Why

Most observability tools require you to:
- Add decorators to every function
- Refactor your code structure
- Change how you call methods
- Learn a new framework

**ShadowDance is different.** It's a transparent wrapper that intercepts method calls without changing your code.

The Unitree robot SDK has no logging, no observability, no way to know why your robot did what it did. ShadowDance fixes that with one line.

Your API client has no tracing. ShadowDance adds it with one line.

Your LLM calls are a black box. ShadowDance opens it with one line.

**No refactoring. No decorators on your functions. No code changes.** Just wrap and go.

## Choose Your Platform

- **LangSmith**: Full-featured LLM observability with datasets, experiments, and evaluation
- **Langfuse**: Open-source alternative with tracing, metrics, and prompt management
- **Weave**: Weights & Biases LLM observability with automatic tracing
- **Custom**: Build your own adapter (see [adapters/README.md](shadowdance/adapters/README.md))

## Testing

```bash
# Run unit tests
python test_shadowdance.py
```

## License

MIT
