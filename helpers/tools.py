import datetime
import os
from typing import override

from askui.models.shared.tools import Tool


class GetCurrentTimeTool(Tool):
    """Get the current time in UTC."""

    def __init__(self):
        super().__init__(
            name="get_current_time_tool",
            description="Retrieves the current time. No input is required.",
            input_schema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

    @override
    def __call__(self) -> str:
        return f"Current UTC time: {datetime.datetime.now(datetime.UTC).strftime('%A, %B %d, %Y at %H:%M:%S UTC')}"


class FileReadTool(Tool):
    """Reads content from a specific file."""

    def __init__(self, absolute_file_path: str):
        if not os.path.isfile(absolute_file_path):
            error_msg = f"File not found: {absolute_file_path}"
            raise RuntimeError(error_msg)
        file_name = (
            os.path.basename(absolute_file_path)
            .strip()
            .replace(" ", "_")
            .replace(".", "_")
            .lower()
        )
        super().__init__(
            name=f"file_read_tool_{file_name}",
            description="Reads content from a file.",
        )
        self._absolute_file_path = absolute_file_path

    @override
    def __call__(self) -> str:
        with open(self._absolute_file_path, "r", encoding="utf-8") as f:
            return f.read()
