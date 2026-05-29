"""Subprocess wrapper for running build/test commands safely."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from forge_core.utils import logger


@dataclass
class ShellResult:
    """Result of a shell command execution."""

    command: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float = 0.0

    @property
    def success(self) -> bool:
        return self.returncode == 0

    @property
    def output(self) -> str:
        return self.stdout + self.stderr


def run(
    command: str,
    cwd: Path | str | None = None,
    timeout: int = 600,
    capture: bool = True,
    env: dict[str, str] | None = None,
) -> ShellResult:
    """Run a shell command and return structured result.

    Args:
        command: Shell command to execute.
        cwd: Working directory.
        timeout: Max seconds before kill (default 10 min).
        capture: Whether to capture stdout/stderr.
        env: Extra environment variables (merged with current env).
    """
    import os
    import time

    full_env = {**os.environ, **(env or {})}

    logger.info(f"$ {command}")

    start = time.time()
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd) if cwd else None,
            capture_output=capture,
            text=True,
            timeout=timeout,
            env=full_env,
        )
        duration = time.time() - start

        return ShellResult(
            command=command,
            returncode=result.returncode,
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            duration_seconds=duration,
        )
    except subprocess.TimeoutExpired:
        duration = time.time() - start
        logger.warn(f"Command timed out after {timeout}s: {command}")
        return ShellResult(
            command=command,
            returncode=-1,
            stdout="",
            stderr=f"TIMEOUT after {timeout}s",
            duration_seconds=duration,
        )
    except Exception as e:
        duration = time.time() - start
        logger.error(f"Command failed: {e}")
        return ShellResult(
            command=command,
            returncode=-1,
            stdout="",
            stderr=str(e),
            duration_seconds=duration,
        )
