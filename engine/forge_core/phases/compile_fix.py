"""Phase 5b — Auto compile-fix loop."""

from __future__ import annotations

from pathlib import Path

from forge_core.ai.provider import complete
from forge_core.core.file_manager import FileManager
from forge_core.models.config import ForgeConfig
from forge_core.utils import logger
from forge_core.utils.shell import run as shell_run

import json


def fix_compilation_errors(
    config: ForgeConfig,
    file_manager: FileManager,
    test_command: str,
    max_attempts: int = 3,
) -> bool:
    """Attempt to fix compilation errors in generated tests.

    Returns True if tests compile after fixes.
    """
    for attempt in range(1, max_attempts + 1):
        result = shell_run(test_command, cwd=config.project_path, timeout=300)

        if result.success:
            return True

        # Check if it's a compilation error (not a test failure)
        if not _is_compile_error(result.output):
            return True  # Tests compiled but some failed — that's okay

        logger.info(f"Compile-fix attempt {attempt}/{max_attempts}")

        # Ask AI to fix
        response = complete(
            config=config.ai,
            system_prompt=(
                "Fix the compilation errors in these test files. "
                "Return JSON with fixed_files: [{path, content}]. "
                "Only fix imports, types, and syntax — don't change test logic."
            ),
            user_prompt=f"Compilation errors:\n```\n{result.output[:4000]}\n```",
            json_mode=True,
        )

        try:
            data = json.loads(response)
            for fix in data.get("fixed_files", []):
                path = fix.get("path", "")
                content = fix.get("content", "")
                if path and content:
                    file_manager.write_file(path, content)
        except json.JSONDecodeError:
            logger.warn("Failed to parse compile-fix response")
            continue

    return False


def _is_compile_error(output: str) -> bool:
    """Detect if the output contains compilation errors (vs test failures)."""
    compile_indicators = [
        "Compilation failed",
        "COMPILE ERROR",
        "error: cannot find symbol",
        "Unresolved reference",
        "SyntaxError",
        "IndentationError",
        "ImportError",
        "ModuleNotFoundError",
        "error TS",
        "cannot resolve",
        "does not exist",
    ]
    return any(indicator.lower() in output.lower() for indicator in compile_indicators)
