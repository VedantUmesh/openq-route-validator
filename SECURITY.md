# Security policy

## Supported versions

Security fixes are applied to the latest published release and the default
branch. Older versions may not receive fixes; upgrade before reporting a
reproducible issue.

## Reporting a vulnerability

Please do **not** open a public issue for a suspected vulnerability.

Use GitHub's **Report a vulnerability** button in the repository's Security
tab to create a private security advisory. Include:

- a concise description and impact assessment;
- affected versions or commit identifiers;
- a minimal reproduction or proof of concept;
- the environment and Python version; and
- any proposed mitigation, if known.

If private vulnerability reporting is unavailable in your GitHub view, contact
the repository maintainers through a private GitHub message and request a
security contact. Do not attach secrets or production data.

Maintainers will acknowledge a report when practical, investigate it privately,
and coordinate disclosure and credit with the reporter. Please allow time for
triage before making details public.

## Security design notes

The parser accepts a deliberately small grammar for states, edges, and gates.
It never evaluates user-provided strings as Python code. Callers embedding the
library should still apply their own input-size and timeout policy; use
`max_states` and `max_steps` for untrusted workloads.
