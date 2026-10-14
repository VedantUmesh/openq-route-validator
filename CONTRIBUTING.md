# Contributing to OpenQ Route Validator

Thank you for helping make a small but dependable routing primitive better.
The project values correctness, clear failure modes, portability, and focused
changes over feature volume.

## Before opening an issue

1. Search existing issues and discussions for duplicates.
2. Confirm the behavior on the current default branch.
3. Remove application-specific details and secrets from examples.
4. For a suspected vulnerability, follow [SECURITY.md](SECURITY.md) instead of
   opening a public issue.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the same checks used by continuous integration:

```bash
ruff check .
pytest
python -m build
```

Runtime code must remain dependency-free and support Python 3.9+. Development
dependencies belong in `pyproject.toml`; do not add a runtime dependency for a
test-only convenience.

## Pull requests

- Keep a pull request focused on one behavior or maintenance goal.
- Add or update tests for every behavior change, including invalid input and
  resource-boundary cases where relevant.
- Update README or API documentation when the public API or CLI changes.
- Preserve deterministic operation ordering unless the change explicitly
  documents a compatibility impact.
- Do not include generated build artifacts, virtual environments, credentials,
  or personal configuration.
- Explain compatibility, security, and performance implications in the PR
  description.

The maintainers may request a smaller patch when a change combines unrelated
refactors with user-facing behavior.

## Commit style

Use a short imperative subject. Conventional prefixes are encouraged:

```text
feat: add bounded route search
fix: reject duplicate topology edges
docs: clarify JSON output schema
test: cover forbidden target states
```

## Design expectations

The router is deliberately explicit. Avoid dynamic evaluation, hidden network
calls, global mutable state, and non-deterministic traversal. New public
objects should be immutable where practical and should have a testable,
documented failure mode.

## Code of conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
