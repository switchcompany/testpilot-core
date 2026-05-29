"""Pydantic models for test results and coverage reports."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TestFileResult(BaseModel):
    """Result of a single generated test file."""

    file_path: str
    test_count: int = 0
    passed: int = 0
    failed: int = 0
    errors: list[str] = Field(default_factory=list)
    compile_errors: list[str] = Field(default_factory=list)


class CoverageEntry(BaseModel):
    """Coverage data for a single source file."""

    file_path: str
    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    lines_covered: int = 0
    lines_total: int = 0


class CoverageReport(BaseModel):
    """Aggregated coverage report."""

    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    files: list[CoverageEntry] = Field(default_factory=list)
    total_lines_covered: int = 0
    total_lines: int = 0
    total_tests: int = 0
    tests_passed: int = 0
    tests_failed: int = 0


class IterationResult(BaseModel):
    """Result of a single generation iteration."""

    iteration: int
    tests_generated: list[TestFileResult] = Field(default_factory=list)
    coverage_before: float = 0.0
    coverage_after: float = 0.0
    coverage_delta: float = 0.0
    rolled_back: bool = False
    duration_seconds: float = 0.0


class RunReport(BaseModel):
    """Final report for a complete Forge Core run."""

    project_name: str = ""
    project_path: str = ""
    language: str = ""
    framework: str = ""
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Coverage
    coverage_before: float = 0.0
    coverage_after: float = 0.0
    coverage_delta: float = 0.0

    # Tests
    total_tests_before: int = 0
    total_tests_after: int = 0
    tests_generated: int = 0
    tests_fixed: int = 0
    test_files_created: list[str] = Field(default_factory=list)

    # Iterations
    iterations: list[IterationResult] = Field(default_factory=list)
    total_iterations: int = 0
    rollbacks: int = 0

    # Learning
    patterns_discovered: int = 0
    journeys_mapped: int = 0
    dtos_registered: int = 0

    # Metadata
    mode: str = "full"
    target_coverage: float = 90.0
    production_files_changed: int = 0  # must always be 0
