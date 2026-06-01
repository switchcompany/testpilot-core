"""Data models for project structure — 4-Level DAG."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Component:
    """A single class/file within a layer."""

    name: str = ""
    file_path: str = ""
    layer: str = ""
    dependencies: list[str] = field(default_factory=list)
    is_tested: bool = False
    existing_test_file: str = ""
    coverage_pct: float = 0.0
    # Method classification for targeted test strategy
    method_classification: str = ""  # "not_implemented" | "pure_logic" | "http_dependent" | "delegate"
    # ROI score: estimated lines coverable per test / complexity
    roi_score: float = 0.0
    # Lines inside lambda/inner classes (coroutine blocks, callbacks)
    lambda_lines: int = 0
    # Auto-detected Koin/DI dependencies from get<Type>() calls
    koin_dependencies: list[str] = field(default_factory=list)
    # Whether this component has inline reified functions (needs MockEngine)
    has_inline_reified: bool = False
    # Whether methods throw NotImplementedError (coverage gold)
    not_implemented_count: int = 0


@dataclass
class Journey:
    """A traced user journey across layers."""

    name: str = ""
    entry_point: str = ""
    entry_type: str = ""
    components: list[str] = field(default_factory=list)
    priority: int = 1
    description: str = ""


@dataclass
class Layer:
    """A functional layer within a module."""

    name: str = ""
    components: list[Component] = field(default_factory=list)


@dataclass
class Module:
    """A module/package within the project."""

    name: str = ""
    path: str = ""
    layers: list[Layer] = field(default_factory=list)
    journeys: list[Journey] = field(default_factory=list)


@dataclass
class TechStack:
    """Detected technology stack."""

    language: str = ""
    framework: str = ""
    build_tool: str = ""
    test_framework: str = ""
    mock_library: str = ""
    coverage_tool: str = ""
    source_root: str = ""
    test_root: str = ""
    test_command: str = ""
    coverage_command: str = ""
    is_monorepo: bool = False
    modules: list[str] = field(default_factory=list)


@dataclass
class ProjectGraph:
    """4-Level DAG: Project → Modules → Layers → Components."""

    name: str = ""
    root_path: str = ""
    tech_stack: TechStack = field(default_factory=TechStack)
    modules: list[Module] = field(default_factory=list)
    total_source_files: int = 0
    total_test_files: int = 0
