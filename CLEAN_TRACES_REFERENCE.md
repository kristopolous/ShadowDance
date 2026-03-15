# Clean Trace Organization - Example Reference

This document shows the clean, hierarchical trace structure for each example.
Run any example and view the organized traces in LangSmith.

---

## 1. Investor Demo ⭐ (Best for presentations)

**Command:** `python examples/investor_demo.py`  
**Project:** `shadowdance-demo`

### Trace Hierarchy:

```
warehouse_pick_and_place (chain) [demo, warehouse, production]
├── perception_phase (chain) [vision]
│   └── [Vision processing simulated]
├── planning_phase (chain) [planning, llm]
│   └── [LLM generating plan]
├── execution_phase (chain) [control]
│   ├── StandUp (tool)
│   ├── Move (tool) ×5
│   └── Damp (tool)
└── return_phase (chain) [control]
    ├── Move (tool)
    └── Damp (tool)

quality_inspection (chain) [demo, inspection, qa]
├── inspection_setup (chain) [setup]
│   └── StandUp (tool)
├── inspect_point_1 (chain) [inspection]
│   └── Move (tool)
├── inspect_point_2 (chain) [inspection]
│   └── Move (tool)
├── inspect_point_3 (chain) [inspection]
│   └── Move (tool)
├── inspect_point_4 (chain) [inspection]
│   └── Move (tool)
└── generate_report (chain) [reporting]
    └── Damp (tool)

emergency_response (chain) [demo, safety, critical]
├── emergency_stop (chain) [safety, critical]
│   ├── Move(0,0,0) (tool)
│   └── Damp (tool)
└── status_report (chain) [reporting]
    └── [Incident logged]
```

---

## 2. Code-as-Policies

**Command:** `python examples/code_as_policies.py`  
**Project:** `shadowdance`

### Trace Hierarchy:

```
code_as_policies_task (chain) [llm, vision, demo]
├── vision_analysis (chain) [vision, llm]
│   └── analyze_scene (llm)
│       └── [VLM call to OpenRouter]
├── code_generation (chain) [planning, llm]
│   └── generate_code (llm)
│       └── [LLM call to OpenRouter]
└── code_execution (chain) [control, robot]
    ├── move_to (tool) ×4
    └── close_gripper (tool)
```

---

## 3. Robot Evaluation

**Command:** `python examples/robot_evaluation.py`  
**Project:** `shadowdance`

### Trace Hierarchy:

```
robot_evaluation (chain) [evaluation, testing]
├── eval_stand_up (chain) [task]
│   └── StandUp (tool)
├── eval_move_forward (chain) [task]
│   └── Move (tool)
├── eval_move_lateral (chain) [task]
│   └── Move (tool)
├── eval_rotate (chain) [task]
│   └── Move (tool)
└── eval_complex_sequence (chain) [task]
    ├── StandUp (tool)
    ├── Move (tool) ×3
    └── Damp (tool)
```

---

## 4. Nested Tracing

**Command:** `python examples/nested_tracing.py`  
**Project:** `shadowdance`

### Trace Hierarchy:

```
pick_up_box (chain) [manipulation, demo]
├── approach_and_grasp (chain) [control]
│   ├── StandUp (tool)
│   ├── Move (tool) ×2
│   └── Damp (tool)
└── release_and_return (chain) [control]
    └── [Task complete]

move_to_position (chain) [navigation, demo]
└── positioning (chain) [control]
    ├── StandUp (tool)
    ├── Move (tool)
    └── StopMove (tool)

complex_manipulation (chain) [complex, demo]
├── stand_up_sequence (chain) [control]
│   ├── StandUp (tool)
│   └── RecoveryStand (tool)
├── movement_pattern (chain) [navigation]
│   └── Move (tool) ×4
└── shutdown_sequence (chain) [control]
    ├── Damp (tool)
    └── StandDown (tool)
```

---

## 5. Simple Examples (No nesting - flat traces)

### openai_client.py
```
chat.completions.create (llm)
└── [OpenAI API call]
```

### basic.py
```
Damp (tool)
StandUp (tool)
Move (tool) ×2
RecoveryStand (tool)
```

---

## Key Benefits of Clean Organization

### Before (Flat):
```
Runs Dashboard:
├── Move (tool)
├── StandUp (tool)
├── Move (tool)
├── Damp (tool)
├── Move (tool)
└── Move (tool)
```
❌ Hard to understand context  
❌ Can't see which task commands belong to  
❌ Debugging requires guessing  

### After (Hierarchical):
```
Runs Dashboard:
├── warehouse_pick_and_place (chain)
│   ├── execution_phase
│   │   ├── StandUp (tool)
│   │   ├── Move (tool) ×5
│   │   └── Damp (tool)
│   └── return_phase
├── quality_inspection (chain)
│   ├── inspect_point_1, 2, 3, 4
│   └── generate_report
└── emergency_response (chain)
    └── emergency_stop
```
✅ Clear task context  
✅ Commands organized by phase  
✅ Debug specific tasks instantly  

---

## How to Add Clean Organization to Your Code

### Pattern 1: @task Decorator (for functions)

```python
from shadowdance import ShadowDance, task

@task("my_task", tags=["demo"])
def my_robot_task(robot):
    with task_context("phase_1", tags=["setup"]):
        robot.StandUp()
    
    with task_context("phase_2", tags=["control"]):
        robot.Move(0.3, 0, 0)
        robot.Damp()
```

### Pattern 2: task_context (for dynamic organization)

```python
from shadowdance import ShadowDance, task_context

for i, task_name in enumerate(tasks):
    with task_context(f"task_{i+1}", tags=["iteration"]):
        robot = ShadowDance(SportClient())
        robot.execute_task(task_name)
```

### Pattern 3: Class decorator

```python
from shadowdance import ShadowDance, task

@task("agent_task", tags=["agent"])
class MyAgent:
    def __init__(self):
        self.robot = ShadowDance(SportClient(), run_type="tool")
    
    def run(self):
        with task_context("perception", tags=["vision"]):
            # ...
```
