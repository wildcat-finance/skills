# Runbook: ship the content-addressed object rule

Derived from the receipted study at `.hexaemeron/study.md`. No task issue is
bound. The run branch is
`fiat/ship-the-content-addressed-object-rule-whose-evi`, cut from `main` at
`54730d3a2fe08fa0d0d93f8fa9bcc6d6c3cee27b`. Step 1 branches from the run
branch; every later step branches from the step below it.

A host condition from the study's constraints applies to every suite command
in this runbook: this machine signs commits globally and the test helpers do
not neutralise signing, so each `unittest` invocation below carries
`GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false`,
written `<sign-off>` here for brevity. Expanding it is mandatory; fixing the
helpers instead is an ask-first item and no step here does it.
`<imprimatur.py>` means
`plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`.

The selected design is `harden-record` (study section 4): the rule's binding
condition is unchanged, and the run adds the four guard tests the draft
lacks, the documentation, the evidence bundle, the committed specification
copies, the reconciled marketplace prose and the `horos-v11.3.3` row.

```design-lock
schema | protasis-design-evidence/v1
sha256 | abf112dbcff8508966d2dbdc49ca8bcf5180aa1cabfcefb14841363b84682392
candidate | harden-record
```

## Step 1: Commit the spec copies

**Goal.** Put the receipted study and this runbook where the repository keeps
them, so the branch carries its own specification.
**Entry.** The run branch at `54730d3a2fe08fa0d0d93f8fa9bcc6d6c3cee27b`,
clean tree, both suites green as recorded in the study's constraints (root
1207, horos 235).
**Exit.** `plugins/horos/docs/content-addressed-objects/study.md` and
`plugins/horos/docs/content-addressed-objects/runbook.md` committed, then all
of: `python3 <imprimatur.py> plugins/horos/docs/content-addressed-objects/study.md`
exit 0,
`python3 <imprimatur.py> plugins/horos/docs/content-addressed-objects/runbook.md`
exit 0, `python3 plugins/horos/skills/horos/scripts/horos.py check .` exit 0,
`<sign-off> python3 -m unittest discover -s tests` green, and
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
green (235 tests at this step).
**Files.** `plugins/horos/docs/content-addressed-objects/study.md`,
`plugins/horos/docs/content-addressed-objects/runbook.md`.
**Tests.** None written; the two existing suites are the gate. Elenchus
runner: `<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos 2> {report}`,
report format unittest text output, report file
`.hexaemeron/elenchus-step-1.txt`.
**Disciplines.** hypomnema: the committed spec copies are a record home the
study's section 12 names. phylax: none, documentation only. ephoros: none,
nothing here runs unattended. metron: none, no performance claim. elenchus:
none, no failure in hand.

## Step 2: Pin the rule with guard tests and document it

**Goal.** Add the four guard tests the draft lacks, without changing the
rule's binding condition, and document the rule in the skill and the example.
**Entry.** Step 1's exit tree.
**Exit.** All of, from the repository root:
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
green at 239 tests,
`<sign-off> python3 -m unittest discover -s tests` green,
`python3 plugins/horos/skills/horos/scripts/horos.py check .` exit 0,
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` changing
no tracked byte (checked by `git status --short` printing nothing under
`.horos/`),
`python3 <imprimatur.py> plugins/horos/skills/horos/SKILL.md` exit 0,
`python3 <imprimatur.py> plugins/horos/examples/README.md` exit 0, and the
fixture README's tamper mutation run once by hand: after
`printf x >> plugins/horos/examples/fixture/store/objects/sha256/7d/7d2aa7ee1155c6102a2dbb74ff9efa27115cec234f2ea4555a0d3a92663d7e82`,
`python3 plugins/horos/skills/horos/scripts/horos.py check plugins/horos/examples/fixture`
exits 1 naming that object as drift, and `git checkout -- plugins/horos/examples/fixture/store`
restores it before the commit.
**Files.** `plugins/horos/tests/test_boundary.py` (tamper and unreadable-object
tests; a new `plugins/horos/tests/test_content_addressed.py` instead if the
boundary module proves the wrong home), `plugins/horos/tests/test_classify.py`
(`ContentAddressedTests`), `plugins/horos/skills/horos/SKILL.md` (rule text
only; the frontmatter version and the marketplace-context block wait for
step 3), `plugins/horos/examples/README.md`.
**Tests.** Four written, each observed red against a deliberately broken rule
before it is kept (study section 11): a tampered object under a sharded
store in a disposable git repository is named as drift by `check` with exit
1; an unreadable store object is counted `files_skipped_unreadable` and never
classified, skipping with a named reason when the suite runs as root; a
deeper shard path `objects/sha256/ab/cd/<digest>` stays readable; an
uppercase algorithm segment `objects/SHA256/<xx>/<digest>` stays readable.
Expected count: the horos suite grows from 235 to 239. Elenchus runner:
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos 2> {report}`,
report format unittest text output, report file
`.hexaemeron/elenchus-step-2.txt`.
**Disciplines.** phylax: this step pins the one boundary the rule opens, a
whole-file read of an untrusted path, and its controls (study section 9);
the shape gate, the symlink refusal and the skipped-count edge are asserted,
not widened. elenchus: the guards are observed red first, against a rule
broken on purpose in a scratch copy, and named for the failure each pins.
hypomnema: the rule's reasons stay in the comments above
`CONTENT_ADDRESSED_ALGORITHMS`, `CONTENT_ADDRESSED_PARENTS` and
`DIGEST_CHUNK_BYTES`; the SKILL.md paragraph cites them rather than
restating them. ephoros: none, the drift line and exit code already exist
and this step only proves they fire. metron: none, no code path changes and
the study's section 10 figures are re-measured in step 3, not here.

## Step 3: Write the evidence bundle, reconcile the prose and record the row

**Goal.** Record what the rule binds on this tree and what it costs, cold-read
every mutable first-party marketplace prose surface and reconcile it with the
tree, and write the evolution row that closes the held job.
**Entry.** Step 2's exit tree.
**Exit.** All of:
`plugins/horos/docs/evidence/skills-content-addressed.md` committed, carrying
the store inventory from `.horos/boundary.json` (entries, bytes, the three
store roots), the `store-hash-ms` figure re-measured at this step by
`python3 .hexaemeron/design-reports/resolve.py harden-record store-hash-ms`
and at or under 250 ms, the drift demonstration from step 2, and the three
refused candidates with their measured values;
`plugins/horos/skills/horos/EVOLUTION.md` carrying exactly one new history
row, axis evolution, version `horos-v11.3.3`, frontier revision
`markdown-outline-extractor`, whose held next job is the Markdown outline
extractor exactly as the `horos-v9.2.3` epoch row names it, with maturity
expected after it;
`plugins/horos/skills/horos/SKILL.md` frontmatter at `version: "11.3.3"`;
`<sign-off> python3 -m unittest tests.test_marketplace_prose` green;
`python3 <imprimatur.py> <file>` exit 0 for every prose file this step
touches; `python3 plugins/horos/skills/horos/scripts/horos.py check .` exit 0;
and both suites green:
`<sign-off> python3 -m unittest discover -s tests` and
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`.
**Files.** `plugins/horos/docs/evidence/skills-content-addressed.md`,
`plugins/horos/skills/horos/EVOLUTION.md`,
`plugins/horos/skills/horos/SKILL.md`, and whichever of
`plugins/horos/README.md`, `plugins/horos/AGENTS.md` and the root
marketplace descriptors the cold-read finds trailing the tree; the known
findings are the "still owes its own frontier run" text and the 7,844,971
figure in every marketplace-context block, and the "Start here" debt in the
plugin README (study section 12).
**Tests.** None written; `tests.test_marketplace_prose` and the two suites
are the gate. Elenchus runner:
`<sign-off> python3 -m unittest discover -s tests 2> {report}`, report format
unittest text output, report file `.hexaemeron/elenchus-step-3.txt`.
**Disciplines.** hypomnema: the ledger row, the evidence bundle and the
reconciled blocks are the record homes the study's section 12 names; the
refused candidates are recorded with their measurements so the next run
re-measures rather than re-argues. metron: the section 10 budget is
re-measured here before the bundle claims a cost. phylax: none, prose,
evidence and ledger only. ephoros: none, nothing runs unattended. elenchus:
none, no failure in hand.

## Step 4: Demonstrate the shipped rule

**Goal.** Run the study's demo path end to end at the run head and record the
result.
**Entry.** Step 3's exit tree.
**Exit.** From the repository root, in order, all as stated:
`python3 plugins/horos/skills/horos/scripts/horos.py check .` exit 0 with
`boundary matches the tree`;
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
green at 239 tests;
`printf x >> plugins/horos/examples/fixture/store/objects/sha256/7d/7d2aa7ee1155c6102a2dbb74ff9efa27115cec234f2ea4555a0d3a92663d7e82`
then
`python3 plugins/horos/skills/horos/scripts/horos.py check plugins/horos/examples/fixture`
exit 1 naming that object as drift;
`git checkout -- plugins/horos/examples/fixture/store` restoring the tree;
`<sign-off> python3 -m unittest discover -s tests` green; and
`<sign-off> python3 -m unittest tests.test_marketplace_prose` green. The
transcript lands in the run's audit log
(`audit/rounds/fiat-ship-the-content-addressed-object-rule-whose-evi.md`).
**Files.** `audit/rounds/fiat-ship-the-content-addressed-object-rule-whose-evi.md`
(demo record appended); no source file changes.
**Tests.** None written; the demo path is the gate. Elenchus runner:
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos 2> {report}`,
report format unittest text output, report file
`.hexaemeron/elenchus-step-4.txt`.
**Disciplines.** ephoros: the demo exercises the whole observable surface,
exit codes and the drift line (study section 8). phylax: none, nothing new
opens. metron: none, the budget was settled in step 3. elenchus: none unless
the demo fails, which stops the line. hypomnema: the demo record's home is
the run's audit log.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Tests: Four written, each observed red
against a deliberately broken rule before it is kept (study section 11): a
tampered object under a sharded store in a disposable git repository is named
as drift by `check` with exit 1; an unreadable store object is counted
`files_skipped_unreadable` and never classified, skipping with a named reason
when the suite runs as root; a deeper shard path
`objects/sha256/ab/cd/<digest>` stays readable; an uppercase algorithm segment
`objects/SHA256/<xx>/<digest>` stays readable. Expected count: the horos suite
grows from 235 to 239. Elenchus runner:
`python3 plugins/horos/tests/run_tests.py --elenchus-report {report}`, report
format `unittest-json-v1`, report file `.hexaemeron/elenchus-step-2.json`.
Complete replacement Files: `plugins/horos/tests/run_tests.py` (new; the
plugin-level suite runner that emits the `elenchus.unittest.v1` report, on the
pattern of `plugins/brevitas/tests/run_tests.py`),
`plugins/horos/tests/test_boundary.py` (tamper and unreadable-object tests; a
new `plugins/horos/tests/test_content_addressed.py` instead if the boundary
module proves the wrong home), `plugins/horos/tests/test_classify.py`
(`ContentAddressedTests`), `plugins/horos/skills/horos/SKILL.md` (rule text
only; the frontmatter version and the marketplace-context block wait for
step 3), `plugins/horos/examples/README.md`.
**Why.** Audit finding S1-R1-03: the runbook's `report format unittest text
output` is not a format `elenchus.py --report-format` accepts, so a fix with a
guard test would classify `inconclusive`. The root runner
`tests/run_tests.py` discovers only `tests/`, not the horos suite, so step 2
needs a plugin-level runner for the guard tests it adds.
**Steps touched.** Step 2.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Tests: None written;
`tests.test_marketplace_prose` and the two suites are the gate. Elenchus
runner: `python3 tests/run_tests.py --elenchus-report {report}`, report
format `unittest-json-v1`, report file `.hexaemeron/elenchus-step-3.json`.
**Why.** Audit finding S1-R1-03: `report format unittest text output` is not a
format `elenchus.py --report-format` accepts; the root runner emits the
`elenchus.unittest.v1` report Elenchus parses.
**Steps touched.** Step 3.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Tests: None written; the demo path is
the gate. Elenchus runner:
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`unittest-json-v1`, report file `.hexaemeron/elenchus-step-4.json`.
**Why.** Audit finding S1-R1-03: `report format unittest text output` is not a
format `elenchus.py --report-format` accepts; the root runner emits the
`elenchus.unittest.v1` report Elenchus parses.
**Steps touched.** Step 4.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Goal: Add the four guard tests the
draft lacks, without changing the rule's binding condition, and document the
rule in the example. The skill text moves to step 3, which owns every edit to
`plugins/horos/skills/horos/SKILL.md`. Complete replacement Files:
`plugins/horos/tests/run_tests.py` (new; the plugin-level suite runner that
emits the `elenchus.unittest.v1` report, on the pattern of
`plugins/brevitas/tests/run_tests.py`), `plugins/horos/tests/test_boundary.py`
(tamper and unreadable-object tests; a new
`plugins/horos/tests/test_content_addressed.py` instead if the boundary module
proves the wrong home), `plugins/horos/tests/test_classify.py`
(`ContentAddressedTests`), `plugins/horos/examples/README.md`, and
`.horos/boundary.json` where the new tracked file moves the walk counts.
**Why.** Building step 2 showed that `plugins/horos/skills/horos/SKILL.md` is
bound by whole-file digest in `tests/fixtures/agent-instruction-v1/manifest.json`
(fixture `horos-boundary-check`, reviewed span bytes 11183 to 12201), so any
edit to it reddens 29 root-suite tests until the fixture chain is re-pinned.
Step 3 must edit the same file for the version and the marketplace-context
block, so one re-pin in step 3 replaces two.
**Steps touched.** Step 2.
**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit
holds. Step 4: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Files:
`plugins/horos/docs/evidence/skills-content-addressed.md`,
`plugins/horos/skills/horos/EVOLUTION.md`,
`plugins/horos/skills/horos/SKILL.md` (frontmatter version, the
marketplace-context block, the digest joining the hard-evidence list in rule 4,
and one short paragraph on what the rule reads, why it runs first and what it
refuses, citing the comments in `horos.py`; the reviewed span at bytes 11183
to 12201 of the pre-edit file, the `### horos-boundary-check` promise, stays
byte for byte), whichever of `plugins/horos/README.md`,
`plugins/horos/AGENTS.md` and the root marketplace descriptors the cold-read
finds trailing the tree, and the fixture chain that binds SKILL.md:
`tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/fixtures/agent-instruction-v1/horos-boundary-check/model.json`,
`tests/fixtures/agent-instruction-v1/horos-boundary-check/source-spans.json`,
`tests/fixtures/agent-instruction-v1/horos-boundary-check/compact.wai`,
`tests/fixtures/agent-instruction-v1/evidence/measurement.json`,
`tests/fixtures/agent-instruction-v1/evidence/parity.json` and
`tests/promise_machine_coverage.json`. Complete replacement Exit: All of:
`plugins/horos/docs/evidence/skills-content-addressed.md` committed, carrying
the store inventory from `.horos/boundary.json` (entries, bytes, the three
store roots), the `store-hash-ms` figure re-measured at this step by
`python3 .hexaemeron/design-reports/resolve.py harden-record store-hash-ms`
and at or under 250 ms, the drift demonstration from step 2, and the three
refused candidates with their measured values;
`plugins/horos/skills/horos/EVOLUTION.md` carrying exactly one new history
row, axis evolution, version `horos-v11.3.3`, frontier revision
`markdown-outline-extractor`, whose held next job is the Markdown outline
extractor exactly as the `horos-v9.2.3` epoch row names it, with maturity
expected after it; `plugins/horos/skills/horos/SKILL.md` frontmatter at
`version: "11.3.3"`; the fixture chain re-pinned so that
`python3 scripts/agent_instruction.py check --manifest tests/fixtures/agent-instruction-v1/manifest.json`
prints a `run.summary` with outcome `accepted` and no refused record,
`python3 scripts/promise_machine.py coverage` prints `clean`, the manifest's
`span_sha256` for `horos-boundary-check` is unchanged, and the re-pin carries
the recorded token counts and parity responses unchanged and says so in the
run's audit record; `<sign-off> python3 -m unittest tests.test_marketplace_prose`
green; `python3 <imprimatur.py> <file>` exit 0 for every prose file this step
touches; `python3 plugins/horos/skills/horos/scripts/horos.py check .` exit 0;
and both suites green: `<sign-off> python3 -m unittest discover -s tests` and
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`.
**Why.** `plugins/horos/skills/horos/SKILL.md` is bound by whole-file digest
in the agent-instruction fixture manifest, and its reviewed span's offsets
enter the corpus digest, so an edit before the span stales both evidence
records. Step 3 already owes the version and marketplace edits to that file,
so it takes the rule paragraph from step 2 and the one re-pin the run needs.
The carried re-pin is the procedure the repository used on 2026-09-04, and it
is honest because the reviewed bytes do not move.
**Steps touched.** Step 3.
**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit
holds. Step 4: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Files:
`plugins/horos/docs/evidence/skills-content-addressed.md` (a final section,
"Demonstration at the run head", carrying the demo path transcript verbatim),
`.horos/boundary.json` where the appended bytes move the walk counts, and
`audit/rounds/fiat-ship-the-content-addressed-object-rule-whose-evi.md`
(the round record carries the same transcript); no source file changes.
Complete replacement Exit: From the repository root, in order, all as stated:
`python3 plugins/horos/skills/horos/scripts/horos.py check .` exit 0 with
`boundary matches the tree`;
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
green at 239 tests;
`printf x >> plugins/horos/examples/fixture/store/objects/sha256/7d/7d2aa7ee1155c6102a2dbb74ff9efa27115cec234f2ea4555a0d3a92663d7e82`
then
`python3 plugins/horos/skills/horos/scripts/horos.py check plugins/horos/examples/fixture`
exit 1 naming that object as drift;
`git checkout -- plugins/horos/examples/fixture/store` restoring the tree;
`<sign-off> python3 -m unittest discover -s tests` green in a clean detached
snapshot of the run head; and
`<sign-off> python3 -m unittest tests.test_marketplace_prose` green. The
transcript is committed as the last section of
`plugins/horos/docs/evidence/skills-content-addressed.md` and lands in the
run's audit log
(`audit/rounds/fiat-ship-the-content-addressed-object-rule-whose-evi.md`)
inside the step's round record; `python3 <imprimatur.py>` exit 0 on the
bundle after the append.
**Why.** The controller refuses an implement receipt whose branch adds no
commit, and the audit log's grammar admits only round records, so the
transcript needs a product home of its own. The evidence bundle already
carries the drift demonstration and is the natural place for the run-head
transcript; the round record still carries it, as the baseline said.
**Steps touched.** Step 4.
**Still holding.** Step 4: entry holds; exit holds.
