# ADR-042: Advance the Python suite to 3.14

## Status

Accepted, 2026-08-28.

## Context

[ADR-038](ADR-038-pin-the-python-suite-to-one-interpreter.md) gave every
repository-owned workflow one supported minor and one exact execution patch.
It selected 3.13 because that was the newest minor every workflow had already
run, while 3.14 had no repository evidence at the decision point.

The local development shell now resolves the exact 3.14.6 patch, that patch is
available to `actions/setup-python`, and the locked Lazarus environment
installs for it. A compatibility run found one changed standard-library
behaviour: boolean `pathlib` predicates suppress every operating-system error
on 3.14. Lazarus used those predicates where it needed to distinguish a
missing output from one that could not be inspected. The existing oversized
output-name test reproduced that loss of distinction.

## Decision

Keep ADR-038's one-interpreter design. Advance the durable minor contract in
[`pyproject.toml`](../../pyproject.toml) to `==3.14.*` and the exact execution
patch in [`.python-version`](../../.python-version) to 3.14.6. Every
repository-owned Python workflow continues to read the exact pin.

Lazarus checks output existence with `Path.lstat()`. A missing path returns
false, while another operating-system or value error remains the bounded
`fixture output cannot be inspected` refusal. The guard simulates suppressed
boolean predicates so it remains meaningful on either interpreter minor.

Goldfinch v1 includes `demo.py` in its fixture identity. Regenerate its
manifest, Ariadne statement, and release from the changed bytes. The resulting
fixture digest is
`06043f4c4e7f62701d55cc0acb948f9330ec218ae50d786daa43ffefb6079eb2`,
the statement file SHA-256 is
`8c1571c67953e0b2df7808e506c1eee0b3f63bfdcc9290877c3d1c7eb67d0bc1`, and
the release digest is
`c6b170ff7b93eb5e2e751f65ca85f3b937005c91fa633cecd801939637c258dc`.

The existing locked Lazarus dependencies remain unchanged because the exact
lock installs on the new interpreter and its full suite remains the dependency
gate. Historical studies, runbooks, proofs, and audit records retain the
versions and bytes they observed. The Goldfinch v0 release remains
byte-identical.

## Alternatives

- Keep 3.13.15. This avoided the compatibility change, but required local
  execution to keep installing an otherwise unused patch after 3.14 became the
  normal shell.
- Put `3.14` rather than an exact patch in `.python-version`. That reduced
  local setup, but let local and hosted runs resolve different patch releases.
- Restore a minor-version matrix. That would test a wider surface, but would
  no longer give repository commands, dependency installation, and workflows
  one execution image.
- Accept the later Lazarus refusal. Both paths failed closed, but the later
  message lost the distinction between an absent output and an output whose
  status the process could not inspect.

## Consequences

Local and hosted repository commands use one exact 3.14.6 interpreter. A later
patch or minor still requires an explicit contract update and fresh evidence.
The `pathlib` guard records the only behaviour change found by this migration;
it does not claim compatibility with every future standard-library change or
with another operating system.
