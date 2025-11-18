## Description

This is a proof of concept demonstrating the use of **AskUI** to automate desktop devices.
As an example, we tested a grocery cashier game and sent a quote request to Bahn Business.
The goal is to showcase AskUI's capabilities for desktop automation (Android and Web are supported too).

## What is AskUI Agent?

AskUI Agent acts as a "brain" that follows instructions and uses a provided set of tools to perform tasks.

AskUI provides a default toolset for each agent type. For example:

* **Default Computer Agent toolset**:

  * Full control of mouse and keyboard
  * Take and analyze screenshots
  * Uses the default display but can list and switch displays

The toolset can be expanded with custom tools.
For this POC, we added custom tools in [tools.py](./helpers/tools.py).

* Example tools: **FileWriteTool** and **FileReadTool** allow the agent to read a CSV and write a `.md` report.

**ℹ️ Remark:** Tools can be anything: sending emails, making API calls, interacting with devices, etc.

## Requirements

* [AskUI Suite Installed](https://docs.askui.com/01-tutorials/00-installation)
* Chrome browser

## Example Agent Output

All outputs are saved under [reports](./reports).

### Cashier Game

Prompt used to play the game:

```python
desktop_agent.act(
    goal="""
    Open "https://www.mortgagecalculator.org/money-games/grocery-cashier/"
    Play the first level of the game.
    Save a screenshot after each interaction.
    Write a detailed report of the gameplay.
    Use only the mouse for interaction.
    Use tools in parallel to speed up gameplay.
    """,
    tools=custom_tools,
)
```

After execution, the agent generated this
[Execution Report.](./reports/20250923_grocery_cashier_game/grocery_cashier_game_test_report.md)


## Setup Steps

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

4. **Install Dependencies** (re-run if `requirements.txt` changes)

   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Agent**

   ```bash
   python ./act.py
   ```
