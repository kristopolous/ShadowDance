"""
Virtual Robot Server for testing ShadowDance.

This module provides a mock robot server that simulates Unitree robot
responses over DDS/RPC, allowing you to test LangSmith tracing without
a physical robot.

Usage:
    # Terminal 1: Start virtual robot
    python examples/virtual_robot_server.py

    # Terminal 2: Run your code
    python examples/basic.py
"""

import json
import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable


@dataclass
class RobotState:
    """Simulated robot state."""
    position: tuple = (0.0, 0.0, 0.0)
    velocity: tuple = (0.0, 0.0, 0.0)
    attitude: tuple = (0.0, 0.0, 0.0)
    battery: float = 100.0
    mode: str = "damp"
    standing: bool = False


class VirtualRobotServer:
    """
    Simulates a Unitree robot server for testing.

    This server responds to the same RPC calls as a real robot,
    allowing you to test ShadowDance tracing without hardware.
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize the virtual robot server.

        Args:
            verbose: If True, print received commands.
        """
        self.state = RobotState()
        self.verbose = verbose
        self._running = False
        self._command_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the virtual robot server."""
        self._running = True
        self._command_thread = threading.Thread(target=self._run_simulation)
        self._command_thread.daemon = True
        self._command_thread.start()
        if self.verbose:
            print("Virtual Robot Server started")

    def stop(self) -> None:
        """Stop the virtual robot server."""
        self._running = False
        if self._command_thread:
            self._command_thread.join(timeout=2.0)
        if self.verbose:
            print("Virtual Robot Server stopped")

    def _run_simulation(self) -> None:
        """Run the simulation loop."""
        while self._running:
            time.sleep(0.1)  # Simulation tick

    def _log_command(self, name: str, params: Dict[str, Any]) -> None:
        """Log a received command."""
        if self.verbose:
            print(f"  [Robot] Received: {name}({params})")

    # Sport Mode Commands (simulated)
    def Damp(self) -> int:
        """Set robot to damp (relaxed) mode."""
        self._log_command("Damp", {})
        self.state.mode = "damp"
        self.state.standing = False
        return 0

    def StandUp(self) -> int:
        """Make robot stand up."""
        self._log_command("StandUp", {})
        self.state.standing = True
        self.state.mode = "stand"
        return 0

    def StandDown(self) -> int:
        """Make robot lie down."""
        self._log_command("StandDown", {})
        self.state.standing = False
        self.state.mode = "damp"
        return 0

    def RecoveryStand(self) -> int:
        """Recover to standing position."""
        self._log_command("RecoveryStand", {})
        self.state.standing = True
        self.state.mode = "stand"
        return 0

    def StopMove(self) -> int:
        """Stop current movement."""
        self._log_command("StopMove", {})
        self.state.velocity = (0.0, 0.0, 0.0)
        return 0

    def Move(self, vx: float, vy: float, vyaw: float) -> int:
        """
        Move with velocity commands.

        Args:
            vx: Forward/backward velocity (m/s)
            vy: Left/right velocity (m/s)
            vyaw: Rotation velocity (rad/s)
        """
        self._log_command("Move", {"vx": vx, "vy": vy, "vyaw": vyaw})
        self.state.velocity = (vx, vy, vyaw)

        # Simulate position update
        dt = 0.1
        self.state.position = (
            self.state.position[0] + vx * dt,
            self.state.position[1] + vy * dt,
            self.state.position[2] + vyaw * dt,
        )
        return 0

    def Euler(self, roll: float, pitch: float, yaw: float) -> int:
        """Set attitude angles."""
        self._log_command("Euler", {"roll": roll, "pitch": pitch, "yaw": yaw})
        self.state.attitude = (roll, pitch, yaw)
        return 0

    def Sit(self) -> int:
        """Make robot sit."""
        self._log_command("Sit", {})
        self.state.standing = False
        self.state.mode = "sit"
        return 0

    def RiseSit(self) -> int:
        """Rise from sitting position."""
        self._log_command("RiseSit", {})
        self.state.standing = True
        self.state.mode = "stand"
        return 0

    def SpeedLevel(self, level: int) -> int:
        """Set speed level."""
        self._log_command("SpeedLevel", {"level": level})
        return 0

    def Hello(self) -> int:
        """Hello gesture."""
        self._log_command("Hello", {})
        return 0

    def Stretch(self) -> int:
        """Stretch gesture."""
        self._log_command("Stretch", {})
        return 0

    def Content(self) -> int:
        """Content gesture."""
        self._log_command("Content", {})
        return 0

    def Dance1(self) -> int:
        """Dance 1."""
        self._log_command("Dance1", {})
        return 0

    def Dance2(self) -> int:
        """Dance 2."""
        self._log_command("Dance2", {})
        return 0

    def SwitchJoystick(self, on: bool) -> int:
        """Switch joystick control."""
        self._log_command("SwitchJoystick", {"on": on})
        return 0

    def Pose(self, flag: bool) -> int:
        """Enable/disable pose mode."""
        self._log_command("Pose", {"flag": flag})
        return 0

    def Scrape(self) -> int:
        """Scrape gesture."""
        self._log_command("Scrape", {})
        return 0

    def FrontFlip(self) -> int:
        """Front flip."""
        self._log_command("FrontFlip", {})
        return 0

    def FrontJump(self) -> int:
        """Front jump."""
        self._log_command("FrontJump", {})
        return 0

    def FrontPounce(self) -> int:
        """Front pounce."""
        self._log_command("FrontPounce", {})
        return 0

    def Heart(self) -> int:
        """Heart gesture."""
        self._log_command("Heart", {})
        return 0

    def LeftFlip(self) -> int:
        """Left flip."""
        self._log_command("LeftFlip", {})
        return 0

    def BackFlip(self) -> int:
        """Back flip."""
        self._log_command("BackFlip", {})
        return 0

    def FreeWalk(self) -> int:
        """Free walk mode."""
        self._log_command("FreeWalk", {})
        return 0

    def FreeBound(self, flag: bool) -> int:
        """Free bound mode."""
        self._log_command("FreeBound", {"flag": flag})
        return 0

    def FreeJump(self, flag: bool) -> int:
        """Free jump mode."""
        self._log_command("FreeJump", {"flag": flag})
        return 0

    def FreeAvoid(self, flag: bool) -> int:
        """Free avoid mode."""
        self._log_command("FreeAvoid", {"flag": flag})
        return 0

    def WalkUpright(self, flag: bool) -> int:
        """Walk upright mode."""
        self._log_command("WalkUpright", {"flag": flag})
        return 0

    def CrossStep(self, flag: bool) -> int:
        """Cross step mode."""
        self._log_command("CrossStep", {"flag": flag})
        return 0

    def StaticWalk(self) -> int:
        """Static walk."""
        self._log_command("StaticWalk", {})
        return 0

    def TrotRun(self) -> int:
        """Trot run."""
        self._log_command("TrotRun", {})
        return 0

    def HandStand(self, flag: bool) -> int:
        """Handstand mode."""
        self._log_command("HandStand", {"flag": flag})
        return 0

    def ClassicWalk(self, flag: bool) -> int:
        """Classic walk mode."""
        self._log_command("ClassicWalk", {"flag": flag})
        return 0

    def AutoRecoverySet(self, enabled: bool) -> int:
        """Set auto recovery."""
        self._log_command("AutoRecoverySet", {"enabled": enabled})
        return 0

    def AutoRecoveryGet(self) -> tuple:
        """Get auto recovery status."""
        self._log_command("AutoRecoveryGet", {})
        return 0, True  # (code, enabled)

    def SwitchAvoidMode(self) -> int:
        """Switch avoid mode."""
        self._log_command("SwitchAvoidMode", {})
        return 0

    def GetState(self) -> Dict[str, Any]:
        """Get current robot state."""
        return {
            "position": self.state.position,
            "velocity": self.state.velocity,
            "attitude": self.state.attitude,
            "battery": self.state.battery,
            "mode": self.state.mode,
            "standing": self.state.standing,
        }


class VirtualRobotClient:
    """
    Client that connects to the VirtualRobotServer.

    This mimics the Unitree SportClient interface but connects
    to our virtual server instead of a real robot.
    """

    def __init__(self, server: VirtualRobotServer):
        """
        Initialize the virtual robot client.

        Args:
            server: The VirtualRobotServer to connect to.
        """
        self._server = server

    def Init(self) -> None:
        """Initialize connection to robot."""
        print("Virtual Robot Client connected")

    def Damp(self) -> int:
        """Set robot to damp mode."""
        return self._server.Damp()

    def StandUp(self) -> int:
        """Make robot stand up."""
        return self._server.StandUp()

    def StandDown(self) -> int:
        """Make robot lie down."""
        return self._server.StandDown()

    def RecoveryStand(self) -> int:
        """Recover to standing position."""
        return self._server.RecoveryStand()

    def StopMove(self) -> int:
        """Stop current movement."""
        return self._server.StopMove()

    def Move(self, vx: float, vy: float, vyaw: float) -> int:
        """Move with velocity commands."""
        return self._server.Move(vx, vy, vyaw)

    def Euler(self, roll: float, pitch: float, yaw: float) -> int:
        """Set attitude angles."""
        return self._server.Euler(roll, pitch, yaw)

    def Sit(self) -> int:
        """Make robot sit."""
        return self._server.Sit()

    def RiseSit(self) -> int:
        """Rise from sitting position."""
        return self._server.RiseSit()

    def SpeedLevel(self, level: int) -> int:
        """Set speed level."""
        return self._server.SpeedLevel(level)

    def Hello(self) -> int:
        """Hello gesture."""
        return self._server.Hello()

    def Stretch(self) -> int:
        """Stretch gesture."""
        return self._server.Stretch()

    def Content(self) -> int:
        """Content gesture."""
        return self._server.Content()

    def Dance1(self) -> int:
        """Dance 1."""
        return self._server.Dance1()

    def Dance2(self) -> int:
        """Dance 2."""
        return self._server.Dance2()

    def SwitchJoystick(self, on: bool) -> int:
        """Switch joystick control."""
        return self._server.SwitchJoystick(on)

    def Pose(self, flag: bool) -> int:
        """Enable/disable pose mode."""
        return self._server.Pose(flag)

    def Scrape(self) -> int:
        """Scrape gesture."""
        return self._server.Scrape()

    def FrontFlip(self) -> int:
        """Front flip."""
        return self._server.FrontFlip()

    def FrontJump(self) -> int:
        """Front jump."""
        return self._server.FrontJump()

    def FrontPounce(self) -> int:
        """Front pounce."""
        return self._server.FrontPounce()

    def Heart(self) -> int:
        """Heart gesture."""
        return self._server.Heart()

    def LeftFlip(self) -> int:
        """Left flip."""
        return self._server.LeftFlip()

    def BackFlip(self) -> int:
        """Back flip."""
        return self._server.BackFlip()

    def FreeWalk(self) -> int:
        """Free walk mode."""
        return self._server.FreeWalk()

    def FreeBound(self, flag: bool) -> int:
        """Free bound mode."""
        return self._server.FreeBound(flag)

    def FreeJump(self, flag: bool) -> int:
        """Free jump mode."""
        return self._server.FreeJump(flag)

    def FreeAvoid(self, flag: bool) -> int:
        """Free avoid mode."""
        return self._server.FreeAvoid(flag)

    def WalkUpright(self, flag: bool) -> int:
        """Walk upright mode."""
        return self._server.WalkUpright(flag)

    def CrossStep(self, flag: bool) -> int:
        """Cross step mode."""
        return self._server.CrossStep(flag)

    def StaticWalk(self) -> int:
        """Static walk."""
        return self._server.StaticWalk()

    def TrotRun(self) -> int:
        """Trot run."""
        return self._server.TrotRun()

    def HandStand(self, flag: bool) -> int:
        """Handstand mode."""
        return self._server.HandStand(flag)

    def ClassicWalk(self, flag: bool) -> int:
        """Classic walk mode."""
        return self._server.ClassicWalk(flag)

    def AutoRecoverySet(self, enabled: bool) -> int:
        """Set auto recovery."""
        return self._server.AutoRecoverySet(enabled)

    def AutoRecoveryGet(self) -> tuple:
        """Get auto recovery status."""
        return self._server.AutoRecoveryGet()

    def SwitchAvoidMode(self) -> int:
        """Switch avoid mode."""
        return self._server.SwitchAvoidMode()

    def GetState(self) -> Dict[str, Any]:
        """Get current robot state."""
        return self._server.GetState()
