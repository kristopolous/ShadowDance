"""
Pick Up Box Demo - Full Stack Robot Manipulation with ShadowDance.

This demo combines:
1. Vision: Detect the box in an image
2. Planning: Generate a step-by-step manipulation plan
3. Execution: Control the robot to execute the plan

All components are wrapped with ShadowDance for full LangSmith observability.

Usage:
    source .venv/bin/activate
    python examples/pick_up_box.py
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from shadowdance import ShadowDance

from examples.virtual_robot import VirtualRobotServer, VirtualRobotClient
from examples.vision import VisionSystem, DetectedObject
from examples.planner import TaskPlanner, ManipulationPlan

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")


class PickUpBoxAgent:
    """
    Agent that coordinates vision, planning, and execution.
    
    This agent is wrapped with ShadowDance to trace the full
    decision-making process.
    """
    
    def __init__(self, robot_client: VirtualRobotClient, 
                 vision_model: str = None,
                 planner_model: str = None):
        """
        Initialize the agent.
        
        Args:
            robot_client: The robot client to control.
            vision_model: Vision model identifier. Defaults to OPENAI_BASE_URL model.
            planner_model: Planning model identifier. Defaults to OPENAI_BASE_URL model.
        """
        self.robot = robot_client
        # Use environment model or mock
        default_model = os.environ.get("DEFAULT_MODEL", "mock")
        self.vision = VisionSystem(model=vision_model or default_model)
        self.planner = TaskPlanner(model=planner_model or default_model)
    
    def execute_task(self, task: str, image_path: str) -> bool:
        """
        Execute a manipulation task.
        
        Args:
            task: Natural language task description.
            image_path: Path to the image showing the scene.
            
        Returns:
            True if the task completed successfully.
        """
        print(f"\n=== Task: {task} ===")
        print(f"Image: {image_path}\n")
        
        # Step 1: Vision - detect objects
        print("--- Step 1: Vision ---")
        objects = self.vision.detect_objects(image_path)
        print(f"Detected {len(objects)} objects:")
        for obj in objects:
            print(f"  - {obj.name} (confidence: {obj.confidence:.2f})")
            if obj.position_3d:
                print(f"    Position: {obj.position_3d}")
        
        # Step 2: Planning - generate manipulation plan
        print("\n--- Step 2: Planning ---")
        context = {"detected_objects": objects}
        plan = self.planner.generate_plan(task, context)
        print(f"Generated plan with {len(plan.steps)} steps:")
        for i, step in enumerate(plan.steps):
            print(f"  {i+1}. {step.action}: {step.description}")
        
        # Step 3: Execution - execute the plan
        print("\n--- Step 3: Execution ---")
        success = self._execute_plan(plan)
        
        print(f"\n=== Task Complete: {'SUCCESS' if success else 'FAILED'} ===")
        return success
    
    def _execute_plan(self, plan: ManipulationPlan) -> bool:
        """Execute a manipulation plan on the robot."""
        for i, step in enumerate(plan.steps):
            print(f"\nExecuting step {i+1}/{len(plan.steps)}: {step.action}")
            
            try:
                # Execute based on action type
                if step.action == "stand_up":
                    self.robot.StandUp()
                
                elif step.action == "move_to_pregrasp":
                    params = step.parameters
                    self.robot.Move(params["vx"], params["vy"], params["vyaw"])
                
                elif step.action == "lower_arm":
                    # Simulated by small move
                    self.robot.Move(0.01, 0, 0)
                
                elif step.action == "close_gripper":
                    # Simulated pause for gripper action
                    time.sleep(0.5)
                    print("  Gripper closed")
                
                elif step.action == "lift_object":
                    # Simulated by standing up
                    self.robot.RecoveryStand()
                
                elif step.action == "return_to_start":
                    params = step.parameters
                    self.robot.Move(params["vx"], params["vy"], params["vyaw"])
                
                else:
                    print(f"  Unknown action: {step.action}")
                
                # Small delay between actions
                time.sleep(step.expected_duration * 0.5)
                
            except Exception as e:
                print(f"  Error executing step: {e}")
                return False
        
        return True


def main():
    """Run the pick up box demo with full ShadowDance tracing."""
    # Enable LangSmith tracing
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "shadowdance"
    
    print("=" * 60)
    print("ShadowDance: Pick Up Box Demo")
    print("=" * 60)
    print("\nThis demo traces the full stack:")
    print("  1. Vision (object detection)")
    print("  2. Planning (LLM decision making)")
    print("  3. Execution (robot control)")
    print("\nAll traced in LangSmith under project: shadowdance\n")
    
    # Start virtual robot
    server = VirtualRobotServer(verbose=True)
    server.start()
    
    robot = VirtualRobotClient(server)
    robot.Init()
    
    # Wrap robot with ShadowDance
    print("Wrapping robot with ShadowDance...")
    robot = ShadowDance(robot)
    
    # Create agent (also wrapped for tracing)
    print("Creating agent with ShadowDance...\n")
    agent = PickUpBoxAgent(robot, vision_model="mock", planner_model="mock")
    agent = ShadowDance(agent)
    
    # Get image path
    image_path = Path(__file__).parent.parent / "assets" / "box-on-table.jpg"
    
    if not image_path.exists():
        print(f"Warning: Image not found at {image_path}")
        print("Using mock vision data...")
    
    # Execute the task
    success = agent.execute_task(
        task="Pick up the white box from the table",
        image_path=str(image_path),
    )
    
    # Cleanup
    server.stop()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print(f"\nView traces at: https://smith.langchain.com")
    print(f"Project: shadowdance")
    print(f"\nYou should see:")
    print("  - execute_task (root trace)")
    print("    - detect_objects (vision)")
    print("    - generate_plan (planning)")
    print("    - _execute_plan (robot control)")
    print("      - StandUp, Move, RecoveryStand, etc.")


if __name__ == "__main__":
    main()
