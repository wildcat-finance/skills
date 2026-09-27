# Decision: Bind a step-created gate runner at its push

## Status

Accepted, 2026-09-27, for the skills#1944 study. Step 1 publishes it in the canonical numberless draft home. It has no ADR number.

## Context

Protasis admits a gate command only as literal `python3` followed by a script in the built-in registry, or in a `command-interfaces` row pinned by SHA-256. It reads that script when the runbook is receipted. A missing script refuses `source-unavailable`, and a changed one refuses `registered-source-drift`. A target with no Python runner has nothing to register.

The miskatonic#14 run (Hexaemeron 1.6.82, 2026-09-26) placed `tests/run_tests.py` in the run worktree as an untracked file before `done runbook`, and Step 1 committed those bytes. When audit finding S1-R1-01 required a change to that runner, the fix needed a runbook amendment carrying a replacement `command-interfaces` fence. The committed runbook copy and its pinned digest had to follow. [skills#1944](https://github.com/wildcat-finance/skills/issues/1944) asks for a runner that Step 1 adds, with no file in the run worktree before Step 1.

## Decision

A `command-interfaces` row may carry the literal `step:1` in place of its digest; Fiat binds the runner's digest from the blob at Step 1's verified push head; and each command naming an unbound runner records the additive result `interface-deferred` inside `protasis-gate-commands/v1`, with no new schema string or init marker.

- At runbook capture, the deferred path must be absent. Commands naming it pass every check except the runner's parser interface, and the path is neither read nor hashed before binding.
- At Step 1's `done push`, the path must be absent at the run's starting commit and a regular-file blob (mode `100644` or `100755`) at the verified push head. The worktree file must equal that blob. The bound digest is the blob's SHA-256, and a fresh gate result validates every command against it. The push receipt and its `done:push` ledger event carry the binding. A refusal names one cause token and exits before any state, ledger or artefact write.
- After binding, the row is an ordinary pinned registration: any byte change refuses `registered-source-drift` until an append-only amendment carries a concrete-digest row.
- A deferred row is admitted in the baseline fence. An amendment fence admits one only while Step 1 has no implementation receipt; after that, an amendment may only repeat an unbound row byte for byte.
- A runbook with no deferred row yields the 1.6.82 result, apart from `adapter_sha256`.

This is trust on first use, the way SSH `known_hosts` keeps the first key it sees. Here the first use is fixed to a signed, verified commit the controller already receipts. The other candidates pin in advance, as pip's `--require-hashes` does.

## Alternatives

Surveyor policy specimens (`docs/deferred-runner-binding/probe.py`) measured four candidates in a disposable no-runner Git fixture. The values are fixture measurements, not production estimates. All four pass the drift, interface-by-step-close, legacy-result and 1,000 ms replay gates. `docs/deferred-runner-binding/design-evidence.json` selects `creating-step-binding` under `unique-frontier`: 0 amendments for an in-step runner fix and 109 added runbook bytes.

- `reviewed-stdlib-runner` has Hexaemeron ship one reviewed stdlib runner. The gate checks its interface at runbook capture, and Step 1 commits a byte-identical copy. The interface check comes earlier, but no target can change the runner inside its own run: the S1-R1-01 fix needs 1 amendment or a Hexaemeron release. The runbook grows 627 bytes. It still needs this design's absence checks, plus a shipped runner and its contract. Each target's copy diverges, as [skills#841](https://github.com/wildcat-finance/skills/issues/841) records. A variant that runs the shipped runner from the plugin root is not a runner Step 1 adds. Its absolute argv also names a per-machine path that checkpoint relocation cannot rebind.
- `runbook-embedded-source` puts the whole runner source in the runbook, and Step 1 commits exactly those bytes. The interface is checked early, under the runbook's own review. But the runner is written during runbook derivation, the runbook grows 4,049 bytes, and every in-step fix needs 1 amendment.
- `pre-placed-untracked` is the released 1.6.82 route. It leaves 1 product file in the run worktree before Step 1, which the issue rules out. The in-step fix needs 1 amendment, and the runbook grows 653 bytes.

## Consequences

The runner's parser interface is checked at Step 1's push instead of at runbook receipt. A command that does not fit the runner therefore surfaces as a failing Exit inside Step 1 and as a binding refusal at the push. An in-step runner fix needs no amendment.

- Only Step 1 creates a runner in this generation. A runner that already exists, or that a later step changes, keeps the amendment route.
- `next` still emits worker packets that name an unbound runner's commands. Every mutation still replays first.
- The run branch holds no runner until integration, so a checkpoint of a bound run restores onto its latest implemented step branch rather than the run branch. The Fiat SKILL "Runbook command evidence" section states the rule.
- A binding pins the runner file only, not the modules it imports. Carried forward as `registered-runner-helper-pin`.
- Success-criteria execution still refuses every local registration (`plugins/hexaemeron/skills/fiat/scripts/criteria_execution.py`). Carried forward as `criteria-exit-local-registration`.
- Replay admission of the released adapter digest `14a857dc44ce43d7a3771a2125b92f86435e39ab8ba2b027ef02b4f36ca48bad` lives in `plugins/hexaemeron/skills/protasis/references/gate-commands.md` and the Protasis ledger. The `awaiting-binding` status lives in that reference and the Fiat SKILL "Runbook command evidence" section.

Five conformance cells stay pending: three due at `step:3`, one at `step:4` and one at `integration`. `docs/deferred-runner-binding/proof.py` is the resolver for each. Integration assigns the number against the actual base; until then, the standing home is `docs/decisions/drafts/bind-a-step-created-runner-at-its-push.md`.
