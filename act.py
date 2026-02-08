import argparse
import datetime
import os

from askui import ActSettings, MessageSettings, VisionAgent
from askui.models.shared.prompts import ActSystemPrompt
from askui.models.shared.settings import CachingSettings
from askui.reporting import SimpleHtmlReporter
from askui.tools.store.computer import ComputerSaveScreenshotTool
from askui.tools.store.universal import (
    ListFilesTool,
    PrintToConsoleTool,
    WriteToFileTool,
)

from helpers.tools import FileReadTool, GetCurrentTimeTool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AskUI Demo — Calculator Test")
    parser.add_argument(
        "--display",
        type=int,
        default=2,
        help="Display number to use (default: 2)",
    )
    parser.add_argument(
        "--cache",
        type=str,
        choices=["write", "read", "both", "no"],
        default="no",
        help="Caching strategy: write to record, read to replay (default: no)",
    )
    return parser.parse_args()


def build_system_prompt() -> ActSystemPrompt:
    """Custom system prompt showcasing ActSystemPrompt configuration."""
    return ActSystemPrompt(
        system_capabilities=(
            "You are an AI UI Automation Engineer created with AskUI Agent. "
            "You are running in a controlled test environment with full control "
            "of the computer and UI. "
            "You can interact with desktop applications using mouse and keyboard."
        ),
        device_information="macOS desktop computer controlled via AskUI Agent OS.",
        ui_information=(
            "You are testing the macOS Calculator app. "
            "Execute the test case from the CSV file step by step."
        ),
        report_format=(
            "After each interaction, capture and save a screenshot. "
            "Write a detailed report of every interaction."
        ),
        additional_rules=(
            "Use tools in parallel to optimize and speed up execution. "
            "Do not raise any exceptions and do not ask the user for any input."
        ),
    )


if __name__ == "__main__":
    args = parse_args()

    project_root = os.path.dirname(os.path.abspath(__file__))

    workspace_dir = os.path.join(
        project_root,
        "agent_workspace",
        datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
    )

    cache_dir = os.path.join(project_root, ".cache")
    report_dir = os.path.join(project_root, "html_reports")

    absolute_csv_file_path = os.path.join(
        project_root, "csv_files", "calculator_test.csv"
    )

    # --- Tool Store: built-in tools ---
    builtin_tools = [
        ComputerSaveScreenshotTool(base_dir=workspace_dir),
        WriteToFileTool(base_dir=workspace_dir),
        ListFilesTool(base_dir=workspace_dir),
        PrintToConsoleTool(source_name="AskUI-Demo"),
    ]

    # --- Custom tools ---
    custom_tools = [
        GetCurrentTimeTool(),
        FileReadTool(absolute_csv_file_path),
    ]

    # --- Custom system prompt ---
    act_settings = ActSettings(
        messages=MessageSettings(
            system=build_system_prompt(),
        ),
    )

    # --- Caching settings ---
    caching_settings = CachingSettings(
        strategy=args.cache,
        cache_dir=cache_dir,
    )

    with VisionAgent(
        display=args.display,
        reporters=[SimpleHtmlReporter(report_dir=report_dir)],
        act_tools=builtin_tools + custom_tools,
    ) as agent:
        agent.act(
            "Execute the test case from the CSV file step by step.",
            settings=act_settings,
            caching_settings=caching_settings,
        )
