# Decision: Gate Fiat mutations and continue audit loops

## Status

Accepted, 2026-09-20, for the skills#871 study. Step 1 publishes it in the canonical numberless draft home, and Step 8 of that run completes it against the built product. It has no ADR number.

## Context

In run #622 an agent raised `audit.max_rounds` from 8 to 16 at an exhausted audit loop, resumed, and published the recipe in PR #681. `hexctl verify` had passed. No declared Promise authorised any of it, and the user caught it by reading.

At `aededf66434ed4b4e3994bbaab5f1005fe10b453`, `main()` in `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` takes the run lock for all 19 names in `MUTATING` and checks no Promise and no directive. `cmd_resume` clears any halt on a free-text note without consulting `_next_directive`. `commit()` appends the ledger line and then replaces `state.json`, with no `fsync` and no label; the design resolver stopped that real function between the two writes and found the ledger holding entry 44 beside the preimage state, with nothing on disk saying so. Five state or ledger writes bypass `commit()`, and three transaction writers keep their own pending records.

ADR-028 decided that an exhausted loop continues as a new bounded loop on the same ledger. `main` did not build that transition. It built cumulative carryover custody and replacement admission, which change ledgers.

The measured comparison is `docs/fiat-transition-gate/design-evidence.json` and the 32 reports under `docs/fiat-transition-gate/design/reports/`. The selected candidate is `dispatcher-grant-wal` and the selection rule is `unique-frontier`. The resolver's procedures model the constructions over a disposable synthetic preimage; they are not the product.

## Decision

1. One dispatcher gate, grant-required writers and a labelled write-ahead commit. `main()` stays the single entry. Under the run lock it checks gate integrity, verifies the state and ledger preimage, recomputes `_next_directive`, and asks the pure `transition_gate.evaluate` for one grant keyed by handler and subcommand. The grant names the Promise id, consequence, transition, directive, state digest and ledger tail. `commit()` and every other writer refuse without the live grant. `commit()` stages both postimages and the grant, publishes a durable label, replaces the ledger, replaces the state, then retires the label. Recovery completes a labelled transaction or reports the exact preimage. The five direct writes move behind `commit()`, and the three existing pending-record writers are registered as named recovery directives, not rewritten.
2. Audit history is a sequence of loops. An exhausted loop continues through an append-only `audit.continuations` array on the same step and ledger. Legacy flat rounds are loop 1 and stay byte-identical. Each loop starts at round 1, and no state, log heading, directive, handover or file name represents a round 9. The loop sits beside replacement admission and not instead of it: they are two separate exits from an exhausted loop, each under its own Promise.
3. `resume` is typed at an exhausted-loop halt. A bare `resume --note ...` refuses there. `resume --to audit-verdict` is granted because it exposes only the directive the halt covered, and a halted run on `main` must resume before `done audit --no-further-leads`. Everywhere else a bare `resume` keeps working.

Same-account limit. The gate ships inside the artefact it gates, and its integrity pins are checked by a process under the same OS account as the caller. They are tamper evidence and deterministic refusal. They are not privilege isolation, and no document from this work may say otherwise.

Relation to ADR-028 (`docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`): this record builds the checked new-loop transition that ADR-028 accepted on 2026-08-27 and `main` left unbuilt. It keeps ADR-028's rules: a per-loop ceiling, no round 9, an immutable prior loop, and a new loop that accepts or closes no inherited finding. It does not edit ADR-028.

Relation to ADR-047 (`docs/decisions/ADR-047-freeze-fiat-configuration-after-init.md`): the `config set` freeze stands unchanged, including for `audit.max_rounds`, which the skills#871 issue would have allowed before the first audit receipt. ADR-047 closed one command; this record puts every mutating command behind one Promise check. It does not edit ADR-047.

## Alternatives

- **`per-handler-gate`:** each of the 19 handlers calls the gate itself and `commit()` stays as it is. It offers small, local diffs. It fails `crash-window-labelled`, because the real `commit()` left an unlabelled ledger-ahead state, and it needs 19 ordering proofs where the selected design needs one (`gate-call-sites` 19 against 1).
- **`external-writer-broker`:** a broker process under another OS identity owns the writer and the pins. It is the only construction that could support a prevention claim. It fails `runs-under-one-account-stdlib`, because the run environment has no second identity and a restored checkpoint would not carry one, and it fails `added-processes-per-mutation` with 1 against a ceiling of 0. The issue defers it, and it stays a non-goal.
- **`gate-with-replacement-exit`:** the selected gate and writer with no same-ledger loop. It is the smallest delivery and adds no second representation of audit history. It fails `appends-loop-two-same-ledger`, which is specimen 8 of the issue and ADR-028.

All four candidates passed `refuses-622-widening`, `legacy-loop-one-bytes-identical` and `max-grant-bytes` (493 bytes or fewer against 65,536). The `runs-under-one-account-stdlib` cell is a declared property of each construction checked against the process's effective user; it is the weakest measurement in the matrix.

## Consequences

Ordering is proved from source in one place, the dispatcher and `commit()`. A missing, stale, malformed, over-broad or unsupported link refuses before either file changes, and each refusal test compares state and ledger bytes. A live label blocks every mutation except its own recovery. An exhausted loop stays halted unless `start-audit-loop`, `done audit --no-further-leads`, `halt`, `reset` or replacement admission is granted. `verify`, `status`, `next`, checkpoint inspection and exact rollback stay available after any refusal.

The cost is the largest edit to `hexctl.py`, about 25 writer call sites, and the coverage re-pin cascade from `tests/promise_machine_coverage.json` in every step that touches the controller. Three conformance cells of `dispatcher-grant-wal` remain due against the product: `product-refuses-622-specimens`, `product-appends-loop-two` and `product-every-mutator-mapped`.

Not covered: privilege isolation or a broker under another OS identity; the external acceptance fence of ADR-072; a design-amendment transition (skills#1524); any mutation, verdict or approval of the live #622 run or its 30 findings; and changes to replacement admission or carryover custody beyond passing the gate. The grant and handover schemas, `fiat-transition-grant/v1` and its siblings, are decision 4 of study section 12 and live in `plugins/hexaemeron/skills/fiat/references/transition-gate.md`, not here.

The study and runbook are `docs/fiat-transition-gate/study.md` and `docs/fiat-transition-gate/runbook.md`. Number assignment belongs to integration against the actual base; the standing home until then is `docs/decisions/drafts/gate-fiat-mutations-and-continue-audit-loops.md`.
