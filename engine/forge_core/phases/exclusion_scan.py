"""Phase 1.5 — Coverage exclusion scan."""

from __future__ import annotations

from forge_core.core.file_manager import FileManager
from forge_core.models.config import ForgeConfig
from forge_core.models.project import TechStack
from forge_core.utils import logger


def run(
    config: ForgeConfig,
    file_manager: FileManager,
    tech_stack: TechStack,
) -> list[str]:
    """Scan for coverage exclusions in build/config files.

    Returns list of excluded package/path patterns.
    """
    exclusions: list[str] = []

    # Check common exclusion locations based on language
    if tech_stack.language.lower() in ("kotlin", "java"):
        _scan_gradle_exclusions(file_manager, exclusions)
        _scan_jacoco_exclusions(file_manager, exclusions)
    elif tech_stack.language.lower() == "python":
        _scan_pytest_exclusions(file_manager, exclusions)
    elif tech_stack.language.lower() == "go":
        _scan_go_exclusions(file_manager, exclusions)

    if exclusions:
        logger.info(f"Exclusions: {', '.join(exclusions[:5])}")

    return exclusions


def _scan_gradle_exclusions(fm: FileManager, exclusions: list[str]) -> None:
    """Scan build.gradle for jacocoTestReport exclusions."""
    for f in ["build.gradle", "build.gradle.kts"]:
        content = fm.read_file(f)
        if "classDirectories" in content and "exclude" in content:
            # Extract excluded patterns
            import re

            for m in re.finditer(r"""exclude\s*\(\s*["'](.+?)["']""", content):
                exclusions.append(m.group(1))


def _scan_jacoco_exclusions(fm: FileManager, exclusions: list[str]) -> None:
    """Scan jacoco config for exclusions."""
    content = fm.read_file("jacoco.exec")
    # JaCoCo exclusions are typically in build files, handled above


def _scan_pytest_exclusions(fm: FileManager, exclusions: list[str]) -> None:
    """Scan pyproject.toml or .coveragerc for omit patterns."""
    import re

    for f in ["pyproject.toml", ".coveragerc", "setup.cfg"]:
        content = fm.read_file(f)
        if content:
            for m in re.finditer(r"omit\s*=\s*(.+?)(?:\n\[|\n\n|\Z)", content, re.DOTALL):
                paths = m.group(1).strip().split("\n")
                exclusions.extend(p.strip() for p in paths if p.strip())


def _scan_go_exclusions(fm: FileManager, exclusions: list[str]) -> None:
    """Go doesn't have standard exclusion configs — check Makefile."""
    content = fm.read_file("Makefile")
    if content:
        import re

        for m in re.finditer(r"-coverprofile.*?(?:grep\s+-v\s+)(.+?)(?:\s|$)", content):
            exclusions.append(m.group(1))
