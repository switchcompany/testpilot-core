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
    # New fields from assembler-service learnings
    has_serializable_dtos: bool = False
    serializable_classes: list[str] = field(default_factory=list)
    has_inline_reified: bool = False
    inline_reified_methods: list[str] = field(default_factory=list)
    koin_dependencies: list[str] = field(default_factory=list)
    not_implemented_methods: list[str] = field(default_factory=list)
    method_classifications: dict[str, str] = field(default_factory=dict)


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
    """Parse Java/Kotlin file for package, imports, classes, methods.

    Also detects:
    - @Serializable annotations (need Json.decodeFromString workaround)
    - inline reified functions (need MockEngine, not MockK)
    - Koin get<Type>() dependency injection calls
    - NotImplementedError / TODO() method bodies (coverage gold)
    - Method classification: pure_logic vs http_dependent vs delegate
    """
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

    # Detect @Serializable annotations (Kotlin serialization)
    serializable_pattern = re.compile(
        r"@Serializable\s*(?:\([^)]*\))?\s*(?:data\s+)?class\s+(\w+)", re.MULTILINE
    )
    for m in serializable_pattern.finditer(content):
        info.serializable_classes.append(m.group(1))
    if info.serializable_classes:
        info.has_serializable_dtos = True

    # Detect inline reified functions (MockK cannot intercept these)
    inline_reified_pattern = re.compile(
        r"(?:suspend\s+)?inline\s+fun\s+<reified\s+\w+[^>]*>\s+(\w+)", re.MULTILINE
    )
    for m in inline_reified_pattern.finditer(content):
        info.inline_reified_methods.append(m.group(1))
    if info.inline_reified_methods:
        info.has_inline_reified = True

    # Detect Koin dependency injection: get<Type>(), inject<Type>()
    koin_pattern = re.compile(r"(?:get|inject)<(\w+)>\s*\(\s*\)")
    for m in koin_pattern.finditer(content):
        dep = m.group(1)
        if dep not in info.koin_dependencies:
            info.koin_dependencies.append(dep)

    # Methods (fun for Kotlin, public/private/protected for Java)
    for m in re.finditer(
        r"(?:fun|public|private|protected|internal)\s+(?:(?:static|suspend|override|open|abstract)\s+)*(?:\w+\s+)?(\w+)\s*\(",
        content,
    ):
        name = m.group(1)
        if name not in ("class", "interface", "if", "for", "while", "return", "new"):
            info.methods.append(name)

    # Detect NotImplementedError / TODO() methods (coverage gold — 3 lines per test)
    not_impl_pattern = re.compile(
        r"(?:fun|override\s+fun)\s+(\w+)\s*\([^)]*\)[^{]*\{[^}]*"
        r"(?:throw\s+NotImplementedError|TODO\(\))",
        re.DOTALL,
    )
    for m in not_impl_pattern.finditer(content):
        info.not_implemented_methods.append(m.group(1))

    # Method classification based on body patterns
    _classify_methods(content, info)

    return info


def _classify_methods(content: str, info: FileInfo) -> None:
    """Classify methods into categories for targeted test strategy.

    Categories:
    - not_implemented: throws NotImplementedError or TODO()
    - pure_logic: no external calls, just data transformation
    - http_dependent: calls HTTP clients, uses coroutineScope/withContext
    - delegate: simply delegates to another method/service
    """
    # Split content into method bodies (rough heuristic)
    method_pattern = re.compile(
        r"(?:fun|override\s+fun|suspend\s+fun)\s+(\w+)\s*\([^)]*\)[^{]*\{",
        re.MULTILINE,
    )
    for m in method_pattern.finditer(content):
        name = m.group(1)
        if name in ("class", "interface", "if", "for", "while"):
            continue

        # Get approximate method body (next 500 chars after opening brace)
        body_start = m.end()
        body_preview = content[body_start:body_start + 500].lower()

        if name in info.not_implemented_methods:
            info.method_classifications[name] = "not_implemented"
        elif any(kw in body_preview for kw in [
            "httpclient", "client.", "getfailsafe", "withcontext", "coroutinescope",
            "async {", ".post(", ".get(", ".put(", ".delete(",
        ]):
            info.method_classifications[name] = "http_dependent"
        elif body_preview.count(".") <= 3 and "return" in body_preview:
            info.method_classifications[name] = "pure_logic"
        else:
            info.method_classifications[name] = "delegate"


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

    Includes new metadata: @Serializable DTOs, inline reified functions,
    Koin dependencies, method classifications, and NotImplemented counts.
    """
    # Group by module → layer
    modules: dict[str, dict[str, list[FileInfo]]] = {}
    for fi in file_infos:
        mod = modules.setdefault(fi.module, {})
        layer = mod.setdefault(fi.layer, [])
        layer.append(fi)

    # Collect project-wide signals
    total_serializable = sum(len(fi.serializable_classes) for fi in file_infos)
    total_inline_reified = sum(len(fi.inline_reified_methods) for fi in file_infos)
    total_not_impl = sum(len(fi.not_implemented_methods) for fi in file_infos)
    all_koin_deps = set()
    for fi in file_infos:
        all_koin_deps.update(fi.koin_dependencies)

    lines = [
        f"Project has {len(file_infos)} source files across {len(modules)} modules.\n",
    ]

    # Project-wide signals for test strategy
    if total_serializable or total_inline_reified or total_not_impl:
        lines.append("## Testing Signals")
        if total_serializable:
            lines.append(
                f"  ⚠ {total_serializable} @Serializable DTOs detected — "
                "use Json.decodeFromString instead of direct constructors"
            )
        if total_inline_reified:
            lines.append(
                f"  ⚠ {total_inline_reified} inline reified functions detected — "
                "use MockEngine, not MockK (MockK cannot intercept inline reified)"
            )
        if total_not_impl:
            lines.append(
                f"  ✦ {total_not_impl} NotImplemented methods — "
                "coverage gold, 3 lines per test with assertThrows"
            )
        if all_koin_deps:
            lines.append(
                f"  ⚙ Koin DI dependencies detected: {', '.join(sorted(all_koin_deps))}"
            )
        lines.append("")

    for mod_name, layers in sorted(modules.items()):
        lines.append(f"\n## Module: {mod_name}")
        for layer_name, files in sorted(layers.items()):
            class_list = []
            for fi in files:
                class_names = ", ".join(fi.classes[:5]) if fi.classes else Path(fi.path).stem
                method_count = len(fi.methods)
                dep_count = len(fi.imports)
                extras = []
                if fi.has_serializable_dtos:
                    extras.append(f"@Serializable:{len(fi.serializable_classes)}")
                if fi.has_inline_reified:
                    extras.append(f"inline-reified:{len(fi.inline_reified_methods)}")
                if fi.not_implemented_methods:
                    extras.append(f"NotImpl:{len(fi.not_implemented_methods)}")
                if fi.koin_dependencies:
                    extras.append(f"Koin:[{','.join(fi.koin_dependencies)}]")
                extra_str = f" | {', '.join(extras)}" if extras else ""
                class_list.append(
                    f"  - {fi.path} → [{class_names}] "
                    f"({method_count} methods, {dep_count} imports, {fi.line_count} lines{extra_str})"
                )
            lines.append(f"  Layer: {layer_name} ({len(files)} files)")
            lines.extend(class_list[:20])  # cap per layer to avoid bloat
            if len(class_list) > 20:
                lines.append(f"  ... and {len(class_list) - 20} more files")

    return "\n".join(lines)
