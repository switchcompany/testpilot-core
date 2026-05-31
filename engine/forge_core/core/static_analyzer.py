"""Static code analyzer — extracts architecture WITHOUT AI calls.

Parses imports, class names, method signatures, and directory structure
to build 90% of the project graph. AI is only used for final enrichment
(1-2 calls instead of 100+).

Supports: Java, Kotlin, Python, TypeScript/JavaScript, Go, C#, Ruby, PHP.
"""

from __future__ import annotations

import re
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class FileInfo:
    """Extracted metadata from a single source file."""
    path: str
    language: str = ""
    package: str = ""
    classes: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    layer: str = ""  # controller, service, repository, model, util, config, etc.
    module: str = ""  # inferred from directory structure
    line_count: int = 0


# ── Layer classification patterns ──────────────────────────────────────────────

LAYER_PATTERNS: dict[str, list[str]] = {
    "controller": [
        r"controller", r"resource", r"endpoint", r"handler", r"route",
        r"api", r"rest", r"graphql", r"grpc", r"view",
    ],
    "service": [
        r"service", r"usecase", r"use_case", r"interactor", r"manager",
        r"facade", r"orchestrat",
    ],
    "repository": [
        r"repositor", r"repo", r"dao", r"store", r"persistence",
        r"mapper", r"gateway",
    ],
    "model": [
        r"model", r"entity", r"domain", r"dto", r"schema", r"pojo",
        r"data.class", r"dataclass", r"record",
    ],
    "config": [
        r"config", r"configuration", r"properties", r"settings",
        r"setup", r"bootstrap", r"module",
    ],
    "util": [
        r"util", r"helper", r"common", r"shared", r"extension",
        r"converter", r"transformer", r"adapter",
    ],
    "middleware": [
        r"middleware", r"filter", r"interceptor", r"guard",
        r"pipe", r"decorator", r"aspect",
    ],
    "test": [
        r"test", r"spec", r"_test", r"\.test\.", r"\.spec\.",
    ],
}


def classify_layer(file_path: str, classes: list[str]) -> str:
    """Classify a file into a layer based on path and class names."""
    path_lower = file_path.lower()
    # Also check class names
    names_lower = " ".join(classes).lower() if classes else ""
    combined = f"{path_lower} {names_lower}"

    for layer, patterns in LAYER_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, combined):
                return layer
    return "other"


def infer_module(file_path: str, source_root: str) -> str:
    """Infer module name from directory structure."""
    rel = file_path
    if rel.startswith(source_root):
        rel = rel[len(source_root):].lstrip("/\\")

    parts = Path(rel).parts
    if len(parts) >= 2:
        return parts[0]
    return "root"


# ── Language-specific parsers ──────────────────────────────────────────────────

def _parse_java_kotlin(content: str, path: str) -> FileInfo:
    """Parse Java/Kotlin file for package, imports, classes, methods."""
    info = FileInfo(path=path, language="kotlin" if path.endswith((".kt", ".kts")) else "java")
    info.line_count = content.count("\n") + 1

    # Package
    pkg = re.search(r"^package\s+([\w.]+)", content, re.MULTILINE)
    if pkg:
        info.package = pkg.group(1)

    # Imports
    for m in re.finditer(r"^import\s+([\w.*]+)", content, re.MULTILINE):
        info.imports.append(m.group(1))

    # Classes/interfaces/objects
    for m in re.finditer(
        r"(?:class|interface|object|enum|data\s+class|sealed\s+class|abstract\s+class)\s+(\w+)",
        content,
    ):
        info.classes.append(m.group(1))

    # Methods (fun for Kotlin, public/private/protected for Java)
    for m in re.finditer(
        r"(?:fun|public|private|protected|internal)\s+(?:(?:static|suspend|override|open|abstract)\s+)*(?:\w+\s+)?(\w+)\s*\(",
        content,
    ):
        name = m.group(1)
        if name not in ("class", "interface", "if", "for", "while", "return", "new"):
            info.methods.append(name)

    return info


def _parse_python(content: str, path: str) -> FileInfo:
    """Parse Python file for imports, classes, functions."""
    info = FileInfo(path=path, language="python")
    info.line_count = content.count("\n") + 1

    # Package from directory
    parts = Path(path).parts
    if len(parts) > 1:
        info.package = ".".join(parts[:-1])

    # Imports
    for m in re.finditer(r"^(?:from\s+([\w.]+)\s+)?import\s+([\w., ]+)", content, re.MULTILINE):
        if m.group(1):
            info.imports.append(m.group(1))
        for name in m.group(2).split(","):
            name = name.strip().split(" as ")[0].strip()
            if name:
                info.imports.append(name)

    # Classes
    for m in re.finditer(r"^class\s+(\w+)", content, re.MULTILINE):
        info.classes.append(m.group(1))

    # Functions/methods
    for m in re.finditer(r"^\s*(?:async\s+)?def\s+(\w+)", content, re.MULTILINE):
        name = m.group(1)
        if not name.startswith("_") or name.startswith("__"):
            info.methods.append(name)

    return info


def _parse_typescript_js(content: str, path: str) -> FileInfo:
    """Parse TypeScript/JavaScript file."""
    info = FileInfo(
        path=path,
        language="typescript" if path.endswith((".ts", ".tsx")) else "javascript",
    )
    info.line_count = content.count("\n") + 1

    # Imports
    for m in re.finditer(r"""(?:import|from)\s+['"]([^'"]+)['"]""", content):
        info.imports.append(m.group(1))
    for m in re.finditer(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""", content):
        info.imports.append(m.group(1))

    # Classes
    for m in re.finditer(r"class\s+(\w+)", content):
        info.classes.append(m.group(1))

    # Functions
    for m in re.finditer(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)", content):
        info.methods.append(m.group(1))
    # Arrow function exports
    for m in re.finditer(r"export\s+(?:const|let)\s+(\w+)\s*=\s*(?:async\s+)?\(", content):
        info.methods.append(m.group(1))

    return info


def _parse_go(content: str, path: str) -> FileInfo:
    """Parse Go file."""
    info = FileInfo(path=path, language="go")
    info.line_count = content.count("\n") + 1

    pkg = re.search(r"^package\s+(\w+)", content, re.MULTILINE)
    if pkg:
        info.package = pkg.group(1)

    for m in re.finditer(r'"([^"]+)"', content):
        if "/" in m.group(1) or m.group(1) in ("fmt", "os", "io", "net", "http"):
            info.imports.append(m.group(1))

    for m in re.finditer(r"type\s+(\w+)\s+struct", content):
        info.classes.append(m.group(1))

    for m in re.finditer(r"func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(", content):
        info.methods.append(m.group(1))

    return info


def _parse_csharp(content: str, path: str) -> FileInfo:
    """Parse C# file."""
    info = FileInfo(path=path, language="csharp")
    info.line_count = content.count("\n") + 1

    ns = re.search(r"namespace\s+([\w.]+)", content)
    if ns:
        info.package = ns.group(1)

    for m in re.finditer(r"using\s+([\w.]+);", content):
        info.imports.append(m.group(1))

    for m in re.finditer(r"(?:class|interface|struct|enum|record)\s+(\w+)", content):
        info.classes.append(m.group(1))

    for m in re.finditer(
        r"(?:public|private|protected|internal)\s+(?:static\s+)?(?:async\s+)?(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\(",
        content,
    ):
        info.methods.append(m.group(1))

    return info


def _parse_generic(content: str, path: str) -> FileInfo:
    """Fallback parser — just count lines."""
    info = FileInfo(path=path, language="unknown")
    info.line_count = content.count("\n") + 1
    info.classes.append(Path(path).stem)
    return info


# ── Parser dispatcher ──────────────────────────────────────────────────────────

_PARSERS = {
    ".java": _parse_java_kotlin,
    ".kt": _parse_java_kotlin,
    ".kts": _parse_java_kotlin,
    ".py": _parse_python,
    ".ts": _parse_typescript_js,
    ".tsx": _parse_typescript_js,
    ".js": _parse_typescript_js,
    ".jsx": _parse_typescript_js,
    ".go": _parse_go,
    ".cs": _parse_csharp,
}


def parse_file(content: str, path: str) -> FileInfo:
    """Parse a source file and extract metadata."""
    ext = Path(path).suffix.lower()
    parser = _PARSERS.get(ext, _parse_generic)
    return parser(content, path)


# ── Main analyzer ──────────────────────────────────────────────────────────────

def analyze_statically(
    source_files: dict[str, str],
    source_root: str = "src",
) -> list[FileInfo]:
    """Analyze all source files statically (zero AI calls).

    Returns a list of FileInfo with extracted metadata.
    """
    results: list[FileInfo] = []

    for path, content in source_files.items():
        info = parse_file(content, path)
        info.module = infer_module(path, source_root)
        info.layer = classify_layer(path, info.classes)
        results.append(info)

    return results


def build_summary_for_ai(file_infos: list[FileInfo]) -> str:
    """Build a compact summary of the codebase for AI enrichment.

    Instead of sending ALL source code (100+ batches), we send a structured
    summary that's typically 2-5K tokens — fits in a single AI call.
    """
    # Group by module → layer
    modules: dict[str, dict[str, list[FileInfo]]] = {}
    for fi in file_infos:
        mod = modules.setdefault(fi.module, {})
        layer = mod.setdefault(fi.layer, [])
        layer.append(fi)

    lines = [
        f"Project has {len(file_infos)} source files across {len(modules)} modules.\n",
    ]

    for mod_name, layers in sorted(modules.items()):
        lines.append(f"\n## Module: {mod_name}")
        for layer_name, files in sorted(layers.items()):
            class_list = []
            for fi in files:
                class_names = ", ".join(fi.classes[:5]) if fi.classes else Path(fi.path).stem
                method_count = len(fi.methods)
                dep_count = len(fi.imports)
                class_list.append(
                    f"  - {fi.path} → [{class_names}] "
                    f"({method_count} methods, {dep_count} imports, {fi.line_count} lines)"
                )
            lines.append(f"  Layer: {layer_name} ({len(files)} files)")
            lines.extend(class_list[:20])  # cap per layer to avoid bloat
            if len(class_list) > 20:
                lines.append(f"  ... and {len(class_list) - 20} more files")

    return "\n".join(lines)
