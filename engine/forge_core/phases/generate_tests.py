"""Phase 5 — Iterative test generation with journey-weighted prioritization."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from forge_core.ai.prompts import build_file_context, load_prompt
from forge_core.ai.provider import complete
from forge_core.core.agent_manager import AgentManager
from forge_core.core.coverage import run_coverage
from forge_core.core.file_manager import FileManager
from forge_core.models.config import ForgeConfig
from forge_core.models.dto import DTORegistry
from forge_core.models.project import Component, ProjectGraph
from forge_core.models.test_result import IterationResult, TestFileResult
from forge_core.utils import logger


@dataclass
class GenerationResult:
    """Aggregate result of the generation loop."""

    iterations: list[IterationResult] = field(default_factory=list)
    total_tests_generated: int = 0


def run(
    config: ForgeConfig,
    file_manager: FileManager,
    prompts_dir: Path,
    project_graph: ProjectGraph,
    dto_registry: DTORegistry,
    agent_manager: AgentManager,
    baseline_coverage: float,
    learnings: str = "",
) -> GenerationResult:
    """Run the iterative test generation loop."""
    result = GenerationResult()
    tech = project_graph.tech_stack

    # Build prioritized target list (journey-weighted)
    targets = _prioritize_targets(project_graph)
    if not targets:
        logger.warn("No generation targets found")
        return result

    logger.info(f"Targets: {len(targets)} components to test")

    # Load prompts
    write_prompt = load_prompt(prompts_dir, "write-unit-tests")
    system_prompt = write_prompt or (
        "You are a backend test engineer. Write unit tests for the given source code.\n"
        "Rules: idiomatic tests, proper mocking, no production code changes.\n"
        "Return JSON with test_files: [{path, content}]."
    )

    if learnings:
        system_prompt += f"\n\nPast learnings:\n{learnings[:2000]}"

    # Add DTO registry context
    if dto_registry.count > 0:
        dto_context = _build_dto_context(dto_registry)
        system_prompt += f"\n\nDTO Registry (use these exact constructors):\n{dto_context}"

    # Iterative loop
    current_coverage = baseline_coverage
    best_coverage = baseline_coverage
    stall_count = 0
    batch_size = 5

    for iteration in range(1, config.max_iterations + 1):
        batch_start = (iteration - 1) * batch_size
        batch_targets = targets[batch_start : batch_start + batch_size]

        if not batch_targets:
            logger.info(f"All targets covered after {iteration - 1} iterations")
            break

        logger.info(f"Iteration {iteration}/{config.max_iterations}: {len(batch_targets)} targets")

        # Register agent scope
        scope_id = f"gen-iter-{iteration}"
        agent_manager.register(scope_id, [t.file_path for t in batch_targets])

        # Read source files for this batch
        batch_files: dict[str, str] = {}
        for target in batch_targets:
            content = file_manager.read_file(target.file_path)
            if content:
                batch_files[target.file_path] = content

        file_context = build_file_context(batch_files)

        # Generate tests
        response = complete(
            config=config.ai,
            system_prompt=system_prompt,
            user_prompt=(
                f"Write unit tests for these source files.\n\n"
                f"Language: {tech.language}\n"
                f"Framework: {tech.framework}\n"
                f"Test framework: {tech.test_framework}\n"
                f"Mock library: {tech.mock_library}\n\n"
                f"{file_context}"
            ),
            json_mode=True,
            max_tokens=8192,
        )

        # Parse and write test files
        iter_result = IterationResult(iteration=iteration, coverage_before=current_coverage)
        tests_written = _write_generated_tests(response, file_manager, iter_result)

        if tests_written == 0:
            agent_manager.record_error(scope_id, "no_tests_generated")
            action = agent_manager.heartbeat(scope_id)
            if action in ("split", "terminate"):
                logger.warn(f"Agent {scope_id}: {action} — moving to next batch")
                continue

        # Run coverage check
        coverage = run_coverage(config.project_path, tech.coverage_command)
        iter_result.coverage_after = coverage.line_coverage
        iter_result.coverage_delta = coverage.line_coverage - current_coverage

        # Rollback protection
        if coverage.line_coverage < best_coverage:
            logger.warn(
                f"Coverage dropped {best_coverage:.1f}% → {coverage.line_coverage:.1f}% — rolling back"
            )
            file_manager.rollback()
            iter_result.rolled_back = True
        else:
            file_manager.checkpoint()
            agent_manager.record_progress(scope_id)
            if coverage.line_coverage > best_coverage:
                best_coverage = coverage.line_coverage
            current_coverage = coverage.line_coverage

        agent_manager.complete(scope_id)
        result.iterations.append(iter_result)

        # Early exit if target reached
        if current_coverage >= config.target_coverage:
            logger.success(f"Target coverage {config.target_coverage}% reached!")
            break

        # Stall detection
        if iter_result.coverage_delta < 0.5:
            stall_count += 1
            if stall_count >= 3:
                logger.warn("Coverage stalled for 3 iterations — stopping")
                break
        else:
            stall_count = 0

    return result


def _prioritize_targets(graph: ProjectGraph) -> list[Component]:
    """Build ROI-weighted priority list of components to test.

    ROI scoring (lines coverable per test / complexity):
    - NotImplemented methods: ROI=10 (1-2 lines/test, trivial complexity)
    - Pure logic (mappers/processors): ROI=8 (10-20 lines/test, low complexity)
    - Service delegates: ROI=5 (5-10 lines/test, medium complexity)
    - HTTP-dependent (adapter try/catch): ROI=3 (3-5 lines/test, medium complexity)
    - HTTP-dependent (MockEngine deep): ROI=4 (15-30 lines/test, high complexity)

    Two-phase strategy:
    - Phase A (shallow): Cover method entry points first (quick coverage gains)
    - Phase B (deep): Cover lambda/inner class bodies (requires MockEngine)
    """
    all_components: list[Component] = []

    # Collect all components with ROI scoring
    for module in graph.modules:
        journey_components = set()
        for journey in module.journeys:
            journey_components.update(journey.components)

        for layer in module.layers:
            for comp in layer.components:
                if not comp.is_tested:
                    # Calculate ROI score based on method classification and layer
                    comp.roi_score = _calculate_roi(comp, layer.name)

                    # Boost priority for journey components
                    if comp.name in journey_components:
                        comp.roi_score *= 1.5

                    all_components.append(comp)

    # Sort by ROI score descending (highest value first)
    all_components.sort(key=lambda c: c.roi_score, reverse=True)

    return all_components


def _calculate_roi(comp: Component, layer_name: str) -> float:
    """Calculate ROI score for a component based on its characteristics.

    Higher ROI = more lines covered per unit of test-writing effort.
    """
    # Base ROI by layer type
    layer_roi = {
        "repository": 8.0,   # mappers/transformers — pure logic, highest ROI
        "util": 7.0,         # pure helpers
        "service": 5.0,      # business logic with mocks
        "controller": 4.0,   # route handlers
        "middleware": 3.0,    # interceptors/filters
        "config": 1.0,       # usually excluded from coverage
        "model": 1.0,        # usually excluded from coverage
    }
    roi = layer_roi.get(layer_name, 4.0)

    # Boost for NotImplemented methods (coverage gold)
    if comp.not_implemented_count > 0:
        roi += comp.not_implemented_count * 0.5

    # Boost for pure logic classification
    if comp.method_classification == "pure_logic":
        roi *= 1.3
    elif comp.method_classification == "not_implemented":
        roi *= 1.5  # trivial to test

    # Penalty for inline reified (needs MockEngine — harder to test)
    if comp.has_inline_reified:
        roi *= 0.7

    # Penalty for heavy lambda coverage gaps (needs deep MockEngine tests)
    if comp.lambda_lines > 50:
        roi *= 0.8

    return round(roi, 2)


def _build_dto_context(registry: DTORegistry) -> str:
    """Build a compact DTO reference for the system prompt.

    Includes:
    - Construction strategy (@Serializable → Json.decodeFromString)
    - Namespace collision warnings with import aliases
    - Required vs optional params
    """
    lines: list[str] = []

    # Warn about @Serializable DTOs upfront
    serializable = registry.serializable_dtos()
    if serializable:
        lines.append(
            f"⚠ {len(serializable)} @Serializable DTOs detected. "
            "Use Json.decodeFromString<Type>(jsonString) instead of direct constructors. "
            "Direct construction causes 'seen0/serializationConstructorMarker' compile errors."
        )
        lines.append("")

    # Warn about namespace collisions
    collisions = registry.get_collisions()
    if collisions:
        lines.append("⚠ Namespace collisions — use import aliases:")
        for name, entries in collisions.items():
            for entry in entries:
                alias = entry.package.replace(".", "_").replace("model_dto_", "") + "_" + name
                lines.append(f"  - {entry.fully_qualified_name} as {alias}")
        lines.append("")

    for entry in list(registry.entries.values())[:50]:  # cap at 50 DTOs
        required = [p for p in entry.params if not p.nullable and not p.default]
        optional = [p for p in entry.params if p.nullable or p.default]

        req_str = ", ".join(f"{p.name}: {p.type}" for p in required)
        opt_count = len(optional)

        strategy = ""
        if entry.construction_strategy == "json_decode":
            strategy = " [USE Json.decodeFromString]"
        elif entry.has_builder:
            strategy = " [USE builder]"

        lines.append(f"- {entry.class_name}({req_str}){strategy}")
        if opt_count:
            lines.append(f"  + {opt_count} optional params")

    return "\n".join(lines)


def _write_generated_tests(
    response: str, file_manager: FileManager, iter_result: IterationResult
) -> int:
    """Parse AI response and write test files. Returns count written."""
    count = 0
    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        logger.warn("Failed to parse test generation JSON")
        return 0

    for test in data.get("test_files", []):
        path = test.get("path", "")
        content = test.get("content", "")
        if path and content:
            file_manager.write_file(path, content)
            iter_result.tests_generated.append(
                TestFileResult(
                    file_path=path,
                    test_count=content.count("@Test") + content.count("def test_") + content.count("func Test"),
                )
            )
            count += 1

    return count
