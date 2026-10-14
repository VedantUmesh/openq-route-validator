"""Command-line interface for finding and validating safe routes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Optional, Sequence, Tuple

from .errors import RouteError
from .model import Gate, RouteProblem, RouteResult, Topology, parse_gate
from .router import solve, validate_route


class _CLIUsageError(Exception):
    """Internal exception used to keep command-line errors concise."""


_EDGE_PATTERN = re.compile(r"\s*(\d+)\s*->\s*(\d+)\s*")


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _CLIUsageError(message)


def _add_topology_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--nodes",
        type=int,
        default=3,
        help="number of bit nodes (default: 3)",
    )
    parser.add_argument(
        "--edge",
        action="append",
        default=None,
        metavar="CONTROL->TARGET",
        help="directed CNOT edge; repeat to define a custom topology",
    )
    parser.add_argument(
        "--forbidden",
        nargs="*",
        default=[],
        metavar="STATE",
        help="states that routes must never enter",
    )


def _add_output_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )


def _build_parser(command: str) -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog="openq-route",
        description="Find and validate safe routes in finite directed bit-state networks.",
    )
    if command == "find":
        parser.add_argument("--initial", default="000", help="starting bit-state")
        parser.add_argument("--target", default="111", help="target bit-state")
        _add_topology_arguments(parser)
        parser.add_argument(
            "--max-states",
            type=int,
            default=None,
            help="stop after discovering this many states",
        )
        parser.add_argument(
            "--max-steps",
            type=int,
            default=None,
            help="only search routes up to this many gates",
        )
        parser.add_argument(
            "--stats",
            action="store_true",
            help="include search diagnostics in text output",
        )
    else:
        parser.add_argument("--initial", default="000", help="starting bit-state")
        parser.add_argument("--target", default="111", help="target bit-state")
        _add_topology_arguments(parser)
        parser.add_argument(
            "--gate",
            action="append",
            default=[],
            metavar="GATE",
            help="route operation such as 'X(0)' or 'CNOT(0,1)'; repeat in order",
        )
    _add_output_arguments(parser)
    return parser


def _parse_edge(text: str) -> Tuple[int, int]:
    match = _EDGE_PATTERN.fullmatch(text)
    if not match:
        raise RouteError(f"invalid edge '{text}'; expected CONTROL->TARGET")
    return int(match.group(1)), int(match.group(2))


def _topology(nodes: int, edge_texts: Optional[Sequence[str]]) -> Topology:
    edges = None if edge_texts is None else tuple(_parse_edge(text) for text in edge_texts)
    return Topology(nodes=nodes, cnot_edges=edges)


def _result_payload(problem: RouteProblem, result: RouteResult) -> dict:
    return {
        "schema": 1,
        "initial": problem.initial,
        "target": problem.target,
        "gates": [str(gate) for gate in result.gates],
        "states": list(result.states),
        "steps": result.steps,
        "explored_states": result.explored_states,
    }


def _error_payload(error: Exception) -> dict:
    details = {
        "code": getattr(error, "code", "cli_error"),
        "message": str(error),
    }
    for key in ("state", "step", "explored_states"):
        value = getattr(error, key, None)
        if value is not None:
            details[key] = value
    gate = getattr(error, "gate", None)
    if gate is not None:
        details["gate"] = str(gate)
    return {"schema": 1, "error": details}


def _print_error(error: Exception, output_format: str) -> int:
    if output_format == "json":
        print(json.dumps(_error_payload(error), sort_keys=True))
    else:
        print(f"error: {error}", file=sys.stderr)
    return 2


def _print_find_text(result: RouteResult, stats: bool) -> None:
    print(f"Found {result.steps} step(s):")
    for step, (gate, state) in enumerate(zip(result.gates, result.states[1:]), start=1):
        print(f"Step {step}: {gate} -> |{state}>")
    if stats:
        print(f"Explored states: {result.explored_states}")


def _print_validate_text(gates: Sequence[Gate], states: Sequence[str]) -> None:
    print(f"Valid route with {len(gates)} step(s):")
    for step, (gate, state) in enumerate(zip(gates, states[1:]), start=1):
        print(f"Step {step}: {gate} -> |{state}>")


def _run_find(args: argparse.Namespace) -> int:
    topology = _topology(args.nodes, args.edge)
    problem = RouteProblem(
        initial=args.initial,
        target=args.target,
        forbidden=tuple(args.forbidden),
        topology=topology,
        max_states=args.max_states,
        max_steps=args.max_steps,
    )
    result = solve(problem)
    if args.format == "json":
        print(json.dumps(_result_payload(problem, result), sort_keys=True))
    else:
        _print_find_text(result, args.stats)
    return 0


def _run_validate(args: argparse.Namespace) -> int:
    topology = _topology(args.nodes, args.edge)
    gates = tuple(parse_gate(text) for text in args.gate)
    states = validate_route(
        args.initial,
        args.target,
        gates,
        forbidden=tuple(args.forbidden),
        topology=topology,
    )
    if args.format == "json":
        payload = {
            "schema": 1,
            "initial": args.initial,
            "target": args.target,
            "gates": [str(gate) for gate in gates],
            "states": states,
            "steps": len(gates),
            "valid": True,
        }
        print(json.dumps(payload, sort_keys=True))
    else:
        _print_validate_text(gates, states)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the CLI and return a process-style exit code."""

    raw_args = list(sys.argv[1:] if argv is None else argv)
    command = "find"
    if raw_args and raw_args[0] in {"find", "validate"}:
        command = raw_args.pop(0)
    parser = _build_parser(command)
    output_format = "json" if "--format=json" in raw_args else "text"
    if "--format" in raw_args:
        format_index = raw_args.index("--format")
        if format_index + 1 < len(raw_args):
            output_format = raw_args[format_index + 1]

    try:
        args = parser.parse_args(raw_args)
        if command == "find":
            return _run_find(args)
        return _run_validate(args)
    except (_CLIUsageError, RouteError, ValueError) as error:
        return _print_error(error, output_format)


if __name__ == "__main__":
    raise SystemExit(main())
