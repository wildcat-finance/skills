# Study: assign ADR numbers at merge, not at authoring time

Issue: [wildcat-finance/skills#888](https://github.com/wildcat-finance/skills/issues/888)

Survey base: `main` at `ff47f3070c8dce05c767b6c0dad65234c56870de`, 2 September 2026.
This is a fresh recovery run. The earlier #888 run was halted after an
out-of-order Step 2 merge; its signed product and audit branches remain
evidence, not an authority to skip this run's receipts.

## Assumptions

Assuming, unless corrected:

1. New records continue to enter `main` through pull requests; a direct push
   is outside this delivery.
2. The checked-in Python interpreter and native Git are the only implementation
   dependencies; no allocator service or database is introduced.
3. Existing numbered records and their numeric references remain byte-stable.
4. The GitHub base-owned workflow may be published before the live ruleset is
   activated; an observed or evaluate-only ruleset is not enforcement.
5. A run's exact integration base is the only input that may allocate a number.

## 1. Problem statement

Authors currently choose an ADR number before a branch reaches `main`. Another
delivery can land that number in the interval, and differently named files
merge without a Git conflict. A working prototype lets an author use a stable
`adr/<slug>` identity, derives the final number from the exact merge base, and
refuses a stale composition. The local proof is
`docs/adr-merge-assignment/local-proof.md`; the executable proof is the focused
Hypomnema, Fiat, workflow, root, and Hexaemeron suites named by the runbook.

## 2. Prior art

The current tree has the numbered-record checker in
`tests/test_decision_records.py`, Hypomnema's record and source-reference
rules in `plugins/hexaemeron/skills/hypomnema/`, and Fiat's signed stack and
sync receipts in `plugins/hexaemeron/skills/fiat/`. ADR-068 and the Fiat
`early_merge` implementation are relevant recovery precedent: a public merge
is evidence only when the controller can verify its exact topology.

The latest merged repository changes were reread from the current base,
including the source-link exemption merge (#1116) and the earlier Fiat
early-step-merge change (#1110). They alter the repository and controller
surface but do not supply an ADR allocator or a base-owned status. The earlier
#888 audit records remain at `audit/rounds/` and are read as historical source;
the fresh run will append its own records.

Outside approaches were also considered: `adr-tools` allocates from a local
maximum, Rust RFCs use a pre-acceptance identity, and MADR keeps numbers out of
headings. None supplies exact-base replay plus an enforced merge boundary.

## 3. Constraints and non-goals

The run starts at the exact base above and keeps the repository's Python pin,
Apache-2.0 licence, native Git, signed contributor identity, and existing
controller limits. Allocation is bounded to 32 drafts, uses ASCII-byte order,
and chooses the greatest number on the exact base plus one; holes are spent.

No existing ADR is renumbered. The run does not change the live GitHub
ruleset, review or bypass policy, merge method, credentials, issue #889, or a
separate repository. It does not claim production race freedom until a later
authorised canary makes the status context required and active. No Solidity,
performance optimisation, deployment, or remote checkpoint is in scope.

## 4. Design options

### A. Allocate in a shared reservation ledger

The ledger could reserve the next number at authoring time. It introduces
abandoned reservations and a service-like authority, and still leaves a gap
between reservation and merge. Rejected.

### B. Read the base immediately before merge

This narrows the race but two candidates can read the same base before either
lands. It is useful diagnostic evidence, not exclusion. Rejected.

### C. Stable slug plus exact-base assignment and a base-owned gate

Drafts keep `adr/<slug>` while the allocator replays immutable base and
product objects, records the ordered mapping and signed trailers, and the
base-owned workflow refuses a stale candidate. This keeps assignment at merge
and gives both local and hosted evidence. Selected.

## 5. Risk register seed

```risk-register
git-object-input | immutable base and product Git objects | read native objects with replacement and repointing disabled
candidate-bytes | draft and final record paths and headings | mutate only the path and exact first heading, preserving all other bytes
stale-base | merge-time base ref and assignment report | compare the exact protected base and refuse a moved or reused assignment
workflow-input | pull-request event fields and remote refs | treat candidate code as data and write status only for the exact head
partial-state | controller ledger and assignment report | write pending then terminal evidence atomically and replay it on recovery
provenance | commit signatures and assignment trailers | require the configured signer, exact trailers, and GitHub verification
hostile-config | Git attributes, hooks, aliases, and environment | reject or neutralise them before any worktree-observing Git operation
publication-state | stacked branches and pull-request topology | retarget before each merge and receipt the exact merge commit
```

## 6. Glossary seeds

`stable reference` — lowercase ASCII `adr/<slug>` identity used before numbering.

`assignment base` — the exact protected-base commit used to derive numbers.

`assignment report` — closed `fiat-decision-assignments/v1` mapping and object evidence.

`base-owned gate` — status logic that evaluates the protected base and exact candidate head.

`composition` — the signed tree that carries the assigned final records.

## 7. Sources

Issue #888 and its filing contract; `tests/test_decision_records.py`;
`plugins/hexaemeron/skills/hypomnema/SKILL.md` and `EVOLUTION.md`;
`plugins/hexaemeron/skills/fiat/SKILL.md`, `EVOLUTION.md`, and
`references/push-discipline.md`; the fresh and historical audit records under
`audit/`; ADR-068; GitHub ruleset documentation on evaluate versus active
enforcement; and the outside ADR references named under Prior art.

## 8. Signals, and the questions behind them

At 03:00 an operator needs to know which base and head were evaluated, which
mapping was assigned, whether the candidate was stale, and whether the hosted
status belongs to the event head. Steps 2 and 3 emit bounded report and receipt
fields; Step 4 emits pending and terminal status evidence. Ephoros owns the
signal contract.

## 9. Boundaries, per capability

The allocator boundary is untrusted Git objects, paths, bytes, and process
configuration; fixed argv, descriptor-safe reads, byte/count ceilings, and
replacement-object refusal close it. The controller boundary is reports,
signatures, trailers, and sync ancestry; exact replay and signed receipts
close it. The workflow boundary is event input and remote refs; protected-base
checkout, candidate-as-data handling, exact-head status writes, and least
privilege close it. Phylax owns these controls.

## 10. The budget, or its absence

There is no performance claim. Existing byte, path, object, report, and test
ceilings remain the budget; any future speed work must first record a Metron
measurement. Metron therefore has no active optimisation task in this run.

## 11. The fail-closed posture

Missing, stale, malformed, moved, unsigned, or topology-inconsistent evidence
stops the dependent transition. Each executable fix must reproduce the parent
failure, reduce it to the cause, and leave a regression guard before the
controller receipt. Elenchus owns this order.

## 12. Decisions and their homes

The stable-reference and allocation policy lives in the unnumbered decision
record created in Step 1 and later receives its merge-time ADR number. The
allocator contract and its generation row live in Hypomnema; composition and
assignment receipts live in Fiat's ledger and report; the local demonstration
lives beside the assignment study. Hypomnema owns these homes.
