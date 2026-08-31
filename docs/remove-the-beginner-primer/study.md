# Study: remove the child-or-golden-retriever primer and its generator

Issue #975, measured against `wildcat-finance/skills` at
`840d8dd3596fd6394901ba85a693bea00c69bf25`.

## Assumptions

Stated before the content that rests on them. Proceeding on these unless
corrected.

1. Python 3.14.6, the exact interpreter in `.python-version`, with stdlib
   `unittest`. Confirmed: `python3 -V` reports 3.14.6 in this worktree.
2. The base ref is `main` at `840d8dd3596fd6394901ba85a693bea00c69bf25`, and
   the run branch `fiat/975-remove-the-child-or-golden-retriever-primer` is cut
   from it.
3. `TMPDIR` is set to a real path for every command in this run. The host
   default under `/var/folders` is a symlink and several suites refuse it.
4. The three decisions the issue left open are settled by the Creator and are
   recorded in section 3 as constraints, not as findings of this study.
5. The decision-record number proposed in section 3 is re-confirmed against
   `origin/main` immediately before the record is written, and renumbered at
   integration if it collides.
6. This run publishes no replacement for the primer and writes no prose
   standing in for one.

## 1. Problem statement

**What is being built.** A removal. Fifteen tracked files carrying the
beginner primer, its generated images and PDFs, its builder, and its focused
test leave the repository. Every reference to them from a file that survives is
either updated or deliberately left as a historical record. The accepted
decision that governs the primer is marked superseded rather than deleted, and a
new record says why the subject stopped existing.

**For whom.** The repository's maintainers. The primer's own gate cannot run
correctly anywhere, and the binaries it leaves in `docs/assets/` and
`docs/pdf/` block any Fiat run whose base advance touches those paths from
receipting its integration.

**What a working prototype means here.** The tree contains no primer, no
builder and no primer test; the boundary and dead-code manifests describe the
tree as it now is; the root suite runs green on a host with the image libraries
present, which it cannot do today; and the beginner-facing section of
`README.md` no longer links a path that does not exist.

**The demo path that proves it.** From the run worktree, with `TMPDIR` set to a
real path:

```bash
git ls-files | grep -iE 'child.or.a.golden.retriever|child_or_golden_retriever'
python3 scripts/run_checks.py --scope root --jobs 2
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 scripts/dead_code.py baseline --check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 scripts/portable_promise_machine.py check
```

The first command must print nothing. The second must print `outcome green`;
its exit status is not its verdict, because `unstable-source` sets exit 3 and a
red outcome was observed at exit 0 while preparing this study. The rest must
each exit zero.

## 2. Prior art

### The primer's own delivery

The primer landed through two merged pull requests, `#674` (the step) and
`#675` (the run), reachable from merge commits `966aba40` and `934c4710`. Both
pull request bodies are unreadable: they were opened by
`shoggoth-wildcat-labs`, whose issues and pull requests are not visible through
the API, and `gh pr view` reports that neither number resolves. The merge
commit messages carry only the shared title, "Explain Shoggoth, Hex, Fiat and
the Interceptor". **This is an evidence gap.** Where a Fiat run records
unfinished work in the body of its last pull request, that record cannot be
read here. The audit record below is the substitute, and it is complete enough
to carry the delivery forward.

### Audit sources

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
runs from the target root and exits zero. The whole-set currency check reports
45 pairs, every one `committed=match`, so a verified synopsis would have been a
legitimate reading view. It was not used for the two records that matter.

| In-scope source | What was read | Evidence for the choice |
| --- | --- | --- |
| `audit/rounds/docs-a-child-or-a-golden-retriever.md` | **The source, in full.** | It is the subject of this removal; the synopsis is 5 lines against a 63-line source and would drop finding ids. |
| `audit/rounds/fiat-700-proxy-model-traffic-without-giving-the-worke.md` | **The source**, at the line naming the primer. | Its only in-scope content is one finding row; the synopsis is 29 lines against 472 and does not carry that row's file list. |
| `audit/rounds/fiat-390-...md`, `fiat-557-...md`, `fiat-774-...md` | **The sources**, at their primer lines. | Found by content sweep; the issue did not name them. Each mentions the primer only inside `Leads not pursued`. |

No plugin `audit/AUDIT.md` is in scope: this run changes no plugin code.

**The primer's own record, carried forward.** Four rounds, schema
`fiat-audit-round/v2`. Fourteen risk ids reviewed in every round:
`role-confusion`, `current-state-drift`, `mascot-identity`, `generated-text`,
`reference-leakage`, `binary-review`, `accessibility-gap`, `layout-overflow`,
`source-output-drift`, `toolchain-gap`, `horos-currency`, `link-decay`,
`branch-authority`, `scope-creep`. Three findings, `S1-R1-01` (low),
`S1-R2-01` (medium) and `S1-R3-01` (medium), each marked fixed in its commit.
Round 4 carries the empty finding row and `Elenchus verdict: null`. Nothing is
left open. `Not checked` across the rounds names the Pashov and
`solidity-auditor` passes as waived for a step shipping no Solidity, human
comprehension, PDF/UA conformance, the pre-publication branch URL, the waived
step checkpoint, and any merge to main. None of those survives the subject.
`Leads not pursued` records the mascot archive digest, the cover digest and the
byte-identical rebuild claim, all of which stop applying once the files are
gone.

**The finding this removal answers.** `S1-R2-01` is the reason issue #975
exists. It records that the focused test originally pinned a private
interpreter path, and that the fix made the test skip its two
dependency-backed checks when Pillow, pypdf and ReportLab do not import. That
fix made the test portable and, in the same move, made it silent in CI.
`.github/workflows/repo.yml` installs none of the three; a grep for
`pip install`, `Pillow`, `reportlab` and `pypdf` in that file returns nothing.
`docs/fiat-integration-path-bound-study.md:134` records the same shape and
calls it structurally invisible to the gate that exists to catch it.

**What the gate does on a capable host.** Verified in this worktree:
`python3 -m unittest tests.test_child_or_golden_retriever_primer` raises
`AssertionError: deterministic primer check failed` from `setUpClass`, having
run 0 tests. Nine of ten builder checks pass; `deterministic-rebuild` fails on
three artefacts, not the two the issue names:
`docs/assets/a-child-or-a-golden-retriever-whos-who.png`,
`docs/assets/a-child-or-a-golden-retriever-fiat-flow.png`, and
`docs/pdf/a-child-or-a-golden-retriever.pdf`. The PDF is a correction to the
issue's account. `python3 scripts/run_checks.py --scope root --jobs 2` reports
`root-suite failed`, `outcome red`, `failures test-failure`, and exits 0.

### The decision record

`docs/decisions/ADR-039-keep-one-source-for-the-beginner-primer.md` is
`Accepted, 2026-08-27`. It makes `docs/a-child-or-a-golden-retriever.md` the
canonical reader-facing source and names the builder, the cover, the two
generated mascots and the four generated views. Its consequences section
already anticipates a visual replacement but requires the source note to be
updated, which is not what happens here: the subject stops existing outright.

### An in-flight run holds the next number

`origin/fiat/936-report-dead-code-baseline-staleness-instead` carries commit
`6a7baf1a`, `docs(dead-code): renumber the decision record to ADR-059`. That
branch is not an ancestor of `origin/main`, whose highest record is `ADR-058`.
The record's own status section documents the collision it survived: its
runbook allocated `ADR-054`, `main` advanced by 115 paths during the audit
loop, `ADR-054` through `ADR-058` all landed, and
`tests/test_decision_records.py` reported the collision on the merged tree.
That is the precedent this study follows in section 3.

That run is also directly relevant to step ordering. It exists to make
`baseline --check` report staleness instead of refusing. Until it lands, the
refusal described in section 4 is live.

### Outside this repository

Nothing. The primer is repository-local prose and a repository-local builder.
No package, standard or external artefact is involved.

## 3. Constraints and non-goals

### Starting ref and toolchain

- Base `main` at `840d8dd3596fd6394901ba85a693bea00c69bf25`; run branch
  `fiat/975-remove-the-child-or-golden-retriever-primer`.
- Python 3.14.6, per `.python-version`. Recent runbooks in `docs/` invoke it as
  `mise exec python@3.14.6 -- python3 ...`; that form is available and is the
  house style for a step's exit command.
- `TMPDIR` must point at a real directory. On this host the default resolves
  under `/var/folders`, and `/var` is a symlink; suites that refuse a symlinked
  lexical parent fail on it. Setting `TMPDIR` to a path under `/private/tmp`
  takes the Lazarus suite from 86 errors to 599 tests OK. This is a property of
  the host, not a defect in the repository, and three separate audit records
  (`fiat-390`, `fiat-557`, `fiat-774`) already record it.

### Decided by the Creator, 30 August 2026

Recorded here so a later reader knows these were decided rather than assumed.
Their source is the Creator's direction relayed in this run's controller
packet, answering the three questions issue #975 left open.

1. **The primer's own two audit records go with it.**
   `audit/rounds/docs-a-child-or-a-golden-retriever.md` and its
   `.synopsis.md` are deleted with everything else. The issue left this open;
   it is now closed.
2. **`README.md` loses the references and gains nothing.** The three links go.
   The beginner entry point is left unspoken. No replacement prose, no
   substitute link, and no sentence about future plans.
3. **The replacement is out of scope.** The Creator is handling it separately.
   This study does not design one and does not recommend one.

### The decision-record number

`ADR-059` is the next number free on `origin/main`, and it is already taken by
the in-flight `#936` run. This study proposes **`ADR-060`**. That number is
safe only until another run claims it. `tests/test_decision_records.py`
compares against `origin/main` and catches a collision while the second branch
is still a pull request, so the failure mode is a rename at integration rather
than a duplicate on main. Re-confirm before writing the record; renumber if the
test reports a collision.

### Non-goals

- No replacement primer, and no decision about whether one is needed.
- No change to how generated artefacts are checked in general. Whether any
  other output should be byte-compared against an unpinned toolchain is a
  separate question this removal makes less urgent.
- No history rewrite. The 10,946,434-byte figure is the tracked size at the
  base commit; Git keeps the objects.
- No edit to the historical studies, runbooks and audit records that cite the
  primer as evidence for decisions taken at the time.
- No widening of `tests/test_python_contract.py`'s exclusion list, and no other
  repair discovered in passing.

## 4. Design options

The verified inventory, the reference set and the gate mechanics are settled
first, because the options differ only in how the work is cut into steps.

### The verified inventory

Fifteen tracked files, 10,946,434 bytes. Both figures match the issue exactly,
measured independently by `git ls-files` filtered on
`child.or.a.golden.retriever|child_or_golden_retriever|child-or-a-golden` and
summed with `wc -c`.

| Path | Bytes |
| --- | --- |
| `audit/rounds/docs-a-child-or-a-golden-retriever.md` | 14,371 |
| `audit/rounds/docs-a-child-or-a-golden-retriever.synopsis.md` | 14,729 |
| `docs/a-child-or-a-golden-retriever.md` | 6,528 |
| `docs/a-child-or-a-golden-retriever-runbook.md` | 4,874 |
| `docs/a-child-or-a-golden-retriever-source-note.md` | 8,419 |
| `docs/a-child-or-a-golden-retriever-study.md` | 25,175 |
| `docs/assets/a-child-or-a-golden-retriever-cover.png` | 1,166,639 |
| `docs/assets/a-child-or-a-golden-retriever-fiat-flow.png` | 980,185 |
| `docs/assets/a-child-or-a-golden-retriever-mascot-fiat.png` | 1,682,633 |
| `docs/assets/a-child-or-a-golden-retriever-mascot-roles.png` | 2,171,579 |
| `docs/assets/a-child-or-a-golden-retriever-whos-who.png` | 1,068,085 |
| `docs/pdf/a-child-or-a-golden-retriever.pdf` | 3,689,253 |
| `docs/pdf/a-child-or-a-golden-retriever-quick-start.pdf` | 43,767 |
| `scripts/build_child_or_golden_retriever_primer.py` | 45,832 |
| `tests/test_child_or_golden_retriever_primer.py` | 24,365 |

### Every reference from a file that survives

Found by two sweeps over tracked content: one on the path patterns above, one
on the words `primer` and `beginner` to catch a reference made by description
rather than by filename.

**Updated.**

| Reference | Action |
| --- | --- |
| `README.md:29-32` | Delete the three links and the sentence carrying them. Nothing replaces them. `README.md` is in scope for `tests/test_shipped_prose_lints.py`, which holds every shipped document to a clean Imprimatur score, so the remaining paragraph must lint clean. |
| `docs/decisions/ADR-039-...md` | Status becomes superseded; see below. |
| `.horos/boundary.json` | Regenerated by a scan. Seven entries, all `category: binary`, `grade: hard`, 10,802,141 bytes: the five PNGs and both PDFs. After removal, entries fall from 135 to 128, `bytes_binary` from 54,685,567 to 43,883,426, and `files_walked` from 2,132 to 2,117. |
| `.dead-code/baseline.json` | Republished. It names `scripts/build_child_or_golden_retriever_primer.py` and `tests/test_child_or_golden_retriever_primer.py` among 439 findings. |

**Left alone, as records of what was true when written.** Nine documents, not
the seven the issue names. `docs/fiat-controller-checkpoint-study.md` and its
runbook; `docs/fiat-integration-path-bound-study.md` and its runbook;
`docs/fiat-step-branch-extensions-runbook.md`;
`docs/fiat-sync-run-generator-aggregates-runbook.md`;
`docs/protasis-amendment-block-check-runbook.md`; and two the issue missed,
`docs/ci-plugin-suite-gate/runbook.md:34` and
`docs/fiat-sync-resolution-guard-runbook.md:25,33,37`, which refer to the
primer by description rather than by path. Four audit records from other runs,
not two: `fiat-700`, `fiat-390`, `fiat-557`, `fiat-774`. None of these is in
the shipped-prose lint's scope, which excludes `audit/` and `docs/**` for
exactly this reason.

**The reference the issue got wrong.**
`plugins/hexaemeron/docs/fiat-author-publisher-separation/runbook.md:17` names
`docs/a-child-or-a-golden-retriever-study.md` and
`scripts/build_child_or_golden_retriever_primer.py` in its `Files` line. The
issue names only the `.agents/` mirror of this file and says to refresh it
through the ordinary portable sync. That is a no-op. The mirror at
`.agents/skills/promise-machine/runtime/plugins/hexaemeron/docs/fiat-author-publisher-separation/runbook.md`
is byte-identical to its source, confirmed by `diff`; the sync copies
`plugins/` into `.agents/`, so an unchanged source yields an unchanged mirror.
The source is a historical delivery record of the same class as the nine
documents above, so it is **left alone**, and the mirror therefore needs no
action at all. `python3 scripts/portable_promise_machine.py check` is clean now
and stays clean. The portable runtime carries no boundary file naming the
primer.

**Checked and not a reference.**
`plugins/hexaemeron/skills/fiat/references/prose-pass.md:9` uses the word
`primers` generically, in a list of prose kinds. It is a live skill reference,
so it was checked by eye rather than by pattern. It needs no change.

**Manifests that name nothing.** Neither `tests/check-map-v1.json` nor
`tests/promise_machine_coverage.json` names any of the fifteen paths, verified
by grep. Confirmed against the issue.

### What ADR-039 needs

The convention is a house convention, not a mechanical one.
`tests/test_decision_records.py` checks the filename pattern, number
uniqueness within the tree, agreement between filename and first heading, and
non-collision with `origin/main`. It does not read the status line. So the
shape comes from what earlier records actually do, and two are clean
exemplars:

- `ADR-011` opens `## Status` with `Superseded, 2026-08-23.` followed by a
  Markdown link to the superseding record and one sentence saying what it
  retains and what it replaces. The body below is untouched.
- `ADR-038` opens with `Superseded, 2026-08-28.`, then a blank line, then a
  link to `ADR-042` and a sentence naming what changed and what stays in force.

The superseding record states the relation in the other direction: `ADR-016`
opens `Accepted, 2026-08-23. Supersedes the communication-only authorship boundary in [ADR-011](...)`. Two records use a different word for a different
situation, and neither fits here: `ADR-030` is `Retired` because its proposal
was never accepted, and `ADR-028` records a replacement made at the Creator's
direction.

So `ADR-039` keeps its body and gains a status of `Superseded, <date>.` with a
link to the new record. The new record is `Accepted, <date>.` and supersedes
`ADR-039` by name, recording that the single-source design held while the
primer existed and that the primer was removed rather than rebuilt.

### The gate mechanics that fix the order

Two gates constrain how the work is committed.

**Horos.** `horos.py` scans with `git ls-files -z --cached --others
--exclude-standard`. `--cached` reads the index, so a deletion that is not
staged is still counted. The scan must run **after `git add`** of the
deletions, and its output is staged into the same commit.

**Dead code.** `require_baseline_publication` in `scripts/dead_code.py:3722`
enforces three things about `.dead-code/baseline.json` against the checkout:
the recorded source commit must differ from `HEAD` (line 3728), it must be an
ancestor of `HEAD` (line 3738), and `git diff --name-only source..HEAD` must
equal exactly `{".dead-code/baseline.json"}` (lines 3753-3760). The last is the
binding one. It means the baseline must be published in a commit that changes
nothing else, sitting directly on the commit it was computed from.

This settles whether the removal can be split. At the removal commit, the diff
from the current baseline's source commit `8cc85686` includes all fifteen
deleted paths plus `README.md` and the records, so `baseline --check` refuses
with `baseline is stale; source changed after publication`. **The removal
commit is red for the dead-code scope.** A step must be green at both ends, so
the removal and the baseline republication cannot be two steps. They are two
commits inside one step. Verified alongside this: `baseline --check` exits 0 at
the current `HEAD`, because `8cc85686..840d8dd3` touches only the baseline
itself, and the precedent commit `38345929` shows the same two-commit shape.

### The options

**A. One step, one commit.** Refused, not chosen against. The dead-code gate
makes it impossible: the baseline cannot be published in the commit whose
changes it describes.

**B. One step, two commits.** Commit one stages the fifteen deletions, edits
`README.md`, marks `ADR-039` superseded, adds the new record, runs the Horos
scan after `git add` and stages the boundary. Commit two republishes
`.dead-code/baseline.json` and nothing else. The step's exit runs the full
demo path at the tip, where both gates pass. Trades away any intermediate
green checkpoint: an operator who stops after commit one has a red tree.

**C. Two steps, removal then baseline.** Refused for the reason above. Step one
would exit red on the dead-code scope, which is not an exit.

**D. Three steps: records, then deletion, then baseline.** Splits the prose
from the deletion so the decision records land first. It is buildable, and its
first step is green. It trades away truthfulness in exchange for nothing:
`ADR-039` would be marked superseded, and a new record would say the primer was
removed, while the primer still sat in the tree. It also triples the audit
loop, which dominates the clock, for a change whose whole content is one
boundary.

**Chosen: B.** It is the option cheapest to comprehend that still meets the
problem statement. The primer stops existing is one boundary and one pull
request; the second commit exists only because a manifest cannot describe the
commit that carries it. Single-step Fiat runs are house practice here, and the
primer's own delivery was one.

### What the removal leaves unowned

Nothing. `tests/check-map-v1.json` maps ownership by directory: `tests` and
`scripts` both belong to scope `root`, and no per-file `owners` entry names
either primer file. The `root-suite` check runs `python3 -m unittest discover
-s tests` and keeps 38 other test modules, so no check loses its subject and no
scope becomes newly empty. Five scopes (`docs`, `schemas`, `promise-machine`,
`marketplace`, `ci`) already carry zero checks, so an empty scope is a normal
state in this manifest rather than a condition this change could introduce.

Removing the primer's two audit records does not disturb
`audit_synopsis.py --check`. The pair appears in the whole-set listing as one
entry with `committed=match`; source and synopsis are deleted together, so the
set shrinks by one pair and stays current. This closes the last unknown issue
#975 recorded.

## 5. Risk register seed

The removal itself is small. What deserves the hardest look is the set of
things that could be deleted or edited beyond it, and the two manifests that
must describe the tree exactly.

```risk-register
over-deletion | the fifteen-path delete set | no tracked path outside the verified inventory is removed, checked by diffing the deleted set against the study's table
historical-record-edit | the nine surviving documents and four audit records that cite the primer | none of them is modified; a diff of the step shows no change under audit/ except the two deleted primer records
readme-gap-filled | the beginner section of README.md | the three links and their sentence are gone and no replacement prose, substitute link or future-plans sentence was written
readme-lint-regression | README.md after the edit | tests/test_shipped_prose_lints.py passes, since README.md is in that lint's scope and the surrounding paragraph is re-flowed
adr-number-collision | the new decision record's number | tests/test_decision_records.py passes against a fetched origin/main, and the number is re-confirmed immediately before the record is written
adr-039-deleted | docs/decisions/ADR-039-keep-one-source-for-the-beginner-primer.md | the file still exists, its body is unchanged, and only its Status section gained a superseded line and a link
boundary-staleness | .horos/boundary.json | the scan ran after git add, entries fell 135 to 128, and horos.py check . reports the boundary matches the tree
baseline-publication-shape | .dead-code/baseline.json | the republishing commit changes that path and nothing else, and baseline --check exits 0 at the step tip
mirror-drift | .agents/skills/promise-machine/runtime | portable_promise_machine.py check exits 0 with no hand edit to any mirrored file
outcome-misread | the run_checks verdict | the outcome line was read and says green; exit status alone was not accepted as the verdict
tmpdir-symlink | the temporary root every command inherits | TMPDIR resolves to a real path with no symlinked parent, so a suite failure is a real failure
generated-artefact-orphan | docs/assets and docs/pdf after removal | no unreferenced primer binary survives, and no other tracked binary lost its only reference
```

`over-deletion` and `historical-record-edit` are the two that matter most. The
delete set was measured twice by pattern, and the surviving citations are
records of what was true when written. A round that finds either boundary
crossed should stop rather than repair, because the repair is a revert.

`readme-gap-filled` is unusual: it checks that something was **not** written.
The Creator decided the beginner entry point is left unspoken, and the natural
instinct while editing that paragraph is to soften the gap. That instinct is
the defect here.

## 6. Glossary seeds

- **The primer.** `docs/a-child-or-a-golden-retriever.md` and the four
  generated views built from it. Named for its opening question about how to
  address an agent.
- **The builder.** `scripts/build_child_or_golden_retriever_primer.py`, which
  reads the primer's marked sections and produces both PNGs and both PDFs.
- **Deterministic rebuild.** The builder check that regenerates each view and
  compares it byte for byte against the committed file. It is the check that
  fails on any host whose Pillow and FreeType differ from the build host's.
- **Boundary.** `.horos/boundary.json`, the deterministic classification of
  token sinks that agents consult before reading. Regenerated by a scan, never
  edited by hand.
- **Baseline.** `.dead-code/baseline.json`, the report-only dead-code finding
  set, published in a commit that changes only itself.
- **Publication commit.** The commit that carries a regenerated manifest and
  nothing else, required by the dead-code gate.
- **Superseded.** A decision-record status meaning the record still describes a
  choice that was made, but a later numbered record now governs. The body is
  never edited and the file is never deleted.
- **Historical record.** A study, runbook or audit round that cites something
  as evidence for a decision taken at the time. It keeps saying what it said.
- **Portable mirror.** `.agents/skills/promise-machine/runtime`, a generated
  byte copy of parts of `plugins/`. Refreshed by sync, never edited directly.

## 7. Sources

- Issue #975, `gh issue view 975 --repo wildcat-finance/skills`, the inventory
  and reference list this study verified.
- `840d8dd3596fd6394901ba85a693bea00c69bf25`, the base commit every figure was
  measured at.
- `audit/rounds/docs-a-child-or-a-golden-retriever.md`, four rounds, read in
  full as the source.
- `docs/decisions/ADR-039-keep-one-source-for-the-beginner-primer.md`, the
  accepted decision this removal supersedes.
- `docs/decisions/ADR-011-...md` and `ADR-038-...md`, the two clean exemplars
  of the superseded status convention; `ADR-016-...md` for the forward
  direction.
- `origin/fiat/936-report-dead-code-baseline-staleness-instead` at `6a7baf1a`,
  which holds `ADR-059` and documents an integration-time renumbering.
- `scripts/dead_code.py:3722-3760`, `require_baseline_publication`, the gate
  that fixes the commit order.
- `plugins/horos/skills/horos/scripts/horos.py:585-587`, the `--cached` scan
  that requires staged deletions.
- `tests/test_decision_records.py:110`, the collision check against the default
  branch.
- `tests/test_shipped_prose_lints.py:1-22,80-105`, the scope that includes
  `README.md` and excludes `audit/` and `docs/**`.
- `tests/check-map-v1.json`, `checks`, `scopes` and `owners`, for what the
  removal leaves unowned.
- `docs/fiat-integration-path-bound-study.md:134`, the earlier record of the
  CI-invisible gate.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:6820,6855`, the
  integration revalidation coverage gate that the primer binaries obstruct.
- `plugins/hexaemeron/skills/protasis/SKILL.md` version 5.9.0, the content
  contract this study is held to.

## 8. Signals, and the questions behind them

**None, and here is why.** This delivery adds no code that runs. It deletes a
builder and a test, edits prose, and regenerates two manifests. Nothing
introduced here executes unattended, holds a queue, serves a request or runs on
a schedule, so there is no three-in-the-morning question for it to answer and
no step that could emit a signal.

The one thing an operator will want to know afterwards is whether a Fiat run
whose base advance touches `docs/assets/` or `docs/pdf/` can now receipt its
integration. That is answered by the run either receipting or not, at
`hexctl.py:6855`, and it is already visible without new instrumentation.
[ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal must carry if that judgement
changes.

## 9. Boundaries, per capability

**None opened, and here is why.** No boundary in
[phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md)'s list is widened. The delivery accepts no data
from outside the process, fetches no URL, reads no credential, adds no
dependency and feeds no agent. The two subprocess-spawning commands it runs,
the Horos scan and the dead-code baseline build, already exist, already run in
the root suite, and are invoked here with no new argument.

Two boundaries are **narrowed**, which is worth recording because narrowing is
still a change. Deleting the builder removes the repository's only in-tree
consumer of Pillow, pypdf and ReportLab as a build path, and deleting seven
`grade: hard` binary entries removes 10,802,141 bytes from the classified
binary surface. Neither needs a control; both feed the `over-deletion` and
`generated-artefact-orphan` entries in section 5, which check the narrowing was
exactly as wide as intended.

## 10. The budget, or its absence

**None, and here is why.** No performance claim is made or implied. The
delivery makes the repository smaller, and nobody has asserted a target for how
much smaller or how much faster anything gets.

One measurement is worth recording as evidence rather than as a budget, because
the removal changes it and a reader will otherwise wonder: the root suite loses
one module, and the `deterministic-rebuild` failure that makes
`scripts/run_checks.py --scope root` report `outcome red` today disappears with
it. That is a correctness change, not a speed one, and it is already an exit
criterion in section 1 rather than a budget.
[metron](../../plugins/hexaemeron/skills/metron/SKILL.md) owns what a budget carries if a target is set
later.

## 11. The fail-closed posture

**What stops the run.** Any of these, at the step tip:
`scripts/run_checks.py --scope root` reporting an outcome other than `green`;
`horos.py check .` not reporting that the boundary matches the tree;
`dead_code.py baseline --check` exiting non-zero;
`promise_machine.py check` or `coverage --check` exiting non-zero;
`portable_promise_machine.py check` exiting non-zero; or the tracked-path grep
printing anything. Also fail-closed: a `git status` showing any modification
under `audit/` other than the two deleted records, or under the nine surviving
historical documents.

Two ways of failing here read as success and must be refused explicitly. First,
`run_checks.py` exit 0 with a red outcome, observed while preparing this study.
The outcome line is the verdict; exit status is not, because `unstable-source`
sets exit 3 independently of what the checks found. Second, a suite failing for
`TMPDIR` reasons rather than for what this change did. Before treating any
failure as real, confirm `TMPDIR` resolves to a path with no symlinked parent.

**The guard convention.** A fix during the audit loop follows
[elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md)'s rule: the guard fails against the unfixed
tree and passes against the fixed one, and it is committed with the fix. For
this delivery a guard is most likely to be a check that something was not
touched, since the plausible defects are over-deletion and an edited historical
record. The current red in `tests/test_child_or_golden_retriever_primer.py` is
not a failure to triage. It is the subject. Removing the file removes it, and
it is not a reason to change anything else.

## 12. Decisions and their homes

One decision here is expensive to reverse, and it already has a home.

**Removing the primer without a replacement.** Reversing it means restoring
10.4 MiB from history, restoring an accepted decision to force, and rebuilding
a gate that never worked. The record is a new file under
`docs/decisions/`, proposed as
`ADR-060-remove-the-beginner-primer-and-its-generator.md`, and states that the
single-source design in `ADR-039` held while the primer existed, that the
deterministic rebuild could not survive an unpinned Pillow and FreeType, that
the binaries blocked integration receipts for unrelated runs, and that the
replacement is a separate piece of work. `ADR-039` gains a superseded status
pointing at it, in the shape section 4 establishes from `ADR-011` and
`ADR-038`. [hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a
record and where each one lives.

Three decisions made in this run are **not** expensive to reverse and get no
record. Deleting the primer's two audit records is a judgement about whether a
completed audit outlives its subject, and restoring two Markdown files from
history costs nothing. Leaving `README.md`'s beginner section unspoken is
reversed by writing a sentence. Choosing one step over three is a runbook
shape, not a durable choice; it is recorded in section 4 with the gate that
forces it, which is where a later reader will look.

The `ADR-060` number is not itself a decision. It is an allocation, and
section 3 records that it is provisional until integration.

## Boundaries this study states

**Always.** Read the `outcome` line of `scripts/run_checks.py`, never its exit
status alone. Set `TMPDIR` to a real path before any command. Run the Horos
scan after `git add` and stage its output into the same commit. Lint every
shipped document with Imprimatur before it is committed. Re-confirm the
decision-record number against a freshly fetched `origin/main` immediately
before writing the record.

**Ask first.** Writing any replacement prose into `README.md`. Editing any
historical study, runbook or audit record that cites the primer. Deleting a
path not in the fifteen-path inventory. Changing `tests/check-map-v1.json`,
`tests/promise_machine_coverage.json` or `.github/workflows/repo.yml`. Touching
`plugins/hexaemeron/docs/fiat-author-publisher-separation/runbook.md` or its
mirror.

**Never.** Delete `ADR-039` or edit its body. Hand-edit `.horos/boundary.json`,
`.dead-code/baseline.json` or anything under
`.agents/skills/promise-machine/runtime`. Rewrite history to drop the primer
objects. Delete a failing test to make a suite pass, other than the primer test
itself, which is deleted because its subject is. Claim a command ran when it
did not.
