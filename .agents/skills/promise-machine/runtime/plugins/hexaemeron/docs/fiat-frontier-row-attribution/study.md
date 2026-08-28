# Study: subtract already-published rows from the frontier close gate

Target skill: Fiat, on the generation axis. The held frontier job
([skills#363](https://github.com/wildcat-finance/skills/issues/363)) is not
touched.

Assuming, unless corrected:

1. Python 3.12 or later and stdlib `unittest`. `hexctl.py` stays stdlib-only.
2. The run starts from `ea4d238abb3968d25542ac03e199619d4b7c6a73` on `main`,
   the merge of [PR #532](https://github.com/wildcat-finance/skills/pull/532).
3. This run drives the installed `fiat-v5.14.1` controller while the repository
   holds `fiat-v5.15.1`, recorded in the `controller_version` receipt. Its own
   receipts therefore carry no attribution container.
4. Concurrent Fiat runs against one repository are normal here, not an edge
   case. Three landed on `main` during the issue 466 run.
5. No repository settings, branch protection or GitHub configuration change.

## 1. Problem statement

`frontier_close_fault` decides whether a run that declared `--frontier` closed
its ledger. It counts the history rows added since `init` and refuses anything
other than exactly one. That count cannot tell this run's row from a row another
run published meanwhile, so the second of two concurrent frontier runs on one
skill is refused for work it did not do.

This is not hypothetical. The issue 466 run added exactly one row,
`fiat-v5.15.1`. While it was in its steps phase the Sapheneia audit-record run
published `fiat-v5.14.1`. Its single permitted sync merge brought that row into
its worktree, and `done integrate` refused with `gained 2 history row(s); the
contract allows exactly one per completed frontier job`. The refusal is
unliftable from inside that run: the run branch is frozen at its sync commit by
`done_integrate`, so the row cannot be renumbered, and the installed controller
runs the gate. That run merged under a recorded halt with no integration
receipt.

For whom: any Fiat run that declares a frontier while another run is live
against the same skill. A working prototype here means the gate charges a run
for its own rows and no others, while still refusing a run that added two rows
of its own or none.

Demo path: the regressions in
`plugins/hexaemeron/tests/test_hexctl.py::TestFrontierClose`, each observed to
fail against `ea4d238abb3968d25542ac03e199619d4b7c6a73` and pass after, plus a
replay of the exact issue 466 topology.

## 2. Prior art

**In this repository.** `frontier_close_fault` in
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` already carries a comment
about this class of fault: it anchors on the init-time version rather than the
stored row count, "because a snapshot taken while the gate misread a ledger's
row spelling counted a real history as empty", citing
[skills#443](https://github.com/wildcat-finance/skills/issues/443). This is the
second iteration of the same lesson. The first fixed a bad anchor; this fixes
what is counted after it.

`done_sync_run` already records the exact remote base commit the run merged, in
`state["integrate"]["sync"]["base_commit"]`, and `bounded_git` already performs
argv-only reads with an output cap and no shell. The evidence needed to tell a
foreign row from this run's own row is therefore already recorded and already
readable.

**The last two merged pull requests that changed Fiat.**
[PR #532](https://github.com/wildcat-finance/skills/pull/532) is the issue 466
attribution run, published as `fiat-v5.15.1`. Its `## Carried forward` names
this defect first, as the reason its own receipt was refused, and states the
proposed shape: the gate should subtract rows already present in the base it is
merging into, and the base's ledger is readable from the recorded base commit.
This run answers that item.
[PR #524](https://github.com/wildcat-finance/skills/pull/524) published
`fiat-v5.14.1`, the row that triggered the refusal, and added the
`--audit-filter sapheneia:sapheneia` declaration every round now carries. It
carried nothing forward about the gate.

**Audit records.** `audit/AUDIT.md` holds eight records from the issue 466 run
under `Fiat merged attribution`. Step 2 round 1 and step 3 rounds 1 and 2 record
the installed-controller split. None records a lead about the frontier gate,
because the refusal surfaced at integration, after the last round closed. The
Sapheneia run's records carry no gate lead either.

**Outside.** Nothing external governs this. The rule is the repository's own
versioning contract in `plugins/hexaemeron/skills/VERSIONING.md`, which says a
completed frontier job records one row; it does not say a run owns every row
that appears while it runs.

## 3. Constraints and non-goals

Starting ref `ea4d238abb3968d25542ac03e199619d4b7c6a73` on `main`. Python 3.12
or later, stdlib only. Every new read goes through `bounded_git`. No new state
container: the sync receipt already holds the base commit.

Non-goals:

- No change to the versioning contract itself. The rule stays one row per
  completed frontier job; only the arithmetic that checks it changes.
- No retroactive receipt for the issue 466 run. Its state is halted and its
  branch frozen; this run does not reopen it.
- No relaxation for a run with no recorded sync. Without a sync nothing foreign
  can have entered the worktree, so that path keeps today's behaviour exactly.
- No attempt to identify a row's author. The question is only whether a row was
  already published in the base.

## 4. Design options

**A. Subtract rows already present in the recorded sync base.** When the run has
a sync receipt, read the ledger at the recorded base commit, collect its row
versions, and count only rows after the anchor whose version is absent from that
set. Require exactly one, and require the newest row to be one of the run's own.
Trade: one extra bounded `git show` on the integrate path, and the gate now
depends on a blob being readable. Where that read fails it falls back to today's
count rather than passing, so a broken read cannot weaken the gate.

**B. Anchor on the last row this run did not write.** Equivalent in effect, but
it needs to know which rows the run wrote, and the ledger records evidence and
change text rather than authorship. It would have to infer authorship from
prose.

**C. Make the run renumber its row during the sync.** The row would then chain
from whatever landed meanwhile. `done_integrate` requires the run branch tip to
equal the single permitted sync commit, so there is nowhere to put the edit
except inside the sync merge itself, and the run that needs it most is the one
already frozen. Unreachable by construction.

**D. Drop the count and rely on the axis arithmetic alone.** The last row must
already chain from the row before it, so a wrong version is caught either way.
Trade: it stops catching a run that appended two of its own rows, which is the
silent-finish case the gate exists for.

**Chosen: A.** It uses evidence the run already records, it is the only option
that distinguishes foreign rows without inventing authorship, and it keeps every
refusal the gate makes today. What it trades away is independence from the base
blob: the gate now reads one more thing, and that read is bounded and failure
tolerant in the safe direction.

## 5. Risk register seed

Two concerns deserve prose. The first is direction of failure: a base ledger
that cannot be read must leave the gate at least as strict as it is today, never
looser, because this gate is the only thing standing between a silent frontier
finish and the ledger. The second is the newest-row rule: subtracting foreign
rows would otherwise let a run pass while a row published later
follows its own row, which would put the header and the newest row out of step.

```risk-register
base-read-failure | the git show of the base ledger blob | an unreadable or malformed base ledger falls back to today's count and never to a pass
foreign-row-overcount | the set of versions read from the base | only exact version labels present in the base are subtracted, and a duplicated label cannot subtract twice
own-row-not-newest | the last history row against the base version set | a run whose own row is not the newest row is refused, so the header and the newest row stay one row
two-own-rows | the count after subtraction | a run that appended two rows of its own is still refused, which is the silent-finish case the gate exists for
no-sync-unchanged | a run with no recorded sync receipt | the path with no sync keeps today's arithmetic byte for byte
bounded-git-read | the argv of the added git show | argv-only, no shell, output capped by the existing reader, and a nonzero exit distinguished from empty output
```

## 6. Glossary seeds

- **Anchor.** The init-time version row the gate counts forward from.
- **Foreign row.** A history row already present in the recorded sync base.
- **Own row.** A row after the anchor that is not foreign.
- **Silent finish.** A frontier run that ends without recording its row.

## 7. Sources

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `frontier_close_fault`,
  `done_integrate`, `done_sync_run`, `ledger_rows`, `bounded_git`.
- `plugins/hexaemeron/skills/VERSIONING.md`, the one-row rule.
- [PR #532](https://github.com/wildcat-finance/skills/pull/532) and its
  `## Carried forward`, and
  [PR #524](https://github.com/wildcat-finance/skills/pull/524).
- The halted issue 466 run state, holding the exact refusal text.
- [skills#443](https://github.com/wildcat-finance/skills/issues/443), the first
  iteration of this fault.

## 8. Signals, and the questions behind them

Fiat runs under a person at a terminal, so the receipts and the refusal text are
the record. Two questions have to be answerable.

- *Why was this run's frontier receipt refused?* The refusal names which check
  failed and, after this change, how many rows it attributed to the run against
  how many it subtracted as already published.
- *Which rows did the gate treat as foreign?* The integration receipt records
  the subtracted versions, so a reader does not have to re-derive them.

[ephoros](../../skills/ephoros/SKILL.md) owns what those must carry. No new
metric, log or alert: a command exiting non-zero with a named reason is the
emission.

## 9. Boundaries, per capability

[phylax](../../skills/phylax/SKILL.md) owns the boundary list and the controls.

- **A new git read of a historical blob** (the only new boundary). Worth taking:
  the base's ledger rows. Control: `bounded_git`, argv-only, no shell, the
  existing output cap, and a failure that falls back to the stricter count.
  `bounded-git-read`, `base-read-failure`.
- **Parsing untrusted historical text.** Worth taking: the version labels.
  Control: the existing `ledger_rows` regex, which the evolution suite shares,
  and exact-label matching rather than prefix matching.
  `foreign-row-overcount`.
- **Persisted state.** Worth taking: the subtracted versions, for the reader.
  Control: version labels only, inside the existing integrate receipt.

## 10. The budget, or its absence

None, and no performance claim is made. The change adds one bounded `git show`
on the integrate path, once per run, and only when a sync receipt exists.
[metron](../../skills/metron/SKILL.md) owns budgets and forbids a
speed-motivated change without a recorded before and after; no step here makes
one.

## 11. The fail-closed posture

An unreadable, malformed or empty base ledger leaves the gate at today's
arithmetic. A run whose own row is not the newest is refused. A run that
appended two of its own rows is refused. Every refusal names the check that
failed and changes no state.

[elenchus](../../skills/elenchus/SKILL.md) owns the triage order and the guard
rule. The fix lands with regressions that fail against
`ea4d238abb3968d25542ac03e199619d4b7c6a73` and pass after. Runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
format `elenchus.unittest.v1`, report file `tmp/elenchus/step-1.json`.

## 12. Decisions and their homes

[hypomnema](../../skills/hypomnema/SKILL.md) owns which decisions earn a record.

- **The EVOLUTION row**, `plugins/hexaemeron/skills/fiat/EVOLUTION.md`: one
  generation entry, `fiat-v5.16.1`, retaining the `state-shape-validation`
  revision, its digest and the held issue 363 target.
- **No ADR.** The decision is a correction to an existing check rather than a
  new boundary, and its reasoning fits the ledger row and this study. ADR-018
  already records the surrounding attribution decision, and a record per bug fix
  would bury the ones that matter.

## Boundaries the study must state

**Always.** Both suites before the implement receipt:
`python3 -m unittest discover -s tests` and
`python3 plugins/hexaemeron/tests/run_tests.py`. The Imprimatur lint then the
Vulgate mask on every shipped document. The Protasis checker on this study and
the runbook. `python3 scripts/promise_machine.py check` with the three `fiat-*`
runtime digests refreshed in the same commit.

**Ask first.** Adding a dependency. Changing the versioning contract. Touching
CI. Reopening the halted issue 466 run. Relaxing any existing refusal.

**Never.** Weaken the gate on a failed read. Grant a retroactive receipt. Infer
a row's authorship from its prose. Delete a failing test to make a suite pass.
Claim a command ran when it did not.
