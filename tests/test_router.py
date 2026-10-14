import pytest

from openq_route_validator import Gate, RouteError, find_route, validate_route


def test_finds_shortest_safe_route_to_111():
    route = find_route("000", "111", forbidden=["010", "101"])
    assert len(route) == 3
    assert validate_route("000", "111", route, forbidden=["010", "101"]) == [
        "000",
        "100",
        "110",
        "111",
    ]


def test_directed_cnot_is_applied_only_on_valid_edges():
    assert validate_route("100", "110", [Gate("CNOT", 1, 0)]) == ["100", "110"]
    with pytest.raises(RouteError, match="directed edges"):
        validate_route("100", "101", [Gate("CNOT", 2, 0)])


def test_forbidden_state_is_rejected():
    with pytest.raises(RouteError, match="forbidden state"):
        validate_route("000", "010", [Gate("X", 1)], forbidden=["010"])


def test_invalid_state_is_rejected():
    with pytest.raises(RouteError, match="exactly three bits"):
        find_route("00", "111")
