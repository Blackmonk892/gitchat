import os

LANGUAGE_CONFIG = {
    "python": {
        # 'pyright-langserver' works if installed via pip
        "cmd": ["pyright-langserver", "--stdio"],
        "extensions": [".py"],
        "language_id_by_extension": {
            ".py": "python"
        },
        "root_marker": ["pyproject.toml", "setup.py", ".git"]
    },
    "javascript": {
        # shell=True will automatically find the .cmd file for this
        "cmd": ["typescript-language-server", "--stdio"],
        "extensions": [".js", ".jsx", ".ts", ".tsx"],
        "language_id_by_extension": {
            ".js": "javascript",
            ".jsx": "javascriptreact",
            ".ts": "typescript",
            ".tsx": "typescriptreact"
        },
        "root_marker": ["package.json", ".git"]
    },
    "go": {
        "cmd": ["gopls"],
        "extensions": [".go"],
        "language_id_by_extension": {
            ".go": "go"
        },
        "root_marker": ["go.mod", ".git"]
    }
}


def get_config(file_path: str):
    lower = file_path.lower()
    for lang, cfg in LANGUAGE_CONFIG.items():
        if any(lower.endswith(ext) for ext in cfg["extensions"]):
            return lang, cfg
    return None, None


def get_language_id(file_path: str, lang: str, cfg: dict) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    mapping = cfg.get("language_id_by_extension", {})
    return mapping.get(ext, lang)
