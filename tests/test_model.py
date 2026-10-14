import pytest

from openq_route_validator import (
    Gate,
    InvalidGateError,
    InvalidTopologyError,
    Topology,
    parse_gate,
    parse_state,
)


def test_topology_defaults_to_a_directed_cycle_for_any_node_count():
    assert Topology(nodes=4).cnot_edges == ((0, 1), (1, 2), (2, 3), (3, 0))


def test_gate_factories_and_parser_use_the_public_text_format():
    assert Gate.x(2) == parse_gate(" X(2) ")
    assert Gate.cnot(0, 1) == parse_gate("cnot(0, 1)")
    assert str(Gate.cnot(0, 1)) == "CNOT(0,1)"


def test_parser_rejects_code_like_gate_input():
    with pytest.raises(InvalidGateError, match="expected X"):
        parse_gate("__import__('os').system('whoami')")


def test_topology_rejects_duplicates_self_edges_and_out_of_range_edges():
    with pytest.raises(InvalidTopologyError, match="duplicate"):
        Topology(nodes=3, cnot_edges=((0, 1), (0, 1)))
    with pytest.raises(InvalidTopologyError, match="self"):
        Topology(nodes=3, cnot_edges=((1, 1),))
    with pytest.raises(InvalidTopologyError, match="outside"):
        Topology(nodes=3, cnot_edges=((0, 3),))


def test_parse_state_supports_custom_topologies():
    assert parse_state("0101", nodes=4) == (0, 1, 0, 1)
