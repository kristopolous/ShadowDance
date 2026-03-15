"""
LangChain agent integration example for ShadowDance.

This example shows how ShadowDance traces nest automatically
within LangChain agent run trees.

Usage:
    export LANGCHAIN_API_KEY=your_key
    export LANGCHAIN_TRACING_V2=true
    export LANGCHAIN_PROJECT=unitree-demo
    python examples/agent_integration.py
"""

import os
from typing import Optional

from langchain.agents import tool
from langchain_core.runnables import RunnableConfig

from qwen import ShadowDance


class MockRobotClient:
    """Mock robot client for demonstration."""

    def __init__(self):
        self._position = (0.0, 0.0, 0.0)

    def Init(self) -> None:
        """Initialize the robot connection."""
        print("Robot connected")

    def Move(self, vx: float, vy: float, vyaw: float) -> int:
        """Move the robot."""
        self._position = (
            self._position[0] + vx,
            self._position[1] + vy,
            self._position[2] + vyaw,
        )
        print(f"Moved to: {self._position}")
        return 0

    def StandUp(self) -> int:
        """Make robot stand up."""
        print("Robot stood up")
        return 0

    def Damp(self) -> int:
        """Set to damp mode."""
        print("Damp mode")
        return 0


@tool
def robot_standup() -> str:
    """Make the robot stand up from a sitting or lying position.

    Use this when you need the robot to get ready for movement.
    """
    client = MockRobotClient()
    client = ShadowDance(client)
    client.Init()
    client.StandUp()
    return "Robot is now standing"


@tool
def robot_move(vx: float, vy: float, vyaw: float) -> str:
    """Move the robot with velocity commands.

    Args:
        vx: Forward/backward velocity (-1.0 to 1.0 m/s)
        vy: Left/right velocity (-1.0 to 1.0 m/s)
        vyaw: Rotation velocity (-1.0 to 1.0 rad/s)

    Use this to navigate the robot to different positions.
    """
    client = MockRobotClient()
    client = ShadowDance(client)
    client.Init()
    client.Move(vx, vy, vyaw)
    return f"Robot moved with velocity ({vx}, {vy}, {vyaw})"


@tool
def robot_damp() -> str:
    """Set the robot to damp mode (relaxed state).

    Use this when you want the robot to be compliant or
    before shutting down.
    """
    client = MockRobotClient()
    client = ShadowDance(client)
    client.Init()
    client.Damp()
    return "Robot is in damp mode"


def create_robot_agent():
    """Create a simple robot control agent."""
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    # Get API key (optional, for actual LLM usage)
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("OPENAI_API_KEY not set. Running in demo mode only.")
        print("Set OPENAI_API_KEY to run the full agent example.")
        return None

    # Create the LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Create the prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a robot control assistant. Help users control a Unitree "
                "robot by calling the appropriate tools. Always ensure the robot "
                "is standing before moving.",
            ),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    # Create the agent
    tools = [robot_standup, robot_move, robot_damp]
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    return agent_executor


def main():
    """Run the agent integration example."""
    # Disable LangSmith tracing for demo
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

    print("=== ShadowDance LangChain Integration Demo ===\n")

    # Demo 1: Direct tool usage (traces will be flat)
    print("--- Direct Tool Calls ---")
    result = robot_standup.invoke({})
    print(f"Result: {result}\n")

    result = robot_move.invoke({"vx": 0.3, "vy": 0, "vyaw": 0.1})
    print(f"Result: {result}\n")

    # Demo 2: Agent usage (traces will be nested)
    print("--- Agent Execution ---")
    agent = create_robot_agent()

    if agent:
        response = agent.invoke(
            {"input": "Make the robot stand up and then move forward slowly."}
        )
        print(f"\nAgent response: {response['output']}")

    print("\n=== Demo Complete ===")
    print(
        "\nWith LANGCHAIN_TRACING_V2=true, all these calls would appear in LangSmith "
        "with proper nesting under the agent's run tree."
    )


if __name__ == "__main__":
    main()
