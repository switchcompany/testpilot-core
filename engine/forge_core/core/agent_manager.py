"""Agent manager — heartbeat monitoring, stuck detection, scope splitting."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from forge_core.utils import logger


@dataclass
class AgentState:
    """Tracks the state of a generation agent."""

    scope_id: str
    target_files: list[str]
    started_at: float = field(default_factory=time.time)
    tool_calls: int = 0
    last_progress_at: float = field(default_factory=time.time)
    errors: list[str] = field(default_factory=list)
    consecutive_same_error: int = 0
    last_error: str = ""
    completed: bool = False


class AgentManager:
    """Manages agent lifecycle with heartbeat and stuck detection.

    Rules from copilot-instructions.md:
    - Heartbeat every 10 tool calls
    - Fruitless detection: same error 3x
    - Auto-termination after 20 fruitless calls
    - Scope splitting for stuck agents
    """

    MAX_FRUITLESS_CALLS = 20
    SAME_ERROR_THRESHOLD = 3
    HEARTBEAT_INTERVAL = 10

    def __init__(self):
        self._agents: dict[str, AgentState] = {}

    def register(self, scope_id: str, target_files: list[str]) -> AgentState:
        """Register a new agent scope."""
        state = AgentState(scope_id=scope_id, target_files=target_files)
        self._agents[scope_id] = state
        return state

    def heartbeat(self, scope_id: str) -> str:
        """Record a heartbeat. Returns action: 'continue', 'split', or 'terminate'."""
        state = self._agents.get(scope_id)
        if not state:
            return "terminate"

        state.tool_calls += 1

        # Check fruitless threshold
        if state.consecutive_same_error >= self.SAME_ERROR_THRESHOLD:
            logger.warn(f"Agent {scope_id}: same error {state.consecutive_same_error}x — splitting scope")
            return "split"

        if state.tool_calls >= self.MAX_FRUITLESS_CALLS and not state.last_progress_at > state.started_at:
            logger.warn(f"Agent {scope_id}: {state.tool_calls} calls with no progress — terminating")
            return "terminate"

        # Periodic heartbeat log
        if state.tool_calls % self.HEARTBEAT_INTERVAL == 0:
            elapsed = time.time() - state.started_at
            logger.info(f"Agent {scope_id}: {state.tool_calls} calls, {elapsed:.0f}s elapsed")

        return "continue"

    def record_error(self, scope_id: str, error: str) -> None:
        """Record an error from an agent."""
        state = self._agents.get(scope_id)
        if not state:
            return

        state.errors.append(error)
        if error == state.last_error:
            state.consecutive_same_error += 1
        else:
            state.consecutive_same_error = 1
            state.last_error = error

    def record_progress(self, scope_id: str) -> None:
        """Record that an agent made progress (wrote a file, coverage increased)."""
        state = self._agents.get(scope_id)
        if state:
            state.last_progress_at = time.time()
            state.consecutive_same_error = 0

    def split_scope(self, scope_id: str) -> list[list[str]]:
        """Split a stuck agent's scope into smaller pieces."""
        state = self._agents.get(scope_id)
        if not state or len(state.target_files) <= 1:
            return []

        files = state.target_files
        mid = len(files) // 2
        return [files[:mid], files[mid:]]

    def complete(self, scope_id: str) -> None:
        """Mark an agent as completed."""
        state = self._agents.get(scope_id)
        if state:
            state.completed = True

    @property
    def active_count(self) -> int:
        return sum(1 for s in self._agents.values() if not s.completed)
