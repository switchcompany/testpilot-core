"""Data models for DTO registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DTOParam:
    """A single constructor/field parameter of a DTO."""

    name: str = ""
    type: str = ""
    default: str = ""
    nullable: bool = False


@dataclass
class DTOEntry:
    """A single DTO class registered in the global registry."""

    class_name: str = ""
    package: str = ""
    file_path: str = ""
    params: list[DTOParam] = field(default_factory=list)
    has_builder: bool = False
    has_factory: bool = False
    is_serializable: bool = False
    construction_strategy: str = "direct"  # "direct" | "json_decode" | "builder" | "factory"
    validation_annotations: list[str] = field(default_factory=list)
    nested_dtos: list[str] = field(default_factory=list)
    used_in_journeys: list[str] = field(default_factory=list)
    used_in_layers: list[str] = field(default_factory=list)
    namespace_aliases: dict[str, str] = field(default_factory=dict)

    def mock_snippet(self) -> str:
        """Generate a minimal mock/test instance snippet.

        Uses the correct construction strategy:
        - direct: standard constructor call
        - json_decode: Json.decodeFromString for @Serializable DTOs with synthetic constructors
        - builder/factory: uses builder or factory method
        """
        if self.construction_strategy == "json_decode":
            fields = ", ".join(
                f'\\"{p.name}\\": {_json_default(p)}' for p in self.params if not p.nullable
            )
            return (
                f'Json.decodeFromString<{self.class_name}>'
                f'("""{{{fields}}}""")'
            )

        params_str = ", ".join(
            f'{p.name}={"null" if p.nullable else repr(p.default) if p.default else "TODO"}'
            for p in self.params
        )
        return f"{self.class_name}({params_str})"

    @property
    def fully_qualified_name(self) -> str:
        """Return package.ClassName for disambiguation."""
        if self.package:
            return f"{self.package}.{self.class_name}"
        return self.class_name


def _json_default(param: DTOParam) -> str:
    """Return a JSON-safe default value for a DTO param type."""
    t = param.type.lower().rstrip("?")
    if param.default:
        return repr(param.default)
    if t in ("string", "str"):
        return '"test"'
    if t in ("int", "long", "short", "byte", "integer"):
        return "0"
    if t in ("double", "float", "number"):
        return "0.0"
    if t in ("boolean", "bool"):
        return "false"
    if t.startswith("list") or t.startswith("array"):
        return "[]"
    return "null"


@dataclass
class DTORegistry:
    """Global registry of all DTOs in the project."""

    entries: dict[str, DTOEntry] = field(default_factory=dict)

    def register(self, entry: DTOEntry) -> None:
        # Use fully qualified name if there's a namespace collision
        if entry.class_name in self.entries:
            existing = self.entries[entry.class_name]
            if existing.package != entry.package:
                # Namespace collision — store both with qualified keys
                self.entries[existing.fully_qualified_name] = existing
                self.entries[entry.fully_qualified_name] = entry
                # Keep short name pointing to the first one registered
                return
        self.entries[entry.class_name] = entry

    def get(self, class_name: str) -> Optional[DTOEntry]:
        return self.entries.get(class_name)

    def get_qualified(self, class_name: str, package_hint: str = "") -> Optional[DTOEntry]:
        """Resolve a DTO by name, using package hint to disambiguate collisions."""
        entry = self.entries.get(class_name)
        if entry and (not package_hint or entry.package == package_hint):
            return entry
        # Try fully qualified lookup
        for key, e in self.entries.items():
            if e.class_name == class_name and (not package_hint or package_hint in e.package):
                return e
        return None

    def get_collisions(self) -> dict[str, list[DTOEntry]]:
        """Return DTOs with the same class_name but different packages."""
        by_name: dict[str, list[DTOEntry]] = {}
        for entry in self.entries.values():
            by_name.setdefault(entry.class_name, []).append(entry)
        return {name: entries for name, entries in by_name.items() if len(entries) > 1}

    def serializable_dtos(self) -> list[DTOEntry]:
        """Return all DTOs that require Json.decodeFromString construction."""
        return [e for e in self.entries.values() if e.is_serializable]

    def for_journey(self, journey_name: str) -> list[DTOEntry]:
        return [e for e in self.entries.values() if journey_name in e.used_in_journeys]

    @property
    def count(self) -> int:
        return len(self.entries)
