# Architecture and invariants

OpenQ Route Validator has a deliberately narrow execution model. A route is a
sequence of operations over a finite tuple of classical bits.

## Data flow

```text
RouteProblem
    │ validate topology, states, and bounds
    ▼
deterministic BFS ── forbidden-state filter ── parent pointers
    │
    ▼
RouteResult ── gates, visited states, unique states discovered
```

The CLI is a thin adapter around this flow. It parses a strict text grammar,
constructs the same public models, and serializes either human-readable text or
versioned JSON. It does not implement a second routing algorithm.

## Core invariants

1. **Finite state space.** A topology with `n` nodes has at most `2 ** n`
   states. The solver never creates a state outside that space.
2. **Directed operations.** A CNOT is legal only when its exact `(control,
   target)` pair is present in `Topology.cnot_edges`; reverse edges are not
   inferred.
3. **Safety before progress.** The initial, target, and every intermediate state
   are checked against the forbidden set. A route that touches a forbidden
   state is never returned.
4. **Shortest result.** Breadth-first traversal and unit-cost operations mean
   the first goal dequeued is shortest by gate count.
5. **Stable ties.** Operations are generated in node order followed by the
   topology's declared edge order. Repeated runs with the same input return the
   same route.
6. **No code execution.** Gate and edge strings are parsed with regular
   expressions. They are never passed to `eval`, a shell, or an import hook.

## Resource bounds

`max_steps` bounds route depth. `max_states` bounds the number of unique states
discovered. A bound is not treated as proof that no route exists: reaching one
raises `SearchLimitError`. Only a complete bounded-free search can raise
`NoRouteError`.

The library leaves policy around timeouts, process isolation, and request
quotas to its host application. For untrusted workloads, combine the two
router bounds with an application-level deadline.

## Compatibility surface

The compatibility helpers intentionally return the original shapes:

- `find_route(...) -> list[Gate]`
- `validate_route(...) -> list[str]`

New callers that need diagnostics should use `RouteProblem` and `solve()`. The
`RouteError.code` value is the stable machine-facing contract; message text is
for people and logs.
