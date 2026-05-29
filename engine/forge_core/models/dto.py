"""Pydantic models for DTO registry."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DTOParam(BaseModel):
    """A single constructor/field parameter of a DTO."""

    name: str
    type: str
    default: str = ""
    nullable: bool = False


class DTOEntry(BaseModel):
    """A single DTO class registered in the global registry."""

    class_name: str
    package: str
    file_path: str
    params: list[DTOParam] = Field(default_factory=list)
    has_builder: bool = False
    has_factory: bool = False
    validation_annotations: list[str] = Field(default_factory=list)
    nested_dtos: list[str] = Field(default_factory=list)  # class names of nested DTOs
    used_in_journeys: list[str] = Field(default_factory=list)
    used_in_layers: list[str] = Field(default_factory=list)

    def mock_snippet(self) -> str:
        """Generate a minimal mock/test instance snippet."""
        params_str = ", ".join(
            f'{p.name}={"null" if p.nullable else repr(p.default) if p.default else "TODO"}'
            for p in self.params
        )
        return f"{self.class_name}({params_str})"


class DTORegistry(BaseModel):
    """Global registry of all DTOs in the project — read once, shared everywhere."""

    entries: dict[str, DTOEntry] = Field(default_factory=dict)  # class_name → DTOEntry

    def register(self, entry: DTOEntry) -> None:
        self.entries[entry.class_name] = entry

    def get(self, class_name: str) -> "Optional[DTOEntry]":
        return self.entries.get(class_name)

    def for_journey(self, journey_name: str) -> list[DTOEntry]:
        return [e for e in self.entries.values() if journey_name in e.used_in_journeys]

    @property
    def count(self) -> int:
        return len(self.entries)
