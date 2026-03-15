"""
Demonstrates nested tracing with @task decorator and task_context.

Shows how robot primitives are nested under task runs for better organization.

Usage:
    source .venv/bin/activate
    python examples/nested_tracing.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from shadowdance import ShadowDance, task, task_context
from examples.virtual_robot import VirtualRobotServer, VirtualRobotClient

load_dotenv(Path(__file__).parent.parent / ".env")


# ============================================================================
# Example 1: Using @task decorator (recommended)
# ============================================================================

@task("pick_up_box", tags=["manipulation", "demo"])
def pick_up_box(robot):
    """Pick up a box - all robot commands nested under this task."""
    print("\nExecuting: Pick up box task")
    
    with task_context("approach_and_grasp", tags=["control"]):
        robot.StandUp()
        robot.Move(0.3, 0, 0)
        robot.Move(0, 0.1, 0)
    
    with task_context("release_and_return", tags=["control"]):
        robot.Damp()
    
    print("Task complete!")
    return True


@task("move_to_position", tags=["navigation", "demo"])
def move_to_position(robot, x: float, y: float, yaw: float):
    """Move robot to specified position."""
    print(f"\nExecuting: Move to ({x}, {y}, {yaw})")
    
    with task_context("positioning", tags=["control"]):
        robot.StandUp()
        robot.Move(x, y, yaw)
        robot.StopMove()
    
    print("Position reached!")
    return True


# ============================================================================
# Example 2: Using task_context (for dynamic names)
# ============================================================================

def execute_custom_task(robot, task_name: str, commands: list):
    """Execute a custom task with dynamic name."""
    
    with task_context(task_name, tags=["custom"]):
        for cmd_name, args, kwargs in commands:
            method = getattr(robot, cmd_name)
            method(*args, **kwargs)


# ============================================================================
# Example 3: Nested tasks (tasks within tasks)
# ============================================================================

@task("complex_manipulation", tags=["complex", "demo"])
def complex_manipulation(robot):
    """Complex task with nested sub-tasks."""
    print("\nExecuting: Complex manipulation sequence")
    
    # Sub-task 1: Stand up
    with task_context("stand_up_sequence", tags=["control"]):
        robot.StandUp()
        robot.RecoveryStand()
    
    # Sub-task 2: Move in pattern
    with task_context("movement_pattern", tags=["navigation"]):
        robot.Move(0.2, 0, 0)
        robot.Move(0, 0.2, 0)
        robot.Move(-0.2, 0, 0)
        robot.Move(0, -0.2, 0)
    
    # Sub-task 3: Finish
    with task_context("shutdown_sequence", tags=["control"]):
        robot.Damp()
        robot.StandDown()
    
    print("Complex sequence complete!")
    return True


# ============================================================================
# Main demo
# ============================================================================

def main():
    """Run the nested tracing demo."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "shadowdance"
    
    print("\n" + "="*60)
    print("ShadowDance: Nested Tracing Demo")
    print("="*60)
    print("\nThis demonstrates:")
    print("  1. @task decorator for automatic nesting")
    print("  2. task_context for dynamic task names")
    print("  3. Nested tasks for complex operations")
    print("\nIn LangSmith you'll see:")
    print("  - pick_up_box (chain)")
    print("    └── StandUp, Move, Damp (tool)")
    print("  - move_to_position (chain)")
    print("    └── StandUp, Move, StopMove (tool)")
    print("  - complex_manipulation (chain)")
    print("    ├── stand_up_sequence")
    print("    ├── movement_pattern")
    print("    └── shutdown_sequence")
    
    # Start virtual robot
    server = VirtualRobotServer(verbose=False)
    server.start()
    
    try:
        # Create robot with ShadowDance
        robot = VirtualRobotClient(server)
        robot.Init()
        robot = ShadowDance(robot, run_type="tool")
        
        # Demo 1: @task decorator
        print("\n" + "-"*60)
        print("Demo 1: @task decorator")
        print("-"*60)
        pick_up_box(robot)
        
        # Demo 2: Another @task decorator
        print("\n" + "-"*60)
        print("Demo 2: @task with parameters")
        print("-"*60)
        move_to_position(robot, 0.5, 0.3, 0.1)
        
        # Demo 3: task_context
        print("\n" + "-"*60)
        print("Demo 3: task_context (dynamic)")
        print("-"*60)
        execute_custom_task(
            robot, 
            "custom_wave_pattern",
            [
                ("Move", (0.1, 0, 0), {}),
                ("Move", (0, 0.1, 0), {}),
                ("Damp", (), {}),
            ]
        )
        
        # Demo 4: Nested tasks
        print("\n" + "-"*60)
        print("Demo 4: Nested tasks")
        print("-"*60)
        complex_manipulation(robot)
        
    finally:
        server.stop()
    
    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60)
    print("\nView traces at: https://smith.langchain.com")
    print("Project: shadowdance")
    print("\nYou should see nested runs:")
    print("  ✓ pick_up_box → [StandUp, Move, Damp]")
    print("  ✓ move_to_position → [StandUp, Move, StopMove]")
    print("  ✓ custom_wave_pattern → [Move, Move, Damp]")
    print("  ✓ complex_manipulation → [stand_up_sequence, movement_pattern, shutdown_sequence]")
    print()


if __name__ == "__main__":
    main()
