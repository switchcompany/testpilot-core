"""Safe file read/write with rollback protection."""

from __future__ import annotations

import shutil
from pathlib import Path

from forge_core.utils import logger


class FileManager:
    """Manages file operations with rollback support.

    Tracks all written files so they can be reverted if coverage drops.
    """

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self._written_files: dict[str, str | None] = {}  # path → original content (None if new)
        self._backup_dir: Path | None = None

    def read_file(self, relative_path: str) -> str:
        """Read a file from the project."""
        full_path = self.project_path / relative_path
        if not full_path.exists():
            return ""
        return full_path.read_text(encoding="utf-8")

    def read_files(self, glob_pattern: str) -> dict[str, str]:
        """Read multiple files matching a glob pattern. Returns {relative_path: content}."""
        results: dict[str, str] = {}
        for path in sorted(self.project_path.glob(glob_pattern)):
            if path.is_file():
                rel = str(path.relative_to(self.project_path))
                try:
                    results[rel] = path.read_text(encoding="utf-8")
                except (UnicodeDecodeError, PermissionError):
                    continue
        return results

    def write_file(self, relative_path: str, content: str) -> None:
        """Write a file, tracking it for potential rollback."""
        full_path = self.project_path / relative_path

        # Store original state for rollback
        if relative_path not in self._written_files:
            if full_path.exists():
                self._written_files[relative_path] = full_path.read_text(encoding="utf-8")
            else:
                self._written_files[relative_path] = None

        # Ensure parent dirs exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

    def rollback(self) -> int:
        """Rollback all files written since last checkpoint. Returns count of files rolled back."""
        count = 0
        for rel_path, original in self._written_files.items():
            full_path = self.project_path / rel_path
            if original is None:
                # File was newly created — delete it
                if full_path.exists():
                    full_path.unlink()
                    count += 1
            else:
                # File was modified — restore original
                full_path.write_text(original, encoding="utf-8")
                count += 1

        if count:
            logger.warn(f"Rolled back {count} files")
        self._written_files.clear()
        return count

    def checkpoint(self) -> None:
        """Accept current state — clear rollback history."""
        self._written_files.clear()

    def list_source_files(self, source_root: str = "src") -> list[str]:
        """List all source files under the source root."""
        root = self.project_path / source_root
        if not root.exists():
            return []
        return [
            str(p.relative_to(self.project_path))
            for p in sorted(root.rglob("*"))
            if p.is_file() and not p.name.startswith(".")
        ]

    def list_test_files(self, test_root: str = "src/test") -> list[str]:
        """List all test files under the test root."""
        root = self.project_path / test_root
        if not root.exists():
            return []
        return [
            str(p.relative_to(self.project_path))
            for p in sorted(root.rglob("*"))
            if p.is_file() and not p.name.startswith(".")
        ]

    @property
    def pending_rollback_count(self) -> int:
        return len(self._written_files)
