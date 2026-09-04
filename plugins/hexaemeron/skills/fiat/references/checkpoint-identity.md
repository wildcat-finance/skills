# Fiat checkpoint identity

`hexctl --dir <run-worktree> checkpoint identity` prints the semantic identity
of one verified Fiat checkpoint. It reads the controller state, ledger, source
receipts, observation bindings and Git objects. It does not take the mutation
lock or write a file, ledger entry, Git ref or object.

This identity names checkpoint meaning. The native checkpoint manifest names
the exact controller capsule from `checkpoint export`. A future archive digest
may name exact carrier bytes. None can stand in for another.

## Accepted boundary

The command accepts only a run created with a bound `fiat-run-anchor/v1`
receipt and an immutable full-commit `state.base`. The verified ledger tail
must be one of:

- `done:push`, with the boundary step's final `push.verified_commits` entry as
  the working commit; or
- `audit-round`, while the same step is open at the controller's active
  `audit-verdict`, with `last_local_commit(step)` as the working commit.

The working commit must exist locally and descend from the anchor's
`initial_base_sha`. The step number comes from the ledger tail. A later
controller receipt closes the earlier boundary.

## Pure helper

Issue 561 may call:

```python
checkpoint_identity_from_captured(state_bytes, ledger_bytes, evidence)
```

`state_bytes` and `ledger_bytes` are already captured `bytes`. The ledger must
be a non-empty, newline-terminated exact prefix within the controller file
ceiling. Every line is strict UTF-8 JSON with no duplicate key, the chain must
recompute, and the tail state must equal the captured state fingerprint. The
helper opens no path and writes nothing.

`evidence` is exactly:

```json
{
  "schema": "fiat-checkpoint-identity-evidence/v1",
  "git": {
    "repository": "wildcat-finance/skills",
    "refs": {
      "<recorded-ref>": "<full-commit-sha>"
    },
    "initial_base_sha": "<full-commit-sha>",
    "working_commit_sha": "<full-commit-sha>",
    "ancestry": "verified"
  },
  "sources": {
    "study_sha256": "<lowercase-sha256>",
    "runbook_sha256": "<lowercase-sha256>"
  },
  "observations": {
    "status": "absent",
    "bindings": 0,
    "sha256": "<lowercase-sha256>"
  }
}
```

The `refs` object has exactly the controller's bounded recorded ref set. Its
values prove a stable Git read but do not enter the semantic object. A branch
tip may move between two stable calls without changing `snapshot_id`; movement
during one call refuses before output. `initial_base_sha` and
`working_commit_sha` must match the captured receipts, and `ancestry` is the
result of the fixed-argument Git ancestry check.

Current study and runbook source bytes must recompute to `sources`. A runbook
amendment history must reach the stated current digest.

When `run_observations` is absent, `observations` uses the example above and
its digest is over the canonical bytes of:

```json
{"schema":"fiat-checkpoint-observations/v1","status":"absent"}
```

When bindings exist, `status` is `bound`, `bindings` is the exact positive
count, and `sha256` hashes their canonical ordered array. Each binding must
retain its immediate ledger join. Available prefixes pass the existing byte,
structure, run, interval and redaction checks. An unavailable binding retains
its closed reason receipt and remains `bound`; identity does not call it an
accepted capture.

## Policy projection

`policy_sha256` hashes this closed object:

```json
{
  "schema": "fiat-checkpoint-behavior-policy/v1",
  "skills": {
    "prose_lint": "hexaemeron:imprimatur",
    "voice": "hexaemeron:vulgate",
    "security": [
      "hexaemeron:x-ray",
      "hexaemeron:solidity-auditor",
      "hexaemeron:fizz"
    ]
  },
  "audit": {
    "max_rounds": 8,
    "fold": false,
    "stacked_suffix": "--audit"
  },
  "git": {
    "draft_pr": false
  },
  "solidity": "auto"
}
```

Only stored values are projected. `config.git.origin`,
`config.git.worktree`, `config.audit.log_path`, `config.git.base`,
`config.git.run_branch_prefix` and values already fixed by the run anchor are
not policy fields. `max_rounds` is an exact non-Boolean integer from 1 through
1,000,000.

## Result and digest

The command writes one canonical JSON line to stdout:

```json
{
  "schema": "fiat-checkpoint-identity-result/v1",
  "identity": {
    "schema": "fiat-checkpoint-identity/v1",
    "run": {
      "schema": "fiat-run-anchor/v1"
    },
    "boundary": {
      "kind": "post-push",
      "step": 2,
      "working_commit_sha": "<full-commit-sha>"
    },
    "evidence": {
      "ledger_entries": 31,
      "ledger_sha256": "<lowercase-sha256>",
      "ledger_tail": "<lowercase-sha256>",
      "observation_bindings": 0,
      "observation_sha256": "<lowercase-sha256>",
      "observation_status": "absent",
      "policy_sha256": "<lowercase-sha256>",
      "run_anchor_sha256": "<lowercase-sha256>",
      "runbook_sha256": "<lowercase-sha256>",
      "state_fingerprint": "<lowercase-sha256>",
      "study_sha256": "<lowercase-sha256>"
    }
  },
  "snapshot_id": "<lowercase-sha256>"
}
```

`run` is the complete verified anchor, not only the schema field shown in the
abbreviated example. `snapshot_id` is:

```text
sha256(
  b"wildcat-fiat-checkpoint-identity/v1\0"
  + canonical(identity).encode("utf-8")
)
```

The hashed canonical identity has no trailing newline. The wrapper and display
newline are outside it.

Carrier filename, compression, file order, timestamp, permission, proposed
archive digest, native capsule-manifest digest and current branch tips do not
enter `identity`. Absolute paths and source text do not appear in the result.

## Refusals

The command refuses before stdout when:

- captured inputs exceed their caps, are not exact `bytes`, contain malformed
  or duplicate-key JSON, or do not form an appendable joined ledger;
- the immutable base or run anchor is absent, unbound, malformed or mismatched;
- the tail is outside the two checkpoint boundaries, its step is ambiguous,
  or its final local commit is missing or unreceipted;
- policy, source, observation, ref, repository, commit or ancestry evidence is
  malformed, incomplete or disagrees with the captured run; or
- state, ledger, source bytes, observation bytes or Git evidence changes during
  the stable-read sequence.

Refusal does not change state, ledger, Git or filesystem bytes. Native
`checkpoint export` and `checkpoint restore` retain their existing legacy
behavior and transport meaning.
