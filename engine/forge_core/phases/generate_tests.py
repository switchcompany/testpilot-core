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
    """Build journey-weighted priority list of components to test."""
    all_components: list[Component] = []

    # Collect all components
    for module in graph.modules:
        # Components in journeys get highest priority
        journey_components = set()
        for journey in module.journeys:
            journey_components.update(journey.components)

        for layer in module.layers:
            for comp in layer.components:
                if not comp.is_tested:
                    # Boost priority for journey components
                    if comp.name in journey_components:
                        all_components.insert(0, comp)
                    else:
                        all_components.append(comp)

    return all_components


def _build_dto_context(registry: DTORegistry) -> str:
    """Build a compact DTO reference for the system prompt."""
    lines: list[str] = []
    for entry in list(registry.entries.values())[:50]:  # cap at 50 DTOs
        params = ", ".join(f"{p.name}: {p.type}" for p in entry.params)
        lines.append(f"- {entry.class_name}({params})")
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
