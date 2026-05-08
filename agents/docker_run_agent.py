import queue
import subprocess
import threading
import time


class DockerRunAgent:
    """Runs the output project via docker compose, captures stdout for a fixed window, then stops."""

    def __init__(self, output_dir: str = "outputs", timeout: int = 30):
        self.output_dir = output_dir
        self.timeout = timeout

    def run(self) -> str:
        proc = subprocess.Popen(
            ["docker", "compose", "up", "--build"],
            cwd=self.output_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        lines = []
        q = queue.Queue()

        def _read():
            for line in proc.stdout:
                q.put(line.rstrip())
            q.put(None)

        threading.Thread(target=_read, daemon=True).start()

        deadline = time.time() + self.timeout
        while time.time() < deadline:
            try:
                line = q.get(timeout=0.5)
                if line is None:
                    break
                lines.append(line)
                print(line)
            except queue.Empty:
                continue

        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

        subprocess.run(
            ["docker", "compose", "down"],
            cwd=self.output_dir,
            capture_output=True,
        )

        return "\n".join(lines)
