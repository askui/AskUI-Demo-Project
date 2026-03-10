from askui.models.shared.tools import Tool
from .tools.greeting_tool import GreetingTool


def get_agent_tools() -> list[Tool]:
    """
    Get the custom tools for the agent.
    """
    return [
    GreetingTool(),
    ]
