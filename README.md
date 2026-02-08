## Description

This is a demo project showcasing **AskUI** features for desktop UI automation.
The agent opens the macOS Calculator app, computes **20 - 10**, and verifies the result is **10**.
Test steps are defined in a CSV file and executed by the agent automatically.

## Features Demonstrated

### Custom System Prompt

The agent's behavior is configured via `ActSystemPrompt`, which lets you define:

- **system_capabilities** — what the agent can do
- **device_information** — the platform it runs on
- **ui_information** — context about the app under test
- **report_format** — how to document results
- **additional_rules** — extra constraints (e.g., parallel tool use)

See `build_system_prompt()` in [act.py](./act.py).

### Tool Store (Built-in Tools)

AskUI provides ready-made tools that the agent can use during execution:

| Tool | Description |
|------|-------------|
| `ComputerSaveScreenshotTool` | Save screenshots to the workspace |
| `WriteToFileTool` | Write files (reports, logs) to the workspace |
| `ListFilesTool` | List files in the workspace |
| `PrintToConsoleTool` | Print messages to the console |

### Custom Tools

You can extend the agent with your own tools. This project adds two in [helpers/tools.py](./helpers/tools.py):

| Tool | Description |
|------|-------------|
| `FileReadTool` | Reads the CSV test case file so the agent knows what to execute |
| `GetCurrentTimeTool` | Returns the current UTC time |

Tools can do anything: send emails, call APIs, interact with databases, etc.

### CSV-Driven Test Cases

Test steps are defined in [csv_files/calculator_test.csv](./csv_files/calculator_test.csv).
The agent reads this file via `FileReadTool` and executes each step in order.
To change what the agent does, edit the CSV — no code changes needed.

### Trajectory Caching

Caching records the agent's action trajectory (the sequence of tool calls and decisions) so it can be replayed later without re-running the AI model. This speeds up repeated runs and saves API costs.

| Strategy | Behavior |
|----------|----------|
| `write` | Record actions to `.cache/` for future replay |
| `read` | Replay from a previously cached trajectory |
| `both` | Read from cache if available, otherwise execute and write **(default)** |
| `no` | Disable caching entirely |

Cache files are stored in the `.cache/` directory at the project root.

```bash
# First run: executes live and caches the trajectory
python act.py --cache write

# Subsequent runs: replays from cache (fast, no API calls)
python act.py --cache read

# Default: reads cache if available, writes if not
python act.py

# Disable caching
python act.py --cache no
```

### HTML Reporting

After each run, a detailed HTML report is generated in `html_reports/`.
Reports include timestamps, agent messages, screenshots, and a full log of every interaction.

## Project Structure

```
.
├── act.py                             # Main script — configures and runs the agent
├── csv_files/
│   └── calculator_test.csv            # Test case: open Calculator, 20-10, verify 10
├── helpers/
│   ├── __init__.py
│   └── tools.py                       # Custom tools (FileReadTool, GetCurrentTimeTool)
├── html_reports/                      # Generated HTML reports (after running)
├── agent_workspace/                   # Screenshots and files saved by the agent
├── .cache/                            # Cached action trajectories
└── requirements.txt
```

## Requirements

- [AskUI Suite Installed](https://docs.askui.com/01-tutorials/00-installation)
- macOS with Calculator app

## Setup

1. **Open AskUI Shell**

   ```bash
   askui-shell
   ```

2. **Configure AskUI Credentials** (first-time setup only)

   1. Create an access token: [Access Token Guide](https://docs.askui.com/02-how-to-guides/01-account-management/04-tokens)
   2. Set up credentials: [Credentials Setup Guide](https://docs.askui.com/04-reference/02-askui-suite/02-askui-suite/ADE/Public/AskUI-SetSettings)

3. **Enable Python Environment**

   ```bash
   AskUI-EnablePythonEnvironment -name 'AskUIDemo' -CreateIfNotExists
   ```

4. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Agent**

   ```bash
   python act.py
   ```

   Options:

   ```bash
   python act.py --display 1      # Use display 1 instead of 2
   python act.py --cache no        # Run without caching
   python act.py --cache write     # Record trajectory only
   python act.py --cache read      # Replay from cache only
   ```
