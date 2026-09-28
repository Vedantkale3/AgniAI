"""
Local Python sandbox runner.

This runner is intended for controlled local demonstrations. It executes
user-provided Python in a temporary child process, applies a timeout, and
returns stdout/stderr without crashing the FastAPI process.
"""

import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from app.config import settings


async def run_python_sandboxed(code: str) -> dict:
    if not code or not code.strip():
        return {
            "ok": False,
            "stdout": "",
            "stderr": "No Python code was provided.",
            "timed_out": False,
            "return_code": None,
        }

    sandbox_dir = Path(tempfile.mkdtemp(prefix="mrpl_sandbox_"))
    script_path = sandbox_dir / "main.py"
    script_path.write_text(code, encoding="utf-8")

    creation_flags = 0

    if os.name == "nt":
        creation_flags = subprocess.CREATE_NO_WINDOW

    process = None

    try:
        process = await asyncio.to_thread(
            subprocess.Popen,
            [sys.executable, "-I", str(script_path)],
            cwd=str(sandbox_dir),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creation_flags,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                asyncio.to_thread(process.communicate),
                timeout=settings.sandbox_timeout_seconds,
            )

            return {
                "ok": process.returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "timed_out": False,
                "return_code": process.returncode,
            }

        except asyncio.TimeoutError:
            process.kill()
            stdout, stderr = await asyncio.to_thread(
                process.communicate
            )

            return {
                "ok": False,
                "stdout": stdout,
                "stderr": (
                    stderr
                    or "Sandbox execution timed out."
                ),
                "timed_out": True,
                "return_code": process.returncode,
            }

    except Exception as error:
        if process is not None and process.poll() is None:
            process.kill()
            await asyncio.to_thread(process.communicate)

        return {
            "ok": False,
            "stdout": "",
            "stderr": f"Sandbox failed to start: {error}",
            "timed_out": False,
            "return_code": None,
        }

    finally:
        try:
            for path in sandbox_dir.iterdir():
                path.unlink(missing_ok=True)
            sandbox_dir.rmdir()
        except OSError:
            pass


def cleanup_sandbox(workdir: str | None) -> None:
    if not workdir:
        return

    path = Path(workdir)

    if not path.exists() or not path.is_dir():
        return

    for child in path.iterdir():
        if child.is_file():
            child.unlink(missing_ok=True)

    path.rmdir()
