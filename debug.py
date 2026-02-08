import subprocess
import sys
import os
import time

# --- CONFIG ---
# We will test the Javascript server since that's your main target
CMD = ["cmd.exe", "/c", "typescript-language-server.cmd", "--stdio"]
PROJECT_PATH = "C:\\Users\\xoxo3\\Desktop\\Projects\\google_docs_clone"
# --------------


def to_uri(path):
    from pathlib import Path
    return Path(path).as_uri()


def run_debug():
    print(f"🚀 Launching: {CMD}")
    process = subprocess.Popen(
        CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False
    )

    # 1. Send Initialize
    root_uri = to_uri(PROJECT_PATH)
    body = f'{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{"processId":{os.getpid()},"rootUri":"{root_uri}","capabilities":{{"textDocument":{{"documentSymbol":{{"hierarchicalDocumentSymbolSupport":true}}}}}}}}}}'
    message = f"Content-Length: {len(body)}\r\n\r\n{body}"

    print(f"📤 Sending Payload:\n{message}")
    process.stdin.write(message.encode('utf-8'))
    process.stdin.flush()

    print("\n⏳ Listening for raw output (Max 5 seconds)...")
    start = time.time()
    while time.time() - start < 5:
        # Read stdout
        output = process.stdout.read(1)  # Read byte by byte
        if output:
            sys.stdout.buffer.write(output)
            sys.stdout.flush()

        # Read stderr (Errors)
        err = process.stderr.read(1)
        if err:
            sys.stdout.buffer.write(b"\n[STDERR] ")
            sys.stdout.buffer.write(err)
            sys.stdout.flush()

    process.terminate()
    print("\n✅ Done.")


if __name__ == "__main__":
    run_debug()
