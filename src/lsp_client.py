import subprocess
import json
import threading
import time
import logging
from typing import Dict, Any, Optional


class LSPClient:
    def __init__(self, command: list):
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0  # Unbuffered
        )
        self.request_id = 0
        self.responses = {}
        self.lock = threading.Lock()
        self.running = True

        # Start listener thread
        self.listener = threading.Thread(target=self._listen, daemon=True)
        self.listener.start()

    def _listen(self):
        """Continuously reads stdout from the LSP server."""
        while self.running:
            line = self.process.stdout.readline()
            if not line:
                break

            # 1. Parse Header (Content-Length: 123)
            content_length = 0
            try:
                header = line.decode('utf-8').strip()
                if header.startswith("Content-Length:"):
                    content_length = int(header.split(":")[1])
                    self.process.stdout.readline()  # Skip empty line
                else:
                    continue
            except:
                continue

            # 2. Read Body
            if content_length > 0:
                body = self.process.stdout.read(content_length)
                try:
                    data = json.loads(body)
                    if "id" in data:
                        with self.lock:
                            self.responses[data["id"]] = data
                except json.JSONDecodeError:
                    pass

    def send_request(self, method: str, params: Dict[str, Any]) -> Any:
        """Sends a JSON-RPC request and waits for the response."""
        self.request_id += 1
        req_id = self.request_id

        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }

        body = json.dumps(request)
        message = f"Content-Length: {len(body)}\r\n\r\n{body}"

        self.process.stdin.write(message.encode('utf-8'))
        self.process.stdin.flush()

        # Wait for response (Pollling for simplicity in this synchronous CLI)
        start_time = time.time()
        while time.time() - start_time < 5:  # 5s timeout
            with self.lock:
                if req_id in self.responses:
                    resp = self.responses.pop(req_id)
                    return resp.get("result")
            time.sleep(0.01)

        return None

    def shutdown(self):
        self.running = False
        try:
            self.send_request("shutdown", {})
            self.process.terminate()
        except:
            pass
