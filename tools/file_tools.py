import os
from typing import Optional


OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")


def ensure_outputs_dir() -> None:
    os.makedirs(OUTPUTS_DIR, exist_ok=True)


def write_file_to_outputs(file_path: str, content: str) -> str:
    """Plain helper to write a file into outputs/ (callable directly by app)."""
    ensure_outputs_dir()
    safe_relative_path = file_path.lstrip("/\\")
    abs_path = os.path.join(OUTPUTS_DIR, safe_relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote file to {abs_path}"


def clear_outputs_dir(remove_all: bool = False) -> None:
    """Remove previous artifacts in outputs/.

    If remove_all is False, it keeps non-core backups and directories; it primarily
    clears common generated artifacts (html/css/js, PRD, logs). If True, it removes
    everything inside outputs/.
    """
    ensure_outputs_dir()
    if remove_all:
        for name in os.listdir(OUTPUTS_DIR):
            path = os.path.join(OUTPUTS_DIR, name)
            if os.path.isdir(path):
                # Best-effort recursive removal
                for root, dirs, files in os.walk(path, topdown=False):
                    for f in files:
                        try:
                            os.remove(os.path.join(root, f))
                        except Exception:
                            pass
                    for d in dirs:
                        try:
                            os.rmdir(os.path.join(root, d))
                        except Exception:
                            pass
                try:
                    os.rmdir(path)
                except Exception:
                    pass
            else:
                try:
                    os.remove(path)
                except Exception:
                    pass
        return

    # Selective clean of typical generated files
    core_files = [
        'PRD.md', 'file_breakdown.json', 'index.html', 'style.css', 'script.js',
        'qa_log.json', '_debug_raw_coder_output.txt', '_debug_errors.txt'
    ]
    for name in core_files:
        path = os.path.join(OUTPUTS_DIR, name)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass


def write_file_tool(file_path: str, content: str) -> str:
    """Write content to a file inside the outputs/ directory.

    Args:
        file_path: Relative path inside outputs/ (e.g., "index.html" or "subdir/file.txt").
        content: The file content to write.

    Returns:
        Success message with absolute path.
    """
    return write_file_to_outputs(file_path, content)


def read_file_from_outputs(file_path: str) -> str:
    """Read and return content of a file from outputs/ directory.

    Args:
        file_path: Relative path inside outputs/.

    Returns:
        File content as string.
    """
    ensure_outputs_dir()
    safe_relative_path = file_path.lstrip("/\\")
    abs_path = os.path.join(OUTPUTS_DIR, safe_relative_path)
    if not os.path.exists(abs_path):
        return f"ERROR: File does not exist: {abs_path}"
    with open(abs_path, "r", encoding="utf-8") as f:
        return f.read()


def read_file_tool(file_path: str) -> str:
    """Read and return content of a file from outputs/ directory.

    Args:
        file_path: Relative path inside outputs/.

    Returns:
        File content as string.
    """
    return read_file_from_outputs(file_path)


