## Features

- **Android Agent Testing**: Android UI automation with AskUI AndroidVisionAgent
- **Visual Testing**: AI-powered visual validation
- **Hierarchical Task Runner**: Folder-based task execution with rules, setup, and teardown
- **Custom Tools**: Extensible tool framework for specialized testing
- **Automated Reporting**: HTML report generation with visual evidence
- **Multi-Format Tasks**: Support for CSV, Markdown, Text, JSON, and PDF task files

## Project Structure

```
harman/
├── main.py                        # Entry point - hierarchical folder runner
├── pyproject.toml                 # PEP 621 project metadata
├── pdm.lock                       # PDM dependency lock file
├── requirements.txt               # Python dependencies
├── .env.template                  # Environment variables template
├── helpers/                       # Custom tools and utilities
│   ├── __init__.py
│   ├── get_tools.py               # Tool factory function
│   └── tools/
│       ├── __init__.py
│       └── greeting_tool.py       # Example custom tool
├── tasks/                         # Task definitions (hierarchical)
│   └── demo/
│       ├── rules.md               # Rules for this task group
│       ├── demo.csv               # Test task: Bluetooth settings
│       └── demo2.csv              # Test task: WiFi settings
├── prompts/                       # Prompt parts for the system prompt (MD files)
│   ├── system_capabilities.md     # Agent capabilities description
│   ├── device_information.md      # Android device context
│   └── report_format.md           # Report formatting guidelines
└── agent_workspace/               # Generated per run (timestamped)
```

## Task Hierarchy

Tasks are organized in folders under `tasks/`. Each folder can contain:

| File | Purpose |
|------|---------|
| `rules.(md\|txt\|csv\|json\|pdf)` | Context/rules injected as system prompt for all tasks in folder |
| `setup.(md\|txt\|csv\|json\|pdf)` | Executed before tasks in folder |
| `teardown.(md\|txt\|csv\|json\|pdf)` | Executed after all tasks in folder |
| `*.csv`, `*.md`, `*.txt`, `*.json`, `*.pdf` | Task files (executed in sorted order) |
| Subdirectories | Subgroups that inherit parent rules |

Rules cascade from parent to child folders, so subgroups inherit their parent's context.

## Prerequisites

- Python >3.11, <3.14
- askui Python library with Android support
- Android SDK and emulators (for Android testing)

## Dependencies

- `askui[android]==0.25.0` - AI-powered UI automation with Android support
- `python-dotenv==1.2.1` - Environment variable management

## Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd harman
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv

   # On Windows:
   venv\Scripts\activate

   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up Android emulators (if running Android tests):
   ```bash
   adb devices
   ```

5. Configure environment variables:
   ```bash
   cp .env.template .env
   # Edit .env file with your values:
   # - ANTHROPIC_API_KEY: Your Anthropic API key
   # - ANTHROPIC_BASE_URL: Harman's internal AI service endpoint
   ```

## Usage

### Running Tasks

```bash
# Run all tasks from the default tasks/ folder
python main.py

# Run tasks from a specific subfolder
python main.py tasks/demo

# Run a single task file (with setup/teardown from its folder hierarchy)
python main.py tasks/demo/demo.csv

# Custom caching options
python main.py tasks/demo --cache-strategy read --cache-dir .custom_cache
```

### Adding New Tasks

1. Create a new folder under `tasks/` for your task group
2. Add a `rules.md` with context and rules for the group
3. Optionally add `setup` and `teardown` files
4. Add task files (CSV, Markdown, etc.) - they execute in sorted order

### Adding Custom Tools

1. Create new tool classes in `helpers/tools/`
2. Inherit from `askui.models.shared.tools.Tool`
3. Register tools in `helpers/get_tools.py`

### Available AI Models

The project supports multiple Claude models:
- `claude-sonnet-4-20250514`
- `claude-haiku-4-5-20251001`
- `claude-sonnet-4-5-20250929`
- `sonnet-3.7-asia`

## Reports

Test execution generates HTML reports in the `agent_workspace/` directory with:
- Timestamped run directories
- Visual evidence of test steps
- Detailed execution logs
- Per-task markdown reports and screenshots
