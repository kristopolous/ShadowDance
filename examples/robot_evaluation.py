"""
Robot Evaluation with Datasets and Experiments.

This example shows how to:
1. Create a dataset of robot tasks
2. Run experiments to evaluate robot performance
3. Compare different robot configurations

Usage:
    source .venv/bin/activate
    python examples/robot_evaluation.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from shadowdance import ShadowDance, task, task_context
from examples.virtual_robot import VirtualRobotServer, VirtualRobotClient

load_dotenv(Path(__file__).parent.parent / ".env")


# ============================================================================
# Step 1: Define evaluation tasks
# ============================================================================

EVALUATION_TASKS = [
    {
        "name": "stand_up",
        "description": "Robot should stand up from rest position",
        "commands": [("StandUp", {}, 0)],  # (method, kwargs, expected_result)
    },
    {
        "name": "move_forward",
        "description": "Robot should move forward 0.3 m/s",
        "commands": [("Move", {"vx": 0.3, "vy": 0, "vyaw": 0}, 0)],
    },
    {
        "name": "move_lateral",
        "description": "Robot should move sideways 0.2 m/s",
        "commands": [("Move", {"vx": 0, "vy": 0.2, "vyaw": 0}, 0)],
    },
    {
        "name": "rotate",
        "description": "Robot should rotate in place",
        "commands": [("Move", {"vx": 0, "vy": 0, "vyaw": 0.5}, 0)],
    },
    {
        "name": "complex_sequence",
        "description": "Robot should execute a sequence of commands",
        "commands": [
            ("StandUp", {}, 0),
            ("Move", {"vx": 0.2, "vy": 0, "vyaw": 0}, 0),
            ("Move", {"vx": 0, "vy": 0.1, "vyaw": 0}, 0),
            ("Damp", {}, 0),
        ],
    },
]


# ============================================================================
# Step 2: Run evaluation against dataset
# ============================================================================

@task("robot_evaluation", tags=["evaluation", "testing"])
def run_evaluation(robot, dataset_name: str = "robot-evaluation"):
    """
    Run evaluation tasks and log results to dataset.
    
    Args:
        robot: ShadowDance-wrapped robot client
        dataset_name: Name of dataset for experiments
    """
    print(f"\n{'='*60}")
    print(f"Running Evaluation: {dataset_name}")
    print(f"{'='*60}\n")
    
    results = []
    
    for task in EVALUATION_TASKS:
        with task_context(f"eval_{task['name']}", tags=["task"]):
            print(f"Task: {task['name']} - {task['description']}")
            
            task_success = True
            task_results = []
            
            for method_name, kwargs, expected in task["commands"]:
                try:
                    method = getattr(robot, method_name)
                    result = method(**kwargs)
                    success = result == expected
                    task_results.append({
                        "method": method_name,
                        "success": success,
                        "result": result,
                        "expected": expected,
                    })
                    if not success:
                        task_success = False
                        print(f"  ✗ {method_name}: got {result}, expected {expected}")
                    else:
                        print(f"  ✓ {method_name}: {result}")
                        
                except Exception as e:
                    task_success = False
                    task_results.append({
                        "method": method_name,
                        "success": False,
                        "error": str(e),
                    })
                    print(f"  ✗ {method_name}: ERROR - {e}")
            
            results.append({
                "task": task["name"],
                "success": task_success,
                "results": task_results,
            })
            print()
    
    # Summary
    total_tasks = len(results)
    successful_tasks = sum(1 for r in results if r["success"])
    
    print(f"{'='*60}")
    print(f"Evaluation Complete: {successful_tasks}/{total_tasks} tasks passed")
    print(f"{'='*60}\n")
    
    return results


# ============================================================================
# Step 3: Compare configurations
# ============================================================================

def compare_configurations():
    """Compare different robot configurations using experiments."""
    print("\n" + "="*60)
    print("Robot Configuration Comparison")
    print("="*60)
    
    # Start virtual robot
    server = VirtualRobotServer(verbose=False)
    server.start()
    
    try:
        # Configuration 1: Standard (traced with dataset)
        print("\n--- Configuration 1: Standard (with dataset logging) ---")
        robot1 = VirtualRobotClient(server)
        robot1.Init()
        robot1 = ShadowDance(robot1, run_type="tool", log_to_dataset="robot-eval-v1")
        results1 = run_evaluation(robot1, "robot-eval-v1")
        
        # Configuration 2: You could test different parameters, versions, etc.
        print("\n--- Configuration 2: Alternative (with dataset logging) ---")
        robot2 = VirtualRobotClient(server)
        robot2.Init()
        robot2 = ShadowDance(robot2, run_type="tool", log_to_dataset="robot-eval-v2")
        results2 = run_evaluation(robot2, "robot-eval-v2")
        
        # Compare results
        print("\n" + "="*60)
        print("Comparison Summary")
        print("="*60)
        
        v1_success = sum(1 for r in results1 if r["success"])
        v2_success = sum(1 for r in results2 if r["success"])
        
        print(f"Configuration 1: {v1_success}/{len(results1)} tasks")
        print(f"Configuration 2: {v2_success}/{len(results2)} tasks")
        
        if v1_success > v2_success:
            print("→ Configuration 1 performed better")
        elif v2_success > v1_success:
            print("→ Configuration 2 performed better")
        else:
            print("→ Both configurations performed equally")
        
    finally:
        server.stop()
    
    print("\n" + "="*60)
    print("View datasets and experiments at: https://smith.langchain.com")
    print("Datasets created:")
    print("  - robot-eval-v1")
    print("  - robot-eval-v2")
    print("\nYou can now:")
    print("  1. View individual task executions")
    print("  2. Compare runs across experiments")
    print("  3. Add more test cases to the dataset")
    print("  4. Run regression tests on code changes")
    print("="*60 + "\n")


def main():
    """Run the robot evaluation demo."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "shadowdance"
    
    print("\n" + "="*60)
    print("ShadowDance: Robot Evaluation with Datasets")
    print("="*60)
    print("\nThis demonstrates:")
    print("  1. Creating datasets of robot tasks")
    print("  2. Logging executions for experiments")
    print("  3. Comparing robot configurations")
    print("\nIn LangSmith you can:")
    print("  - View all task executions in the dataset")
    print("  - Run experiments to evaluate changes")
    print("  - Compare success rates across versions")
    print()
    
    compare_configurations()
    
    return 0


if __name__ == "__main__":
    exit(main())
