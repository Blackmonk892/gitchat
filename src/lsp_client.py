import subprocess
import json
import threading
import time
import sys
import os


class LSPClient:
    def __init__(self, command: list):
        self.command = command
        self.responses = {}
        self.request_id = 0
        self.lock = threading.Lock()
        self.running = True

        # --- WINDOWS FIX: Use shell=True ---
        # This bypasses the need for 'cmd /c' wrappers and fixes pipe buffering issues.
        use_shell = (sys.platform == "win32")

        print(f"🔌 LSP Launching (shell={use_shell}): {self.command}")

        try:
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=use_shell,  # <--- CRITICAL FIX
                bufsize=0         # Unbuffered
            )
        except Exception as e:
            print(f"❌ Failed to start LSP: {e}")
            self.running = False
            return

        # Start Listeners
        self.listener = threading.Thread(
            target=self._listen_stdout, daemon=True)
        self.listener.start()

        self.error_listener = threading.Thread(
            target=self._listen_stderr, daemon=True)
        self.error_listener.start()

    def _read_headers(self):
        """
        Read LSP headers until the empty line.
        Returns a dict of lower-cased header names to values.
        """
        headers = {}
        while True:
            line = self.process.stdout.readline()
            if not line:
                return None
            text = line.decode('utf-8', errors='ignore').strip()
            if text == "":
                break
            if ":" in text:
                name, value = text.split(":", 1)
                headers[name.strip().lower()] = value.strip()
        return headers

    def _listen_stderr(self):
        """Prints any errors from the server in RED."""
        while self.running:
            try:
                line = self.process.stderr.readline()
                if not line:
                    break
                # Clean up the output
                msg = line.decode('utf-8', errors='ignore').strip()
                if msg:
                    print(f"\033[91m[LSP ERROR] {msg}\033[0m")
            except:
                break

    def _listen_stdout(self):
        """Reads JSON-RPC messages from the server."""
        while self.running:
            try:
                # 1. Read Headers
                headers = self._read_headers()
                if not headers:
                    break

                # 2. Parse Length
                if "content-length" not in headers:
                    continue
                length = int(headers["content-length"])

                # 3. Read Body
                body = self.process.stdout.read(length)
                if not body:
                    break

                response = json.loads(body)
                if "id" in response:
                    with self.lock:
                        self.responses[response["id"]] = response

            except Exception as e:
                # print(f"Reader Error: {e}")
                pass

    def _send_message(self, payload: dict):
        body = json.dumps(payload)
        message = f"Content-Length: {len(body)}\r\n\r\n{body}"
        self.process.stdin.write(message.encode('utf-8'))
        self.process.stdin.flush()

    def send_request(self, method: str, params: dict, timeout_s: float = 5.0) -> dict:
        if not self.running:
            return None

        self.request_id += 1
        req_id = self.request_id

        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }

        try:
            self._send_message(payload)
        except OSError:
            return None

        # Wait for response
        start = time.time()
        while time.time() - start < timeout_s:
            with self.lock:
                if req_id in self.responses:
                    resp = self.responses.pop(req_id)
                    if "error" in resp:
                        err = resp.get("error") or {}
                        code = err.get("code")
                        msg = err.get("message")
                        print(f"\033[91m[LSP ERROR] {code}: {msg}\033[0m")
                        return None
                    return resp.get("result")
            time.sleep(0.01)

        return None

    def send_notification(self, method: str, params: dict):
        if not self.running:
            return
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        try:
            self._send_message(payload)
        except OSError:
            return

    def shutdown(self):
        self.running = False
        try:
            self.process.terminate()
        except:
            pass
