"""Stable exception types raised by :mod:`openq_route_validator`."""

from __future__ import annotations

from typing import Any, Optional


class RouteError(ValueError):
    """Base class for invalid inputs and unsuccessful route searches.

    The ``code`` attribute is intentionally stable so applications can handle
    errors without matching human-readable messages.  Optional context fields
    are populated when the router has useful information about the failure.
    """

    code = "route_error"

    def __init__(
        self,
        message: str,
        *,
        state: Optional[str] = None,
        step: Optional[int] = None,
        gate: Any = None,
        explored_states: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.state = state
        self.step = step
        self.gate = gate
        self.explored_states = explored_states


class InvalidStateError(RouteError):
    """Raised when a bit-state is malformed for the selected topology."""

    code = "invalid_state"


class InvalidTopologyError(RouteError):
    """Raised when a topology contains invalid or duplicate edges."""

    code = "invalid_topology"


class InvalidGateError(RouteError):
    """Raised when a gate is malformed or unsupported."""

    code = "invalid_gate"


class ForbiddenStateError(RouteError):
    """Raised when a route starts in or enters a forbidden state."""

    code = "forbidden_state"


class NoRouteError(RouteError):
    """Raised when the complete finite state space has no valid route."""

    code = "no_route"


class SearchLimitError(RouteError):
    """Raised when a caller-provided search bound is reached."""

    code = "search_limit"


__all__ = [
    "ForbiddenStateError",
    "InvalidGateError",
    "InvalidStateError",
    "InvalidTopologyError",
    "NoRouteError",
    "RouteError",
    "SearchLimitError",
]
