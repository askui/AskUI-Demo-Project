from pathlib import Path

from askui.models.shared.prompts import ActSystemPrompt

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _read_prompt(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()


def create_system_prompt(
    ui_information: str = "", additional_rules: str = ""
) -> ActSystemPrompt:
    return ActSystemPrompt(
        system_capabilities=_read_prompt("system_capabilities.md"),
        device_information=_read_prompt("device_information.md"),
        ui_information=ui_information,
        report_format=_read_prompt("report_format.md"),
        additional_rules=additional_rules,
    )
