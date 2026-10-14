"""Copy-paste example: solve a bounded route in a four-node topology."""

from openq_route_validator import RouteProblem, Topology, solve

problem = RouteProblem(
    initial="1000",
    target="1111",
    topology=Topology(
        nodes=4,
        cnot_edges=((0, 1), (1, 2), (2, 3)),
    ),
    max_states=256,
    max_steps=12,
)

result = solve(problem)
print(f"Found {result.steps} steps after exploring {result.explored_states} states")
for gate, state in zip(result.gates, result.states[1:]):
    print(f"{gate} -> |{state}>")
