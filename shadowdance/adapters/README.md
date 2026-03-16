# ShadowDance Adapters

Observability backend implementations for ShadowDance.

## Overview

ShadowDance uses an **adapter pattern** to support multiple observability backends. Each adapter implements the same interface, allowing you to switch backends via the `PLATFORM` environment variable.

```
┌─────────────────────────────────┐
│      ShadowDance Wrapper        │
│  (platform-agnostic interface)  │
└───────────────┬─────────────────┘
                │
    ┌───────────┼───────────┬───────────┐
    │           │           │           │
┌───▼──────┐ ┌──▼──────┐ ┌──▼──────┐   │
│ LangSmith│ │ Langfuse│ │  Weave  │   │
│ Adapter  │ │ Adapter │ │ Adapter │   │
└──────────┘ └─────────┘ └─────────┘   │
                                       │
                        ┌──────────────┘
                        │
                  ┌─────▼──────┐
                  │   Custom   │
                  │  Adapters  │
                  └────────────┘
```

## Quick Start

```bash
# Use LangSmith (default)
export PLATFORM=langsmith
export LANGCHAIN_API_KEY=your-api-key

# Use Langfuse
export PLATFORM=langfuse
export LANGFUSE_PUBLIC_KEY=your-public-key
export LANGFUSE_SECRET_KEY=your-secret-key

# Use Weave (Weights & Biases)
export PLATFORM=weave
export WANDB_API_KEY=your-api-key  # Or use wandb login
```

```python
from shadowdance import ShadowDance

# Automatically uses the adapter based on PLATFORM env var
client = ShadowDance(my_client, run_type="tool")
```

## Available Adapters

### LangSmithAdapter

**Module:** `shadowdance.adapters.langsmith`

Full-featured observability by LangChain.

**Features:**
- Nested tracing with parent runs
- Dataset logging for evaluation
- Token usage and cost tracking
- Rich metadata support

**Environment Variables:**
```bash
LANGCHAIN_API_KEY=...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=your-project
```

**Usage:**
```bash
export PLATFORM=langsmith
```

---

### LangfuseAdapter

**Module:** `shadowdance.adapters.langfuse`

Open-source LLM observability platform.

**Features:**
- Nested tracing with parent spans
- Dataset logging for evaluation
- Token usage tracking
- Self-hosted or cloud deployment

**Environment Variables:**
```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional
```

**Usage:**
```bash
export PLATFORM=langfuse
```

---

### WeaveAdapter

**Module:** `shadowdance.adapters.weave`

Weights & Biases Weave for LLM observability.

**Features:**
- Automatic LLM call tracking (OpenAI, Cohere, LiteLLM)
- Custom tracing with `@weave.op()` decorator
- Hierarchical traces with parent/child calls
- Input/output logging with timestamps

**Environment Variables:**
```bash
WANDB_API_KEY=...
WANDB_ENTITY=your-entity  # Optional
WANDB_PROJECT=your-project  # Optional, defaults to "shadowdance"
```

**Usage:**
```bash
export PLATFORM=weave
```

**Note:** Requires `wandb` package: `pip install wandb`

---

### ExampleAdapter (Template)

**Module:** `shadowdance.adapters.example`

Template for creating custom adapters.

**Usage:**
```bash
cp shadowdance/adapters/example.py shadowdance/adapters/my_adapter.py
# Implement the methods
```

Then update `_get_adapter()` in `shadowdance/__init__.py`:

```python
from .adapters.my_adapter import MyAdapter

def _get_adapter():
    platform = os.environ.get("PLATFORM", "langsmith").lower()
    if platform == "my_backend":
        return MyAdapter()
    # ... other platforms
```

## Adapter Interface

All adapters implement `ObservabilityAdapter`:

```python
from shadowdance.adapters import ObservabilityAdapter, TraceEvent, DatasetExample

class MyCustomAdapter(ObservabilityAdapter):
    def capture_event(self, event: TraceEvent) -> Optional[str]:
        """Called when a traced method starts."""
        pass

    def complete_event(self, event_id: str, event: TraceEvent) -> None:
        """Called when a traced method finishes."""
        pass

    def update_event(self, event_id: str, metadata: dict) -> None:
        """Called to add metadata (usage, cost, etc.)."""
        pass

    def log_example(self, example: DatasetExample) -> None:
        """Called to log to a dataset."""
        pass

    def get_current_event(self) -> Optional[TraceEvent]:
        """Return current event for nesting (or None)."""
        pass

    def flush(self, timeout_ms: Optional[float] = None) -> None:
        """Flush queued events on shutdown."""
        pass
```

## Design Principles

### 1. Fire-and-Forget

Adapters send traces asynchronously. Observability **never blocks user code**.

```python
# In adapter implementation:
def capture_event(self, event: TraceEvent) -> Optional[str]:
    # Send in background thread
    threading.Thread(target=self._send, args=(event,), daemon=True).start()
    return event_id  # Return immediately
```

### 2. Timestamps Captured by ShadowDance

`TraceEvent` captures timestamps, not adapters. This ensures:
- **Accurate latency** measurement regardless of adapter implementation
- **Consistent behavior** across all backends
- **No clock skew** between capture and send

```python
# ShadowDance captures timestamps:
event = TraceEvent(name="Move", run_type="tool")  # start_time captured here
result = method(*args, **kwargs)
event.complete(outputs={"result": result})  # end_time captured here

# Adapter receives pre-timestamped event:
adapter.capture_event(event)  # Just send it, don't timestamp
```

### 3. Graceful Degradation

Adapters **never raise exceptions** to user code. Failures are logged at `DEBUG` level.

```python
def capture_event(self, event: TraceEvent) -> Optional[str]:
    try:
        # ... send event
        return event_id
    except Exception as e:
        logger.debug(f"Adapter: Failed to capture event: {e}")
        return None  # Drop trace gracefully
```

### 4. Drop Under Load

Under high load or network issues, traces may be dropped. This is **by design**:
- Observability should not affect application reliability
- Better to drop traces than block user code
- Production systems typically see >99% trace delivery anyway

## TraceEvent

The `TraceEvent` dataclass carries all trace data:

```python
from shadowdance.adapters import TraceEvent

event = TraceEvent(
    name="Move",
    run_type="tool",
    inputs={"args": (0.3, 0, 0), "kwargs": {}},
    parent_event=None,  # For nested traces
)

# Timestamps captured automatically:
print(event.start_time)  # perf_counter() when created

# Complete the event:
event.complete(outputs={"result": 0})
print(event.duration_ms)  # Calculated automatically
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Name of the traced operation |
| `run_type` | RunType | Type: tool, chain, llm, etc. |
| `inputs` | dict | Input arguments |
| `outputs` | dict | Output result |
| `error` | Exception | Error if one occurred |
| `metadata` | dict | Additional metadata |
| `start_time` | float | perf_counter() at start |
| `end_time` | float | perf_counter() at end |
| `duration_ms` | float | Calculated duration |
| `parent_event` | TraceEvent | Parent for nesting |

## DatasetExample

For logging examples to evaluation datasets:

```python
from shadowdance.adapters import DatasetExample

example = DatasetExample(
    dataset_name="robot-tasks",
    inputs={"method": "Move", "args": (0.3, 0, 0)},
    outputs={"result": 0, "success": True},
    metadata={"duration_ms": 12.5, "model": "gpt-4"},
)

adapter.log_example(example)
```

## Creating a Custom Adapter

### Step 1: Copy the Template

```bash
cp shadowdance/adapters/example.py shadowdance/adapters/my_backend.py
```

### Step 2: Implement the Methods

```python
# shadowdance/adapters/my_backend.py

from . import ObservabilityAdapter, TraceEvent, DatasetExample
import logging

logger = logging.getLogger(__name__)

class MyBackendAdapter(ObservabilityAdapter):
    def __init__(self):
        self._client = MyBackendClient(api_key="...")
        self._events = {}

    def capture_event(self, event: TraceEvent) -> Optional[str]:
        # Create trace in your backend
        trace = self._client.create_trace(
            name=event.name,
            type=event.run_type,
            input=event.inputs,
            metadata=event.metadata,
            timestamp=event.start_time,  # Use ShadowDance's timestamp
        )
        event_id = str(id(trace))
        self._events[event_id] = trace
        return event_id

    def complete_event(self, event_id: str, event: TraceEvent) -> None:
        trace = self._events.pop(event_id, None)
        if trace:
            trace.end(
                output=event.outputs,
                error=event.error,
                duration_ms=event.duration_ms,
            )

    def update_event(self, event_id: str, metadata: dict) -> None:
        trace = self._events.get(event_id)
        if trace:
            trace.metadata.update(metadata)

    def log_example(self, example: DatasetExample) -> None:
        dataset = self._client.get_dataset(example.dataset_name)
        dataset.add_example(
            input=example.inputs,
            output=example.outputs,
            metadata=example.metadata,
        )

    def get_current_event(self) -> Optional[TraceEvent]:
        # Return None if your backend doesn't support context
        return None

    def flush(self, timeout_ms: Optional[float] = None) -> None:
        self._client.flush(timeout=timeout_ms)
```

### Step 3: Register the Adapter

Edit `shadowdance/__init__.py`:

```python
from .adapters.my_backend import MyBackendAdapter

def _get_adapter():
    platform = os.environ.get("PLATFORM", "langsmith").lower()
    
    if platform == "my_backend":
        return MyBackendAdapter()
    elif platform == "langfuse":
        return LangfuseAdapter()
    # ...
```

### Step 4: Use It

```bash
export PLATFORM=my_backend
export MY_BACKEND_API_KEY=...
```

## Testing Your Adapter

```python
from shadowdance.adapters import ObservabilityAdapter, TraceEvent, DatasetExample

class MockAdapter(ObservabilityAdapter):
    def __init__(self):
        self.events = []
        self.examples = []

    def capture_event(self, event: TraceEvent) -> str:
        event_id = str(len(self.events))
        self.events.append((event_id, event))
        return event_id

    def complete_event(self, event_id: str, event: TraceEvent) -> None:
        pass

    def update_event(self, event_id: str, metadata: dict) -> None:
        pass

    def log_example(self, example: DatasetExample) -> None:
        self.examples.append(example)

    def get_current_event(self) -> Optional[TraceEvent]:
        return None

    def flush(self, timeout_ms: Optional[float] = None) -> None:
        pass

# Test it
adapter = MockAdapter()
event = TraceEvent(name="test", run_type="tool", inputs={"x": 1})
event_id = adapter.capture_event(event)
event.complete(outputs={"result": 42})
adapter.complete_event(event_id, event)
assert len(adapter.events) == 1
```

## Performance Considerations

### Latency

ShadowDance adds minimal latency:
- **Timestamp capture**: ~0.001ms (time.perf_counter())
- **Event creation**: ~0.01ms (dataclass instantiation)
- **Background send**: 0ms (fire-and-forget thread)

**Total overhead**: <0.1ms per traced call

### Memory

- Each `TraceEvent`: ~200 bytes
- Queued events: Depends on adapter (LangSmith/Langfuse send immediately)
- Under sustained high load: May queue briefly before sending

### Throughput

- **LangSmith**: ~1000 traces/sec (background threads)
- **Langfuse**: ~1000 traces/sec (built-in batching)
- **Custom**: Depends on your implementation

## Troubleshooting

### Traces Not Appearing

1. Check `PLATFORM` environment variable
2. Verify API keys are set
3. Check adapter logs at DEBUG level:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### High Latency

If you're seeing latency, it's likely **not** ShadowDance:
- ShadowDance sends in background threads
- Check network latency to observability backend
- Check if adapter is actually sending async

### Dropped Traces

Some trace loss is normal under load:
- Network issues
- Backend rate limiting
- High concurrency

If >1% traces drop, check:
- Network connectivity
- Backend API limits
- Consider increasing adapter's internal queue

## See Also

- [Main README](../README.md) - General ShadowDance documentation
- [LangSmith Docs](https://docs.smith.langchain.com/)
- [Langfuse Docs](https://langfuse.com/docs)
