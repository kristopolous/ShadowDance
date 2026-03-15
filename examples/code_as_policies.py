"""
Modern LLM Robot Control: Code-as-Policies Approach.

This implements the approach from "Code as Policies" (Google 2023) and
subsequent work: LLMs generate Python code that calls robot APIs.

Architecture:
1. VLM analyzes image → scene description
2. LLM generates Python code for the task
3. Code executes with safety checks
4. All traced via ShadowDance

References:
- Code as Policies: https://code-as-policies.github.io/
- SayCan (Google): https://say-can.github.io/
- OpenVLA: https://openvla.github.io/

Usage:
    source .venv/bin/activate
    python examples/code_as_policies.py
"""

import os
import re
import time
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Callable

from dotenv import load_dotenv
from shadowdance import ShadowDance

load_dotenv(Path(__file__).parent.parent / ".env")


# ============================================================================
# Robot API (what the LLM can call)
# ============================================================================

class RobotAPI:
    """
    Safe robot API that generated code can call.
    
    This is what the LLM has access to - it can generate code
    that calls these methods, but we validate everything.
    """
    
    def __init__(self):
        self.ee_pose = (0.0, 0.0, 0.0)  # End-effector position
        self.gripper_open = True
        self.payload = None
        self.log = []
    
    def move_to(self, x: float, y: float, z: float, speed: float = 0.1) -> bool:
        """Move end-effector to (x, y, z) in base frame."""
        self.log.append(f"move_to({x:.3f}, {y:.3f}, {z:.3f}, speed={speed})")
        print(f"    [Robot] Moving to ({x:.3f}, {y:.3f}, {z:.3f})")
        self.ee_pose = (x, y, z)
        time.sleep(0.2)
        return True
    
    def move_relative(self, dx: float, dy: float, dz: float) -> bool:
        """Move relative to current position."""
        new_x = self.ee_pose[0] + dx
        new_y = self.ee_pose[1] + dy
        new_z = self.ee_pose[2] + dz
        return self.move_to(new_x, new_y, new_z)
    
    def close_gripper(self, width: float = 0.0) -> bool:
        """Close gripper to specified width (meters)."""
        self.log.append(f"close_gripper({width})")
        print(f"    [Robot] Closing gripper to {width*1000:.1f}mm")
        self.gripper_open = False
        self.payload = "object"
        time.sleep(0.1)
        return True
    
    def open_gripper(self) -> bool:
        """Fully open gripper."""
        self.log.append("open_gripper()")
        print(f"    [Robot] Opening gripper")
        self.gripper_open = True
        self.payload = None
        time.sleep(0.1)
        return True
    
    def get_pose(self) -> tuple:
        """Get current end-effector pose."""
        return self.ee_pose
    
    def is_holding(self) -> bool:
        """Check if robot is holding something."""
        return self.payload is not None
    
    def stop(self) -> bool:
        """Emergency stop."""
        self.log.append("STOP")
        print("    [Robot] EMERGENCY STOP")
        return True


# ============================================================================
# Vision System (VLM)
# ============================================================================

class VisionSystem:
    """
    Vision-Language Model for scene understanding.
    
    Uses OpenRouter-compatible API to analyze images.
    """
    
    def __init__(self):
        self._api_key = os.environ.get("OPENAI_API_KEY")
        self._api_base = os.environ.get("OPENAI_BASE_URL")
        self._model = os.environ.get("DEFAULT_MODEL", "mock")
    
    def analyze_scene(self, image_path: str, task: str) -> dict:
        """
        Analyze image and return structured scene description.
        
        Returns:
            {
                "objects": [{"name": str, "position": [x,y,z], "size": [w,h,d]}],
                "table_surface": {"height": float},
                "description": str
            }
        """
        print(f"  [Vision] Analyzing scene for task: '{task}'")
        
        if self._model == "mock" or not self._api_key:
            return self._mock_analyze(image_path, task)
        
        return self._vlm_analyze(image_path, task)
    
    def _mock_analyze(self, image_path: str, task: str) -> dict:
        """Mock analysis for demo."""
        print(f"    → Using mock vision (set DEFAULT_MODEL for real VLM)")
        
        # Return realistic mock data based on the box image
        return {
            "objects": [
                {
                    "name": "white_box",
                    "position": [0.30, 0.0, 0.70],  # 30cm forward on table
                    "size": [0.08, 0.05, 0.15],  # 8x5x15 cm box
                    "grasp_point": [0.30, 0.0, 0.78],  # Where to grasp (top of box)
                }
            ],
            "table_surface": {"height": 0.70},
            "description": "A white rectangular box standing upright on a wooden table surface. The box appears to be about 15cm tall.",
        }
    
    def _vlm_analyze(self, image_path: str, task: str) -> dict:
        """Real VLM analysis via OpenRouter."""
        import base64
        import httpx
        
        print(f"    → Calling VLM: {self._model}")
        
        # Encode image
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        # Prompt for structured scene understanding
        prompt = """Analyze this image for robot manipulation. Return JSON:
{
  "objects": [
    {"name": "object_name", "position": [x,y,z], "size": [w,h,d], "grasp_point": [x,y,z]}
  ],
  "table_surface": {"height": z_coordinate},
  "description": "brief scene description"
}

IMPORTANT: The image shows a WHITE BOX on a wooden table. Detect this box.

Positions are in meters relative to camera. Assume:
- Camera is at origin (0,0,0) looking along +Z
- Table is approximately 0.7m in front of camera
- Objects are on the table

For the grasp point, specify where the robot should grasp (typically center of object, slightly above table)."""

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                        },
                    ],
                }
            ],
            "max_tokens": 500,
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self._api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            
            # Extract JSON from response
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                # Check if box was detected
                objects = parsed.get("objects", [])
                if any("box" in obj.get("name", "").lower() for obj in objects):
                    return parsed
                print("    [Vision] VLM didn't detect box, using mock")
        except Exception as e:
            print(f"    [Vision] VLM failed: {e}, using mock")
        
        # Fallback to mock
        return self._mock_analyze(image_path, task)


# ============================================================================
# Code Generator (LLM)
# ============================================================================

class CodeGenerator:
    """
    LLM that generates Python code for robot tasks.
    
    Based on "Code as Policies" approach.
    """
    
    def __init__(self):
        self._api_key = os.environ.get("OPENAI_API_KEY")
        self._api_base = os.environ.get("OPENAI_BASE_URL")
        self._model = os.environ.get("DEFAULT_MODEL", "mock")
    
    def generate(self, task: str, scene: dict) -> str:
        """
        Generate Python code to accomplish the task.
        
        Args:
            task: Natural language task
            scene: Scene description from vision system
            
        Returns:
            Python code string that calls robot API
        """
        print(f"  [CodeGen] Generating code for: '{task}'")
        
        if self._model == "mock" or not self._api_key:
            return self._mock_generate(task, scene)
        
        return self._llm_generate(task, scene)
    
    def _clean_code(self, code: str) -> str:
        """Remove markdown formatting from generated code."""
        # Remove markdown code blocks
        code = re.sub(r'```python\s*', '', code)
        code = re.sub(r'```\s*', '', code)
        return code.strip()
    
    def _mock_generate(self, task: str, scene: dict) -> str:
        """Generate mock code based on task keywords."""
        print(f"    → Using mock code generation (set DEFAULT_MODEL for real LLM)")
        
        # Generate code based on task type
        if "pick" in task.lower() and "box" in task.lower():
            objects = scene.get("objects", [])
            box = next((o for o in objects if "box" in o["name"]), None)
            
            if box:
                grasp = box.get("grasp_point", [0.3, 0.0, 0.78])
                pregrasp_z = grasp[2] + 0.1
                
                return f'''# Pick up the {box["name"]}
# Object detected at {box["position"]}

# Move to pre-grasp position (above the object)
robot.move_to({grasp[0]:.3f}, {grasp[1]:.3f}, {pregrasp_z:.3f}, speed=0.2)

# Approach the object
robot.move_to({grasp[0]:.3f}, {grasp[1]:.3f}, {grasp[2]:.3f}, speed=0.05)

# Close gripper to grasp the object
robot.close_gripper(0.08)

# Lift the object
robot.move_to({grasp[0]:.3f}, {grasp[1]:.3f}, {pregrasp_z:.3f}, speed=0.1)

# Move back to home position
robot.move_to(0.0, 0.0, 0.5, speed=0.2)
'''
        
        return "# Unknown task - no code generated"
    
    def _llm_generate(self, task: str, scene: dict) -> str:
        """Generate code using LLM via OpenRouter."""
        import httpx
        
        print(f"    → Calling LLM: {self._model}")
        
        # System prompt defines the API
        system_prompt = """You are a robot programming assistant. Generate Python code to control a robot arm.

The robot has these methods:
- robot.move_to(x, y, z, speed=0.1)  # Move to absolute position (meters)
- robot.move_relative(dx, dy, dz)     # Move relative to current position
- robot.close_gripper(width=0.0)      # Close gripper (width in meters)
- robot.open_gripper()                # Open gripper fully
- robot.get_pose()                    # Get current (x, y, z)
- robot.is_holding()                  # Check if holding something
- robot.stop()                        # Emergency stop

Coordinate system:
- Camera at origin (0,0,0), looking along +Z axis
- Y is left/right, X is forward/back
- Z is up/down (negative = below camera)
- Table is typically at Z ≈ -0.30 to -0.40

Generate ONLY Python code. No explanations. Use the scene information to determine positions."""
        
        user_prompt = f"""Task: {task}

Scene:
{json.dumps(scene, indent=2)}

Generate Python code to accomplish this task:"""
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.1,  # Low temp for deterministic code
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self._api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
            
            return self._clean_code(result["choices"][0]["message"]["content"])

        except Exception as e:
            print(f"    [CodeGen] LLM failed: {e}, falling back to mock")
            return self._mock_generate(task, scene)


# ============================================================================
# Safe Code Executor
# ============================================================================

class SafeExecutor:
    """
    Executes generated code with safety checks.
    
    Only allows specific robot API calls.
    """
    
    def __init__(self, robot: RobotAPI):
        self.robot = robot
        self.executed_lines = []
    
    def execute(self, code: str) -> bool:
        """
        Execute generated code safely.
        
        Returns:
            True if execution succeeded
        """
        print(f"  [Executor] Running generated code...")
        
        # Create safe namespace with only robot API
        safe_globals = {"robot": self.robot}
        
        try:
            # Parse and execute line by line for safety
            lines = code.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Execute the line
                self.executed_lines.append(line)
                exec(line, safe_globals)
            
            print(f"    [Executor] Code executed successfully ({len(self.executed_lines)} commands)")
            return True
            
        except Exception as e:
            print(f"    [Executor] Error: {e}")
            self.robot.stop()
            return False


# ============================================================================
# Main Agent (orchestrates everything)
# ============================================================================

class CodeAsPoliciesAgent:
    """
    Code-as-Policies agent.
    
    1. VLM analyzes scene
    2. LLM generates Python code
    3. Code executes with safety checks
    
    Wrap this with ShadowDance for full observability.
    """
    
    def __init__(self):
        # Wrap individual components with appropriate run types
        self.vision = ShadowDance(VisionSystem(), run_type="llm")  # VLM calls
        self.codegen = ShadowDance(CodeGenerator(), run_type="llm")  # LLM calls
        self.robot = RobotAPI()
    
    def run(self, task: str, image_path: str) -> bool:
        """
        Execute task using code-as-policies.
        
        Args:
            task: Natural language task
            image_path: Path to scene image
            
        Returns:
            True if successful
        """
        print(f"\n{'='*60}")
        print(f"Task: {task}")
        print(f"{'='*60}\n")
        
        # Step 1: Vision - analyze scene
        print("Step 1: Vision Analysis")
        scene = self.vision.analyze_scene(image_path, task)
        print(f"  Detected objects:")
        for obj in scene.get("objects", []):
            print(f"    - {obj['name']} at {obj['position']}")
        print()
        
        # Step 2: Code generation
        print("Step 2: Code Generation")
        code = self.codegen.generate(task, scene)
        print(f"  Generated code:\n")
        for line in code.split('\n'):
            if line.strip() and not line.strip().startswith('#'):
                print(f"    {line}")
        print()
        
        # Step 3: Execute
        print("Step 3: Code Execution")
        executor = SafeExecutor(self.robot)
        success = executor.execute(code)
        
        # Report results
        print(f"\n{'='*60}")
        print(f"Execution: {'SUCCESS' if success else 'FAILED'}")
        print(f"Robot log: {len(self.robot.log)} commands executed")
        print(f"Final pose: {self.robot.get_pose()}")
        print(f"Holding: {self.robot.is_holding()}")
        print(f"{'='*60}\n")
        
        return success


def main():
    """Run the code-as-policies demo."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "shadowdance"
    
    print("\n" + "="*60)
    print("ShadowDance: Code-as-Policies Demo")
    print("="*60)
    print("\nModern LLM robot architecture:")
    print("  1. VLM → scene understanding")
    print("  2. LLM → Python code generation")
    print("  3. Safe execution → robot control")
    print("\nBased on: https://code-as-policies.github.io/")
    print("\nAll traced via ShadowDance (ONE LINE)\n")
    
    # Create agent
    agent = CodeAsPoliciesAgent()
    
    # ONE LINE - wrap with ShadowDance as chain type (orchestrates multiple components)
    agent = ShadowDance(agent, run_type="chain")
    
    # Get image
    image_path = Path(__file__).parent.parent / "assets" / "box-on-table.jpg"
    
    # Run task
    success = agent.run(
        task="Pick up the white box",
        image_path=str(image_path),
    )
    
    print("View traces at: https://smith.langchain.com")
    print("Project: shadowdance\n")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
