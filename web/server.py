"""
AskUI Demo Project — Web UI Backend
Run: uvicorn web.server:app --reload
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = PROJECT_ROOT / "tasks"
TEST_DATA_DIR = PROJECT_ROOT / "test_data"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
CACHE_DIR = PROJECT_ROOT / ".askui_cache"
WORKSPACE_DIR = PROJECT_ROOT / "agent_workspace"
HELPERS_DIR = PROJECT_ROOT / "helpers"

TASK_EXTENSIONS = {".txt", ".md", ".pdf", ".csv", ".json"}
SPECIAL_STEMS = {"rules", "setup", "teardown"}

app = FastAPI(title="AskUI Demo Project")


# ── Models ───────────────────────────────────────────────────────────────────
class TaskContent(BaseModel):
    path: str
    content: str


class DatasetBody(BaseModel):
    records: list[dict[str, Any]]


class PromptBody(BaseModel):
    content: str


class FolderCreate(BaseModel):
    path: str


class RunRequest(BaseModel):
    target: str = "tasks"
    cache_strategy: str = "auto"


class SettingsBody(BaseModel):
    values: dict[str, str]


# ── Helpers ──────────────────────────────────────────────────────────────────
def _safe_resolve(base: Path, relative: str) -> Path:
    """Resolve a relative path under base, preventing directory traversal."""
    resolved = (base / relative).resolve()
    if not str(resolved).startswith(str(base.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path")
    return resolved


def _build_tree(folder: Path, rel: str = "") -> list[dict]:
    """Recursively build a folder/file tree."""
    if not folder.exists():
        return []
    items: list[dict] = []
    for entry in sorted(folder.iterdir()):
        entry_rel = f"{rel}/{entry.name}" if rel else entry.name
        if entry.is_dir():
            items.append(
                {
                    "name": entry.name,
                    "path": entry_rel,
                    "type": "folder",
                    "children": _build_tree(entry, entry_rel),
                }
            )
        elif entry.suffix in TASK_EXTENSIONS:
            items.append(
                {
                    "name": entry.name,
                    "path": entry_rel,
                    "type": "file",
                    "format": entry.suffix.lstrip("."),
                    "special": entry.stem in SPECIAL_STEMS,
                }
            )
    return items


def _count_task_files(folder: Path) -> int:
    if not folder.exists():
        return 0
    count = 0
    for f in folder.rglob("*"):
        if f.is_file() and f.suffix in TASK_EXTENSIONS and f.stem not in SPECIAL_STEMS:
            count += 1
    return count


# ── Dashboard ────────────────────────────────────────────────────────────────
@app.get("/api/dashboard")
def dashboard():
    tasks_count = _count_task_files(TASKS_DIR)

    datasets_count = 0
    if TEST_DATA_DIR.exists():
        datasets_count = sum(
            1
            for f in TEST_DATA_DIR.iterdir()
            if f.is_file() and f.suffix in (".json", ".csv")
        )

    runs = []
    if WORKSPACE_DIR.exists():
        runs = sorted(
            [d.name for d in WORKSPACE_DIR.iterdir() if d.is_dir()], reverse=True
        )

    cache_count = 0
    if CACHE_DIR.exists():
        cache_count = sum(
            1 for f in CACHE_DIR.iterdir() if f.is_file() and f.suffix == ".json"
        )

    # Tool count from helpers
    tool_count = 1  # GreetingTool

    return {
        "tasks_count": tasks_count,
        "datasets_count": datasets_count,
        "runs_count": len(runs),
        "cache_count": cache_count,
        "tool_count": tool_count,
        "recent_runs": runs[:5],
    }


# ── Tasks ────────────────────────────────────────────────────────────────────
@app.get("/api/tasks")
def list_tasks():
    return _build_tree(TASKS_DIR)


@app.get("/api/tasks/content")
def get_task_content(path: str = Query(...)):
    file_path = _safe_resolve(TASKS_DIR, path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Task not found")
    if file_path.suffix == ".pdf":
        return {"content": f"[PDF file — cannot display inline]", "format": "pdf"}
    return {
        "content": file_path.read_text(encoding="utf-8"),
        "format": file_path.suffix.lstrip("."),
    }


@app.post("/api/tasks/content")
def save_task_content(body: TaskContent):
    file_path = _safe_resolve(TASKS_DIR, body.path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(body.content, encoding="utf-8")
    return {"ok": True}


@app.post("/api/tasks/folder")
def create_task_folder(body: FolderCreate):
    folder_path = _safe_resolve(TASKS_DIR, body.path)
    folder_path.mkdir(parents=True, exist_ok=True)
    return {"ok": True}


@app.delete("/api/tasks")
def delete_task(path: str = Query(...)):
    file_path = _safe_resolve(TASKS_DIR, path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    if file_path.is_dir():
        import shutil

        shutil.rmtree(file_path)
    else:
        file_path.unlink()
    return {"ok": True}


# ── Run ──────────────────────────────────────────────────────────────────────
_active_process: subprocess.Popen | None = None


@app.post("/api/run")
def run_task(body: RunRequest):
    global _active_process
    target = body.target
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "main.py"),
        target,
        "--cache-strategy",
        body.cache_strategy,
    ]

    def stream():
        global _active_process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        _active_process = process
        try:
            for line in iter(process.stdout.readline, ""):
                yield f"data: {json.dumps({'line': line.rstrip()})}\n\n"
            process.wait()
            yield f"data: {json.dumps({'done': True, 'code': process.returncode})}\n\n"
        finally:
            _active_process = None

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/run/stop")
def stop_run():
    global _active_process
    if _active_process is None:
        raise HTTPException(status_code=404, detail="No active run")
    import signal
    _active_process.send_signal(signal.SIGTERM)
    try:
        _active_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _active_process.kill()
    _active_process = None
    return {"ok": True}


# ── Runs / Reports ──────────────────────────────────────────────────────────
@app.get("/api/runs")
def list_runs():
    if not WORKSPACE_DIR.exists():
        return []
    runs = []
    for d in sorted(WORKSPACE_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        # Count reports
        reports = list(d.rglob("*_report.md"))
        html_reports = list(d.glob("*.html"))
        runs.append(
            {
                "id": d.name,
                "timestamp": d.name,
                "report_count": len(reports),
                "html_reports": [h.name for h in html_reports],
            }
        )
    return runs


@app.get("/api/runs/{run_id}/files")
def list_run_files(run_id: str):
    run_dir = _safe_resolve(WORKSPACE_DIR, run_id)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    files = []
    for f in sorted(run_dir.rglob("*")):
        if f.is_file():
            files.append(
                {
                    "name": f.name,
                    "path": str(f.relative_to(run_dir)),
                    "type": f.suffix.lstrip("."),
                    "size": f.stat().st_size,
                }
            )
    return files


@app.get("/api/runs/{run_id}/file")
def get_run_file(run_id: str, path: str = Query(...)):
    run_dir = _safe_resolve(WORKSPACE_DIR, run_id)
    file_path = _safe_resolve(run_dir, path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if file_path.suffix == ".html":
        return HTMLResponse(file_path.read_text(encoding="utf-8"))
    if file_path.suffix == ".png":
        from fastapi.responses import FileResponse

        return FileResponse(file_path, media_type="image/png")
    if file_path.suffix in (".md", ".txt", ".csv", ".json"):
        return {"content": file_path.read_text(encoding="utf-8"), "format": file_path.suffix.lstrip(".")}
    from fastapi.responses import FileResponse

    return FileResponse(file_path)


# ── Test Data ────────────────────────────────────────────────────────────────
@app.get("/api/test-data")
def list_test_data():
    if not TEST_DATA_DIR.exists():
        return []
    datasets = []
    for f in sorted(TEST_DATA_DIR.iterdir()):
        if f.is_file() and f.suffix in (".json", ".csv"):
            record_count = 0
            try:
                if f.suffix == ".json":
                    data = json.loads(f.read_text(encoding="utf-8"))
                    record_count = len(data) if isinstance(data, list) else 1
                elif f.suffix == ".csv":
                    record_count = sum(1 for _ in open(f)) - 1  # minus header
            except Exception:
                pass
            datasets.append(
                {
                    "name": f.stem,
                    "format": f.suffix.lstrip("."),
                    "record_count": record_count,
                    "filename": f.name,
                }
            )
    return datasets


@app.get("/api/test-data/{name}")
def get_test_data(name: str):
    json_path = TEST_DATA_DIR / f"{name}.json"
    csv_path = TEST_DATA_DIR / f"{name}.csv"
    if json_path.exists():
        data = json.loads(json_path.read_text(encoding="utf-8"))
        records = data if isinstance(data, list) else [data]
        return {"records": records, "format": "json"}
    if csv_path.exists():
        import csv as csv_mod

        with open(csv_path, encoding="utf-8", newline="") as fh:
            reader = csv_mod.DictReader(fh)
            records = list(reader)
        return {"records": records, "format": "csv"}
    raise HTTPException(status_code=404, detail="Dataset not found")


@app.put("/api/test-data/{name}")
def update_test_data(name: str, body: DatasetBody):
    json_path = TEST_DATA_DIR / f"{name}.json"
    csv_path = TEST_DATA_DIR / f"{name}.csv"
    target = json_path if json_path.exists() else csv_path if csv_path.exists() else json_path
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(body.records, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": True}


@app.post("/api/test-data/{name}")
def create_test_data(name: str, body: DatasetBody):
    json_path = TEST_DATA_DIR / f"{name}.json"
    if json_path.exists():
        raise HTTPException(status_code=409, detail="Dataset already exists")
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(body.records, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": True}


@app.delete("/api/test-data/{name}")
def delete_test_data(name: str):
    for ext in (".json", ".csv"):
        p = TEST_DATA_DIR / f"{name}{ext}"
        if p.exists():
            p.unlink()
            return {"ok": True}
    raise HTTPException(status_code=404, detail="Dataset not found")


# ── Tools ────────────────────────────────────────────────────────────────────
@app.get("/api/tools")
def list_tools():
    """Return metadata about available custom tools."""
    tools = [
        {
            "name": "greeting_tool",
            "title": "Greeting",
            "description": "Creates personalized greeting messages with time-based and language customization. Supports English, Spanish, and French.",
            "icon": "👋",
            "inputs": ["name (required)", "time_of_day (required)", "language (optional)"],
            "file": "helpers/tools/greeting_tool.py",
        },
    ]
    return tools


# ── Prompts ──────────────────────────────────────────────────────────────────
@app.get("/api/prompts")
def list_prompts():
    if not PROMPTS_DIR.exists():
        return []
    return [
        {"name": f.stem, "filename": f.name}
        for f in sorted(PROMPTS_DIR.iterdir())
        if f.is_file() and f.suffix == ".md"
    ]


@app.get("/api/prompts/{name}")
def get_prompt(name: str):
    file_path = PROMPTS_DIR / f"{name}.md"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"content": file_path.read_text(encoding="utf-8"), "name": name}


@app.put("/api/prompts/{name}")
def update_prompt(name: str, body: PromptBody):
    file_path = PROMPTS_DIR / f"{name}.md"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Prompt not found")
    file_path.write_text(body.content, encoding="utf-8")
    return {"ok": True}


# ── Cache ────────────────────────────────────────────────────────────────────
@app.get("/api/cache")
def list_cache():
    if not CACHE_DIR.exists():
        return []
    items = []
    for f in sorted(CACHE_DIR.iterdir()):
        if f.is_file() and f.suffix == ".json":
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                items.append(
                    {
                        "name": f.stem,
                        "filename": f.name,
                        "size": f.stat().st_size,
                        "created": data.get("metadata", {}).get("created_at", ""),
                        "last_executed": data.get("metadata", {}).get(
                            "last_executed_at", ""
                        ),
                        "valid": data.get("metadata", {}).get("is_valid", False),
                    }
                )
            except Exception:
                items.append({"name": f.stem, "filename": f.name, "size": f.stat().st_size})
    return items


@app.delete("/api/cache/{name}")
def delete_cache_entry(name: str):
    file_path = CACHE_DIR / f"{name}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Cache entry not found")
    file_path.unlink()
    return {"ok": True}


@app.delete("/api/cache")
def clear_cache():
    if CACHE_DIR.exists():
        for f in CACHE_DIR.iterdir():
            if f.is_file() and f.suffix == ".json":
                f.unlink()
    return {"ok": True}


# ── Settings (.env) ──────────────────────────────────────────────────────
ENV_FILE = PROJECT_ROOT / ".env"

# Keys we expose in the UI (add more as needed)
SETTING_KEYS = [
    "ASKUI_WORKSPACE_ID",
    "ASKUI_TOKEN",
    "ASKUI_INFERENCE_SERVER_URL",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
]


def _read_env() -> dict[str, str]:
    """Parse .env file into a dict."""
    values: dict[str, str] = {}
    if not ENV_FILE.exists():
        return values
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip("'\"")
            values[key] = val
    return values


def _write_env(values: dict[str, str]) -> None:
    """Write dict back to .env, preserving comments and unknown keys."""
    existing_lines: list[str] = []
    if ENV_FILE.exists():
        existing_lines = ENV_FILE.read_text(encoding="utf-8").splitlines()

    written_keys: set[str] = set()
    new_lines: list[str] = []
    for line in existing_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.partition("=")[0].strip()
            if key in values:
                new_lines.append(f"{key}={values[key]}")
                written_keys.add(key)
                continue
        new_lines.append(line)

    # Append any new keys not already in file
    for key, val in values.items():
        if key not in written_keys:
            new_lines.append(f"{key}={val}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


@app.get("/api/settings")
def get_settings():
    env = _read_env()
    return {
        "values": {k: env.get(k, "") for k in SETTING_KEYS},
        "keys": SETTING_KEYS,
    }


@app.put("/api/settings")
def update_settings(body: SettingsBody):
    current = _read_env()
    for key, val in body.values.items():
        if key in SETTING_KEYS:
            current[key] = val
    _write_env(current)
    return {"ok": True}


# ── Static files & SPA fallback ─────────────────────────────────────────────
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    index = STATIC_DIR / "index.html"
    return HTMLResponse(index.read_text(encoding="utf-8"))
