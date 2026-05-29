"""Phase 1 — Detect tech stack by reading build files."""

from __future__ import annotations

from pathlib import Path

from forge_core.ai.prompts import build_file_context, load_prompt
from forge_core.ai.structured import extract
from forge_core.core.file_manager import FileManager
from forge_core.models.config import ForgeConfig
from forge_core.models.project import TechStack

# Build files to check for each language ecosystem
BUILD_FILES = [
    "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
    "pom.xml",
    "package.json", "tsconfig.json",
    "pyproject.toml", "setup.py", "requirements.txt", "Pipfile",
    "go.mod", "go.sum",
    "Cargo.toml",
    "*.csproj", "*.sln",
    "Gemfile",
    "composer.json",
    "Makefile", "CMakeLists.txt",
]


def run(
    config: ForgeConfig,
    file_manager: FileManager,
    prompts_dir: Path,
) -> TechStack:
    """Detect the project's technology stack."""
    # Read build/config files
    build_contents: dict[str, str] = {}
    for pattern in BUILD_FILES:
        if "*" in pattern:
            found = file_manager.read_files(pattern)
            build_contents.update(found)
        else:
            content = file_manager.read_file(pattern)
            if content:
                build_contents[pattern] = content

    # Also check for common directory structures
    project_path = config.project_path
    dir_hints: list[str] = []
    for d in ["src/main", "src/test", "src", "lib", "tests", "test", "spec", "app"]:
        if (project_path / d).exists():
            dir_hints.append(d)

    # Use AI to analyze
    prompt = load_prompt(prompts_dir, "detect-tech-stack")
    file_context = build_file_context(build_contents)
    user_prompt = (
        f"Analyze this project's build files and detect the tech stack.\n\n"
        f"Directory structure hints: {', '.join(dir_hints)}\n\n"
        f"{file_context}"
    )

    return extract(
        config=config.ai,
        system_prompt=prompt or "You are a build system analyst. Detect the tech stack.",
        user_prompt=user_prompt,
        response_model=TechStack,
    )
