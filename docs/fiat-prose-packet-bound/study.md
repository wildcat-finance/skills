# Let a prose phase survive a large generated diff

Assuming, unless corrected:

1. The interpreter pinned in `.python-version`, with stdlib `unittest`, and no
   new third-party dependency.
2. The run starts from `main` at `840d8dd3596fd6394901ba85a693bea00c69bf25`,
   the tip of `origin/main` when the run branch was cut.
3. The controller under edit is
   `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, and the copy this
   session executes is byte-identical to it at that ref, SHA-256
   `6f6901851f7ebb5e1f027075d4cac90b75b9ea2016a9b5faf581a0e6a57364aa`.
4. This run advances the Fiat ledger by one generation. It does not touch the
   held `Next Fiat job`, its frontier revision, or its digest.
5. The version label is resolved by the runbook's `version-relations` block at
   integration rather than chosen now, because `main` here takes merges in
   bursts and a label picked early collides.

I will proceed on these unless corrected.

## 1. Problem statement

A Fiat step whose branch diff exceeds 500 paths cannot reach its prose phase.
`hexctl next` exits non-zero and emits no directive, so the step can be neither
executed nor receipted, and the run halts with no route forward.

The refusal comes from the packet builder, not from anything about prose:

```python
raw = bounded_git(base_dir, ["diff", "--name-only", "-z", f"{pr_base}..{branch}", "--"])
...
unique = sorted(set(paths))
if len(unique) > GIT_PATHS_MAX:
    die(f"git diff returned more than {GIT_PATHS_MAX} paths")
```

`scribe_files` is reached only from `delegation_packet` when the action is
`prose`, and `delegation_packet` is called by `next`. A refusal there kills the
directive rather than the phase, which is why the run cannot fall back to
executing the packet inline.

Built for whom: a Fiat run whose step removes, vendors, or renames a large
generated tree. The prose pass reads authored text; the count that stops it is
a count of files that carry none.

**Working prototype.** A step branch whose diff removes more than 500 generated
files reaches `prose`, its packet lists every prose artefact the step changed,
and the phase can be receipted.

**Demo path.** Against a disposable repository built by the test fixture:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl_prose_packet_bounds
```

The case constructs a step branch deleting more than `GIT_PATHS_MAX` generated
files alongside one changed Markdown artefact, asserts that `next` emits the
`prose` directive, and asserts that the emitted `brief.files` contains that
Markdown path.

## 2. Prior art

**In this repository.**

`GIT_PATHS_MAX = 500` has four call sites on `main`. Two of them were separated
from the shared constant by [skills#774](https://github.com/wildcat-finance/skills/issues/774)
and now read `INTEGRATION_PATHS_MAX = 4096`: the integration path delta and the
revalidation artefact's path arrays. The two that still read the shared
constant are a commit-range limit measured in commits, and this prose diff.

The constant's own comment records the reasoning that this run contradicts:

```python
# Integration revalidation reads a surface that grows with the base, so it
# carries its own ceiling. GIT_PATHS_MAX still bounds the commit range, the
# prose diff and the checkpoint ref set, none of which grow that way.
```

The prose diff does grow that way. It is one step's change, and a step that
deletes a generated payload produces thousands of paths without any of them
being prose.

[skills#679](https://github.com/wildcat-finance/skills/issues/679) did the
separation first and went green.
[skills#680](https://github.com/wildcat-finance/skills/issues/680) reverted it
wholesale, and its record names a cancelled continuation as the reason, not a
defect in the change. Reading #680 as a rejection on merits is the available
misreading; #774 later landed the same shape.

The audit record for #774, `audit/rounds/fiat-774-bound-integration-revalidation-separately-fr.md`,
was read at source. Its risk register is the closest available template for
this one: `shared-constant-widening`, `integration-site-scope`,
`byte-ceiling-bypass`, `upper-bound-absent`, `refusal-order`,
`generated-copy-drift`, `boundary-currency` and `version-propagation` all
transfer. Both of its rounds are closed and neither leaves a lead about the
prose diff. Three leads it records stay open and outside this run: the shared
duplicate-or-oversized diagnostic in `_checkpoint_ref_names`, and two
environmental failures against a host path-length limit and a deep-JSON case.
One of its leads is operationally binding here: `tests/test_python_contract.py`
walks the tree for prose making a bare interpreter version claim and does not
exclude `.hexaemeron/`, so this run's pull-request drafts must not name one.

**Audit sources read.** The whole-set currency check,
`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`,
exits 0 from the target root, so a committed synopsis is the normal reading
view. In-scope skill: `fiat`. Sources consulted and which view was read:

| Source | View read | Evidence |
| --- | --- | --- |
| `audit/rounds/fiat-774-bound-integration-revalidation-separately-fr.md` | source | closest precedent; read in full rather than through its 4-line synopsis |
| `audit/rounds/fiat-710-give-sync-run-one-checked-transition-across.md` | synopsis | currency check `committed=match` |
| `audit/rounds/fiat-923-honest-step-branch-extensions-after-push-rec.md` | synopsis | currency check `committed=match` |
| `audit/rounds/fiat-940-site-the-generated-skills-sh-payload.md` | synopsis | currency check `committed=match` |
| `plugins/hexaemeron/audit/AUDIT.md` | synopsis | currency check `committed=match` |

**Last two merged pull requests changing this file.**
[#968](https://github.com/wildcat-finance/skills/pull/968) admitted honest
step-branch extensions after push receipts. Its `## Carried forward` names five
observations from PR #922 about the router-selection grading corpus and the ADR
numbering collision surface tracked in
[#798](https://github.com/wildcat-finance/skills/issues/798); none touches the
prose packet, and all stay outside this run as stated non-goals.
[#943](https://github.com/wildcat-finance/skills/pull/943) moved study-amendment
shape checks into Protasis; it carries nothing forward that bears on this
topic.

**The adjacent issue.**
[skills#971](https://github.com/wildcat-finance/skills/issues/971) proposes
retiring `GENERATOR_AGGREGATE_REGISTRY`'s single entry on the grounds that its
prefix no longer exists. Measured against `main` at the starting ref, both of
its factual claims are false: `git ls-files .agents/skills/promise-machine/runtime/`
reports 995 tracked files, and `python3 scripts/portable_promise_machine.py check`
exits 0 printing `checked .agents/skills/promise-machine/runtime`. The 995
deletions exist only on the step-3 branch of the halted
[skills#949](https://github.com/wildcat-finance/skills/issues/949) run, at
`f04efa78`, where they were counted. #971 generalised a branch-local state to
the repository, and its premise becomes true when #949 integrates.

**Outside.** `git diff --diff-filter` is the documented selector for change
kinds; the lowercase form excludes a kind rather than selecting it. No external
package is involved.

## 3. Constraints and non-goals

**Constraints.**

- Starting ref `840d8dd3596fd6394901ba85a693bea00c69bf25` on `main`.
- The interpreter pinned in `.python-version`; stdlib only.
- `GIT_PATHS_MAX` itself is not raised. On `main` it still guards a commit
  range measured in commits and the checkpoint ref set, and widening the shared
  constant loosens both silently.
- Editing `hexctl.py` moves four checked-in digests that no call-site analysis
  of the controller finds: the portable runtime mirror copy, the source digests
  in `tests/promise_machine_coverage.json`, `INTEGRATED_CONTROLLER_SHA256` in
  `plugins/hexaemeron/tests/test_issue_429_recovery.py`, and
  `.horos/boundary.json`. Each is named in the step that changes the
  controller, and each is recomputed from this tree rather than replayed.
- The fix must not depend on `GENERATOR_AGGREGATE_REGISTRY`, because #971 will
  eventually remove or repoint its only entry.
- No pull-request draft or committed prose names a bare interpreter version.

**Non-goals.**

- **Retiring the stale generator aggregate prefix.** The run topic names this,
  and it is withdrawn. The evidence is in item 2: the prefix is live on `main`,
  its command exits 0, and the deletion that would justify the change sits on
  an unmerged branch. Acting now would also strip the aggregate absorption that
  #949's own `sync-run` revalidation will need for those 995 deleted paths.
  #971 stays open, blocked on #949, and is named in the run pull request's
  `## Carried forward`.
- Raising or removing `GIT_PATHS_MAX` at its two remaining call sites.
- Any change to the integration revalidation bounds settled by #774.
- Re-releasing or re-pinning the installed plugin. A merged controller change
  reaches a running agent only after the plugin is re-released, and
  [skills#895](https://github.com/wildcat-finance/skills/issues/895) records
  `plugin update` reporting success while staying on a stale commit. This run
  verifies that the installed digest moved and reports the result; it does not
  own the release mechanism.
- Changing what the prose pass does with the files it is handed.

## 4. Design options

**A. Exclude deletions only.** Add `--diff-filter=d` to the diff read. A
deleted path cannot carry prose, so nothing a prose pass could act on is lost.
One flag. Trade: a step that *adds* a large generated tree still refuses at
500, so the reported shape is fixed and its mirror image is not.

**B. Exclude registered generator prefixes.** Join the diff against
`GENERATOR_AGGREGATE_REGISTRY` and drop paths under a registered prefix. Trade:
it couples the prose packet to a registry with one entry that #971 is queued to
remove, and item 2 shows that entry's status is already contested. Rejected on
that dependency alone.

**C. Select by prose-bearing extension.** Keep only paths a prose pass reads.
Trade: the smallest packet, and the only option that can silently drop real
prose. A changed description string or a module docstring sits in a file the
filter discards, and the pass then reports success having read nothing. The
issue names silent truncation as something to avoid. Rejected.

**D. A separate named ceiling.** Give the call its own constant, as #774 did
for integration. Trade: it moves the cliff from 500 to a larger number without
changing the shape, and leaves the constant's comment still wrong about why.

**Chosen: A and D together.** Drop deletions, then bound what remains with a
constant of its own, and make the refusal say what it protects.

Why this pick. It is the cheapest construction to comprehend that meets the
problem statement, and it answers all four of the issue's acceptance checks
without inventing a mechanism: deletions carry no prose, so dropping them is
justified by what the packet is for rather than by a count; everything added or
modified stays in the packet, so nothing prose-bearing is lost; the remainder
keeps a stated bound, so an authored-prose diff that is genuinely enormous
still refuses rather than truncating; and the comment stops claiming the prose
diff cannot grow with the work. It takes on the trade in option A, where an
additive generated tree is handled by the ceiling rather than by the filter,
and states that bound instead of hiding it.

## 5. Risk register seed

The packet builder reads path names produced by `git` from a repository this
process does not control, and the existing grammar checks on those names are
the control that must survive the change. The version work carries the ordinary
generated-artefact hazards: four checked-in digests move together, and a
resolved label must not be written as a literal anywhere the relation check
reads.

```risk-register
prose-artefact-loss | the packet builder's path selection | a step's changed Markdown still appears in brief.files after filtering
deletion-filter-scope | the git diff change-kind argument | renames and copies survive the filter and only deletions are dropped
silent-truncation | the packet builder's refusal path | an oversized authored-prose diff refuses rather than returning a short list
shared-constant-widening | the two GIT_PATHS_MAX call sites this run does not touch | the commit range and checkpoint ref set keep their existing bound
refusal-diagnostic | the die() message on the prose path | the refusal names the prose packet and what the ceiling protects
registry-independence | the packet builder's inputs | the selection rule reads no entry from GENERATOR_AGGREGATE_REGISTRY
unsafe-path-grammar | the retained path validation loop | absolute, dot and out-of-scope paths still refuse after filtering
byte-ceiling-bypass | the bounded git read | the existing output byte ceiling still bounds the read before any count is taken
generated-copy-drift | the four checked-in digests of the controller | every one is recomputed from this tree rather than replayed from either side
boundary-currency | .horos/boundary.json | the boundary is regenerated against the staged tree and its guard passes
version-propagation | the ledger row and skill metadata | the relation resolves, the held next job is byte-identical, and no literal label appears outside the block
```

## 6. Glossary seeds

- **Prose packet.** The `brief` the controller emits for the `prose` action,
  whose `files` array names what the pass may act on.
- **Scribe.** The delegated agent that receives the prose packet.
- **Step diff.** `git diff --name-only <pr_base>..<branch>`, the change one
  step's pull request shows.
- **Digest cascade.** The four checked-in digests of the controller that move
  whenever its bytes move.
- **Version relation.** The runbook block that defers a version label to
  integration instead of writing it now.

## 7. Sources

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, at the constants block
  and at `scribe_files` and `delegation_packet`.
- `audit/rounds/fiat-774-bound-integration-revalidation-separately-fr.md`.
- [skills#972](https://github.com/wildcat-finance/skills/issues/972), the task
  issue; [skills#971](https://github.com/wildcat-finance/skills/issues/971),
  the adjacent issue held open; [skills#679](https://github.com/wildcat-finance/skills/issues/679),
  [skills#680](https://github.com/wildcat-finance/skills/issues/680) and
  [skills#774](https://github.com/wildcat-finance/skills/issues/774), the bound
  precedent; [skills#895](https://github.com/wildcat-finance/skills/issues/895),
  the stale re-pin record.
- `docs/decisions/ADR-049-bound-integration-revalidation-separately.md`.
- `plugins/hexaemeron/skills/VERSIONING.md` and
  `plugins/hexaemeron/skills/fiat/EVOLUTION.md`.

## 8. Signals, and the questions behind them

`hexctl` is invoked from a terminal by a person or an agent driving a run, so
there is no unattended process emitting telemetry. The signals that matter are
the two the command already prints, and both are inadequate today.

- *Why did the prose phase refuse?* Answered by the refusal string. Today it
  reads `git diff returned more than 500 paths`, which names a number and not
  the thing the number protects, so a contributor removing a generated tree
  learns only that a limit exists. The step that changes the builder makes the
  refusal name the prose packet and the ceiling that applies to it.
- *Which paths did the packet actually carry?* Answered by `brief.files` in the
  emitted envelope, which is already complete and machine-readable. Filtering
  changes what it contains, so the same step's test asserts the retained
  Markdown path is present rather than only that the count fell.

[ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal carries.

## 9. Boundaries, per capability

One boundary, and it is not new. The builder consumes path names emitted by a
`git` subprocess against a repository whose contents this process does not
control, decodes them as UTF-8, and joins them to the filesystem through
`scoped_path`.

What is worth taking there: a path that is absolute, is `.` or `..`, or escapes
the target directory, reaching a later filesystem join. The controls that close
it already exist in `scribe_files`: the UTF-8 decode refusal, the absolute and
dot refusals, and the `scoped_path` call on every retained entry. The
change must run all of them on exactly the set it returns. Adding a filter
upstream of those checks is the way this boundary reopens, so the filter is
applied to the argv of the read rather than to the validated list, and the
validation loop keeps running over whatever survives.

The bounded read itself is unchanged: `bounded_git` still applies the existing
output byte ceiling and timeout before any path is counted, so the count is not
the first line of defence and is not being asked to be.

[phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list and the controls.

## 10. The budget, or its absence

None. This run makes no performance claim. The read it changes is one
already-bounded `git diff` per `next` invocation on a step in the prose phase,
and dropping deleted paths can only shorten it. No before-and-after measurement
is owed, and [metron](../../plugins/hexaemeron/skills/metron/SKILL.md) is not invoked for a change made for
correctness rather than speed.

## 11. The fail-closed posture

What stops the run: the builder refuses rather than returning a partial list.
An oversized authored-prose diff still exits non-zero, and the refusal is
raised before any packet is constructed, so a caller never receives a truncated
`files` array that reads as complete. A UTF-8 decode failure or an unsafe path
refuses on the existing paths, unchanged.

Guard-test convention for a fix in this run: a repair admitted during an audit
round arrives with a case that fails without it, in the module named by the
step's `Tests` field, and the round records `guarded`. Where a repair adds
coverage rather than changing behaviour, the round records the weaker verdict
honestly rather than claiming a guard that no red test demonstrates.

[elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage order and the guard rule.

## 12. Decisions and their homes

One decision is expensive to reverse: that the prose packet selects by what a
prose pass can act on, and carries a ceiling of its own rather than the shared
one. Reversing it later means either re-coupling two unrelated bounds or
choosing a different selection rule after runs have depended on this one, and
the reasoning that rejected the registry join and the extension filter is not
recoverable from the diff.

It earns an architecture decision record under `docs/decisions/`, alongside
ADR-049, which settled the same question for the integration surface. The
number is claimed at integration rather than now, because ADR numbering here
has a live collision surface tracked in
[#798](https://github.com/wildcat-finance/skills/issues/798).

The withdrawal of the topic's second clause is recorded in item 3 and in the
run pull request's `## Carried forward`, not in a record of its own: it is a
scope decision for this run, not a standing architectural choice.

[hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a record and where
each one lives.
