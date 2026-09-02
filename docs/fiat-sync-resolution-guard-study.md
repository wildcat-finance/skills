# Fiat sync resolution guard study

Assuming, unless corrected:

1. Issue [#891](https://github.com/wildcat-finance/skills/issues/891)
   authorises a fail-closed controller change for integration syncs whose Git
   trees could have discarded concurrent work.
2. The implementation branch starts from the signed #889 candidate at
   `83652238f9e22d6857bb0106681cb391438d1ddd`. It must not publish until that
   commit is on `main` and the branch has been checked against the then-current
   protected base.
3. A path acknowledgement means that the operator inspected the named path's
   merged result. It does not prove the result is semantically correct and does
   not replace the existing revalidation checks.
4. Publication uses `laurenceday`; governed commits remain authored by
   Shoggoth and are signed with `B83B60AE16F5DD1A`.

## 1. Problem statement

Fiat proves that a sync commit has ordered parents `[product, base]`, is signed,
is the remote run-branch tip, and has green path-scoped revalidation. Those
facts do not prove that the merge tree retained both parents' concurrent work.
Git can create a clean merge whose tree takes one complete side for a shared
registry. Rebuilding an older sync against a newer base can also lose a manual
resolution carried only by the older merge. Neither case creates a conflict,
and the current receipt does not expose either risk.

Success adds one immutable Git-object guard to `done sync-run`:

- On every first sync, find paths changed by both product and base from their
  common ancestor. When their final entries differ and the sync entry equals
  either complete parent entry, require the exact path to be acknowledged.
- On supersession, intersect paths changed from product to the active sync with
  paths changed from the active sync's recorded base to the new base. Require
  every intersecting path to be acknowledged even when the rebuilt tree looks
  plausible.
- Store the two path sets and the exact acknowledgement set in the sync receipt,
  display their counts, and replay them before integration.
- Refuse missing, extra, duplicate, or unsorted acknowledgements before any
  state or ledger byte changes.

The controller does not attempt a semantic merge. It makes the two known
silent-loss surfaces visible and converts them into an explicit operator gate.

## 2. Prior art

`done_sync_run` already resolves the product and base commits, requires one
native merge base, checks exact ordered parents, binds the remote tips, validates
the complete integration path surface, verifies local and GitHub signatures,
and only then writes state. The native relation helpers disable replacement
objects, inherited Git configuration, lazy fetch and interactive prompts. This
change uses the same boundary and mutation order.

`fiat-integration-revalidation/v1` and `/v2` prove that every computed path or
registered aggregate has a recorded exit-zero check. That evidence remains
necessary, but it answers whether the composed tree passed named checks rather
than whether a clean Git merge discarded one parent's entry.

The controller retains superseded sync receipts and requires a reason, a new
signed commit, preserved product evidence, and no more than eight
supersessions. The retained active receipt contains the old base and sync
commits needed to derive the rebuild intersection without trusting the
worktree.

Git's recursive merge machinery can detect textual conflicts, but `git
checkout --ours`, `git checkout --theirs`, a generated tree, or `commit-tree`
can still produce a valid two-parent commit that selects a whole parent entry.
The reliable evidence is the tree entry identity at each exact commit, not the
command that happened to create it.

## 3. Constraints and non-goals

The existing sync topology, signature checks, GitHub verification, integration
revalidation schemas, path ceilings, supersession limit and mutation order stay
in force. The new guard reads commits and trees only through bounded native Git
subprocesses. Paths remain repository-relative, UTF-8, safe, sorted and unique.
Missing entries are legitimate identities so additions and deletions remain
visible.

The guard does not parse JSON, YAML, Markdown or source files; infer semantic
intent; auto-merge registries; accept globs; read mutable worktree content; or
claim an acknowledgement proves correctness. It does not change a completed
historical run. An active legacy sync without the new receipt cannot be
integrated by the new controller; it must be superseded and freshly receipted.

Always: compute from exact native commit objects, require an exact sorted
acknowledgement set, validate before mutation, preserve both risk sets in the
receipt, run the focused incident cases and complete controller suite, and
verify signed commits before push. Ask first: change the definition of a risky
path, permit partial acknowledgement, add a content-aware merger, or weaken an
existing sync gate. Never: silently accept a whole-side selection, treat green
revalidation as proof of merge preservation, infer acknowledgement from a
command name, or rewrite an old receipt.

## 4. Design options

**A. Ban `git checkout --ours` and `--theirs`.** Rejected. The controller does
not observe the local construction command, and equivalent trees can be made
through an index, a merge driver or `git commit-tree`.

**B. Reject every overlapping path whose product and base entries differ.**
This is simple and fail-closed, but it prevents legitimate semantic resolutions
and gives the operator no bounded recovery. Rejected.

**C. Parse known shared registries and merge their records.** This can prove
more for a small set of formats, but turns Fiat into a content merger and leaves
other shared files unprotected. Rejected for this controller change.

**D. Derive risky paths from commit and tree identities, require their exact
explicit acknowledgement, and retain the result. Chosen.** The trade is that a
human can acknowledge a wrong result. The guard therefore does not replace
revalidation; it ensures that the precise silent-loss candidates cannot pass
unseen.

The receipt schema is `fiat-sync-resolution-guard/v1` with exact fields
`schema`, `side_selected_paths`, `superseded_intersection_paths`, and
`acknowledged_paths`. The required acknowledgement set is the sorted union of
the first two arrays. A first sync has no superseded intersection. A
supersession compares the old composition delta `product..old_sync` with the
base advance `old_base..new_base`.

For whole-side detection, the controller computes product and base deltas from
their one native merge base, intersects the paths, then reads `(mode, type,
object-id)` or absence at product, base and sync. A path is risky only when the
product and base entries differ and the sync entry equals either complete
parent entry. A semantic union with a third tree entry does not require this
acknowledgement.

## 5. Risk register seed

```risk-register
hidden-whole-side | a clean merge selects one complete parent entry for a path both sides changed | compare native product base and sync tree entries and require the exact path flag
rebuild-loss | a newer base overwrites a resolution carried only by the active sync | intersect old composition paths with the old-base to new-base advance and require the exact path flag
false-correctness-claim | an acknowledgement is mistaken for semantic proof | receipt and prose state that acknowledgement records inspection only and revalidation remains mandatory
path-confusion | aliases duplicates or ordering make the acknowledged set ambiguous | accept only canonical safe sorted unique repository-relative paths and exact set equality
object-substitution | replacement refs or inherited Git config change the commits being inspected | use the native relation Git boundary with replacement objects and inherited config disabled
partial-receipt | a refusal follows a state or ledger write | derive validate and compare every guard field before assigning integrate.sync or calling commit
stale-replay | a stored guard no longer describes the active sync objects | recompute at integration and version-resolution replay from stored commit identities
legacy-active-sync | an older controller receipt lacks the guard | refuse integration and require a fresh signed superseding sync
unbounded-tree-query | a large path surface exhausts argv output or time | reuse integration path and output ceilings and batch literal path queries under the Git deadline
```

## 6. Glossary seeds

Whole-side selection: for a path changed differently by product and base, a
sync tree entry that is byte-for-byte one complete parent entry.

Superseded intersection: paths changed by the active composition and also by
the base advance against which its replacement was rebuilt.

Acknowledgement: an exact repeated CLI path declaration recording that the
operator inspected one risk candidate; it is not an approval or correctness
proof.

Tree entry identity: the Git mode, object type and object id for one literal
path at one commit, or absence when that path does not exist.

## 7. Sources

- Issue [#891](https://github.com/wildcat-finance/skills/issues/891).
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, especially native
  relation reads, integration revalidation, `done_sync_run`, replay and
  `done_integrate`.
- `docs/fiat-sync-run-generator-aggregates-study.md` and ADR-049 for the
  existing integration path and object-read boundaries.
- Git tree and commit object semantics exercised by the checked-in disposable
  fixture, without relying on a particular porcelain merge command.

## 8. Signals, and the questions behind them

Ephoros applies because the controller is used unattended inside a delivery
loop. The sync receipt answers which risky paths were found in each class and
which exact paths were acknowledged. Human status prints the counts; JSON
status retains the full bounded arrays. A refusal prints the missing or invalid
path set and the exact repeated `--acknowledge-sync-path` recovery form.

## 9. Boundaries, per capability

Phylax applies to Git subprocesses and CLI input. The controller passes fixed
argv, literal pathspecs and full commit ids to the existing native Git reader;
uses its 30-second and 2 MiB bounds; accepts no shell text; disables replacement
objects, inherited configuration, lazy fetch and prompting; and reads no
network or worktree content. Acknowledgements pass the existing safe-path
grammar before any object read.

## 10. The budget, or its absence

No speed improvement is claimed. Path enumeration is already capped at 4,096
per integration delta. Tree identities are read in bounded batches so argv and
output remain below existing limits, and every batch uses the existing Git
deadline. The focused fixture proves behaviour, not throughput. The complete
Hexaemeron suite and hosted plugin graph remain the delivery budgets.

## 11. The fail-closed posture

Elenchus applies. The parent controller must fail the new whole-side,
supersession, exact-set and parser cases for the missing mechanism. The repaired
controller must make the semantic-union specimen green without an
acknowledgement and make every risky specimen red until its exact sorted path
set is supplied. Any malformed object output, path, active receipt or replay is
a refusal before state mutation.

## 12. Decisions and their homes

Hypomnema places the durable rule in
`docs/decisions/ADR-057-require-explicit-sync-resolution-acknowledgements.md`.
`hexctl.py` owns the executable schema and derivation. Fiat `SKILL.md` owns the
operator boundary and recovery command. The focused issue-891 test owns the
incident-shaped examples. `EVOLUTION.md` records the version and retained
frontier. This study and its runbook remain at the repository root under
`docs/`.
