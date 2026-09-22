# Hermes kickoff 1355

This directory records the checked study and the first preparation step for
Wildcat V2 Ethereum protected layouts and method identifiers.

## Records

`study.md` fixes the scope and selected design. `runbook.md` fixes the
ordered delivery gates. `design-evidence.json` is the immutable Protasis
matrix. `evidence/prepared-harnesses.json` is a public summary of nine signed
test-harness revisions.

## Checks

Run the public summary check from the repository root:

```bash
python3 scripts/kickoff_hermes_1355.py validate \
  --manifest docs/kickoff/1355/evidence/prepared-harnesses.json
```

The complete preparation check additionally reads the run-local restricted
evidence directory:

```bash
python3 scripts/kickoff_hermes_1355.py conformance \
  --candidate prepared-source-group \
  --criterion prepared-state \
  --report .hexaemeron/design-reports/prepared-source-group-prepared-state.json
```

Success establishes that the named prepared commits are signed children of
their source pins, their fixed-seed suites passed, and every difference is
confined to the admitted test files. It does not establish the final protected
inventory, deployment mapping, a Hermes Gate 1 result or authority to publish
private source.

## Evidence boundary

The private fee-recipient and role-provider source, complete logs and source
worktrees stay beneath `.hexaemeron/restricted/step-1/`, which Git ignores.
The public manifest carries their digests and counts without source bytes or
absolute paths. A later restricted-delivery gate must name an authorised,
retrievable destination before integration.
