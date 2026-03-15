"""
Vision module for detecting objects in images.

This module provides a vision system that can use OpenAI-compatible
APIs (like OpenRouter) for object detection in images.
"""

import base64
import json
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from dotenv import load_dotenv

# Load environment for API keys
load_dotenv(Path(__file__).parent.parent / ".env")


@dataclass
class DetectedObject:
    """Represents a detected object in an image."""
    name: str
    confidence: float
    bounding_box: tuple  # (x, y, width, height)
    position_3d: Optional[tuple] = None  # (x, y, z) in meters
    orientation: Optional[tuple] = None  # (roll, pitch, yaw)


class VisionSystem:
    """
    Vision system for detecting and localizing objects.
    
    Uses OpenAI-compatible APIs for vision inference.
    """
    
    def __init__(self, model: str = "mock"):
        """
        Initialize the vision system.
        
        Args:
            model: Model identifier. Use "mock" for testing,
                   or an OpenAI-compatible model name for real inference.
        """
        self.model = model
        self._api_key = os.environ.get("OPENAI_API_KEY")
        self._api_base = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE")
    
    def detect_objects(self, image_path: str) -> list[DetectedObject]:
        """
        Detect objects in an image.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            List of detected objects with positions.
        """
        if self.model == "mock":
            return self._mock_detect(image_path)
        else:
            return self._real_detect(image_path)
    
    def _mock_detect(self, image_path: str) -> list[DetectedObject]:
        """Mock detection returning pre-defined results."""
        print(f"  [Vision] Mock detection on: {image_path}")
        
        # Simulate detecting a box on a table
        return [
            DetectedObject(
                name="white_box",
                confidence=0.95,
                bounding_box=(80, 40, 100, 120),  # Approximate box location
                position_3d=(0.3, 0.0, -0.15),  # 30cm forward, 15cm below camera
                orientation=(0, 0.1, 0),  # Slight tilt
            ),
            DetectedObject(
                name="table_surface",
                confidence=0.99,
                bounding_box=(0, 100, 262, 92),
                position_3d=(0, 0, 0),
                orientation=(0, 0, 0),
            ),
        ]
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _real_detect(self, image_path: str) -> list[DetectedObject]:
        """Real detection using OpenAI-compatible API."""
        import httpx
        
        print(f"  [Vision] Real detection on: {image_path} using {self.model}")
        
        # Encode image
        base64_image = self._encode_image(image_path)
        
        # Build the request
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        
        # Prompt for object detection
        prompt = """Analyze this image and identify all objects that could be manipulated by a robot.
For each object, provide:
1. Object name (be specific, e.g., 'white rectangular box')
2. Approximate position in the image (bounding box as x, y, width, height)
3. Estimated 3D position relative to camera (distance, left/right, up/down)

Respond in JSON format:
{
  "objects": [
    {"name": "...", "bbox": [x, y, w, h], "position_3d": [x, y, z], "confidence": 0.0-1.0}
  ]
}"""
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 1000,
        }
        
        # Make the request
        url = f"{self._api_base}/chat/completions"
        
        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            result = response.json()
        
        # Parse response
        content = result["choices"][0]["message"]["content"]
        
        # Try to extract JSON from response
        try:
            # Find JSON in response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(content[start:end])
                
                objects = []
                for obj in data.get("objects", []):
                    objects.append(
                        DetectedObject(
                            name=obj.get("name", "unknown"),
                            confidence=obj.get("confidence", 0.5),
                            bounding_box=tuple(obj.get("bbox", [0, 0, 0, 0])),
                            position_3d=tuple(obj.get("position_3d", [0, 0, 0])) if obj.get("position_3d") else None,
                        )
                    )
                return objects
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  [Vision] Failed to parse response: {e}")
            print(f"  Raw response: {content[:200]}")
        
        # Fallback to mock
        print("  [Vision] Falling back to mock detection")
        return self._mock_detect(image_path)
    
    def estimate_grasp_pose(self, obj: DetectedObject) -> dict:
        """
        Estimate a good grasp pose for the detected object.
        
        Args:
            obj: The detected object to grasp.
            
        Returns:
            Grasp configuration with position and orientation.
        """
        if obj.position_3d is None:
            raise ValueError("Object has no 3D position")
        
        # Simple heuristic: grasp from above, slightly tilted
        grasp_x = obj.position_3d[0]
        grasp_y = obj.position_3d[1]
        grasp_z = obj.position_3d[2] + 0.1  # 10cm above object
        
        return {
            "position": (grasp_x, grasp_y, grasp_z),
            "orientation": (0, 0.3, 0),  # Tilted down 30 degrees
            "grip_width": 0.08,  # 8cm grip
        }
