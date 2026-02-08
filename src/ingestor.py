import os
import sys
from pathlib import Path
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from src.lsp_client import LSPClient
from src.language_config import get_config
from src.graph import KnowledgeGraph 
from src.utils import to_uri


class LSPIngestor:
    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()
        self.graph = KnowledgeGraph()
        self.clients = {}

    def _get_client(self, lang: str, config: dict):
        if lang not in self.clients:
            print(f"🔌 Starting {lang} server...")
            client = LSPClient(config["cmd"])

            root_uri = to_uri(self.root)
            client.send_request("initialize", {
                "processId": os.getpid(),
                "rootUri": root_uri,
                "capabilities": {
                    "textDocument": {
                        "documentSymbol": {"hierarchicalDocumentSymbolSupport": True},
                        "references": {}
                    }
                }
            })
            client.send_request("initialized", {})
            self.clients[lang] = client
        return self.clients[lang]

    def process_file(self, file_path: Path):
        lang, config = get_config(str(file_path))
        if not lang:
            return

        client = self._get_client(lang, config)
        uri = to_uri(file_path)

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        client.send_request("textDocument/didOpen", {
            "textDocument": {
                "uri": uri,
                "languageId": lang,
                "version": 1,
                "text": text
            }
        })

        symbols = client.send_request("textDocument/documentSymbol", {
            "textDocument": {"uri": uri}
        })

        if symbols:
            self._ingest_symbols(str(file_path), symbols)

    def _ingest_symbols(self, file_path: str, symbols: list):

        for sym in symbols:

            name = sym["name"]
            kind = sym["kind"]

            self.graph.add_node(name, file_path, kind)

            if "children" in sym:
                self._ingest_symbols(file_path, sym["children"])

    def run(self):

        files = [Path(root)/f for root, _, fs in os.walk(self.root)
                 for f in fs]

        for f in tqdm(files, desc="Analyzing"):
            self.process_file(f)

        for client in self.clients.values():
            client.shutdown()

        self.graph.save("knowledge_map.json")
