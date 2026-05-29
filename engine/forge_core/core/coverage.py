"""Coverage runner — execute test commands and parse coverage reports."""

from __future__ import annotations

import re
from pathlib import Path

from forge_core.models.test_result import CoverageEntry, CoverageReport
from forge_core.utils import logger
from forge_core.utils.shell import run


def run_tests(project_path: Path, test_command: str) -> tuple[bool, str]:
    """Run the project's test command. Returns (success, output)."""
    result = run(test_command, cwd=project_path, timeout=600)
    return result.success, result.output


def run_coverage(project_path: Path, coverage_command: str) -> CoverageReport:
    """Run the project's coverage command and parse the report."""
    result = run(coverage_command, cwd=project_path, timeout=600)

    report = CoverageReport()

    # Try parsing various coverage report formats
    report = _try_parse_jacoco(project_path, report)
    if report.total_lines == 0:
        report = _try_parse_cobertura(project_path, report)
    if report.total_lines == 0:
        report = _try_parse_lcov(project_path, report)
    if report.total_lines == 0:
        report = _try_parse_pytest_cov(result.output, report)
    if report.total_lines == 0:
        report = _try_parse_go_cover(result.output, report)
    if report.total_lines == 0:
        # Fallback: try to extract percentage from output
        report = _try_parse_generic(result.output, report)

    # Count tests from output
    test_counts = _parse_test_counts(result.output)
    report.total_tests = test_counts.get("total", 0)
    report.tests_passed = test_counts.get("passed", 0)
    report.tests_failed = test_counts.get("failed", 0)

    return report


def _try_parse_jacoco(project_path: Path, report: CoverageReport) -> CoverageReport:
    """Parse JaCoCo CSV or XML report (Kotlin/Java)."""
    # Look for CSV report first
    csv_patterns = [
        "build/reports/jacoco/test/jacocoTestReport.csv",
        "build/reports/jacoco/jacocoTestReport.csv",
        "target/site/jacoco/jacoco.csv",
    ]
    for pattern in csv_patterns:
        csv_path = project_path / pattern
        if csv_path.exists():
            return _parse_jacoco_csv(csv_path, report)

    # Try XML
    xml_patterns = [
        "build/reports/jacoco/test/jacocoTestReport.xml",
        "target/site/jacoco/jacoco.xml",
    ]
    for pattern in xml_patterns:
        xml_path = project_path / pattern
        if xml_path.exists():
            return _parse_jacoco_xml(xml_path, report)

    return report


def _parse_jacoco_csv(csv_path: Path, report: CoverageReport) -> CoverageReport:
    """Parse JaCoCo CSV report."""
    import csv

    total_missed = 0
    total_covered = 0

    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                missed = int(row.get("LINE_MISSED", 0))
                covered = int(row.get("LINE_COVERED", 0))
                total_missed += missed
                total_covered += covered

                pkg = row.get("PACKAGE", "")
                cls = row.get("CLASS", "")
                total = missed + covered
                if total > 0:
                    report.files.append(
                        CoverageEntry(
                            file_path=f"{pkg}/{cls}",
                            line_coverage=round(covered / total * 100, 1),
                            lines_covered=covered,
                            lines_total=total,
                        )
                    )

        total = total_missed + total_covered
        report.total_lines = total
        report.total_lines_covered = total_covered
        if total > 0:
            report.line_coverage = round(total_covered / total * 100, 1)
    except Exception as e:
        logger.warn(f"Failed to parse JaCoCo CSV: {e}")

    return report


def _parse_jacoco_xml(xml_path: Path, report: CoverageReport) -> CoverageReport:
    """Parse JaCoCo XML report — extract LINE counter from root."""
    import xml.etree.ElementTree as ET

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for counter in root.findall("counter"):
            if counter.get("type") == "LINE":
                missed = int(counter.get("missed", 0))
                covered = int(counter.get("covered", 0))
                total = missed + covered
                report.total_lines = total
                report.total_lines_covered = covered
                if total > 0:
                    report.line_coverage = round(covered / total * 100, 1)
                break
    except Exception as e:
        logger.warn(f"Failed to parse JaCoCo XML: {e}")

    return report


def _try_parse_cobertura(project_path: Path, report: CoverageReport) -> CoverageReport:
    """Parse Cobertura XML report."""
    cobertura_paths = [
        "coverage.xml",
        "build/reports/cobertura/coverage.xml",
        "target/site/cobertura/coverage.xml",
    ]
    for pattern in cobertura_paths:
        xml_path = project_path / pattern
        if xml_path.exists():
            try:
                import xml.etree.ElementTree as ET

                tree = ET.parse(xml_path)
                root = tree.getroot()
                rate = float(root.get("line-rate", 0))
                report.line_coverage = round(rate * 100, 1)
                return report
            except Exception:
                continue
    return report


def _try_parse_lcov(project_path: Path, report: CoverageReport) -> CoverageReport:
    """Parse LCOV info file."""
    lcov_paths = ["coverage/lcov.info", "lcov.info"]
    for pattern in lcov_paths:
        lcov_path = project_path / pattern
        if lcov_path.exists():
            try:
                content = lcov_path.read_text(encoding="utf-8")
                lf = sum(int(m.group(1)) for m in re.finditer(r"LF:(\d+)", content))
                lh = sum(int(m.group(1)) for m in re.finditer(r"LH:(\d+)", content))
                if lf > 0:
                    report.total_lines = lf
                    report.total_lines_covered = lh
                    report.line_coverage = round(lh / lf * 100, 1)
                return report
            except Exception:
                continue
    return report


def _try_parse_pytest_cov(output: str, report: CoverageReport) -> CoverageReport:
    """Parse pytest-cov output for TOTAL line."""
    match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
    if match:
        report.line_coverage = float(match.group(1))
    return report


def _try_parse_go_cover(output: str, report: CoverageReport) -> CoverageReport:
    """Parse go test -cover output."""
    match = re.search(r"coverage:\s+([\d.]+)%", output)
    if match:
        report.line_coverage = float(match.group(1))
    return report


def _try_parse_generic(output: str, report: CoverageReport) -> CoverageReport:
    """Try to extract any coverage percentage from output."""
    patterns = [
        r"(?:line|statement|code)\s*coverage[:\s]+(\d+(?:\.\d+)?)\s*%",
        r"(\d+(?:\.\d+)?)\s*%\s*(?:line|statement|code)\s*coverage",
        r"Total[:\s]+(\d+(?:\.\d+)?)\s*%",
    ]
    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            report.line_coverage = float(match.group(1))
            return report
    return report


def _parse_test_counts(output: str) -> dict[str, int]:
    """Extract test pass/fail counts from build output."""
    counts: dict[str, int] = {"total": 0, "passed": 0, "failed": 0}

    # Gradle/JUnit style
    m = re.search(r"(\d+)\s+tests?\s+completed,\s+(\d+)\s+failed", output)
    if m:
        counts["total"] = int(m.group(1))
        counts["failed"] = int(m.group(2))
        counts["passed"] = counts["total"] - counts["failed"]
        return counts

    # pytest style
    m = re.search(r"(\d+)\s+passed", output)
    if m:
        counts["passed"] = int(m.group(1))
    m = re.search(r"(\d+)\s+failed", output)
    if m:
        counts["failed"] = int(m.group(1))
    counts["total"] = counts["passed"] + counts["failed"]

    # Go style
    m = re.search(r"ok\s+.+\s+([\d.]+)s", output)
    if m and counts["total"] == 0:
        # go test doesn't show counts easily, estimate from "--- PASS:" lines
        counts["passed"] = len(re.findall(r"--- PASS:", output))
        counts["failed"] = len(re.findall(r"--- FAIL:", output))
        counts["total"] = counts["passed"] + counts["failed"]

    return counts
