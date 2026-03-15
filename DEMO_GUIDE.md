# ShadowDance Investor Demo Guide

## Quick Start (5 minutes)

### 1. Run the Demo

```bash
cd /path/to/ShadowDance
source .venv/bin/activate
python examples/investor_demo.py
```

### 2. Open LangSmith

Navigate to: **https://smith.langchain.com**

### 3. View the Demo Project

- **Project:** `shadowdance-demo`
- You'll see 3 task runs appear in real-time

---

## What You'll See

### Task 1: Warehouse Pick and Place

```
warehouse_pick_and_place (chain) - 2.5s
├── perception_phase (llm) - 200ms
│   └── [Vision processing simulated]
├── planning_phase (llm) - 200ms
│   └── [LLM generating plan]
├── execution_phase (chain) - 1.2s
│   ├── StandUp (tool) - 100ms
│   ├── Move (tool) - 100ms ×5
│   └── Damp (tool) - 100ms
└── return_phase (chain) - 300ms
    └── Move (tool), Damp (tool)
```

**Key Point:** Every robot command is automatically traced with inputs, outputs, and timing.

---

### Task 2: Quality Inspection

```
quality_inspection (chain) - 1.8s
├── inspection_setup - 100ms
│   └── StandUp (tool)
├── inspect_point_1 (tool) - 150ms
├── inspect_point_2 (tool) - 150ms
├── inspect_point_3 (tool) - 150ms
├── inspect_point_4 (tool) - 150ms
└── generate_report - 100ms
    └── Damp (tool)
```

**Key Point:** Loops and iterations are clearly organized - debug specific inspection points.

---

### Task 3: Emergency Response

```
emergency_response (chain) - 150ms
├── emergency_stop (safety) - 50ms
│   ├── Move(0,0,0) (tool)
│   └── Damp (tool)
└── status_report - 100ms
    └── [Incident logged]
```

**Key Point:** Safety-critical events are prominently logged for compliance and debugging.

---

## Investor Talking Points

### Problem
- Robot systems are **black boxes** - impossible to debug
- No visibility into **why** robots made decisions
- Production issues take **hours** to diagnose
- Safety incidents are **untraceable**

### Solution: ShadowDance
- **One line** of code adds full observability
- **Automatic tracing** - no manual instrumentation
- **Hierarchical organization** - see the forest AND the trees
- **LLM + Robot** tracing in one dashboard

### Value Proposition
- **Debug faster:** Find root causes in minutes, not hours
- **Compliance ready:** Full audit trail of all robot actions
- **LLM observability:** See what the AI decided and why
- **Production proven:** Built on LangSmith, used by thousands

---

## Live Demo Script

### Opening (30 seconds)
> "Today's robot systems are black boxes. When something goes wrong, you have no idea why. Let me show you how ShadowDance fixes that with one line of code."

### Run Demo (1 minute)
> "I'm running a warehouse automation task. Watch what happens in LangSmith..."

*[Run `python examples/investor_demo.py`]*

### Show LangSmith (2 minutes)
> "Here's the trace. At the top level, you see the task: 'warehouse_pick_and_place'. Click into it..."

*[Click into warehouse_pick_and_place]*

> "You can see each phase: perception, planning, execution. Now click into execution_phase..."

*[Click into execution_phase]*

> "Every robot command is here: StandUp, Move, Damp. Click on any Move to see exact parameters..."

*[Click on a Move command]*

> "Inputs, outputs, timing - everything you need to debug. Now imagine this is your production robot that stopped working at 2 AM. Instead of guessing, you **know** exactly what happened."

### Close (30 seconds)
> "One line of code. Full observability. That's ShadowDance."

---

## FAQ

**Q: Does this work with real robots?**  
A: Yes! The demo uses a virtual robot, but swap in Unitree, Franka, or any ROS-based robot and it just works.

**Q: What about LLMs?**  
A: ShadowDance traces both. Wrap your OpenAI/Anthropic calls the same way - see the full decision chain from LLM reasoning to robot action.

**Q: Is this production-ready?**  
A: Yes, built on LangSmith which processes millions of traces daily. Just shipped v0.3.0 to PyPI.

**Q: How much does it cost?**  
A: ShadowDance is MIT licensed (free). LangSmith has a generous free tier, then usage-based pricing.

---

## Contact

- **PyPI:** https://pypi.org/project/shadowdance/
- **GitHub:** https://github.com/kristopolous/ShadowDance
- **Demo Video:** [Add link if you record one]
