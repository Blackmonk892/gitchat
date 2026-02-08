from src.graph import KnowledgeGraph
from src.utils import to_uri
from src.language_config import get_config, get_language_id
from src.lsp_client import LSPClient
import os
import sys
import time
from pathlib import Path
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class LSPIngestor:
    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()
        self.graph = KnowledgeGraph()
        self.clients = {}
        self.ignore_dirs = {
            ".git", ".hg", ".svn", "node_modules", "dist", "build", ".next", ".venv", "venv"
        }

    def _get_client(self, lang: str, config: dict):
        if lang not in self.clients:
            print(f"🔌 Starting {lang} server...")
            client = LSPClient(config["cmd"])

            root_uri = to_uri(self.root)
            init_result = client.send_request("initialize", {
                "processId": os.getpid(),
                "rootPath": str(self.root),
                "rootUri": root_uri,
                "workspaceFolders": [
                    {"uri": root_uri, "name": self.root.name}
                ],
                "capabilities": {
                    "textDocument": {
                        "documentSymbol": {"hierarchicalDocumentSymbolSupport": True},
                        "references": {}
                    }
                }
            })
            if init_result is None:
                print(
                    "\033[91m[LSP ERROR] initialize failed or timed out\033[0m")
                self.clients[lang] = None
                return None
            client.send_notification("initialized", {})
            client.send_notification(
                "workspace/didChangeConfiguration", {"settings": {}})
            self.clients[lang] = client
        return self.clients[lang]

    def process_file(self, file_path: Path):
        lang, config = get_config(str(file_path))
        if not lang:
            return

        client = self._get_client(lang, config)
        uri = to_uri(file_path)
        language_id = get_language_id(str(file_path), lang, config)

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        symbols = None
        if client:
            client.send_notification("textDocument/didOpen", {
                "textDocument": {
                    "uri": uri,
                    "languageId": language_id,
                    "version": 1,
                    "text": text
                }
            })

            symbols = self._request_symbols(client, uri)

        if symbols:
            self._ingest_symbols(str(file_path), symbols)
        else:
            if lang in {"javascript"}:
                fallback_symbols = self._fallback_js_symbols(text)
                if fallback_symbols:
                    print(f"[LSP] Fallback parser used for {file_path.name}")
                    self._ingest_symbols(str(file_path), fallback_symbols)

    def _ingest_symbols(self, file_path: str, symbols: list):

        for sym in symbols:

            name = sym.get("name")
            kind = sym.get("kind")
            if not name or not kind:
                continue

            self.graph.add_node(name, file_path, kind)

            if "children" in sym and isinstance(sym["children"], list):
                self._ingest_symbols(file_path, sym["children"])

    def _request_symbols(self, client: LSPClient, uri: str):
        # Give the server a brief moment to index the opened document.
        for delay in (0.1, 0.3, 0.6):
            time.sleep(delay)
            symbols = client.send_request("textDocument/documentSymbol", {
                "textDocument": {"uri": uri}
            }, timeout_s=20.0)
            if symbols is not None:
                return symbols
        return None

    def _fallback_js_symbols(self, text: str):
        # Very simple JS/JSX symbol extraction to avoid zero results when LSP is unavailable.
        import re
        symbols = []

        class_re = re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)")
        func_re = re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(")
        arrow_re = re.compile(
            r"\b(const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(async\s*)?\(?[^\n)]*\)?\s*=>"
        )

        for m in class_re.finditer(text):
            symbols.append({"name": m.group(1), "kind": 5})

        for m in func_re.finditer(text):
            symbols.append({"name": m.group(1), "kind": 12})

        for m in arrow_re.finditer(text):
            symbols.append({"name": m.group(2), "kind": 12})

        return symbols

    def run(self):

        files = []
        for root, dirs, fs in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            for f in fs:
                files.append(Path(root) / f)

        for f in tqdm(files, desc="Analyzing"):
            self.process_file(f)

        for client in self.clients.values():
            if client:
                client.shutdown()

        self.graph.save("knowledge_map.json")
