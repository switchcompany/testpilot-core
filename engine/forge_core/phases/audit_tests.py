"""Phase 3 — Audit existing tests and establish baseline."""

from __future__ import annotations

from pathlib import Path

from forge_core.core.coverage import run_coverage
from forge_core.core.file_manager import FileManager
from forge_core.models.config import ForgeConfig
from forge_core.models.project import ProjectGraph
from forge_core.models.test_result import CoverageReport
from forge_core.utils import logger


def run(
    config: ForgeConfig,
    file_manager: FileManager,
    prompts_dir: Path,
    project_graph: ProjectGraph,
) -> CoverageReport:
    """Audit existing tests and get baseline coverage."""
    tech = project_graph.tech_stack

    if not tech.coverage_command:
        logger.warn("No coverage command detected — using test command")
        tech.coverage_command = tech.test_command

    if not tech.coverage_command:
        logger.warn("No test/coverage command found")
        return CoverageReport()

    # Run existing tests and get baseline coverage
    report = run_coverage(config.project_path, tech.coverage_command)

    return report
