# Dead-code report v1

`scripts/dead_code.py` inventories candidates over one clean, tracked Git tree.
It is advisory: a non-zero finding count is a successful report, not evidence
that source is semantically unused. The command never deletes or rewrites a
candidate.

## Read the current state

Run the complete demonstration from the repository root using
`.python-version`:

```bash
python3 scripts/dead_code.py report
python3 scripts/dead_code.py report --json
python3 scripts/dead_code.py baseline --check
python3 scripts/run_checks.py --scope dead-code
```

The first two commands show the live universe without running an analyser. The
baseline check reconstructs its recorded source commit with the fixed
`python,repository` analyser set. It verifies the commit, Git tree, universe,
analyser versions and states, finding identities, and suppression digest. The
checked scope validates the implementation and fixtures. Candidate count does
not gate any command.

## Refresh the baseline

1. Commit every source, schema, documentation and suppression change. Leave
   `.dead-code/baseline.json` at its prior value or a tracked placeholder.
2. From that clean commit, run `python3 scripts/dead_code.py baseline --write`.
3. Inspect the only modified path, `.dead-code/baseline.json`, then commit that
   file alone.
4. Run `python3 scripts/dead_code.py baseline --check` from the new clean
   commit.

This two-commit publication is required because a commit cannot contain its
own object identity. The baseline records the first commit; the second commit
may change only the baseline record. A later source, schema, suppression or
documentation change leaves the record valid but behind the checkout. The
check names that on its `currency` line and still exits 0; repeat the sequence
above when the record should describe the current tree.

The writer is confined to `.dead-code/baseline.json`, refuses a dirty tracked
tree, rejects symlinked output directories and replaces the record atomically.
The checker reads committed bytes and does not clean unrelated temporary
files.

## Suppress one exact candidate

`.dead-code/suppressions.json` is canonical JSON under
`schemas/dead-code-suppressions-v1.schema.json`. Entries are sorted by
`finding_id` and use this closed shape:

```json
{
  "finding_id": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "owner": "team or person responsible for review",
  "path": "path/from/repository/root.py",
  "reason": "why this exact candidate is intentionally retained",
  "symbol": "optional symbol, or null"
}
```

Copy `finding_id`, `path` and `symbol` from the live static report. A wildcard,
duplicate identity, unknown field, missing finding, excluded path, mismatched
target or obsolete entry refuses the baseline write/check. A suppression marks
the baseline record; it does not erase the underlying finding or authorise a
source change.

## Recover from refusal

- `modified tracked file(s)`: commit or deliberately discard the named change,
  then rerun. Ignored Fiat state is outside the analysed universe.
- `baseline ... drift`: review the live report and repeat the two-commit
  refresh. Do not edit recorded identities by hand. A behind-but-valid record
  is not a refusal: read the `currency` line, which names the publication
  commit and the paths that changed after it.
- `unused`, `stale target` or `target does not match`: remove or correct the
  exact suppression, review the resulting candidate, then refresh.
- analyser `degraded` or version drift: repair or accept the tool environment
  explicitly; `failed` and `not-available` states cannot be baselined. Zero
  findings from an incomplete analyser is not a clean result.
- write refusal: inspect `.dead-code` for a symlink, foreign object or failed
  permission. The writer will not sweep it automatically.

A future policy that blocks only newly added candidates needs its own ADR,
reviewed baseline and rollout. ADR-053 explicitly rejects turning this v1
inventory into a diff gate.
