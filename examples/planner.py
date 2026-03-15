"""
Task planner for robot manipulation.

This module uses a language model to generate step-by-step plans
for manipulation tasks like "pick up a box".
"""

import json
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


@dataclass
class PlanStep:
    """A single step in a manipulation plan."""
    action: str
    description: str
    parameters: dict
    expected_duration: float = 1.0  # seconds


@dataclass
class ManipulationPlan:
    """Complete plan for a manipulation task."""
    task: str
    steps: list[PlanStep]
    success_criteria: str


class TaskPlanner:
    """
    Generates manipulation plans using language models.
    
    Uses OpenAI-compatible APIs for planning.
    """
    
    def __init__(self, model: str = "mock"):
        """
        Initialize the planner.
        
        Args:
            model: Model identifier. Use "mock" for testing,
                   or an OpenAI-compatible model name for real planning.
        """
        self.model = model
        self._api_key = os.environ.get("OPENAI_API_KEY")
        self._api_base = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE")
    
    def generate_plan(self, task: str, context: dict) -> ManipulationPlan:
        """
        Generate a plan for the given task.
        
        Args:
            task: Natural language task description (e.g., "pick up the box")
            context: Additional context like detected objects, robot state, etc.
            
        Returns:
            A structured manipulation plan.
        """
        if self.model == "mock":
            return self._mock_plan(task, context)
        else:
            return self._real_plan(task, context)
    
    def _mock_plan(self, task: str, context: dict) -> ManipulationPlan:
        """Generate a mock plan for picking up a box."""
        print(f"  [Planner] Generating plan for: '{task}'")
        
        # Get object position from context if available
        objects = context.get("detected_objects", [])
        box_position = (0.3, 0.0, -0.15)  # Default position
        box_orientation = (0, 0.1, 0)
        
        for obj in objects:
            if "box" in obj.name.lower() and obj.position_3d:
                box_position = obj.position_3d
                box_orientation = obj.orientation or (0, 0.1, 0)
                break
        
        # Calculate grasp position (above the box)
        grasp_x = box_position[0]
        grasp_y = box_position[1]
        grasp_z = box_position[2] + 0.15  # 15cm above
        
        # Generate step-by-step plan
        steps = [
            PlanStep(
                action="stand_up",
                description="Robot stands up from rest position",
                parameters={},
                expected_duration=2.0,
            ),
            PlanStep(
                action="move_to_pregrasp",
                description="Move to pre-grasp position above the box",
                parameters={
                    "position": (grasp_x, grasp_y, grasp_z + 0.1),
                    "vx": 0.2, "vy": 0, "vyaw": 0,
                },
                expected_duration=1.5,
            ),
            PlanStep(
                action="lower_arm",
                description="Lower arm to grasp height",
                parameters={
                    "position": (grasp_x, grasp_y, grasp_z),
                },
                expected_duration=1.0,
            ),
            PlanStep(
                action="close_gripper",
                description="Close gripper to grasp the box",
                parameters={"grip_width": 0.08},
                expected_duration=0.5,
            ),
            PlanStep(
                action="lift_object",
                description="Lift the box to carry height",
                parameters={
                    "position": (grasp_x, grasp_y, grasp_z + 0.15),
                },
                expected_duration=1.0,
            ),
            PlanStep(
                action="return_to_start",
                description="Return to starting position",
                parameters={"vx": -0.2, "vy": 0, "vyaw": 0},
                expected_duration=1.5,
            ),
        ]
        
        return ManipulationPlan(
            task=task,
            steps=steps,
            success_criteria="Box is grasped and lifted successfully",
        )
    
    def _real_plan(self, task: str, context: dict) -> ManipulationPlan:
        """Generate a real plan using an LLM via OpenRouter."""
        import httpx
        from langsmith import get_current_run_tree

        print(f"  [Planner] Generating plan for: '{task}' using {self.model}")

        # Build object context
        objects_info = []
        for obj in context.get("detected_objects", []):
            objects_info.append({
                "name": obj.name,
                "position_3d": obj.position_3d,
                "confidence": obj.confidence,
            })

        # Prompt for planning
        prompt = f"""You are a robot manipulation planner. Generate a step-by-step plan for the task.

Task: {task}

Detected objects in the scene:
{json.dumps(objects_info, indent=2)}

Available robot actions:
- stand_up: Robot stands up from rest position
- move_to_pregrasp: Move to position above object (use Move with vx, vy, vyaw)
- lower_arm: Lower arm to grasp height
- close_gripper: Close gripper to grasp object
- lift_object: Lift the object up
- return_to_start: Return to starting position

Respond in JSON format:
{{
  "steps": [
    {{"action": "action_name", "description": "...", "parameters": {{}}, "expected_duration": 1.0}}
  ],
  "success_criteria": "..."
}}"""

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            # OpenRouter headers for pricing/cost tracking
            "HTTP-Referer": "https://github.com/kristopolous/ShadowDance",
            "X-Title": "ShadowDance",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
        }

        url = f"{self._api_base}/chat/completions"

        try:
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=payload, timeout=30.0)
                response.raise_for_status()
                result = response.json()
            
            # Extract usage stats from OpenRouter response
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            # Get cost from OpenRouter (they provide it directly!)
            cost = usage.get("cost", 0)  # Cost in USD
            
            print(f"  [Planner] Tokens: {prompt_tokens} in, {completion_tokens} out, {total_tokens} total")
            print(f"  [Planner] Cost: ${cost:.6f}")
            
            # Log usage to LangSmith
            try:
                run = get_current_run_tree()
                if run:
                    # Build usage metadata in LangSmith format
                    usage_metadata = {
                        "input_tokens": prompt_tokens,
                        "output_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                    }
                    
                    # Include cost if available
                    if cost > 0:
                        usage_metadata["output_cost"] = cost
                    
                    # Include token details if available
                    if "prompt_tokens_details" in usage:
                        details = usage["prompt_tokens_details"]
                        usage_metadata["input_token_details"] = details
                    
                    if "completion_tokens_details" in usage:
                        details = usage["completion_tokens_details"]
                        usage_metadata["output_token_details"] = details
                    
                    run.set(usage_metadata=usage_metadata)
                    print(f"  [Planner] ✓ Logged usage to LangSmith")
            except Exception as e:
                print(f"  [Planner] Warning: Could not log usage to LangSmith: {e}")

            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(content[start:end])
                
                steps = [
                    PlanStep(
                        action=step.get("action", "unknown"),
                        description=step.get("description", ""),
                        parameters=step.get("parameters", {}),
                        expected_duration=step.get("expected_duration", 1.0),
                    )
                    for step in data.get("steps", [])
                ]
                
                return ManipulationPlan(
                    task=task,
                    steps=steps,
                    success_criteria=data.get("success_criteria", "Task completed"),
                )
        except Exception as e:
            print(f"  [Planner] Error: {e}")
            print("  Falling back to mock plan")
            return self._mock_plan(task, context)
    
    def validate_plan(self, plan: ManipulationPlan, robot_capabilities: list) -> bool:
        """
        Check if the plan is executable by the robot.
        
        Args:
            plan: The plan to validate.
            robot_capabilities: List of actions the robot can perform.
            
        Returns:
            True if the plan is valid.
        """
        for step in plan.steps:
            if step.action not in robot_capabilities:
                print(f"  [Planner] Warning: Robot cannot perform '{step.action}'")
                return False
        return True
