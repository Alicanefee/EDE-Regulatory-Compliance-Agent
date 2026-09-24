"""
EDE Regulatory Compliance Agent — State Machine
===============================================

YAML-driven deterministic state machine. The LLM does NOT pick which agent
to call; the state machine does. Agents are deterministic roles defined in YAML.

See docs/architecture.md for the design.

State flow:
    UPLOAD → INGEST → CLASSIFY → CONFIRM_CLASS → CHECKLIST → COLLECT
    → VALIDATE → REPORT → DONE
                       ↓ (on_error or uncertainty)
                   MANUAL_REVIEW (fallback)

Each state has:
  - entry_condition: what triggers this state
  - agent: which agent to call
  - input: what data the agent needs
  - output: what data the agent produces
  - next: success transition
  - on_error: failure transition (typically MANUAL_REVIEW)
  - on_uncertain: classifier uncertainty → MANUAL_REVIEW (optional)
  - max_loops: prevent infinite cycling (for CONFIRM_CLASS, COLLECT)
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class State(str, Enum):
    """State machine states."""
    UPLOAD = "UPLOAD"
    INGEST = "INGEST"
    CLASSIFY = "CLASSIFY"
    CONFIRM_CLASS = "CONFIRM_CLASS"
    CHECKLIST = "CHECKLIST"
    COLLECT = "COLLECT"
    VALIDATE = "VALIDATE"
    REPORT = "REPORT"
    DONE = "DONE"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass
class StateDefinition:
    """Definition of a state from YAML."""
    name: str
    description: str = ""
    entry_condition: str = ""
    agent: str = ""
    input: str = ""
    output: str = ""
    next: str = ""
    on_error: str = "MANUAL_REVIEW"
    on_uncertain: str | None = None
    action: str | None = None
    max_loops: int | None = None


@dataclass
class StateContext:
    """Mutable context carried through state transitions."""
    current_state: State
    submission_data: dict = field(default_factory=dict)
    ingested_chunks: list[dict] = field(default_factory=list)
    classification_result: dict | None = None
    checklist: list[dict] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)
    user_evidence: list[dict] = field(default_factory=list)
    audit_log: list[dict] = field(default_factory=list)
    loop_counts: dict[str, int] = field(default_factory=dict)
    extra: dict = field(default_factory=dict)


class StateMachine:
    """YAML-driven state machine for regulatory compliance agent.

    Usage:
        sm = StateMachine.from_yaml("data/state_machine.yaml")
        ctx = StateContext(current_state=State.UPLOAD, submission_data={...})
        while ctx.current_state != State.DONE:
            ctx = sm.step(ctx, agent_registry)
    """

    def __init__(self, states: dict[str, StateDefinition]) -> None:
        self.states = states

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "StateMachine":
        """Load state machine definition from YAML file."""
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"State machine YAML not found: {yaml_path}")

        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        states = {}
        for name, definition in data.get("states", {}).items():
            states[name] = StateDefinition(
                name=name,
                description=definition.get("description", ""),
                entry_condition=definition.get("entry_condition", ""),
                agent=definition.get("agent", ""),
                input=definition.get("input", ""),
                output=definition.get("output", ""),
                next=definition.get("next", ""),
                on_error=definition.get("on_error", "MANUAL_REVIEW"),
                on_uncertain=definition.get("on_uncertain"),
                action=definition.get("action"),
                max_loops=definition.get("max_loops"),
            )
        return cls(states)

    def step(
        self,
        ctx: StateContext,
        agent_registry: dict[str, Callable],
    ) -> StateContext:
        """Execute one state transition.

        Args:
            ctx: Current state context
            agent_registry: Map from agent name (e.g. "classifier") to callable

        Returns: Updated context with new current_state.
        """
        state_def = self.states.get(ctx.current_state.value)
        if not state_def:
            raise ValueError(f"Unknown state: {ctx.current_state}")

        # Track loop count for states with max_loops
        if state_def.max_loops:
            ctx.loop_counts[ctx.current_state.value] = ctx.loop_counts.get(ctx.current_state.value, 0) + 1
            if ctx.loop_counts[ctx.current_state.value] > state_def.max_loops:
                ctx.current_state = State.MANUAL_REVIEW
                ctx.audit_log.append({
                    "event": "max_loops_exceeded",
                    "state": ctx.current_state.value,
                    "max_loops": state_def.max_loops,
                })
                return ctx

        # Get the agent for this state
        agent_name = state_def.agent
        agent_fn = agent_registry.get(agent_name)
        if not agent_fn:
            ctx.audit_log.append({
                "event": "agent_not_found",
                "state": ctx.current_state.value,
                "agent": agent_name,
            })
            ctx.current_state = State.MANUAL_REVIEW
            return ctx

        # Execute agent
        try:
            agent_output = agent_fn(ctx)
        except Exception as e:
            ctx.audit_log.append({
                "event": "agent_error",
                "state": ctx.current_state.value,
                "agent": agent_name,
                "error": str(e),
            })
            ctx.current_state = State(state_def.on_error)
            return ctx

        # Log execution
        ctx.audit_log.append({
            "event": "agent_executed",
            "state": ctx.current_state.value,
            "agent": agent_name,
            "output_size": len(str(agent_output)) if agent_output else 0,
        })

        # Determine next state
        next_state_value = self._determine_next_state(state_def, agent_output)
        ctx.current_state = State(next_state_value)
        return ctx

    def _determine_next_state(self, state_def: StateDefinition, agent_output: dict | None) -> str:
        """Determine next state based on agent output."""
        if not agent_output:
            return state_def.next

        # Check for explicit error flag
        if agent_output.get("error"):
            return state_def.on_error

        # Check for uncertainty (CLASSIFY state)
        if agent_output.get("is_uncertain") and state_def.on_uncertain:
            return state_def.on_uncertain

        # Check for user action (CONFIRM_CLASS state)
        if state_def.action == "ask_user_confirmation":
            user_response = agent_output.get("user_response", "yes")
            if user_response == "no":
                return state_def.on_reclassify if hasattr(state_def, "on_reclassify") and state_def.on_reclassify else state_def.on_error
            elif user_response == "manual":
                return state_def.on_error

        # Check for missing documents (COLLECT state)
        if agent_output.get("missing_documents"):
            return state_def.next  # proceed to VALIDATE; missing items flagged in report

        return state_def.next

    def run(
        self,
        ctx: StateContext,
        agent_registry: dict[str, Callable],
        max_steps: int = 50,
    ) -> StateContext:
        """Run the full state machine until terminal state.

        Args:
            ctx: Initial context
            agent_registry: Map from agent name to callable
            max_steps: Safety limit to prevent infinite loops

        Returns: Final context with audit log.
        """
        steps = 0
        while ctx.current_state not in (State.DONE, State.MANUAL_REVIEW):
            if steps >= max_steps:
                ctx.audit_log.append({
                    "event": "max_steps_exceeded",
                    "steps": steps,
                })
                ctx.current_state = State.MANUAL_REVIEW
                break

            ctx = self.step(ctx, agent_registry)
            steps += 1

        ctx.audit_log.append({
            "event": "state_machine_complete",
            "final_state": ctx.current_state.value,
            "total_steps": steps,
        })
        return ctx
