"""
Realistic LLM Robot Stack Demo.

This shows how modern robot systems actually work:

1. LLM parses natural language task → high-level plan
2. VLM analyzes image → object locations  
3. Traditional controller executes motions
4. Feedback loop monitors progress

All traced via ShadowDance for debugging/observability.

Usage:
    source .venv/bin/activate
    python examples/llm_robot_stack.py
"""

import os
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from shadowdance import ShadowDance

load_dotenv(Path(__file__).parent.parent / ".env")


# ============================================================================
# Layer 1: Perception (VLM)
# ============================================================================

@dataclass
class ObjectDetection:
    """Detected object with 3D position."""
    name: str
    position: tuple  # (x, y, z) in meters
    confidence: float


class PerceptionSystem:
    """
    Vision system that analyzes camera images.
    
    In real systems, this might be:
    - A VLM (GPT-4V, Claude, etc.)
    - Traditional CV (YOLO, etc.)
    - Depth camera + segmentation
    """
    
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self._call_count = 0
    
    def analyze_scene(self, image_path: str, query: str) -> list[ObjectDetection]:
        """
        Analyze image to find objects relevant to the task.
        
        Args:
            image_path: Path to camera image
            query: What to look for (e.g., "objects to pick up")
        """
        self._call_count += 1
        print(f"  [Perception] Analyzing scene: '{query}'")
        
        if self.use_llm:
            # Would call VLM here
            print(f"    → Would call VLM with image: {image_path}")
        
        # For demo: return mock detection based on known image
        if "box" in image_path:
            return [
                ObjectDetection("white_box", (0.30, 0.0, -0.15), 0.95),
                ObjectDetection("table", (0.5, 0.0, -0.30), 0.99),
            ]
        return []
    
    def get_robot_pose(self) -> tuple:
        """Get current robot end-effector pose."""
        # In reality: read from robot state
        return (0.0, 0.0, 0.0)


# ============================================================================
# Layer 2: Task Planning (LLM)
# ============================================================================

class TaskPlanner:
    """
    LLM that translates natural language to robot actions.
    
    Real systems: SayCan, PaLM-E, RT-2, etc.
    """
    
    def __init__(self):
        self._call_count = 0
    
    def parse_task(self, task: str, context: dict) -> dict:
        """
        Parse natural language task into executable plan.
        
        Example:
            Input: "pick up the white box"
            Output: {
                "action": "pick",
                "target": "white_box",
                "grasp_pose": [0.3, 0.0, -0.05],
                "pregrasp": [0.3, 0.0, 0.1],
            }
        """
        self._call_count += 1
        print(f"  [Planner] Parsing: '{task}'")
        
        # In reality: LLM call with task + scene description
        # For demo: rule-based parsing
        
        if "pick" in task.lower() and "box" in task.lower():
            return {
                "action": "pick",
                "target": "white_box",
                "phases": [
                    "move_to_pregrasp",
                    "approach_object", 
                    "close_gripper",
                    "lift_object",
                ],
                "grasp_pose": [0.30, 0.0, -0.05],
                "pregrasp_pose": [0.30, 0.0, 0.10],
            }
        
        return {"action": "unknown", "phases": []}


# ============================================================================
# Layer 3: Low-Level Control
# ============================================================================

class RobotController:
    """
    Low-level robot controller.
    
    Executes trajectories, monitors joint states, handles safety.
    """
    
    def __init__(self):
        self.position = (0.0, 0.0, 0.0)
        self.gripper_open = True
        self._executed_actions = []
    
    def move_to(self, position: tuple, speed: float = 0.1) -> bool:
        """Move end-effector to position."""
        print(f"  [Controller] Moving to {position}")
        self.position = position
        self._executed_actions.append(("move", position))
        time.sleep(0.1)  # Simulate motion
        return True
    
    def close_gripper(self, width: float = 0.0) -> bool:
        """Close gripper."""
        print(f"  [Controller] Closing gripper to {width}m")
        self.gripper_open = False
        self._executed_actions.append(("grip_close", width))
        time.sleep(0.05)
        return True
    
    def open_gripper(self) -> bool:
        """Open gripper."""
        print(f"  [Controller] Opening gripper")
        self.gripper_open = True
        self._executed_actions.append(("grip_open",))
        return True
    
    def get_state(self) -> dict:
        """Get robot state."""
        return {
            "position": self.position,
            "gripper_open": self.gripper_open,
        }


# ============================================================================
# Layer 4: High-Level Agent (orchestrates everything)
# ============================================================================

class PickAndPlaceAgent:
    """
    High-level agent that coordinates perception, planning, and control.
    
    This is what you'd actually use ShadowDance on.
    """
    
    def __init__(self):
        self.perception = PerceptionSystem(use_llm=True)
        self.planner = TaskPlanner()
        self.controller = RobotController()
    
    def execute(self, task: str, image_path: str) -> bool:
        """
        Execute a pick-and-place task.
        
        Args:
            task: Natural language task
            image_path: Camera image of scene
            
        Returns:
            True if successful
        """
        print(f"\n{'='*60}")
        print(f"Task: {task}")
        print(f"{'='*60}\n")
        
        # Step 1: Perceive the scene
        print("Step 1: Perception")
        objects = self.perception.analyze_scene(
            image_path, 
            "Find objects mentioned in the task"
        )
        print(f"  Found {len(objects)} objects:")
        for obj in objects:
            print(f"    - {obj.name} at {obj.position}")
        
        # Step 2: Plan the action
        print("\nStep 2: Planning")
        context = {"objects": objects, "image": image_path}
        plan = self.planner.parse_task(task, context)
        print(f"  Plan: {plan['action']}")
        print(f"  Phases: {plan.get('phases', [])}")
        
        # Step 3: Execute the plan
        print("\nStep 3: Execution")
        success = self._execute_plan(plan, objects)
        
        # Step 4: Verify
        print("\nStep 4: Verification")
        final_state = self.controller.get_state()
        print(f"  Final state: {final_state}")
        
        print(f"\n{'='*60}")
        print(f"Result: {'SUCCESS' if success else 'FAILED'}")
        print(f"{'='*60}\n")
        
        return success
    
    def _execute_plan(self, plan: dict, objects: list) -> bool:
        """Execute the planned actions."""
        if plan["action"] != "pick":
            print("  Unknown action type")
            return False
        
        # Find target object
        target = None
        for obj in objects:
            if obj.name == plan.get("target"):
                target = obj
                break
        
        if not target:
            print(f"  Target '{plan.get('target')}' not found")
            return False
        
        # Execute pick sequence
        pregrasp = plan.get("pregrasp_pose", [0.3, 0.0, 0.1])
        grasp = plan.get("grasp_pose", [0.3, 0.0, -0.05])
        
        # Phase 1: Move to pre-grasp
        print("\n  Phase 1: Move to pre-grasp position")
        self.controller.move_to(tuple(pregrasp))
        
        # Phase 2: Approach object
        print("\n  Phase 2: Approach object")
        self.controller.move_to(tuple(grasp), speed=0.05)
        
        # Phase 3: Close gripper
        print("\n  Phase 3: Close gripper")
        self.controller.close_gripper(width=0.08)
        
        # Phase 4: Lift
        print("\n  Phase 4: Lift object")
        lift_pose = (grasp[0], grasp[1], grasp[2] + 0.15)
        self.controller.move_to(lift_pose)
        
        return True


def main():
    """Run the full LLM robot stack demo."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "shadowdance"
    
    print("\n" + "="*60)
    print("ShadowDance: LLM Robot Stack Demo")
    print("="*60)
    print("\nThis demonstrates a realistic LLM robot architecture:")
    print("  1. Perception (VLM) - analyze camera image")
    print("  2. Planning (LLM) - parse task to actions")
    print("  3. Control - execute trajectories")
    print("  4. Agent - orchestrate everything")
    print("\nAll wrapped with ShadowDance for observability.\n")
    
    # Create agent and wrap with ShadowDance
    agent = PickAndPlaceAgent()
    agent = ShadowDance(agent)  # ONE LINE
    
    # Get image path
    image_path = Path(__file__).parent.parent / "assets" / "box-on-table.jpg"
    
    # Execute task
    success = agent.execute(
        task="Pick up the white box from the table",
        image_path=str(image_path),
    )
    
    print("\nView traces at: https://smith.langchain.com")
    print("Project: shadowdance\n")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
