"""GUI-side runner: launches execution_worker in a subprocess with timeout/cancel."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    success: bool
    scene: dict | None
    stdout: str
    stderr: str
    error: dict | None
    duration: float
    timed_out: bool = False
    cancelled: bool = False


class ExecutionRunner:
    """Runs user code out-of-process. Call run() from a worker thread; stop() cancels."""

    def __init__(self, timeout: float = 20.0):
        self.timeout = float(timeout)
        self._proc: subprocess.Popen | None = None
        self._cancelled = False
        self._lock = threading.Lock()

    def stop(self) -> None:
        with self._lock:
            self._cancelled = True
            proc = self._proc
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

    @property
    def cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def run(self, source: str) -> ExecutionResult:
        with self._lock:
            self._cancelled = False
            self._proc = None
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        src_file = out_file = None
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
                f.write(source)
                src_file = f.name
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
                out_file = f.name
            cmd = [sys.executable, "-m", "core.execution_worker",
                   "--source", src_file, "--output", out_file]
            with self._lock:
                if self._cancelled:
                    return ExecutionResult(False, None, "", "", {"line": 0, "message": "Cancelled."}, 0.0, cancelled=True)
                self._proc = subprocess.Popen(cmd, cwd=project_root,
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                proc = self._proc
            try:
                _, stderr_data = proc.communicate(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                try:
                    proc.communicate(timeout=5)
                except Exception:
                    pass
                return ExecutionResult(False, None, "", "Execution timed out.",
                                       {"line": 0, "message": f"Execution timed out after {self.timeout:g}s."},
                                       self.timeout, timed_out=True)
            if self.cancelled:
                return ExecutionResult(False, None, "", "", {"line": 0, "message": "Execution stopped by user."},
                                       0.0, cancelled=True)
            try:
                with open(out_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                err_text = (stderr_data.decode("utf-8", "replace") if stderr_data else "")
                return ExecutionResult(False, None, "", err_text,
                                       {"line": 0, "message": f"Worker produced no valid output: {e}\n{err_text}"},
                                       0.0)
            # Validate payload shape before trusting it
            scene = data.get("scene")
            if data.get("success") and not isinstance(scene, dict):
                return ExecutionResult(False, None, str(data.get("stdout", "")), "",
                                       {"line": 0, "message": "Worker returned malformed scene data."}, 0.0)
            if isinstance(scene, dict):
                objs = scene.get("objects", [])
                if not isinstance(objs, list) or len(objs) > 500:
                    return ExecutionResult(False, None, "", "", {"line": 0, "message": "Invalid scene payload."}, 0.0)
            return ExecutionResult(
                success=bool(data.get("success")),
                scene=scene,
                stdout=str(data.get("stdout", "")),
                stderr=str(data.get("stderr", "")),
                error=data.get("error"),
                duration=float(data.get("duration", 0.0)),
            )
        finally:
            with self._lock:
                self._proc = None
            for p in (src_file, out_file):
                if p:
                    try:
                        os.unlink(p)
                    except OSError:
                        pass
