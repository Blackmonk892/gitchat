import subprocess
import json
import threading
import time
import logging
import sys
import os


class LSPClient:
    def __init__(self, command: list):
        self.command = self._fix_windows_command(command)
        print(f"🔌 LSP Launching: {self.command}")

        try:
            # 1. Start the process
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0  # Unbuffered binary IO
            )
        except Exception as e:
            print(f"❌ Failed to start LSP: {e}")
            self.running = False
            return

        self.request_id = 0
        self.responses = {}
        self.lock = threading.Lock()
        self.running = True

        # 2. Start Listeners (Stdout for data, Stderr for errors)
        self.listener = threading.Thread(
            target=self._listen_stdout, daemon=True)
        self.listener.start()

        self.error_listener = threading.Thread(
            target=self._listen_stderr, daemon=True)
        self.error_listener.start()

    def _fix_windows_command(self, cmd: list) -> list:
        """
        On Windows, executing 'script.cmd' directly via Popen often breaks pipes.
        We must wrap it in 'cmd.exe /c'.
        """
        if sys.platform == "win32":
            executable = cmd[0]
            if executable.lower().endswith(".cmd") or executable.lower().endswith(".bat"):
                # We wrap the command: cmd.exe /c "path/to/script.cmd" arg1 arg2
                return ["cmd.exe", "/c"] + cmd
        return cmd

    def _listen_stderr(self):
        """Reads hidden errors from the server and prints them."""
        while self.running:
            line = self.process.stderr.readline()
            if not line:
                break
            try:
                # Log server errors in RED
                print(
                    f"\033[91m[LSP STDERR] {line.decode('utf-8').strip()}\033[0m")
            except:
                pass

    def _listen_stdout(self):
        """Continuously reads stdout from the LSP server."""
        while self.running:
            try:
                # Check if process is dead
                if self.process.poll() is not None:
                    print("❌ LSP Process died unexpectedly.")
                    break

                # 1. Read Headers
                line = self.process.stdout.readline()
                if not line:
                    break

                header_line = line.decode('utf-8').strip()
                if not header_line.startswith("Content-Length:"):
                    continue

                # 2. Parse Content-Length
                content_length = int(header_line.split(":")[1])
                self.process.stdout.readline()  # Skip the empty line (\r\n)

                # 3. Read Body
                if content_length > 0:
                    body = self.process.stdout.read(content_length)
                    data = json.loads(body)

                    if "id" in data:
                        with self.lock:
                            self.responses[data["id"]] = data
            except Exception as e:
                # print(f"Parser Error: {e}")
                pass

    def send_request(self, method: str, params: dict) -> dict:
        """Sends a JSON-RPC request and waits for the response."""
        if not self.running or self.process.poll() is not None:
            return None

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

        try:
            self.process.stdin.write(message.encode('utf-8'))
            self.process.stdin.flush()
        except Exception:
            return None

        # Wait for response (Increased timeout to 10s for slow Windows pipes)
        start_time = time.time()
        while time.time() - start_time < 10:
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
