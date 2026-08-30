# ADR-054: Require the complete plugin graph

## Status

Accepted, 2026-08-30.

## Context

ADR-045 made `tests/check-map-v1.json` the repository's one executable graph of
path ownership, checks and downstream dependencies. It deliberately left
hosted CI unchanged. GitHub Actions consequently runs the root invariant suite
on every pull request, while only four plugin families have path-filtered
workflows. The protected branch requires the root `invariants` context but no
plugin context, and it accepts a status from a stale base.

The repository now contains sixteen plugins. Copying their commands into
workflows would create a second registry, and requiring path-filtered jobs would
leave some pull requests without the contexts the ruleset expects. A new plugin
could also be present on disk without an owner or suite entry unless the graph
itself proves parity with the plugin directory.

## Decision

Add one unconditional GitHub Actions job whose stable context name is
`plugins`. It runs `scripts/run_checks.py --full`, so the committed graph, its
fixed argv executor and terminal-accounting rules remain the only definition of
complete repository checks. The job runs for every pull request and every push
to `main`, has read-only repository permissions, checks out full history for
the graph's historical signed-release proofs, installs the dependencies the
graph needs, and uploads the executor's bounded JSON report even on failure.

Keep the existing `invariants` context during this migration. Once the exact
pull-request head has produced both contexts successfully, require both
`invariants` and `plugins` in the live default-branch ruleset and enable strict
required-status checking. Preserve all other ruleset fields and add no bypass
actor.

Make graph completeness a root invariant: every directory directly under
`plugins/` must have a scope, at least one suite check, a dependency entry and
an owner. A plugin cannot silently arrive outside the hosted gate.

The baseline must be honestly gateable in a fresh clone. Unreachable historical
fixtures are repaired at their evidence boundary rather than discarded. The
digest-bound Goldfinch producer is not rewritten: its descriptor cases execute
on hosted Ubuntu and explicitly skip only where the local host cannot expose a
traversable process file-descriptor path. Checkpoint JSON receives an explicit
structural-depth ceiling because a byte ceiling alone does not bound the shape
the decoder can allocate.

## Alternatives

- Add one workflow per missing plugin. This duplicates selection policy,
  preserves path-filter gaps and makes the required-context set unstable.
- List all suite commands in one workflow. This creates a second command graph
  that can disagree with ADR-045.
- Require only the new `plugins` context. It already includes the root suite,
  but removing an established required context in the same change makes the
  enforcement migration harder to verify.
- Keep non-strict status checks. A green result against an obsolete base does
  not establish that the protected tip and proposed change compose.

## Consequences

Every pull request now receives one stable plugin-gate context, and that context
can be green only after the complete declared graph reaches terminal success.
New plugin directories fail the root suite until their ownership and suite are
declared. Maintainers can inspect the uploaded report to distinguish assertion,
setup, timeout and scheduler failures.

The root suite runs once in `invariants` and again within `plugins`. Existing
path-specific workflows may also duplicate some work. This is accepted for a
safe migration: the established root signal remains visible, while the complete
graph becomes enforceable without deleting diagnostics. A later performance
change must measure the cost and preserve the same coverage and required-context
availability.
