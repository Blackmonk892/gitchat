import shutil
import sys
import os


def resolve_bin(cmd_name: str) -> str:
    """
    Cross-platform binary resolver.
    On Windows, npm installs create 'name.cmd', which subprocess.Popen 
    doesn't find automatically. This helper fixes that.
    """
    # 1. Try finding the command in the system PATH
    path = shutil.which(cmd_name)
    if path:
        return path

    # 2. If on Windows, explicitly try appending .cmd (common for npm tools)
    if sys.platform == "win32":
        path_cmd = shutil.which(f"{cmd_name}.cmd")
        if path_cmd:
            return path_cmd

    # 3. Return original string (let subprocess fail naturally if still not found)
    return cmd_name

# --- Configuration ---


LANGUAGE_CONFIG = {
    "python": {
        # Pyright usually installs as an .exe on Windows (Scripts folder), so it often works fine.
        # But wrapping it is safer.
        "cmd": [resolve_bin("pyright-langserver"), "--stdio"],
        "extensions": [".py"],
        "root_marker": ["pyproject.toml", "setup.py", ".git"]
    },
    "javascript": {
        # This is the one crashing. It will now resolve to 'typescript-language-server.cmd'
        "cmd": [resolve_bin("typescript-language-server"), "--stdio"],
        "extensions": [".js", ".jsx", ".ts", ".tsx"],
        "root_marker": ["package.json", ".git"]
    },
    "go": {
        "cmd": [resolve_bin("gopls")],
        "extensions": [".go"],
        "root_marker": ["go.mod", ".git"]
    },
    "rust": {
        "cmd": [resolve_bin("rust-analyzer")],
        "extensions": [".rs"],
        "root_marker": ["Cargo.toml", ".git"]
    }
}


def get_config(file_path: str):
    """Detects language based on file extension."""
    # Normalize to lowercase for extension matching
    lower_path = file_path.lower()

    for lang, cfg in LANGUAGE_CONFIG.items():
        if any(lower_path.endswith(ext) for ext in cfg["extensions"]):
            return lang, cfg
    return None, None
