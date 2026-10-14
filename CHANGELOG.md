# Changelog

All notable changes to OpenQ Route Validator are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned

- Publish the first stable 1.0 API after real-world feedback.
- Add optional weighted operations without changing the unweighted default.

## [0.2.0] - 2026-10-14

### Added

- Configurable immutable topologies and custom node counts.
- Explainable `RouteProblem`, `RouteResult`, and `solve()` APIs.
- Stable typed errors for invalid input, forbidden states, no routes, and
  bounded searches.
- Strict gate parsing and `find`/`validate` CLI commands with JSON output.
- Search limits for state count and route depth.
- CI, CodeQL, Dependabot, issue forms, and contributor documentation.

### Preserved

- The original three-node directed cycle defaults.
- The original `find_route()` and `validate_route()` helper behavior.
- Classical bit-state semantics; no quantum-amplitude claims.

## [0.1.0] - 2026-10-14

### Added

- Initial dependency-free route validator and breadth-first search.
