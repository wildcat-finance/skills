# Horos, the runbook

Five steps, dependency order, one pull request each. Every step assumes the
exit state of the one before it and nothing else. The study committed beside
this runbook at [study.md](./study.md) is the spec; both documents landed
here in step 1.

Module trace: scaffold, classify, boundary, skeleton, discipline. One
capability, so no decomposition table; the modules are the steps.

## Step 1: Scaffold and register the plugin

**Goal.** `plugins/horos/` exists in the house shape and every marketplace
surface knows about it.
**Entry.** The run branch, cut from `main` at `6168e54`.
**Exit.** `python3 -m unittest discover -s tests -t .` green with the plugin
set now twelve; `python3 -m unittest discover -s plugins/horos/tests -t
plugins/horos` green; phylax and ephoros clean over `plugins tests`;
imprimatur clean on every new document.
**Files.** `plugins/horos/.claude-plugin/plugin.json` and
`.codex-plugin/plugin.json` (repository, homepage, agreed description,
`interface.shortDescription`); `plugins/horos/skills/horos/SKILL.md` with
frontmatter, `version: "0.1.0"` metadata and a link to its ledger;
`plugins/horos/skills/horos/EVOLUTION.md` with a baseline row whose digest
satisfies the evolution contract; `plugins/horos/README.md` carrying
`## In one line` and the rolling Next Fiat job line with the exact prefix and
suffix the prose contract demands; `.agents/skills/horos/SKILL.md` portable
entrypoint; a row in the root `README.md` selection table; the new plugin
entry in `.claude-plugin/marketplace.json`; copies of the study and this
runbook at `plugins/horos/docs/`; `plugins/horos/tests/__init__.py` and
`test_scaffold.py`.
**Tests.** Extend `tests/test_marketplace_prose.py` (the `PLUGINS` tuple,
`CANONICAL_SKILLS`, the landing-README count) and the fixed name list in
`tests/test_portable_skills.py` to include horos; add `test_scaffold.py`
asserting the two host manifests agree with the marketplace entry.

## Step 2: The classifier

**Goal.** One stdlib script that classifies a tree's token sinks with
evidence, reading at most a fixed prefix of any file.
**Entry.** Step 1's exit state.
**Exit.** Plugin suite green; every rule class has at least one positive and
one negative case.
**Files.** `plugins/horos/skills/horos/scripts/horos.py`;
`plugins/horos/tests/test_classify.py`.
**Tests.** Per rule class (binary, lockfile, generated marker, generated
directory, vendored, single-line blob, minified geometry): a file that earns
the entry and a near-miss that stays readable. A symlink pointing outside the
root is never followed. Undecodable bytes never raise. The walk order is
deterministic and `.git` and `.horos` are never scanned. Expected count:
about eighteen.

## Step 3: Boundary emit and check

**Goal.** `scan` writes the committed boundary artefact; `check` re-derives
it and names every drifted path.
**Entry.** Step 2's exit state.
**Exit.** Plugin suite green; `scan` twice over the same tree produces
byte-identical output; `check` exits 0 on a fresh boundary and non-zero on
any mutation, naming the path.
**Files.** `horos.py` extended; `plugins/horos/tests/test_boundary.py`.
**Tests.** Determinism (two scans, byte-identical, sorted paths, no
timestamps, no absolute paths); atomic write (temporary file plus rename);
drift is reported per path; a boundary entry the tree no longer evidences
fails `check` (the poisoned-boundary case); scan output reports files walked,
bytes per category and files skipped. Expected count: about ten.

## Step 4: The skeleton map

**Goal.** `map` prints the signatures, class structure and first docstring
lines of a Python file so the file can be oriented in without being read.
**Entry.** Step 3's exit state.
**Exit.** Plugin suite green; `map` over a fixture module matches its pinned
output; a file with a syntax error produces a report, not a traceback.
**Files.** `horos.py` extended; `plugins/horos/tests/test_map.py`.
**Tests.** Pinned skeleton for a fixture module covering nested classes,
async functions and decorated definitions; the syntax-error path; a
non-Python path is refused with a clear message. Expected count: about six.

## Step 5: The discipline, the example, the demonstration

**Goal.** The SKILL.md teaches the reading discipline, the shipped example
proves the pipeline, and the demo path from the study runs.
**Entry.** Step 4's exit state.
**Exit.** Study success criteria 1 through 4 all pass as written, from the
repo root; imprimatur clean on every shipped document.
**Files.** `plugins/horos/skills/horos/SKILL.md` full text, including the
verbatim rule that no boundary applies during security review;
`plugins/horos/examples/fixture/` with one file per rule class and the
committed expected boundary; `plugins/horos/examples/README.md` documenting
the mutation that makes `check` fail; `plugins/horos/README.md` finished;
`plugins/horos/tests/test_discipline.py`.
**Tests.** The security-review rule is present verbatim in the SKILL.md
(asserted by test so an edit cannot drop it silently); the example fixture's
committed boundary matches a fresh scan byte for byte; the documented
mutation makes `check` exit non-zero. Expected count: about five.
