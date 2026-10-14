from collections import deque
from itertools import product

import pytest

from openq_route_validator import (
    NoRouteError,
    SearchLimitError,
    Topology,
    find_route,
    validate_route,
)


def _reference_distance(initial, target, topology):
    operations = []
    for node in range(topology.nodes):
        operations.append(("x", node, None))
    operations.extend(("cnot", target_node, control) for control, target_node in topology.cnot_edges)
    queue = deque([(initial, 0)])
    seen = {initial}
    while queue:
        state, distance = queue.popleft()
        if state == target:
            return distance
        for kind, target_node, control in operations:
            bits = list(state)
            if kind == "x" or bits[control]:
                bits[target_node] ^= 1
            next_state = tuple(bits)
            if next_state not in seen:
                seen.add(next_state)
                queue.append((next_state, distance + 1))
    return None


@pytest.mark.parametrize("initial", [tuple(bits) for bits in product((0, 1), repeat=3)])
@pytest.mark.parametrize("target", [tuple(bits) for bits in product((0, 1), repeat=3)])
def test_default_routes_are_shortest_and_valid(initial, target):
    initial_text = "".join(map(str, initial))
    target_text = "".join(map(str, target))
    route = find_route(initial_text, target_text)
    assert len(route) == _reference_distance(initial, target, Topology())
    states = validate_route(initial_text, target_text, route)
    assert states[0] == initial_text
    assert states[-1] == target_text
    assert len(states) == len(route) + 1


def test_no_route_and_search_limits_have_distinct_error_types():
    with pytest.raises(NoRouteError):
        find_route("000", "111", forbidden=["001", "010", "011", "100", "101", "110"])
    with pytest.raises(SearchLimitError):
        find_route("000", "111", max_steps=1)
