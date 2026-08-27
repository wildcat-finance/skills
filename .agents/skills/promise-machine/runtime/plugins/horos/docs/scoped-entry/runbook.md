# Scoped entry, the runbook

| Module id | Responsibility | Depends on |
| --- | --- | --- |
| change-scaffold | pin the ref, commit study and runbook, add failing fixtures | none |
| tracked-universe | a directory with no tracked file is not a hard entry | change-scaffold |
| boundary-currency | root-suite guard that the committed boundary matches a fresh tracked scan | tracked-universe |
| scoped-entry | ancestor resolution and subtree comparison | boundary-currency |
| demonstration | prove the entry discipline end to end and release | scoped-entry |

Build order: change-scaffold, tracked-universe, boundary-currency, scoped-entry,
demonstration.

## Step 1: Scaffold the change

**Goal.** Commit this study and runbook, pin the run ref, and add the failing
fixtures for criteria 4, 5, 6 and 7 without changing runtime behaviour.

**Entry.** `main` at the Fiat run ref, expected to descend from `496f7a1`.
Suites green: horos 176, root 34.

**Exit.** Study and runbook committed under `plugins/horos/docs/scoped-entry/`. Proved by:
`python3 -m unittest discover -s tests` passes, including a scaffold test that
asserts the committed runbook's five module ids and fourteen criteria against
this document; `python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
passes with the four new fixtures present and marked `expectedFailure`, so the
tree stays green at both ends and each fixture still records the failure it
guards; `python3 plugins/horos/tests/benchmark_scope.py --root . --scope plugins/alexandria --runs 5`
writes the entry medians and claims no improvement.

**Files.** `plugins/horos/docs/scoped-entry/study.md`,
`plugins/horos/docs/scoped-entry/runbook.md`,
fixtures under `plugins/horos/tests/fixtures/`, `plugins/horos/tests/benchmark_scope.py`.

**Tests.** Extend the scaffold and prose-contract tests so the study, runbook and
module ids agree. No existing test weakened or skipped.

**Disciplines.** metron: the entry medians are the baseline every later claim is
measured against. hypomnema: the one-boundary scoped semantics are expensive to
reverse. ephoros: the benchmark output needs named counters. phylax: fixtures
carry untrusted paths. elenchus: two of the four fixtures encode failures the
audit record already produced.

## Step 2: A hard entry must cover a tracked file

**Goal.** Stop the classifier emitting hard directory entries that hold no
tracked file, so `check` answers the same on every machine.

**Entry.** Step 1's green exit. `check .` exits 1 with 7 drifted paths, 6 of
them ignored local directories.

**Exit.** No scan emits a phantom entry, and step 1's fixtures for criteria 4
and 5 pass with their markers removed, so a checkout carrying an ignored build
directory exits 0; census attribution is unchanged for every entry that does
cover tracked files. The count depends on the checkout rather than the
repository: a pristine clone produces 87 hard entries either side of the fix,
because it carries no ignored build products, while the maintainer's own
checkout produced 93 with six binding nothing, five under a stale worktree
under `.claude/worktrees/` and one at `plugins/pandects/out/`. That difference
is the defect, so the fixture rather than a repository count is the criterion.
This repository's own `check .` still exits 1 at this step, for the tracked
evidence copy the committed boundary predates, and step 3 owns that refresh.

**Files.** `plugins/horos/skills/horos/scripts/horos.py`, classifier tests,
fixtures, and `.horos/boundary.json` only if a real entry changed.

**Tests.** Untracked directory with a vendored name; untracked directory with a
corroborating sample; a directory with one tracked and several untracked files,
which must still bind; a `.gitattributes`-matched directory holding nothing
tracked; the filesystem-fallback path when git is absent, which must stay
fail-open.

**Disciplines.** elenchus: this is the failure in hand, and the fixture must fail
without the fix. metron: the walk changes, so re-measure `check .`. phylax: the
tracked-universe subprocess is the boundary being relied on. ephoros: the scan
counters must distinguish walked from bound. hypomnema: "a hard entry covers at
least one tracked file" is a rule worth recording beside the classifier.

## Step 3: Guard boundary currency

**Goal.** Make the recurrence from 18 August impossible to land silently: a
tracked generated file committed without a boundary refresh must fail the root
suite.

**Entry.** Step 2's green exit and a repository whose `check .` exits 0.

**Exit.** A root-suite test compares the committed boundary with a fresh
tracked-only scan and fails on any difference; mutation proves it bites by
adding a generated file and by deleting one entry; the current
`plugins/horos/docs/evidence/skills.boundary.json` drift is resolved by
refreshing the boundary in this step; both suites pass.

**Files.** `tests/` guard test, `.horos/boundary.json`, `.horos/candidates.json`,
`.horos/census.json`.

**Tests.** The guard itself, plus the two mutations, plus a determinism case
proving two consecutive scans render byte-identical documents.

**Disciplines.** elenchus: the guard is the fix for a failure that already
recurred once. ephoros: the failure message must name the paths and the
refresh command. metron: none, no performance claim in this step. phylax:
`.horos` writes stay atomic. hypomnema: none, the decision is already recorded
by the guard's existence.

## Step 4: Ancestor-resolved scoped checks

**Goal.** `check <descendant>` answers whether that subtree's hard boundary is
current, using the one ancestor boundary.

**Entry.** Step 3's green exit and a boundary that matches the tree.

**Exit.** Root and descendant invocations select the same boundary root;
in-scope hard drift exits 1 naming each path; sibling hard drift and candidate
drift print without refusing the scope; missing, malformed or escaping ancestry
exits 2; the selected root, scope and unevaluated-global line print on every
run; criteria 7 through 12 pass.

**Files.** `horos.py`, scope tests, CLI help, `SKILL.md`, `plugins/horos/README.md`,
`plugins/horos/examples/scoped-entry/`.

**Tests.** Invocation from root and from the descendant; nearest valid ancestor
when two exist; `..` escape; symlink escape; missing boundary; malformed
boundary; empty scope; scope equal to root; a scope overlapping a directory
entry; in-scope add, remove and change; sibling-only drift; candidate-only
drift; byte-identical output across both invocation sites.

**Disciplines.** phylax: ancestor discovery and canonicalisation cross the
filesystem boundary. ephoros: a local pass must name its scope and refuse the
global implication. metron: prove zero tracked files inspected outside scope and
record the medians. elenchus: every path-resolution failure found gets a
fixture. hypomnema: exit-code meanings and the no-global-claim rule are recorded
in the contract.

## Step 5: Demonstrate and release

**Goal.** Run the whole discipline from inside a skill directory, reconcile every
release surface, and close the generation entry.

**Entry.** Step 4's green exit.

**Exit.** All 14 criteria pass; the scoped-entry example runs from a clean
checkout with pinned output; horos and root suites, phylax, ephoros, imprimatur,
the five-run benchmark, `check .`, version consistency and `git diff --check`
are green; the ledger row reads `horos-v9.3.3` with the frontier line and its
digest byte-identical; the receipt names the exact commands and their output.

**Files.** `plugins/horos/examples/scoped-entry/README.md`,
`plugins/horos/skills/horos/SKILL.md`, `EVOLUTION.md`,
`plugins/horos/README.md`, plugin and marketplace version surfaces, and the root
`.horos` artefacts only if the final scan changes them.

**Tests.** No new implementation test. Run everything above and assert the
example's pinned output.

**Disciplines.** ephoros: the receipt carries scope, drift, counters and the demo
result. hypomnema: the release prose and the ledger row carry the settled
semantics. metron: final medians against step 1. elenchus: no new failure in
hand; every earlier guard stays green. phylax: the final boundary write is the
last filesystem boundary to check.

## Later, not this run

- Three `.gitattributes` lines binding about 9.3 MB of the 9.43 MB JSON weight
  at hard grade, in `plugins/alexandria/examples/compound-v3-phase0-v0/input/responses`,
  `plugins/tabularium/examples/goldfinch-v0` and `plugins/horos/docs/evidence`.
- A JSON structure map, if the maintainer wants it inside this run instead.
- The held frontier job: marker self-exclusion, then the content-addressed rule
  receipt, then the Markdown outline extractor.
