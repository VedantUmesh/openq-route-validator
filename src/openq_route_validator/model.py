"""Immutable domain objects and parsers for safe route planning."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple

from .errors import InvalidGateError, InvalidStateError, InvalidTopologyError

Edge = Tuple[int, int]


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


@dataclass(frozen=True)
class Topology:
    """Directed CNOT topology for a finite bit-state network.

    When ``cnot_edges`` is omitted, nodes are connected in a directed cycle.
    This preserves the original three-node ``0 -> 1 -> 2 -> 0`` behavior while
    making larger pedagogical and production test topologies easy to describe.
    """

    nodes: int = 3
    cnot_edges: Optional[Tuple[Edge, ...]] = None

    def __post_init__(self) -> None:
        if not _is_int(self.nodes) or self.nodes < 1:
            raise InvalidTopologyError("topology nodes must be a positive integer")

        if self.cnot_edges is None:
            edges: Tuple[Edge, ...] = (
                tuple((node, (node + 1) % self.nodes) for node in range(self.nodes))
                if self.nodes > 1
                else ()
            )
        else:
            try:
                edges = tuple(tuple(edge) for edge in self.cnot_edges)  # type: ignore[arg-type]
            except (TypeError, ValueError) as error:
                raise InvalidTopologyError("each CNOT edge must contain two node indexes") from error

        normalized = []
        for edge in edges:
            if len(edge) != 2 or not all(_is_int(node) for node in edge):
                raise InvalidTopologyError("each CNOT edge must contain two integer node indexes")
            control, target = edge
            if control == target:
                raise InvalidTopologyError("CNOT topology cannot contain self edges")
            if not (0 <= control < self.nodes and 0 <= target < self.nodes):
                raise InvalidTopologyError(
                    f"CNOT edge {control}->{target} is outside a {self.nodes}-node topology"
                )
            normalized.append((control, target))

        if len(set(normalized)) != len(normalized):
            raise InvalidTopologyError("CNOT topology cannot contain duplicate edges")

        object.__setattr__(self, "cnot_edges", tuple(normalized))

    @property
    def edge_set(self) -> frozenset[Edge]:
        """Return the configured edges as a fast membership set."""

        return frozenset(self.cnot_edges or ())


DEFAULT_TOPOLOGY = Topology()


@dataclass(frozen=True)
class Gate:
    """A supported operation in a route.

    ``CNOT`` stores the target in ``target`` and the control in ``control`` to
    retain compatibility with the original public constructor.
    """

    name: str
    target: int
    control: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidGateError("gate name must be X or CNOT")
        name = self.name.strip().upper()
        if name not in {"X", "CNOT"}:
            raise InvalidGateError(f"unsupported gate: {self.name}")
        if not _is_int(self.target):
            raise InvalidGateError("gate target must be an integer node index")
        if name == "X" and self.control is not None:
            raise InvalidGateError("X gates do not have a control node")
        if name == "CNOT" and not _is_int(self.control):
            raise InvalidGateError("CNOT gates require an integer control node")
        object.__setattr__(self, "name", name)

    @classmethod
    def x(cls, target: int) -> "Gate":
        """Build a bit-flip gate for ``target``."""

        return cls("X", target)

    @classmethod
    def cnot(cls, control: int, target: int) -> "Gate":
        """Build a directed controlled-NOT gate."""

        return cls("CNOT", target, control)

    def __str__(self) -> str:
        if self.name == "X":
            return f"X({self.target})"
        return f"CNOT({self.control},{self.target})"


@dataclass(frozen=True)
class RouteProblem:
    """All inputs and safety bounds for one route search."""

    initial: str
    target: str
    forbidden: Tuple[str, ...] = ()
    topology: Topology = DEFAULT_TOPOLOGY
    max_states: Optional[int] = None
    max_steps: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.topology, Topology):
            raise TypeError("topology must be a Topology instance")
        object.__setattr__(self, "forbidden", tuple(self.forbidden))
        if self.max_states is not None and (
            not _is_int(self.max_states) or self.max_states < 1
        ):
            raise ValueError("max_states must be a positive integer")
        if self.max_steps is not None and (
            not _is_int(self.max_steps) or self.max_steps < 0
        ):
            raise ValueError("max_steps must be a non-negative integer")


@dataclass(frozen=True)
class RouteResult:
    """A validated shortest route and search diagnostics."""

    gates: Tuple[Gate, ...]
    states: Tuple[str, ...]
    explored_states: int

    @property
    def steps(self) -> int:
        """Number of operations in the route."""

        return len(self.gates)


def parse_state(state: str, nodes: int = 3) -> Tuple[int, ...]:
    """Parse a bit-state such as ``"010"`` into an integer tuple."""

    if not isinstance(state, str) or len(state) != nodes or any(bit not in "01" for bit in state):
        message = (
            "state must contain exactly three bits"
            if nodes == 3
            else f"state must contain exactly {nodes} bits"
        )
        raise InvalidStateError(message)
    return tuple(int(bit) for bit in state)


_X_PATTERN = re.compile(r"X\(\s*(\d+)\s*\)", re.IGNORECASE)
_CNOT_PATTERN = re.compile(r"CNOT\(\s*(\d+)\s*,\s*(\d+)\s*\)", re.IGNORECASE)


def parse_gate(text: str) -> Gate:
    """Parse ``X(n)`` or ``CNOT(control,target)`` without evaluating code."""

    if not isinstance(text, str):
        raise InvalidGateError("gate must be written as X(n) or CNOT(control,target)")
    candidate = text.strip()
    x_match = _X_PATTERN.fullmatch(candidate)
    if x_match:
        return Gate.x(int(x_match.group(1)))
    cnot_match = _CNOT_PATTERN.fullmatch(candidate)
    if cnot_match:
        return Gate.cnot(int(cnot_match.group(1)), int(cnot_match.group(2)))
    raise InvalidGateError(
        f"invalid gate '{text}'; expected X(n) or CNOT(control,target)"
    )


__all__ = [
    "DEFAULT_TOPOLOGY",
    "Edge",
    "Gate",
    "RouteProblem",
    "RouteResult",
    "Topology",
    "parse_gate",
    "parse_state",
]
