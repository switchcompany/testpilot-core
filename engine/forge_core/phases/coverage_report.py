"""Phase 6 — Generate final coverage report."""

from __future__ import annotations

from forge_core.core.coverage import run_coverage
from forge_core.models.config import ForgeConfig
from forge_core.models.project import ProjectGraph
from forge_core.models.test_result import CoverageReport


def run(config: ForgeConfig, project_graph: ProjectGraph) -> CoverageReport:
    """Run the full test suite and generate the final coverage report."""
    tech = project_graph.tech_stack
    command = tech.coverage_command or tech.test_command

    if not command:
        return CoverageReport()

    return run_coverage(config.project_path, command)
