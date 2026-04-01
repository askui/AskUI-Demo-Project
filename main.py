import argparse
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

from askui import ComputerAgent
from askui.models.shared.prompts import ActSystemPrompt
from askui.models.shared.settings import (
    ActSettings,
    MessageSettings,
    CachingSettings,
    CacheExecutionSettings,
    CacheWritingSettings,
)
from askui.models.shared.agent_message_param import CacheControlEphemeralParam
from askui.reporting import SimpleHtmlReporter
from askui.tools.store.universal import (
    ListFilesTool,
    PrintToConsoleTool,
    ReadFromFileTool,
    WriteToFileTool,
)
from askui.tools.store.computer import ComputerSaveScreenshotTool

from helpers import get_agent_tools


# Load Env variables, e.g. API Keys
load_dotenv()

PROMPTS_DIR = Path(__file__).parent / "prompts"
PROCEDURES_DIR = Path(__file__).parent / "procedures"
PLANS_DIR = Path(__file__).parent / "plans"

# Reserved filenames (stem) that provide folder-level context, not tests
SPECIAL_STEMS = {"rules", "setup", "teardown"}

# Supported test file extensions
TEST_EXTENSIONS = {".txt", ".md", ".pdf", ".csv", ".json"}


def _read_prompt(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()


def load_procedures() -> str:
    """Load all procedure files and format them as a prompt section."""
    if not PROCEDURES_DIR.exists():
        return ""
    procedures = []
    for f in sorted(PROCEDURES_DIR.iterdir()):
        if f.is_file() and f.suffix in TEST_EXTENSIONS:
            content = f.read_text(encoding="utf-8").strip()
            procedures.append(f"### {f.stem}\n{content}")
    if not procedures:
        return ""
    return "## Known Procedures\nWhen a test step references a procedure by name, execute the corresponding steps below.\n\n" + "\n\n".join(procedures)


def load_plan(plan_name: str) -> str:
    """Load a plan file by name (without extension) from the plans directory."""
    for ext in TEST_EXTENSIONS:
        candidate = PLANS_DIR / f"{plan_name}{ext}"
        if candidate.exists():
            return candidate.read_text(encoding="utf-8").strip()
    available = [f.stem for f in PLANS_DIR.iterdir() if f.is_file()] if PLANS_DIR.exists() else []
    raise FileNotFoundError(
        f"Plan '{plan_name}' not found in {PLANS_DIR}. Available: {', '.join(available) or 'none'}"
    )


def create_system_prompt(
    ui_information: str = "", additional_rules: str = ""
) -> ActSystemPrompt:
    procedures = load_procedures()
    combined_rules = "\n\n".join(filter(None, [additional_rules, procedures]))
    return ActSystemPrompt(
        system_capabilities=_read_prompt("system_capabilities.md"),
        device_information=_read_prompt("device_information.md"),
        ui_information=ui_information,
        report_format=_read_prompt("report_format.md"),
        additional_rules=combined_rules,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AskUI Vision Agent - Test Automation")
    parser.add_argument(
        "target",
        nargs="?",
        default="tests",
        help="Path to a tests folder or a single test file (default: tests)",
    )
    parser.add_argument(
        "--plan",
        type=str,
        default=None,
        help="Name of a plan file (without extension) from plans/ to execute",
    )
    parser.add_argument(
        "--cache-strategy",
        type=str,
        default="auto",
        help="Caching strategy (default: auto)",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=".askui_cache",
        help="Directory for cache files (default: .askui_cache)",
    )
    parser.add_argument(
        "--cache-delay-between-actions",
        type=float,
        default=1.0,
        help="Delay in seconds between cached actions (default: 1.0)",
    )
    parser.add_argument(
        "--cache-skip-visual-validation",
        action="store_true",
        default=False,
        help="Skip visual validation during cache execution",
    )
    parser.add_argument(
        "--cache-visual-validation-threshold",
        type=int,
        default=10,
        help="Max Hamming distance for visual validation (default: 10)",
    )
    parser.add_argument(
        "--cache-parameter-identification-strategy",
        type=str,
        choices=["llm", "preset"],
        default="llm",
        help="Cache parameter identification strategy (default: llm)",
    )
    parser.add_argument(
        "--cache-visual-verification-method",
        type=str,
        choices=["phash", "ahash", "none"],
        default="phash",
        help="Hash method for visual verification (default: phash)",
    )
    parser.add_argument(
        "--cache-visual-validation-region-size",
        type=int,
        default=100,
        help="Region size for visual validation (default: 100)",
    )
    return parser.parse_args()


def find_special_file(folder: Path, stem: str) -> Path | None:
    """Find a special file (context, setup, teardown) in any supported format."""
    for ext in TEST_EXTENSIONS:
        candidate = folder / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def read_file_content(file_path: Path) -> str:
    """Read a text file's content. Returns empty string for binary formats like PDF."""
    if file_path.suffix == ".pdf":
        return f"[PDF file: {file_path}]"
    return file_path.read_text(encoding="utf-8").strip()


def collect_test_files(folder: Path) -> list[Path]:
    """Collect test files from a folder, excluding special files and subdirectories."""
    test_files = []
    for f in sorted(folder.iterdir()):
        if f.is_file() and f.suffix in TEST_EXTENSIONS and f.stem not in SPECIAL_STEMS:
            test_files.append(f)
    return test_files


def collect_subgroups(folder: Path) -> list[Path]:
    """Collect subdirectories (groups) from a folder, sorted by name."""
    return sorted([d for d in folder.iterdir() if d.is_dir()])


def _make_act_settings(rules: str) -> ActSettings:
    return ActSettings(
        messages=MessageSettings(
            system=create_system_prompt(additional_rules=rules),
            provider_options={"cache_control": CacheControlEphemeralParam()},
        )
    )


def _sanitize_filename(name: str) -> str:
    """Replace characters unsafe for NTFS/FAT filesystems with underscores."""
    import re

    return re.sub(r'[<>:"/\\|?*\x00-\x1f\s]', "_", name)


def _make_caching_settings(
    caching_settings: CachingSettings | None, filename: str
) -> CachingSettings:
    """Clone caching settings and set the cache filename."""
    caching_settings = caching_settings or CachingSettings()
    caching_settings.writing_settings = (
        caching_settings.writing_settings or CacheWritingSettings()
    )
    caching_settings.writing_settings.filename = _sanitize_filename(filename)
    return caching_settings


def run_setup(
    agent: ComputerAgent,
    folder: Path,
    rules: str,
    caching_settings: CachingSettings | None = None,
):
    """Run the setup file for a folder if it exists."""
    setup_file = find_special_file(folder, "setup")
    if not setup_file:
        return
    print(f"[{folder.name}] Running setup...")
    
    agent.act(
        f"Execute the following setup steps:\n\n{read_file_content(setup_file)}",
        act_settings=_make_act_settings(rules),
        caching_settings=_make_caching_settings(
            caching_settings, f"{folder.name}_setup"
        ),
    )



def run_teardown(
    agent: ComputerAgent,
    folder: Path,
    rules: str,
    caching_settings: CachingSettings | None = None,
):
    """Run the teardown file for a folder if it exists."""
    teardown_file = find_special_file(folder, "teardown")
    if not teardown_file:
        return
    print(f"[{folder.name}] Running teardown...")
    agent.act(
        f"Execute the following teardown/cleanup steps:\n\n{read_file_content(teardown_file)}",
        act_settings=_make_act_settings(rules),
        caching_settings=_make_caching_settings(
            caching_settings, f"{folder.name}_teardown"
        ),
    )


def run_single_test(
    agent: ComputerAgent,
    test_file: Path,
    rules: str,
    caching_settings: CachingSettings | None = None,
):
    """Run a single test file with pre-computed rules."""
    print(f"Executing test: {test_file.stem}")

    test_content = read_file_content(test_file)
    test_name = _sanitize_filename(test_file.stem)
    act_settings = _make_act_settings(rules)

    agent.act(
        f"""Execute the following test and write a report.

## Test
{test_content}

## Instructions
1. Execute each test step in order.
2. After each step, take a screenshot and verify the actual result against the expected result.
3. If a step fails, record the failure and continue with the remaining steps.
4. Use PrintToConsoleTool to log progress before each step (e.g., "Step 1: Click the 2 button") and after (e.g., "Step 1: PASSED" or "Step 1: FAILED — actual result was X").
5. Write the report following the report format provided in the system prompt.
6. Save all artifacts into `./{test_name}/`:
   - Report: `./{test_name}/{test_name}_report.md`
   - Screenshots: `./{test_name}/step_{{n}}.png`
""",
        act_settings=act_settings,
        caching_settings=_make_caching_settings(caching_settings, test_name),
    )


def collect_all_test_files(folder: Path) -> list[Path]:
    """Recursively collect all test files from a folder tree."""
    all_files = list(collect_test_files(folder))
    for subgroup in collect_subgroups(folder):
        all_files.extend(collect_all_test_files(subgroup))
    return all_files


def resolve_plan(
    agent: ComputerAgent,
    plan_content: str,
    available_tests: list[Path],
    test_root: Path,
    workspace: Path,
) -> list[Path]:
    """Use the agent to interpret a plan and filter test cases. Returns selected test paths."""
    import json

    test_list = "\n".join(f"- {t.relative_to(test_root)}" for t in available_tests)
    output_file = workspace / "_plan_selection.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    agent.act(
        f"""You are a test plan resolver. Given a plan and a list of available test files, select which tests match the plan.

## Plan
{plan_content}

## Available Tests
{test_list}

## Instructions
Select the test files that match the plan. Write a JSON array of the selected file paths (exactly as listed above) to the file `_plan_selection.json`.
Example output: ["subtraction_test.csv", "addition_test.csv"]

Only output the JSON array, nothing else.
""",
        act_settings=ActSettings(
            messages=MessageSettings(system=create_system_prompt()),
        ),
    )

    if not output_file.exists():
        print("Warning: Plan resolution produced no output. Running all tests.")
        return available_tests

    selected_names = json.loads(output_file.read_text(encoding="utf-8"))
    selected = []
    for name in selected_names:
        full_path = test_root / Path(name)
        if full_path.exists():
            selected.append(full_path)
        else:
            print(f"Warning: Plan selected '{name}' but file not found, skipping.")
    return selected


def run_selected_tests(
    agent: ComputerAgent,
    test_files: list[Path],
    caching_settings: CachingSettings | None = None,
):
    """Run a list of selected test files, each with its full setup/teardown lifecycle."""
    for test_file in test_files:
        run_single_test_with_lifecycle(agent, test_file, caching_settings=caching_settings)


def _collect_folder_chain(folder: Path) -> list[Path]:
    """Collect ancestor folders from filesystem root down to folder (inclusive)."""
    chain: list[Path] = []
    current = folder
    while current != current.parent:
        chain.append(current)
        current = current.parent
    chain.reverse()
    return chain


def run_single_test_with_lifecycle(
    agent: ComputerAgent,
    test_file: Path,
    caching_settings: CachingSettings | None = None,
):
    """
    Run a single test file with full setup/teardown lifecycle.
    Walks the ancestor folder chain and runs setups top-down, then the test,
    then teardowns bottom-up — mirroring how run_folder would behave.
    """
    folder_chain = _collect_folder_chain(test_file.parent)

    # Build cumulative rules per folder level
    levels: list[tuple[Path, str]] = []
    cumulative_rules = ""
    for folder in folder_chain:
        rules_file = find_special_file(folder, "rules")
        local_rules = read_file_content(rules_file) if rules_file else ""
        cumulative_rules = "\n\n".join(filter(None, [cumulative_rules, local_rules]))
        levels.append((folder, cumulative_rules))

    # Setups: top-down
    for folder, rules in levels:
        run_setup(agent, folder, rules, caching_settings=caching_settings)

    # Test
    run_single_test(
        agent, test_file, rules=cumulative_rules, caching_settings=caching_settings
    )

    # Teardowns: bottom-up
    for folder, rules in reversed(levels):
        run_teardown(agent, folder, rules, caching_settings=caching_settings)


def run_folder(
    agent: ComputerAgent,
    folder: Path,
    parent_rules: str = "",
    caching_settings: CachingSettings | None = None,
):
    """
    Run all tests in a folder with the setup/rules/teardown pattern.
    Recurses into subgroup folders.

    Hierarchy:
        1. Read rules (inherits from parent + own) → set as system prompt
        2. Run setup
        3. Run test files
        4. Recurse into subgroups
        5. Run teardown
    """
    # Build cascading rules: parent rules + this folder's rules
    rules_file = find_special_file(folder, "rules")
    local_rules = read_file_content(rules_file) if rules_file else ""
    full_rules = "\n\n".join(filter(None, [parent_rules, local_rules]))

    run_setup(agent, folder, full_rules, caching_settings=caching_settings)

    for test_file in collect_test_files(folder):
        run_single_test(
            agent, test_file, rules=full_rules, caching_settings=caching_settings
        )

    for subgroup in collect_subgroups(folder):
        print(f"[{folder.name}] Entering group: {subgroup.name}")
        run_folder(
            agent, subgroup, parent_rules=full_rules, caching_settings=caching_settings
        )

    run_teardown(agent, folder, full_rules, caching_settings=caching_settings)


if __name__ == "__main__":
    args = parse_args()

    TARGET = Path(__file__).parent / args.target
    if not TARGET.exists():
        raise FileNotFoundError(f"Target not found: {TARGET}")

    is_single_test = TARGET.is_file()
    if is_single_test and TARGET.suffix not in TEST_EXTENSIONS:
        raise ValueError(
            f"Unsupported test file type: {TARGET.suffix}. "
            f"Supported: {', '.join(sorted(TEST_EXTENSIONS))}"
        )

    TEST_FOLDER = TARGET.parent if is_single_test else TARGET

    # Define the agent workspace directory.
    AGENT_WORKSPACE = (
        Path(__file__).parent
        / "agent_workspace"
        / datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    )

    # Build caching settings from CLI args
    caching_settings = CachingSettings(
        strategy=args.cache_strategy,
        cache_dir=args.cache_dir,
        execution_settings=CacheExecutionSettings(
            delay_time_between_actions=args.cache_delay_between_actions,
            skip_visual_validation=args.cache_skip_visual_validation,
            visual_validation_threshold=args.cache_visual_validation_threshold,
        ),
        writing_settings=CacheWritingSettings(
            parameter_identification_strategy=args.cache_parameter_identification_strategy,
            visual_verification_method=args.cache_visual_verification_method,
            visual_validation_region_size=args.cache_visual_validation_region_size,
        ),
    )

    # Read root-level rules for the system prompt
    root_rules_file = find_special_file(TEST_FOLDER, "rules")
    ui_information = read_file_content(root_rules_file) if root_rules_file else ""
    system_prompt = create_system_prompt(ui_information=ui_information)

    act_tools = [
        # Tools to enable reading the tests from the Tests Folder.
        ReadFromFileTool(base_dir=TEST_FOLDER),
        ListFilesTool(base_dir=TEST_FOLDER),
        # Tools to enable writing the reports to the Report Folder.
        WriteToFileTool(base_dir=AGENT_WORKSPACE),
        ListFilesTool(base_dir=AGENT_WORKSPACE),
        # Tools to enable printing to the console
        PrintToConsoleTool(source_name="AskUI Agent"),
        # Tool to save screenshots
        ComputerSaveScreenshotTool(base_dir=str(AGENT_WORKSPACE)),
        # Custom tools
        *get_agent_tools(),
    ]

    agent = ComputerAgent(
        act_tools=act_tools,
        reporters=[SimpleHtmlReporter(report_dir=str(AGENT_WORKSPACE))],
    )
    agent.act_settings.messages.system = system_prompt

    with agent:
        if args.plan:
            plan_content = load_plan(args.plan)
            all_tests = collect_all_test_files(TEST_FOLDER)
            print(f"Resolving plan '{args.plan}' against {len(all_tests)} available tests...")
            selected = resolve_plan(
                agent, plan_content, all_tests, TEST_FOLDER, AGENT_WORKSPACE
            )
            print(f"Plan selected {len(selected)} test(s): {[t.stem for t in selected]}")
            run_selected_tests(agent, selected, caching_settings=caching_settings)
        elif is_single_test:
            run_single_test_with_lifecycle(
                agent, TARGET, caching_settings=caching_settings
            )
        else:
            run_folder(agent, TEST_FOLDER, caching_settings=caching_settings)
