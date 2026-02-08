LANGUAGE_CONFIG = {
    "python": {
        "cmd": ["pyright-langserver", "--stdio"], 
        "extensions": [".py"],
        "root_marker": ["pyproject.toml", "setup.py", ".git"]
    },
    "javascript": {
        "cmd": ["typescript-language-server", "--stdio"],
        "extensions": [".js", ".jsx", ".ts", ".tsx"],
        "root_marker": ["package.json", ".git"]
    },
    "go": {
        "cmd": ["gopls"],
        "extensions": [".go"],
        "root_marker": ["go.mod", ".git"]
    },
    "rust": {
        "cmd": ["rust-analyzer"],
        "extensions": [".rs"],
        "root_marker": ["Cargo.toml", ".git"]
    }
}

def get_config(file_path: str):
    for lang, cfg in LANGUAGE_CONFIG.items():
        if any (file_path.endswith(ext) for ext in cfg["extensions"]):
            return lang, cfg
    return None, None

