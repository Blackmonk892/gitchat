# File: gitchat/main.py
from src.ingestor import LSPIngestor
import sys
import os
import argparse

# 1. Ensure the root directory is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 2. Now we can use absolute or relative imports from src


def main():
    parser = argparse.ArgumentParser(description="LSP Code Mapper")
    parser.add_argument(
        "path", help="Absolute path to the project you want to analyze")
    args = parser.parse_args()

    project_path = args.path

    if not os.path.exists(project_path):
        print(f"❌ Error: Path '{project_path}' not found.")
        return

    print(f"🚀 Initializing LSP Ingestor for: {project_path}")
    ingestor = LSPIngestor(project_path)
    ingestor.run()


if __name__ == "__main__":
    main()
