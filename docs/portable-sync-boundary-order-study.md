# Stage the portable sync before the Horos scan and check mirror import closure

Assuming, unless corrected:

1. Python 3 as pinned in `.python-version`, standard library only, `unittest`
   as the runner. The repository adds no dependency for this.
2. The run starts at `4fe374dd33d43b86d800abe9240d62e09ed7d395`, the tip of
   `origin/main` when the run branch was cut.
3. The committed boundary keeps its `tracked` universe. Widening it to
   `tracked+untracked` is a different change with a different blast radius, and
   it is ruled out in item 3.
4. `plugins/horos/examples/fixture-sol/Market.sol` is a fixture whose two
   relative imports are decorative and are meant to stay unresolved.
5. This is ordinary repository delivery. It advances no skill frontier and
   touches no skill version or `EVOLUTION.md`.

I will proceed on these unless corrected.

## 1. Problem statement

Two generated artefacts in this repository can describe a tree that does not
exist, and both report success while doing it.

The first is an ordering defect. `scripts/portable_promise_machine.py sync`
writes the portable runtime mirror under
`.agents/skills/promise-machine/runtime/`. `plugins/horos/skills/horos/scripts/horos.py
scan . --write` then walks a universe that `resolve_universe` builds from
`git ls-files`, which reads the index. Files the sync has just written are not
in the index yet, so the scan cannot see them, and the boundary it writes
describes the tree as it was before the sync ran. `horos check` then recomputes
from the same index and agrees. The person who could fix this in one command
sees green; CI, working from a clone where everything is committed, sees
`test_the_committed_boundary_matches_a_fresh_scan` fail on
`['.horos/boundary.json#counts']`.

The second is a closure defect, and it is independent of the first.
`portable_promise_machine.py check` compares a declared file set against
digests. It never asks whether the sources it mirrored can resolve their own
relative imports. A mirror in which `HonestAccessHook.sol` imports
`./IRoleProvider.sol` with no such file beside it is a runtime that cannot
compile, and `check` exits 0 over it.

A working prototype means both of these:

- The obvious order works. `sync`, then `scan . --write`, then `git add -A`,
  with no manual staging in between, leaves the committed boundary equal to a
  fresh scan of the same tree.
- A mirror that omits a file its own mirrored sources import makes `check`
  exit non-zero and name the importing file and the unresolved target.

The demo path is one sequence run from the repository root, and it is the
last step's exit:

```bash
python3 scripts/portable_promise_machine.py sync
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
git add -A
python3 -m unittest tests.test_boundary_currency -v
python3 scripts/portable_promise_machine.py check
```

Every command exits 0, and the boundary test passes without the alternation
loop that the working order needs today.

## 2. Prior art

**The carried finding.** This topic is not new work. It is
`S4-R1-03` from the skills#329 run, recorded in
`audit/rounds/fiat-329-janus-resolve-the-manifest-s-permitted-effec.md` with
status `accepted`. Its text names both halves: "the portable-runtime sync
builds its file set from git-tracked files and its check does not verify import
closure, so a new untracked source produces a mirror that omits it while the
check still exits 0". It records how it was found, by adding
`IRoleProvider.sol` and watching the mirrored hook import a file that was not
there, and it records why it was not fixed: "The tooling gap is outside this
run's study, which keeps the repository scripts untouched, so it is recorded
and carried rather than fixed". Issue #854 is that carried item coming back.

I read the synopsis rather than the source for the #329 record. The evidence
for that choice is that
`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exits 0 from the repository root and reports `committed=match` for every pair,
including
`audit/rounds/fiat-329-janus-resolve-the-manifest-s-permitted-effec.synopsis.md`,
which is the condition under which a synopsis is the normal reading view. The
same record's step 6 rounds show the workaround in use: "portable_promise_machine.py
check exit 0 and horos check exit 0, alternated to a fixpoint compared by
content digest". Finding ids and statuses carried out of that record for this
topic: `S4-R1-03` accepted, and nothing else in it bears on these two scripts.

**In-scope skills.** Horos is the only plugin whose code this run may touch,
and `plugins/horos/audit/` does not exist, so it has no plugin-level audit
record to read. The root record `audit/AUDIT.md` and its synopsis were read for
`S4-R1-03` context. `scripts/portable_promise_machine.py` belongs to the
repository root rather than to a plugin, so it has no skill audit record of its
own.

**The last two merged pull requests on each file.**
`scripts/portable_promise_machine.py` was last changed by
[PR#754](https://github.com/wildcat-finance/skills/pull/754), which published
the model proxy conformance fixtures and extended `PORTABLE_TEST_FILES`, and
before that by `f0e7a394`, the commit that created the packaging script and
carries no pull request. `plugins/horos/skills/horos/scripts/horos.py` was last
changed by [PR#752](https://github.com/wildcat-finance/skills/pull/752) in two
commits, `43161db3` and `fdd8221a`, both about conformance corpus and canonical
JSON comparison. Neither pull request body carries a `## Carried forward`
section; #754 has What changed, Why, Audit, Proof and Stack, and #752 has What
changed, Review and Proof. So the unfinished work bearing on this topic is
written in the #329 audit record rather than in either of those bodies.

**The sibling issue.** [#842](https://github.com/wildcat-finance/skills/issues/842)
records two other ways the boundary and the tree disagree: the boundary holds
no `audit/` entry while the synopsis files accumulate, and `scan --write`
rewrites `counts.files_walked` inside a run worktree while every entry stays
identical. Issue #854 says plainly that whether these want one fix "is worth
deciding together". That is an ambiguity, and the reading I chose is recorded
in item 3 rather than resolved silently.

**What already exists in the code.** `resolve_universe` in `horos.py` already
takes `include_untracked` and already emits a `tracked+untracked` label, and
`drifted_paths` in `tests/test_boundary_currency.py` already keys off that
label. `portable_promise_machine.py` already carries `_git_environment()`,
which strips `GIT_DIR`, `GIT_INDEX_FILE`, `GIT_WORK_TREE` and six more before
every git call. That helper exists because git exports those into any process
it spawns, and it is what makes a git write from inside this script safe to
consider at all.

**Found by executing rather than reading.** The current mirror on `main` is
already not import-closed. Resolving all 265 relative Solidity imports across
the mirror's 88 `.sol` files leaves two unresolved, both in
`plugins/horos/examples/fixture-sol/Market.sol`: `./interfaces/IERC20.sol` and
`./libraries/MathUtils.sol`. Neither target exists in the canonical source
either. `Market.sol` is a single-file fixture for the Solidity outline
extractor and its imports were never meant to resolve. A closure check written
the obvious way would go red on the tree it shipped with, which decides the
design in item 4.

## 3. Constraints and non-goals

**Starting ref.** `4fe374dd33d43b86d800abe9240d62e09ed7d395`, the tip of
`origin/main` at the time the run branch `fiat/854-stage-the-portable-sync-before-the-horos-sca`
was cut. The study, the runbook and the branch agree about where this began.

**Toolchain.** Python 3 as pinned in `.python-version`, standard library only,
`unittest` through `python3 plugins/hexaemeron/tests/run_tests.py` and
`python3 -m unittest discover -s tests`. No new dependency.

**Non-goals.**

- The two mechanisms in #842. They are a different disagreement between the
  boundary and the tree: there the walk counts paths the committed universe
  excludes, here the sync creates paths the walk cannot yet see. The reading I
  chose is that #854 ships on its own and #842 stays open, because the fix for
  one does not touch the other's cause. If the maintainer wants them decided
  together, that is a reason to hold this run, not a reason to widen it.
- Changing the committed boundary's universe to `tracked+untracked`. The
  `resolve_universe` docstring says the tracked default exists "so local build
  products and caches never contaminate a committed boundary", and widening it
  would put every untracked scratch file in a working tree into the boundary.
- Advancing the Horos frontier. Its ledger is `open` and its held next job is
  the content-addressed object rule. This run is not that job, so it records no
  ledger row and changes no version, per the versioning contract.
- Resolving absolute or remapped Solidity imports, or Python imports, in the
  closure check. The observed defect is relative imports between mirrored
  sources, and that is the surface the check covers.
- Making `Market.sol` resolve. Its imports are fixture decoration and stay as
  they are.

## 4. Design options

The two defects are separable and want different fixes, so the options are
listed per defect.

**For the ordering defect.**

*Option A: `sync` stages exactly the mirror paths it wrote.* After the atomic
replace, run `git add -A -- .agents/skills/promise-machine/runtime` through the
existing `_git_environment()`, skipping without complaint when the root is not
a git work tree. The following scan then walks an index that already holds the
mirror. Trade: `sync` gains a write to the git index, which is a side effect
its name does not advertise, and a caller running it in a dirty tree finds
mirror paths staged that they did not stage.

*Option B: `scan` refuses when an untracked file would classify.* Loud, local
and immediate. Trade: it fires in every working tree that holds an untracked
file under a classified path, which is most of them during ordinary work, and a
gate that fires constantly is a gate people learn to pass with a flag.

*Option C: document the alternation loop.* Trade: the issue rejects this in its
own words, and it is right to. The failure is silent locally and loud in CI,
which is the wrong way round for a generated artefact; a document does not move
the signal.

**Chosen for the ordering defect: A.** It is the smallest change that makes the
obvious order correct, it puts the repair at the tool that created the
discrepancy, and the machinery that makes it safe is already in the file. B
buys a louder failure at the cost of a gate that cries wolf, and C leaves the
defect in place.

**For the closure defect.**

*Option D: fail on any unresolved relative import in the mirror.* Trade: it goes
red on `main` today, because of `Market.sol`'s two decorative imports. Closing
that needs either an exclusion list, which rots, or an edit to a fixture whose
imports are deliberately dangling.

*Option E: compare closure in the mirror against closure in the source.* For
each relative import in a mirrored file, resolve the target in both trees. Fail
only when it resolves in the canonical source and not in the mirror. Trade: it
says nothing about a source that was already not closed, so a genuinely broken
source import stays invisible to this check.

**Chosen for the closure defect: E.** It states the property the mirror
actually owes, which is that mirroring loses nothing, rather than a property the
source does not hold. It needs no exclusion list, it is green on the current
tree by construction, and it fails exactly the case #329 hit, where
`HonestAccessHook.sol` resolved `./IRoleProvider.sol` in the source and not in
the mirror. What E gives up is named in item 11: a source import that resolves
nowhere is out of its reach, and `Market.sol` is the standing example.

## 5. Risk register seed

The audit loop should look hardest at the git write this run introduces, since
that is the only new boundary, and at whether the closure check can be made to
walk somewhere it should not. `_git_environment()` already covers the inherited
environment, so the concern is what the new call does with a path rather than
what git was told about the repository. The two count fields in the boundary
are in the register because #842 records them moving on their own, and this run
must not be the thing that makes them move.

```risk-register
index-write-scope | the git add sync performs after replacing the mirror | the pathspec is the mirror directory alone and no other path is staged, proved against a tree with unrelated unstaged changes
index-write-environment | the environment of the new git call | the call goes through _git_environment(), so an inherited GIT_INDEX_FILE or GIT_DIR cannot redirect it to another repository's index
non-repository-root | sync run where .git is absent or the root is not a work tree | staging is skipped and sync still exits 0, so a copy-mode install can still regenerate its runtime
import-target-traversal | the relative import targets read out of mirrored Solidity sources | a target containing .. or an absolute path is refused rather than resolved, and no read escapes the mirror or the source root
partial-write | the mirror directory while sync replaces it | sync keeps its temporary-directory-then-replace construction, and a killed run leaves either the old mirror or the new one and never a half-written tree
boundary-counts-churn | counts.files_walked and counts in the committed boundary | this run leaves both fields moving exactly as they already do and adds no new source of churn, which is issue 842's surface and not this one's
closure-check-cost | the closure pass over the mirrored sources | the check stays a bounded read of files already on disk and adds no subprocess and no network call
```

## 6. Glossary seeds

- **Mirror.** The generated tree under `.agents/skills/promise-machine/runtime/`
  that makes a copy-mode Agent Skills install dependency-closed.
- **Canonical source.** The repository file a mirrored file was copied from,
  named in the `source` field of each `MANIFEST.json` row.
- **Universe.** The file set a Horos scan covers. `tracked` means the git index,
  `tracked+untracked` adds untracked-but-not-ignored files, and `filesystem` is
  the fallback when git cannot answer.
- **Boundary.** `.horos/boundary.json`, the committed classification agents read
  before deciding what to read.
- **Import closure.** The property that every relative import in a mirrored
  source resolves to a file inside the mirror.
- **Differential closure.** The weaker property this run checks: every relative
  import that resolves in the canonical source also resolves in the mirror.

## 7. Sources

- `scripts/portable_promise_machine.py`, whole file, at `4fe374dd`.
- `plugins/horos/skills/horos/scripts/horos.py`, `resolve_universe` and
  `scan_tree`, lines 579 to 640.
- `tests/test_boundary_currency.py`, `drifted_paths` and the guard-mutation
  cases, lines 1 to 190.
- `audit/rounds/fiat-329-janus-resolve-the-manifest-s-permitted-effec.synopsis.md`,
  step 4 round 1 and step 6 rounds 1 and 2.
- `AGENTS.md` lines 150 to 157, the sentence that names the sync obligation.
- Issues [#854](https://github.com/wildcat-finance/skills/issues/854) and
  [#842](https://github.com/wildcat-finance/skills/issues/842).
- Pull requests [#754](https://github.com/wildcat-finance/skills/pull/754) and
  [#752](https://github.com/wildcat-finance/skills/pull/752).

## 8. Signals, and the questions behind them

Both tools are commands a person or a CI job runs from a terminal and reads the
exit code of. Neither becomes a daemon, so the on-call questions are about a
failed run rather than about a running system. Two are worth answering, and
both are answered by what the failing command prints. Ephoros owns what a
signal must carry.

- *Which file broke closure, and what did it want?* The closure failure names
  the importing mirrored file and the import target it could not resolve, so
  the reader does not have to reproduce the walk. Step 3 emits this.
- *Did sync stage anything, and what?* When staging is skipped because the root
  is not a git work tree, sync says so rather than staying silent, so a copy-mode
  user does not read a successful sync as a staged one. Step 2 emits this.

## 9. Boundaries, per capability

Phylax owns the boundary list and the controls.

- **A write to the git index, opened by step 2.** What is worth taking here is
  the pathspec and the environment. The controls are a fixed pathspec naming the
  mirror directory alone, no shell, the existing `_git_environment()` on the
  call, and a skip rather than a failure when git cannot answer.
- **Reading import targets out of mirrored sources, opened by step 3.** The
  target string comes from a file in the repository, which is not hostile input
  in the usual sense, but it is still a path from a file deciding what gets
  opened. The control is that a target with a `..` segment or an absolute form
  is refused rather than resolved, and every resolution stays under the mirror
  root or the source root.
- **No new boundary is opened anywhere else.** No network, no subprocess beyond
  the one git call, no credential, no temporary file outside the construction
  `sync` already uses.

## 10. The budget, or its absence

None, and here is why. Neither change is made in the name of speed and neither
claims a performance improvement, so Metron's refusal does not bite. The
closure check adds a bounded pass over files already read from disk, and the
staging call adds one git invocation to a command that already runs several.
Step 3 records the wall-clock of `check` before and after as a courtesy, so a
later run has a number to compare against, but no budget gates this run and
none is proposed.

## 11. The fail-closed posture

Elenchus owns the triage order and the guard rule.

What stops the run: any failure of `python3 plugins/hexaemeron/tests/run_tests.py`
or `python3 -m unittest discover -s tests`, a non-zero
`portable_promise_machine.py check`, a non-zero `horos.py check .`, or a
`git diff --check` failure. A step whose exit command does not pass is not
finished, and the receipt refuses it.

The guard convention: every fix committed in an audit round arrives with a test
that fails against the tree before the fix and passes after it. For the two
defects here, that means a case that reproduces the stale boundary without the
staging change, and a case that builds a mirror missing an imported sibling and
requires `check` to refuse it. A fix without such a test is not a fix, it is a
hope.

What this run cannot catch, stated so nobody reads more into a green check than
is there: differential closure says nothing about an import that resolves in
neither tree. `Market.sol` holds two of those today and will still hold them
when this run lands.

## 12. Decisions and their homes

Hypomnema owns which decisions earn a record and where each one lives.

- **That `sync` writes to the git index.** This is expensive to reverse, because
  callers begin to depend on the mirror being staged after a sync. It earns a
  decision record under `docs/decisions/`, numbered at merge rather than now,
  per the repository's current practice.
- **That closure is checked differentially against the source rather than
  absolutely.** This one is expensive to reverse in the other direction: a later
  reader who wants absolute closure has to understand why the weaker property
  was chosen, and `Market.sol` is the reason. It goes in the same decision
  record, since it is the same run's answer to the same question about what a
  generated mirror owes.
- **Everything else stays in the code.** The pathspec, the skip-when-not-a-repo
  behaviour and the traversal refusal are explained by a comment at the site
  that needs them, not by a document.

## Boundaries the study states

**Always.** Both suites before a commit. The imprimatur lint on every shipped
document. `portable_promise_machine.py check` and `horos.py check .` before any
push, alternated until they agree, until step 2 makes the alternation
unnecessary.

**Ask first.** Adding a dependency. Changing the boundary's universe. Touching
CI. Widening what `sync` stages beyond the mirror directory. Editing a fixture
whose imports are deliberately unresolved.

**Never.** Commit key material. Edit the mirror by hand. Delete or weaken a
failing test to make a suite pass. Claim a command ran when it did not. Change a
skill version or an `EVOLUTION.md` row in a run that advances no frontier.
