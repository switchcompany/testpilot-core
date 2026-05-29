"""Phase 2 — Analyze project architecture and build project graph."""

from __future__ import annotations

from pathlib import Path

from forge_core.ai.prompts import build_file_context, load_prompt
from forge_core.ai.provider import complete
from forge_core.core.file_manager import FileManager
from forge_core.models.config import ForgeConfig
from forge_core.models.project import Component, Layer, Module, ProjectGraph, TechStack
from forge_core.utils import logger
from forge_core.utils.tokens import split_for_context

import json


def run(
    config: ForgeConfig,
    file_manager: FileManager,
    prompts_dir: Path,
    tech_stack: TechStack,
    learnings: str = "",
) -> ProjectGraph:
    """Analyze the project and build the 4-Level DAG."""
    # Read all source files
    source_root = tech_stack.source_root or "src"
    source_files = file_manager.read_files(f"{source_root}/**/*")
    test_files = file_manager.read_files(f"{tech_stack.test_root or 'src/test'}/**/*")

    # Filter to code files only
    code_extensions = _get_code_extensions(tech_stack.language)
    source_files = {
        k: v for k, v in source_files.items()
        if any(k.endswith(ext) for ext in code_extensions)
    }

    graph = ProjectGraph(
        name=config.project_path.name,
        root_path=str(config.project_path),
        tech_stack=tech_stack,
        total_source_files=len(source_files),
        total_test_files=len(test_files),
    )

    # Split files into batches that fit in context
    batches = split_for_context(source_files, max_tokens=80_000, model=config.ai.model)

    prompt = load_prompt(prompts_dir, "analyze-project")
    system_prompt = prompt or (
        "You are a software architect. Analyze this codebase and identify:\n"
        "1. Modules/packages\n2. Layers (controllers, services, adapters, models)\n"
        "3. Key components per layer\n4. Dependencies between components\n"
        "Return JSON with modules, layers, and components."
    )

    if learnings:
        system_prompt += f"\n\nPast learnings:\n{learnings[:2000]}"

    # Process each batch
    all_modules: dict[str, Module] = {}
    for i, batch in enumerate(batches):
        logger.info(f"Analyzing batch {i + 1}/{len(batches)} ({len(batch)} files)")
        file_context = build_file_context(batch)

        response = complete(
            config=config.ai,
            system_prompt=system_prompt,
            user_prompt=(
                f"Analyze these source files and return the architecture as JSON.\n\n"
                f"Project: {config.project_path.name}\n"
                f"Language: {tech_stack.language}\n"
                f"Framework: {tech_stack.framework}\n\n"
                f"{file_context}"
            ),
            json_mode=True,
        )

        _parse_architecture_response(response, all_modules, batch)

    graph.modules = list(all_modules.values())
    return graph


def _parse_architecture_response(
    response: str, modules: dict[str, Module], files: dict[str, str]
) -> None:
    """Parse AI's architecture analysis response and merge into modules dict."""
    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        logger.warn("Failed to parse architecture JSON — using file-based fallback")
        _fallback_from_files(modules, files)
        return

    for mod_data in data.get("modules", [data] if "layers" in data else []):
        mod_name = mod_data.get("name", "main")
        if mod_name not in modules:
            modules[mod_name] = Module(name=mod_name, path=mod_data.get("path", ""))

        mod = modules[mod_name]
        for layer_data in mod_data.get("layers", []):
            layer = Layer(name=layer_data.get("name", ""))
            for comp_data in layer_data.get("components", []):
                layer.components.append(
                    Component(
                        name=comp_data.get("name", ""),
                        file_path=comp_data.get("file_path", ""),
                        layer=layer.name,
                        dependencies=comp_data.get("dependencies", []),
                    )
                )
            mod.layers.append(layer)


def _fallback_from_files(modules: dict[str, Module], files: dict[str, str]) -> None:
    """Build a basic module structure from file paths when AI parsing fails."""
    mod = modules.setdefault("main", Module(name="main", path="src"))
    layers: dict[str, Layer] = {}

    for path in files:
        parts = Path(path).parts
        layer_name = parts[2] if len(parts) > 2 else "root"
        if layer_name not in layers:
            layers[layer_name] = Layer(name=layer_name)
        layers[layer_name].components.append(
            Component(name=Path(path).stem, file_path=path, layer=layer_name)
        )

    mod.layers = list(layers.values())


def _get_code_extensions(language: str) -> list[str]:
    """Get relevant file extensions for a language."""
    ext_map = {
        "kotlin": [".kt", ".kts"],
        "java": [".java"],
        "python": [".py"],
        "go": [".go"],
        "typescript": [".ts", ".tsx"],
        "javascript": [".js", ".jsx"],
        "rust": [".rs"],
        "csharp": [".cs"],
        "c#": [".cs"],
        "ruby": [".rb"],
        "php": [".php"],
        "c++": [".cpp", ".hpp", ".cc", ".h"],
    }
    return ext_map.get(language.lower(), [".py", ".java", ".kt", ".go", ".ts", ".js"])
