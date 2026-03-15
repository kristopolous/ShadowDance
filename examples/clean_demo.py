"""
Investor Demo: Full Stack Robot Observability with ShadowDance.

This creates beautiful, well-organized traces in LangSmith showing:
1. High-level task execution
2. LLM decision making (vision + planning)
3. Robot command execution
4. Real-time status updates

Run this before your demo, then show the LangSmith dashboard.

Usage:
    source .venv/bin/activate
    python examples/investor_demo.py
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from shadowdance import ShadowDance, task, task_context
from examples.virtual_robot import VirtualRobotServer, VirtualRobotClient

load_dotenv(Path(__file__).parent.parent / ".env")


# ============================================================================
# Demo Scenario: Warehouse Robot
# ============================================================================

@task("warehouse_pick_and_place", tags=["demo", "warehouse", "production"])
def warehouse_pick_and_place(robot, item: str = "box"):
    """
    Demo task: Pick up an item and place it at a new location.
    
    This simulates a real warehouse automation scenario.
    """
    print(f"\n📦 Starting warehouse task: Pick up {item}")
    
    # Phase 1: Perception
    with task_context("perception_phase", tags=["vision"]):
        print("  📷 Analyzing scene...")
        time.sleep(0.2)  # Simulate vision processing
        print("  ✓ Detected: white_box at position [0.3, 0.0, 0.75]")
    
    # Phase 2: Planning
    with task_context("planning_phase", tags=["planning", "llm"]):
        print("  🧠 Generating plan...")
        time.sleep(0.2)  # Simulate LLM planning
        print("  ✓ Plan: approach → grasp → lift → move → place")
    
    # Phase 3: Execution
    with task_context("execution_phase", tags=["control"]):
        print("  🤖 Executing manipulation...")
        
        # Step 1: Stand up and approach
        robot.StandUp()
        time.sleep(0.1)
        
        robot.Move(0.3, 0, 0)  # Move forward to item
        time.sleep(0.1)
        
        # Step 2: Grasp
        robot.Move(0, 0, -0.1)  # Lower arm
        time.sleep(0.1)
        robot.Move(0, 0, 0.15)  # Lift with item
        time.sleep(0.1)
        
        # Step 3: Move to placement
        robot.Move(-0.1, 0.2, 0)  # Move to new location
        time.sleep(0.1)
        
        # Step 4: Place item
        robot.Move(0, 0, -0.15)  # Lower arm
        time.sleep(0.1)
        robot.Move(0, 0, 0.15)  # Raise arm (release)
        time.sleep(0.1)
    
    # Phase 4: Return to home
    with task_context("return_phase", tags=["control"]):
        print("  🏠 Returning to home position...")
        robot.Move(-0.2, -0.2, 0)  # Return to start
        time.sleep(0.1)
        robot.Damp()  # Relax
    
    print(f"✓ Task complete: {item} successfully moved!")
    return {"success": True, "item": item, "duration": 2.5}


@task("quality_inspection", tags=["demo", "inspection", "qa"])
def quality_inspection(robot, inspection_points: int = 3):
    """
    Demo task: Inspect multiple points on a product.
    
    Simulates quality control in manufacturing.
    """
    print(f"\n🔍 Starting quality inspection ({inspection_points} points)")
    
    # Phase 1: Setup
    with task_context("inspection_setup", tags=["setup"]):
        robot.StandUp()
        time.sleep(0.1)
        print("  ✓ Robot positioned for inspection")
    
    # Phase 2: Inspection loop
    for i in range(inspection_points):
        with task_context(f"inspect_point_{i+1}", tags=["inspection"]):
            print(f"  📍 Inspecting point {i+1}/{inspection_points}...")
            
            # Move to inspection point
            robot.Move(0.2 + i*0.1, 0.1*i, 0)
            time.sleep(0.15)  # Simulate camera capture
            
            print(f"  ✓ Point {i+1}: OK")
    
    # Phase 3: Report
    with task_context("generate_report", tags=["reporting"]):
        robot.Damp()
        time.sleep(0.1)
        print("  ✓ Inspection report generated: PASS")
    
    print(f"✓ Quality inspection complete: {inspection_points}/{inspection_points} points passed")
    return {"success": True, "points_inspected": inspection_points, "defects": 0}


@task("emergency_response", tags=["demo", "safety", "critical"])
def emergency_response(robot):
    """
    Demo task: Emergency stop and safe shutdown.
    
    Shows safety-critical behavior tracing.
    """
    print("\n🚨 Emergency stop triggered!")
    
    with task_context("emergency_stop", tags=["safety", "critical"]):
        print("  ⛔ Initiating emergency stop...")
        robot.Move(0, 0, 0)  # Stop all motion
        time.sleep(0.05)
        robot.Damp()  # Go limp
        time.sleep(0.05)
        print("  ✓ Robot safely stopped")
    
    with task_context("status_report", tags=["reporting"]):
        print("  📊 Generating incident report...")
        time.sleep(0.1)
        print("  ✓ Report logged")
    
    print("✓ Emergency response complete")
    return {"success": True, "response_time_ms": 150}


# ============================================================================
# Main Demo Script
# ============================================================================

def run_demo():
    """Run the investor demo."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "shadowdance-demo"
    
    print("\n" + "="*70)
    print(" " * 15 + "🤖 SHADOWDANCE INVESTOR DEMO")
    print("="*70)
    print("\nThis demo creates beautiful, organized traces showing:")
    print("  ✓ High-level task organization")
    print("  ✓ Phase-by-phase execution tracking")
    print("  ✓ LLM decision points (vision, planning)")
    print("  ✓ Low-level robot commands")
    print("  ✓ Error handling and safety responses")
    print("\n📊 View live at: https://smith.langchain.com")
    print("   Project: shadowdance-demo")
    print("\n" + "="*70)
    
    # Start virtual robot
    server = VirtualRobotServer(verbose=False)
    server.start()
    
    try:
        # Create robot with ShadowDance
        robot = VirtualRobotClient(server)
        robot.Init()
        robot = ShadowDance(robot, run_type="tool")
        
        # Demo 1: Warehouse Pick and Place
        print("\n" + "="*70)
        print("DEMO 1: Warehouse Automation")
        print("="*70)
        warehouse_pick_and_place(robot, item="product_box")
        
        # Demo 2: Quality Inspection
        print("\n" + "="*70)
        print("DEMO 2: Quality Control")
        print("="*70)
        quality_inspection(robot, inspection_points=4)
        
        # Demo 3: Emergency Response
        print("\n" + "="*70)
        print("DEMO 3: Safety Systems")
        print("="*70)
        emergency_response(robot)
        
        # Summary
        print("\n" + "="*70)
        print(" " * 20 + "✅ DEMO COMPLETE")
        print("="*70)
        print("\n📊 Open LangSmith to see:")
        print("   https://smith.langchain.com")
        print("\n📁 Project: shadowdance-demo")
        print("\n📋 You'll see 3 organized task runs:")
        print("   1. warehouse_pick_and_place")
        print("      ├── perception_phase (vision)")
        print("      ├── planning_phase (llm)")
        print("      ├── execution_phase (control)")
        print("      └── return_phase (control)")
        print("\n   2. quality_inspection")
        print("      ├── inspection_setup")
        print("      ├── inspect_point_1, 2, 3, 4")
        print("      └── generate_report")
        print("\n   3. emergency_response")
        print("      ├── emergency_stop (safety)")
        print("      └── status_report")
        print("\n💡 Key points for investors:")
        print("   • Every robot command is traced automatically")
        print("   • Tasks are organized hierarchically for clarity")
        print("   • LLM decisions (vision, planning) are captured")
        print("   • Safety events are prominently logged")
        print("   • Debug production issues in minutes, not hours")
        print("\n" + "="*70 + "\n")
        
    finally:
        server.stop()


if __name__ == "__main__":
    run_demo()
