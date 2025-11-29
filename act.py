import datetime
import os
from askui import WebVisionAgent
from askui.tools.toolbox import AgentToolbox

from helpers.test_report_template_tool import GetTestReportTemplateTool
from helpers.tools import (
    SaveScreenshotTool,
    GetCurrentTimeTool,
    FileReadTool,
    FileWriteTool,
    FileListTool,
    OpenBrowserTool,
)

def init_custom_tools(
    askui_agent: WebVisionAgent,
    agent_workspace_directory: str,
):
    """
    Initializes the custom tools for the agent.
    Args:
        agent_toolbox: The agent toolbox.
        agent_workspace_directory: The path to the agent workspace directory.
        absolute_csv_file: The path to the absolute CSV file path.
    Returns:
        A list of custom tools.
    """
    return [
        SaveScreenshotTool(askui_agent.tools.os, agent_workspace_directory),
        GetCurrentTimeTool(),
        GetTestReportTemplateTool(),
        FileWriteTool(agent_workspace_directory),
        FileListTool(agent_workspace_directory),
        OpenBrowserTool(askui_agent.tools),
    ]


if __name__ == "__main__":
    agent_workspace_directory_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "agent_workspace",
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
        )
    )

    with (
        WebVisionAgent() as web_agent,
    ):
        custom_tools = init_custom_tools(
            web_agent,
            agent_workspace_directory_path,
        )

        # # Game Play
        # web_agent.act(
        #     """
        #     Open "https://www.mortgagecalculator.org/money-games/grocery-cashier/"
        #     Play the first level of the game.
        #     Save screenshot after each interaction.
        #     Write a detailed report of the game play.
        #     Use only the mouse for interaction with the game UI.
        #     Use Tools in parallel to speed up the game play.
        #     """,
        #     tools=custom_tools,
        # )

        # Send Quote request to GK System
        absolute_csv_file_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "csv_files",
                "demo.csv",
            )
        )
        web_agent.act(
            """
            You are an AI UI Automation Engineer created with AskUI Agent.  
            You are running in a controlled test environment with full control of the computer, browser, and UI.  
            You can analyze and solve image-based questions as part of test execution.
            Analyze the icons and click on the correct one based on the question.
            Execute the test case from the CSV file step by step.  
            After each interaction, capture and save a screenshot.  
            Write a detailed report of every interaction, including visual findings if images are involved.  
            Use tools in parallel to optimize and speed up execution.
            Do Not raise any Exception and do not ask the user for any input.
            """,
            tools=[
                FileReadTool(absolute_csv_file_path),
            ]
            + custom_tools,
        )
        
