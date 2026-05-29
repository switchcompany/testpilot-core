"""Pydantic models for project structure — 4-Level DAG."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Component(BaseModel):
    """A single class/file within a layer."""

    name: str
    file_path: str
    layer: str = ""
    dependencies: list[str] = Field(default_factory=list)
    is_tested: bool = False
    existing_test_file: str = ""
    coverage_pct: float = 0.0


class Journey(BaseModel):
    """A traced user journey across layers."""

    name: str
    entry_point: str
    entry_type: str = ""  # route, consumer, job, grpc, cli
    components: list[str] = Field(default_factory=list)  # ordered list of component names
    priority: int = 1  # 1 = critical, 5 = low
    description: str = ""


class Layer(BaseModel):
    """A functional layer within a module (e.g., controllers, services, adapters)."""

    name: str
    components: list[Component] = Field(default_factory=list)


class Module(BaseModel):
    """A module/package within the project."""

    name: str
    path: str
    layers: list[Layer] = Field(default_factory=list)
    journeys: list[Journey] = Field(default_factory=list)


class TechStack(BaseModel):
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
    modules: list[str] = Field(default_factory=list)


class ProjectGraph(BaseModel):
    """4-Level DAG: Project → Modules → Layers → Components."""

    name: str = ""
    root_path: str = ""
    tech_stack: TechStack = Field(default_factory=TechStack)
    modules: list[Module] = Field(default_factory=list)
    total_source_files: int = 0
    total_test_files: int = 0
