# Scoped entry, the study

State: assumptions confirmed by the maintainer on 2026-08-20. Ready for Fiat.

Evidence ref: `main` @ `496f7a1`. Every number below was measured on that ref
in this working copy. No repository file was changed to produce this document.

Revision 2 replaces the Codex draft of the same topic. It keeps that draft's
design conclusion and discards three things: the marker self-exclusion fix, the
Markdown outline extractor, and a success criterion whose command does not run.

## Assumptions

Confirmed, not assumed, as of 2026-08-20:

1. The repository root stays the single boundary authority. An agent may begin
   below it.
2. "Check on entry" checks only the subtree being entered. Drift elsewhere is
   reported and does not block that subtree.
3. `.horos/candidates.json` stays advisory and never binds an agent.
4. Markdown and JSON are never excluded by file extension.
5. Generation axis. `marker-self-exclusion` stays the held frontier target,
   untouched. This run builds scoped entry plus two guards.

Assumption 5 sets the version arithmetic. Under
`plugins/hexaemeron/skills/VERSIONING.md`, generation is the second
number, so the label moves `horos-v9.2.3` to `horos-v9.3.3`, and the row must
retain the frontier revision and the SHA-256 of
`{status}|{frontier revision}|{current frontier}|{next Fiat job}` byte for byte.
The consequence is that no line of the held frontier text may change: scoped
entry is described in the history row's Change column, nowhere else in the
ledger.

## Proposition

`horos check <path>` accepts the repository root or any descendant. It walks
upward to the nearest `.horos/boundary.json`, stops at the Git worktree root,
treats that directory as the boundary root, freshly classifies only `<path>`,
and compares that result with the slice of the committed hard boundary under
`<path>`.

```text
boundary root: /Users/…/skills
scope: plugins/alexandria
hard boundary: matches
candidates: 3 findings, advisory
outside-scope drift: not evaluated
```

Exit 0 admits the scope. Exit 1 means hard drift inside the scope. Exit 2 means
no usable ancestor boundary, or a path that escapes the worktree. Candidate
drift never changes the exit code.

Two guards ship with it, because a gate that answers differently on each
machine cannot admit anything:

- **G1, tracked universe.** A directory holding no tracked file must not become
  a hard entry.
- **G2, boundary currency.** Committing a tracked generated file, including a
  copy of a boundary or an evidence document, must not leave `check` dirty.

## 1. Problem statement

**What is being built.** Scope awareness for the Horos boundary check, plus the
two guards that make its answer reproducible.

**For whom.** An agent working inside one skill of `wildcat-finance/skills`
that wants to know whether the boundary covering that subtree is current,
without paying for a whole-repository answer and without a boundary file of its
own.

**What a working prototype means here.** From `plugins/alexandria`, one command
answers the admission question against the root boundary, and the same command
from the repository root gives a byte-identical scoped answer. The demo path is
`plugins/horos/examples/scoped-entry/README.md`, run by the last step and
asserted by the plugin suite.

## 2. Prior art

**In Horos.** `plugins/horos/skills/horos/SKILL.md` already requires a checked
boundary, splits hard evidence from candidates, and suspends the boundary during
security review. `plugins/horos/skills/horos/scripts/horos.py` carries `scan`,
`check` and `map`. `check` resolves `.horos/boundary.json` relative to its own
argument, which is the gap: `check plugins/alexandria` exits 2 today.
`docs/refinement/maintainer-spec.md` supplies the two-tier model this keeps.

**In the audit record.** `audit/AUDIT.md` holds 186 rounds, of which 38 are
Horos runs carrying one finding: an implement receipt that asserted a green
suite over a red one (Refinement run, step 2, round 1). No Horos round has ever
returned a classifier finding. Every real failure in this plugin's history has
been artefact reconciliation, and the record names two: `check` flagging the
marking evidence copies as new sinks, refreshed by hand in the close commit
(Marking run, step 4, round 1), and a stale skills count in the same bundle.
The first of those recurred on `496f7a1` because no guard was written. That is
the whole case for G2.

**Outside.** Git's directory-scoped attributes remain the maintainer-owned
classification route, and `linguist-generated` or `linguist-vendored` already
binds at hard grade. Content-addressed stores supply stronger evidence, because
the digest of the bytes can be recomputed from the path's claim.

## 3. Constraints and non-goals

**Constraints.**

- Starting ref `496f7a1` on `main`. Fiat replaces this with its own run ref.
- Python standard library and `unittest`. No new dependency.
- One committed boundary per repository. A scoped check is a comparison, not a
  new artefact.
- Classification stays fail-open. An unproved file stays readable.
- Generation axis: the frontier revision, current frontier and next job stay
  byte-identical, and their recorded SHA-256 must still verify.
- The security-review exception is untouched.
- The instruction chain from the repository root down to the working directory
  is read even when the agent starts below the root.

**Non-goals.**

- The marker self-exclusion fix. That is the held frontier job and stays with it.
- The Markdown outline extractor. Also named in the held frontier order.
- A JSON structure map. Deferred; ask the maintainer to pull it in if wanted.
- Promoting the three JSON-heavy directories through `.gitattributes`. Separate,
  needs no code, listed under Later.
- Nested `.horos` directories.
- Caching. The measured full check is 0.11 s, so invalidation would cost more
  than it saves.
- Any change to what happens during a security review.

## 4. Design options

**A. A boundary inside every skill.** Each skill checks independently with no
ancestor discovery. Cost: several authorities over overlapping files, unclear
precedence, and routine drift whenever a shared rule changes. Rejected.

**B. Run the repository-wide check on every directory entry.** No scanner
change, 0.11 s per call. Cost: unrelated drift blocks a local task, and the
answer never names the scope the agent asked about. Useful as an interim
discipline, wrong as the interface. Rejected.

**C. Resolve one ancestor boundary, check the requested scope.** One authority,
an answer about the files the agent is about to read. Chosen.

**D. Make candidates a second binding boundary.** Suppresses more bytes at once,
and lets filename geometry hide source. Rejected: promotion means adding
evidence or a maintainer attribute, never editing `candidates.json`.

**Chosen, and what it gives up.** C gives up the global claim. A green scoped
check says nothing about sibling directories, and the output must say so in
those words. `check <root>` stays the release-time answer.

## 5. Risk register seed

Ordered by what this plugin's audit history has actually produced, not by what
sounds dangerous.

- **Artefact reconciliation.** Boundary, candidates, census, evidence copies,
  ledger row and README counts drifting out of step. Every Horos failure on
  record is this. Control: G2 as a root-suite test with a mutation proving it
  bites, and one regeneration command named in the runbook.
- **Machine-dependent classification.** Ignored local directories entering the
  fresh scan. Control: G1, plus a fixture holding an untracked directory.
- **Ancestor confusion.** A nested or planted `.horos` selected instead of the
  repository's. Control: stop at the Git worktree root, reject a boundary
  outside it, print the selected root before classifying.
- **Path escape.** `..`, symlinks or case differences moving the scope outside
  the root. Control: canonicalise both paths, never follow symlinks, reject a
  scope that is not a descendant.
- **False local confidence.** A green scoped check read as a global one.
  Control: `outside-scope drift: not evaluated` in the output, and the release
  check stays separate.

## 6. Glossary

- **Boundary root.** The directory owning the `.horos/boundary.json` used for a
  request.
- **Working scope.** The descendant tree an agent is about to read.
- **Admission check.** A fresh comparison of hard evidence inside the working
  scope.
- **Hard entry.** A path excluded by reproducible evidence.
- **Candidate.** A weak signal, reported, never binding.
- **Phantom entry.** A hard entry covering no tracked file. G1 removes these.

## 7. Sources

- `AGENTS.md`, in particular the canonical suite commands at line 81
- `.horos/boundary.json`, `.horos/candidates.json`, `.horos/census.json`
- `plugins/horos/skills/horos/SKILL.md`, `EVOLUTION.md`, `scripts/horos.py`
- `plugins/horos/docs/refinement/maintainer-spec.md`
- `plugins/hexaemeron/skills/VERSIONING.md`
- `audit/AUDIT.md`: Refinement run step 2 round 1; Marking run step 4 round 1;
  Census run step 2 round 1
- Commit `5d5aba7`, the content-addressed object rule
- Commit `496f7a1`, the ref this document measures

## 8. Signals, and the questions behind them

Contract: `plugins/hexaemeron/skills/ephoros/SKILL.md`.

1. Which boundary root and scope did Horos select? Both canonical paths print
   before classification.
2. Why was admission refused? Each hard-drift path prints with its direction,
   added or removed.
3. What did the check cost, and did it stay inside the scope? The output carries
   files walked and tracked files inspected outside the scope, which must be
   zero.
4. What was left unresolved? Candidate count prints separately from hard drift.

No alerting: this is an interactive command, and its exit status plus bounded
stdout are the signal.

## 9. Boundaries, per capability

Contract: `plugins/hexaemeron/skills/phylax/SKILL.md`.

| Capability | Boundary opened | Worth taking | Control |
| --- | --- | --- | --- |
| ancestor resolution | filesystem paths, repository metadata | selecting a planted boundary, escaping the worktree | canonical descendant check, worktree stop, no symlink following, selected paths printed |
| tracked universe | one fixed `git ls-files` invocation | hostile path, unexpected output | fixed argv, no shell, pinned directory, fail-open filesystem fallback |
| boundary read | untrusted JSON in the repository | malformed or oversized document | schema check, bounded read, named refusal |
| artefact regeneration | `.horos` writes | half-written boundary | atomic replace, hard evidence only, root check before commit |

## 10. Budget

Contract: `plugins/hexaemeron/skills/metron/SKILL.md`.

Baseline on `496f7a1`:

```text
/usr/bin/time -p python3 plugins/horos/skills/horos/scripts/horos.py check .
real 0.11
```

Claims to hold:

- A scoped check inspects zero tracked files outside its scope. This is the
  criterion, not wall-clock.
- The recorded median of five warm scoped checks of `plugins/alexandria` is
  reported beside the five-run full-tree median. Numbers are recorded; no
  machine-specific threshold is asserted in a test.

Measurement command, supplied by step 3:

```text
python3 plugins/horos/tests/benchmark_scope.py --root . --scope plugins/alexandria --runs 5
```

Precedent for dismissing a cost lead with a measurement rather than a change is
Census run, step 2, round 1.

## 11. Fail-closed posture

Contract: `plugins/hexaemeron/skills/elenchus/SKILL.md`.

Refuse admission when the path is absent, escapes the worktree, has no usable
ancestor boundary, carries an unreadable or unsupported boundary document, or
holds hard drift inside the scope. Do not refuse for candidate drift or for hard
drift outside the scope, and say which of those two conditions applied.

Every fix carries a test that fails without it. Two are already owed by the
record: the phantom-entry class, and the evidence-copy recurrence that this loop
caught on 18 August and did not guard.

## 12. Decisions and their homes

Contract: `plugins/hexaemeron/skills/hypomnema/SKILL.md`.

- One root boundary with scoped views: `plugins/horos/docs/study.md` and the
  skill contract.
- A green scoped check makes no global claim: CLI help, `SKILL.md`, the example.
- A hard entry must cover at least one tracked file: the classifier rationale
  beside the rule.
- Exit-code meanings: `SKILL.md`, and a decision record under
  `plugins/horos/docs/decisions/` if any of them ever changes.

## Always, ask first, never

**Always.** Both suites before every commit, by the canonical commands at
`AGENTS.md:81`. Phylax and ephoros over changed Python. Imprimatur over shipped
prose. A root-wide `check .` before committing a regenerated boundary. Each step
green at entry and exit.

**Ask first.** Add a dependency. Change the boundary schema or the meaning of an
exit code. Add caching or persistent state. Touch CI. Promote a
repository-specific candidate without a portable rule. Read whole files outside
digest verification.

**Never.** Bind an agent to `candidates.json`. Exclude Markdown, JSON or JSONL
by suffix. Follow a symlink outside the selected root. Execute or import code
from the scanned repository. Apply a boundary during a security review. Create a
nested boundary to make a local check pass. Delete or weaken a failing test to
clear a step. Claim a command ran when it did not. Change the held frontier text
in this run.

## Success criteria

1. `python3 -m unittest discover -s plugins/horos/tests -t plugins/horos` passes,
   at least the 176 tests present at entry plus the new cases.
2. `python3 -m unittest discover -s tests` passes, at least 34 tests.
3. The phylax, ephoros and imprimatur commands named by `AGENTS.md` run clean
   over every changed file.
4. A fixture tree holding an ignored directory with no tracked file produces no
   hard entry for that directory.
5. `check .` exits 0 on a clean tracked checkout, on a machine that also holds
   an ignored build or worktree directory.
6. A root-suite guard fails when a tracked generated file is committed without
   refreshing the boundary, and passes once refreshed. Proved by mutation.
7. `check plugins/alexandria` exits 0 and prints the selected boundary root, the
   scope, and `outside-scope drift: not evaluated`.
8. Running that check from the repository root and from inside
   `plugins/alexandria` produces byte-identical canonical output.
9. A hard mutation inside `plugins/alexandria` exits 1 and names the path. The
   same mutation in a sibling directory leaves the Alexandria check at exit 0.
10. Candidate-only drift inside the scope exits 0, prints, and never enters the
    hard boundary.
11. A missing ancestor boundary, a malformed boundary, a path outside the
    worktree and a symlink escape each exit 2 with a named reason.
12. `benchmark_scope.py` records five-run medians and reports zero tracked files
    inspected outside the scope.
13. The ledger reads `horos-v9.3.3` on the generation axis, the frontier
    revision and its SHA-256 are byte-identical to `horos-v9.2.3`, and
    `tests/test_evolution_contract.py` passes.
14. `plugins/horos/examples/scoped-entry/README.md` runs from a clean checkout
    and its pinned output matches.
