import json
import os
from datetime import datetime

from .file_tools import ensure_outputs_dir, write_file_to_outputs


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def write_qa_log(qa_json: dict) -> None:
    ensure_outputs_dir()
    try:
        content = json.dumps({
            "timestamp": _timestamp(),
            "qa": qa_json,
        }, indent=2)
        write_file_to_outputs(file_path="qa_log.json", content=content)
    except Exception:
        # Best-effort only
        pass


def write_prd(prd_markdown: str) -> None:
    ensure_outputs_dir()
    try:
        write_file_to_outputs(file_path="PRD.md", content=prd_markdown)
    except Exception:
        pass


def write_metrics(metrics: dict) -> None:
    ensure_outputs_dir()
    try:
        existing: dict = {}
        # Append-friendly pattern: keep last run under "latest"
        payload = {
            "timestamp": _timestamp(),
            "latest": metrics,
        }
        write_file_to_outputs(file_path="metrics.json", content=json.dumps(payload, indent=2))
    except Exception:
        pass


