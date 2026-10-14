"""Safe route validation and deterministic breadth-first search."""

from __future__ import annotations

from collections import deque
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .errors import (
    ForbiddenStateError,
    InvalidGateError,
    NoRouteError,
    RouteError,
    SearchLimitError,
)
from .model import (
    DEFAULT_TOPOLOGY,
    Gate,
    RouteProblem,
    RouteResult,
    Topology,
    parse_state,
)

NODES = DEFAULT_TOPOLOGY.nodes
EDGES = DEFAULT_TOPOLOGY.cnot_edges
State = Tuple[int, ...]


def _apply(state: State, gate: Gate, topology: Topology) -> State:
    """Apply one gate after checking it against the selected topology."""

    if not isinstance(gate, Gate):
        raise InvalidGateError("route contains a value that is not a Gate")

    if gate.name == "X":
        if gate.target not in range(topology.nodes) or gate.control is not None:
            raise InvalidGateError("invalid X gate")
        result = list(state)
        result[gate.target] ^= 1
        return tuple(result)

    if gate.name == "CNOT":
        if (
            gate.control is None
            or gate.target not in range(topology.nodes)
            or (gate.control, gate.target) not in topology.edge_set
        ):
            raise InvalidGateError(
                "CNOT must use one of the directed edges configured for the topology"
            )
        result = list(state)
        if state[gate.control]:
            result[gate.target] ^= 1
        return tuple(result)

    raise InvalidGateError(f"unsupported gate: {gate.name}")


def _state_text(state: Sequence[int]) -> str:
    return "".join(str(bit) for bit in state)


def _forbidden_states(forbidden: Iterable[str], topology: Topology) -> Set[State]:
    return {parse_state(item, topology.nodes) for item in forbidden}


def validate_route(
    initial: str,
    target: str,
    gates: Iterable[Gate],
    forbidden: Iterable[str] = (),
    *,
    topology: Topology = DEFAULT_TOPOLOGY,
) -> List[str]:
    """Apply a route and return every visited state, including the initial state.

    The input may be any iterable, including a generator.  Every intermediate
    state is checked before the next gate is applied.
    """

    state = parse_state(initial, topology.nodes)
    expected_target = parse_state(target, topology.nodes)
    forbidden_states = _forbidden_states(forbidden, topology)
    visited = [_state_text(state)]
    if state in forbidden_states:
        raise ForbiddenStateError(
            "initial state is forbidden", state=visited[0], step=0
        )

    for step, gate in enumerate(gates, start=1):
        state = _apply(state, gate, topology)
        text = _state_text(state)
        if state in forbidden_states:
            raise ForbiddenStateError(
                f"route entered forbidden state {text}",
                state=text,
                step=step,
                gate=gate,
            )
        visited.append(text)

    if state != expected_target:
        raise RouteError(f"route ended at {_state_text(state)}, expected {target}")
    return visited


def _operations(topology: Topology) -> Tuple[Gate, ...]:
    flips = tuple(Gate.x(target) for target in range(topology.nodes))
    cnot_gates = tuple(Gate.cnot(control, target) for control, target in topology.cnot_edges)
    return flips + cnot_gates


def _reconstruct(
    parents: Dict[State, Optional[Tuple[State, Gate]]], goal: State
) -> Tuple[Tuple[Gate, ...], Tuple[str, ...]]:
    gates: List[Gate] = []
    states: List[str] = [_state_text(goal)]
    current = goal
    while parents[current] is not None:
        previous, gate = parents[current]  # type: ignore[misc]
        gates.append(gate)
        states.append(_state_text(previous))
        current = previous
    gates.reverse()
    states.reverse()
    return tuple(gates), tuple(states)


def solve(problem: RouteProblem) -> RouteResult:
    """Find a shortest safe route for a fully specified problem."""

    topology = problem.topology
    start = parse_state(problem.initial, topology.nodes)
    goal = parse_state(problem.target, topology.nodes)
    forbidden = _forbidden_states(problem.forbidden, topology)

    if start in forbidden or goal in forbidden:
        raise ForbiddenStateError("initial and target states must not be forbidden")

    parents: Dict[State, Optional[Tuple[State, Gate]]] = {start: None}
    depths: Dict[State, int] = {start: 0}
    queue = deque([start])
    operations = _operations(topology)
    depth_limited = False

    while queue:
        state = queue.popleft()
        depth = depths[state]
        if state == goal:
            gates, states = _reconstruct(parents, goal)
            return RouteResult(gates, states, len(parents))

        if problem.max_steps is not None and depth >= problem.max_steps:
            depth_limited = True
            continue

        for gate in operations:
            next_state = _apply(state, gate, topology)
            if next_state in forbidden or next_state in parents:
                continue
            if problem.max_states is not None and len(parents) >= problem.max_states:
                raise SearchLimitError(
                    f"search reached max_states={problem.max_states}",
                    state=_state_text(state),
                    step=depth,
                    gate=gate,
                    explored_states=len(parents),
                )
            parents[next_state] = (state, gate)
            depths[next_state] = depth + 1
            queue.append(next_state)

    if depth_limited:
        raise SearchLimitError(
            f"search reached max_steps={problem.max_steps}",
            explored_states=len(parents),
        )
    raise NoRouteError("no valid route exists", explored_states=len(parents))


def find_route(
    initial: str,
    target: str,
    forbidden: Iterable[str] = (),
    *,
    topology: Topology = DEFAULT_TOPOLOGY,
    max_states: Optional[int] = None,
    max_steps: Optional[int] = None,
) -> List[Gate]:
    """Find a shortest valid route using X and directed CNOT operations."""

    problem = RouteProblem(
        initial=initial,
        target=target,
        forbidden=tuple(forbidden),
        topology=topology,
        max_states=max_states,
        max_steps=max_steps,
    )
    return list(solve(problem).gates)


__all__ = [
    "EDGES",
    "NODES",
    "find_route",
    "parse_state",
    "solve",
    "validate_route",
]
