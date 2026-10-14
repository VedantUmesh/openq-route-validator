# OpenQ Route Validator

OpenQ Route Validator is a dependency-free Python library and CLI for finding,
validating, and explaining safe routes through finite directed bit-state
networks.

It is intentionally small enough to audit and embed, while providing the
guardrails expected from infrastructure software:

- deterministic breadth-first search for shortest routes;
- configurable directed CNOT topologies, with the original three-node loop as
  the default;
- forbidden-state checks for safety and policy constraints;
- bounded searches for services that need predictable resource use;
- stable, structured errors and machine-readable JSON output; and
- a pure Python API with no runtime dependencies.

The simulator operates on classical bit states. It does **not** simulate
quantum amplitudes, measurement, or quantum hardware.

## Why this project exists

State-space routing appears in test fixtures, workflow schedulers, teaching
tools, safety validators, and small orchestration systems. These callers often
need a trustworthy answer for a finite problem rather than a large framework.
OpenQ Route Validator provides a reviewable reference implementation that can
be used directly in a Python process or as a subprocess in another language.

## Quick start

Requires Python 3.9 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Find a shortest route while avoiding intermediate states:

```bash
openq-route find \
  --initial 000 \
  --target 111 \
  --forbidden 010 101
```

Output:

```text
Found 3 step(s):
Step 1: X(0) -> |100>
Step 2: X(1) -> |110>
Step 3: X(2) -> |111>
```

The original command shape remains supported, so existing scripts can omit the
`find` word:

```bash
openq-route --initial 000 --target 111
```

Validate a route supplied by another system:

```bash
openq-route validate \
  --initial 100 \
  --target 110 \
  --gate 'CNOT(0,1)'
```

## Custom topologies and bounded searches

The default topology is a directed cycle. A custom node count also gets a
directed cycle unless explicit edges are supplied. Quote `->` in shells that
interpret it as redirection.

```bash
openq-route find \
  --nodes 4 \
  --edge '0->1' \
  --edge '1->2' \
  --edge '2->3' \
  --initial 1000 \
  --target 1111 \
  --max-states 256 \
  --max-steps 12 \
  --stats
```

Use JSON when the result is consumed by CI or another program:

```bash
openq-route find --initial 000 --target 111 --format json
openq-route validate --initial 000 --target 111 \
  --gate 'X(0)' --gate 'X(1)' --gate 'X(2)' --format json
```

Successful `find` output has schema version `1` and includes `gates`, `states`,
`steps`, and `explored_states`. Errors use the same schema marker and expose a
stable `error.code`, such as `invalid_state`, `forbidden_state`, `no_route`, or
`search_limit`.

## Python API

```python
from openq_route_validator import (
    RouteProblem,
    Topology,
    find_route,
    solve,
    validate_route,
)

topology = Topology(nodes=3, cnot_edges=((0, 1), (1, 2), (2, 0)))
problem = RouteProblem(
    initial="000",
    target="111",
    forbidden=("010", "101"),
    topology=topology,
    max_states=64,
)

result = solve(problem)
assert result.steps == 3
assert validate_route("000", "111", result.gates, problem.forbidden) == list(result.states)
```

For compatibility with the first release, the concise helpers remain
available:

```python
from openq_route_validator import find_route, validate_route

route = find_route("000", "111", forbidden=["010", "101"])
states = validate_route("000", "111", route, forbidden=["010", "101"])
```

### Public building blocks

- `Topology`: immutable node and directed-edge definition.
- `Gate.x(n)` and `Gate.cnot(control, target)`: explicit operation factories.
- `RouteProblem`: inputs plus optional `max_states` and `max_steps` bounds.
- `RouteResult`: gates, visited states, and unique states discovered.
- `solve()`: returns a complete result with diagnostics.
- `find_route()`: compatibility helper returning `list[Gate]`.
- `validate_route()`: checks every transition and returns visited state text.
- `parse_state()` and `parse_gate()`: strict parsers with no dynamic code
  evaluation.

### Search guarantees

The solver uses breadth-first search, so every returned route is shortest by
gate count. Operation ordering is stable: all `X` gates in ascending node order
are considered before configured CNOT edges in their declared order. Equal-cost
ties are therefore reproducible across runs.

The reachable state space is finite (`2 ** nodes` states), but it can still be
large. Use `max_states` and `max_steps` when routing from a service or CI job.
Hitting either bound raises `SearchLimitError`; exhausting the complete search
without a route raises `NoRouteError`.

## Development

Install the development tools and run the full local check:

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest
python -m build
```

The test suite includes compatibility tests, CLI tests, parser and topology
boundary cases, and exhaustive shortest-path checks over the default 3-bit
state space.

## Project layout

```text
src/openq_route_validator/  library, models, errors, and CLI
tests/                       unit, CLI, and exhaustive behavioral tests
examples/                    copy-paste integration examples
assets/                      project diagrams and static resources
.github/                     CI, CodeQL, Dependabot, and contribution forms
```

## Compatibility and versioning

The project follows semantic versioning for its public Python API and JSON
output schema. The `RouteError` base class and the original `find_route()` and
`validate_route()` signatures are preserved in the 0.2 line. New error
subclasses add stable machine-readable codes without requiring callers to
match message text.

## Security

Please do not disclose vulnerabilities in a public issue. Read
[SECURITY.md](SECURITY.md) for the private reporting process. The project does
not execute gate strings, edge strings, or configuration values as code.

## Contributing

Bug reports, documentation improvements, tests, and focused features are
welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md), run the local checks,
and include a regression test for behavior changes.

## License

OpenQ Route Validator is released under the [MIT License](LICENSE).
