# Runbook: Ephoros reads E001 to E003 on the TypeScript surface it already opens

Derived from `.hexaemeron/study.md` for issue
[#1420](https://github.com/wildcat-finance/skills/issues/1420). Base ref
`e7d0fdea1a636e06725fc55a55d02c24f74a64ee` on `main`, run branch
`fiat/1420-ephoros-next-extend-e001-to-e003-to-the-typ`.

## Two readings recorded rather than resolved silently

**The shipped artefacts take two homes rather than one.** The study and this
runbook ship flat, as `docs/ephoros-typescript-rule-parity-study.md` and
`docs/ephoros-typescript-rule-parity-runbook.md`, which is the form the
previous ephoros run used at `docs/ephoros-wallet-address-telemetry-study.md`.
That is not a style preference. The study's sections 8 to 12 link five phase
skills as `../plugins/hexaemeron/skills/<skill>/SKILL.md` and ADR-010 as
`../docs/decisions/ADR-010-split-address-telemetry-from-boundary-control.md`.
Both forms resolve from `docs/` and from nowhere deeper, and Hypomnema's H001
refuses a link that resolves to nothing, by two routes: the `lint-hypomnema`
check and `tests/test_shipped_tree_lints.py`. Shipping the study one directory
down would force a rewrite of its link targets in a copy that is otherwise
byte-identical to a controller-pinned source. The design record instead takes
the directory form `docs/ephoros-typescript-rule-parity/`, which is what
`docs/commit-gate/design-evidence.json` established, because the record cites
its reports by the record-relative path `reports/<name>.json` and that layout
has to survive the copy.

**The decision record ships in the last step, not the step that decides it.**
The study's section 12 puts the Python-to-TypeScript E001 divergence in an
architecture decision record under `docs/decisions/`, and its number is picked
immediately before the branch is pushed, because `tests/test_decision_records.py`
checks a collision against the default branch and a number drafted early
collides with a concurrent run. That was finding `S2-R1-03` in skills#1238.
Step 2 states the divergence in `SKILL.md` as a limit and pins it with a test.
Step 5 adds the record and turns that sentence into a pointer to it. No step
between them claims a record that does not exist.

## Where the pending conformance gate lands

The design record carries one conformance criterion, `clone-verdict-e001`,
pending on all three candidates and blocking `integration`. Only the selected
candidate's cell is due at that transition, so `span-index` resolves and the
two rejected candidates keep their pending rows untouched.

Step 2 resolves it. It writes
`.hexaemeron/reports/span-index-clone-verdict-e001.json` as one closed
`protasis-design-report/v1` object whose `command` is the resolver the record
names, `python3 .hexaemeron/design-probes/clone_verdict.py`, whose `unit` is
`count`, whose `exit` is zero and whose `value` is the E001 count that probe
prints over the pinned clone. Step 5 re-runs the same probe as part of the demo
path and reports the same number.

## The clone verdict is a measurement, not a target

The study fixed 14 by reading the pinned clone before any recogniser existed:
14 of 21 logger call sites pass an interpolated template literal, 7 in
`useGetWithdrawals.ts`, 5 in `useGetLenderWithdrawals.ts`, 1 in
`updateMarkets.ts` and 1 in `useGetLenders.ts` at the call opening line 29.
A recogniser narrowed until that count falls toward zero is a finding against
this run, not a fix. Step 2 owns that verdict and says so in its Exit.

## The runner contract every step shares

Test command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report
{report}`, report format `elenchus.unittest.v1`, report file
`.hexaemeron/reports/conformance/fiat-1420-step-<N>.json`. Warden receives
those three inputs and may not substitute a nearby suite or infer a command
from `Files`.

Every step's exit runs both suites named by `python3 scripts/run_checks.py
--plan`: the repository root suite `root-suite`, `python3 -m unittest discover
-s tests`, and the plugin's own `hexaemeron-suite`, `python3
plugins/hexaemeron/tests/run_tests.py`. Three lints passing is not the suite.

## Repository obligations every step carries

These come from the study's section 3 and are repeated in each step's `Files`
rather than assumed.

- `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` then the
  same command with `--census --write` run before every commit, because every
  tracked-file edit moves the byte counts `HorosCensusCurrencyTests` reads.
- `lint-ephoros` runs
  `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, the very script three
  of these steps change. Read a non-zero `lint-ephoros` against this run's own
  diff before reading it against the file it names, and never edit the checker
  to make its own lint pass.
- `plugins/hexaemeron/skills/ephoros/DEMONSTRATION.md` pins
  `plugins/hexaemeron/tests/fixtures/ephoros/telemetry-keys/alert-labels.yaml`
  by SHA-256. No step here plans to touch that fixture. If one does, the digest
  is re-pinned in the same commit and `python3 -m unittest
  tests.test_demonstrations -v` proves it.
- `SOURCES.md` is generated and is never hand-edited. Ephoros is not one of the
  four skills whose completed frontier job owes the source-coverage refresh, so
  nothing there moves.
- The last step carries the marketplace-prose and rolling next-job rules:
  `FUTUREPROOFING.md` lists "TypeScript parity for Ephoros rules E001 to E003"
  as an open contribution, and this run closes it.

No step edits any file under `audit/` or under `.hexaemeron/validation/`. The
extracted application clone is read and never written. No absolute path outside
this repository is written into any shipped document.

```design-lock
schema | protasis-design-evidence/v1
sha256 | bc5f6eb2056b9811831684be1265729aa7a4856c66a335a735a21f9915c4cf8b
candidate | span-index
```

## Step 1: Commit the run documents and give the design record a home

**Goal.** Put the study, this runbook, the design record, the fifteen reports
it cites and the probes that produced them into the repository, so every later
step writes into a home the tree lints and the check runner already own.

**Entry.** `fiat/1420-ephoros-next-extend-e001-to-e003-to-the-typ` at
`e7d0fdea1a636e06725fc55a55d02c24f74a64ee`, clean tree, no source file changed.

**Exit.** `docs/ephoros-typescript-rule-parity-study.md` and
`docs/ephoros-typescript-rule-parity-runbook.md` are byte-identical copies of
`.hexaemeron/study.md` and `.hexaemeron/runbook.md` as they stand at this
step's entry. `docs/ephoros-typescript-rule-parity/design-evidence.json` is a
byte-identical copy of `.hexaemeron/design-evidence.json`, and
`docs/ephoros-typescript-rule-parity/reports/` holds the fifteen reports it
cites at the record-relative paths the record names, each at the digest the
record states. `docs/ephoros-typescript-rule-parity/design-probes/` holds the
seven probe modules and the two support modules that produced them.
`tests/test_ephoros_typescript_parity.py` is created with
`ShippedRecordTests`, which proves the copies from inside a clone. Proved by
`python3 -m unittest tests.test_ephoros_typescript_parity -v` at exit zero,
`python3 -m unittest discover -s tests` at exit zero, `python3
plugins/hexaemeron/tests/run_tests.py` at exit zero, and `python3
plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md
.agents/skills/promise-machine/SKILL.md
.agents/skills/promise-machine/PORTABLE.md plugins docs` at exit zero on the
committed tree.

**Files.** `docs/ephoros-typescript-rule-parity-study.md`,
`docs/ephoros-typescript-rule-parity-runbook.md`,
`docs/ephoros-typescript-rule-parity/design-evidence.json`,
`docs/ephoros-typescript-rule-parity/reports/*.json`,
`docs/ephoros-typescript-rule-parity/design-probes/*.py`,
`tests/test_ephoros_typescript_parity.py`, `.horos/boundary.json`,
`.horos/census.json`. The Horos scan and census write run before the commit.
`lint-ephoros` and `lint-phylax` both reach `docs`, so the shipped probes are
linted as ordinary repository Python; they exit clean at this base and a
non-zero result is triaged against this diff first. `SOURCES.md` is not edited.
`DEMONSTRATION.md` is not touched, because no pinned fixture moves here.

**Tests.** `tests/test_ephoros_typescript_parity.py` is created with
`ShippedRecordTests`: the shipped study and runbook exist at their exact paths;
the shipped design record parses as `protasis-design-evidence/v1` and names
`span-index` as its selected candidate; every report the shipped record cites
resolves under `docs/ephoros-typescript-rule-parity/reports/` at the SHA-256
the record states; every link in the shipped study resolves to a file that
exists; and the shipped record's report paths stay record-relative rather than
absolute. Expect five cases. No existing test's assertions change. Step audit
runner contract is test command `python3 plugins/hexaemeron/tests/run_tests.py
--elenchus-report {report}`, report format `elenchus.unittest.v1`, report file
`.hexaemeron/reports/conformance/fiat-1420-step-1.json`.

**Disciplines.** phylax: none, this step adds no input path, starts no process
and reads nothing from outside the repository. ephoros: none, nothing added
here runs unattended, and the step changes no rule. metron: none, no
performance claim is made or moved. elenchus: none, no failure is in hand.
hypomnema: the whole step is a record-siting decision, and where the study,
runbook and design record live is what a later reader follows.

## Step 2: E001 on TypeScript, and the verdict over the pinned clone

**Goal.** Report a log call whose first argument is a message built by
formatting on the TypeScript surface, and record the count that rule produces
over the pinned application clone.

**Entry.** Step 1's exit state.

**Exit.** `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py` reports E001
from `check_typescript` when a call the existing sink gates classify as a log
call takes a first argument that is an interpolated template literal or a
concatenation involving a string literal, reading its spans from the per-file
`_TsSpanIndex` rather than by scanning forward. A template literal carrying no
`${}` stays clean. The fixture
`plugins/hexaemeron/tests/fixtures/ephoros/telemetry-keys/interpolated-message.ts`
was observed red before the recogniser landed: `python3 -m unittest
plugins.hexaemeron.tests.test_ephoros_checker -v` was run with the new test and
without the recogniser, it failed on that case, and the failing output is
recorded in the step's commit message before the fix commit. The committed
expectation for `logger-message.ts` moves from an empty finding list to one
E001 and no E005, under the same red-first observation, so the original claim
that an address inside a message is not an E005 key is kept rather than
deleted. `.hexaemeron/reports/span-index-clone-verdict-e001.json` exists as one
closed `protasis-design-report/v1` object with `candidate` `span-index`,
`criterion` `clone-verdict-e001`, `command` `python3
.hexaemeron/design-probes/clone_verdict.py`, `unit` `count`, `exit` 0 and
`value` 14, and that value is the number the probe printed rather than a number
the rule was narrowed to reach. `SKILL.md` states the constant-template limit.
Proved by `python3 -m unittest plugins.hexaemeron.tests.test_ephoros_checker -v`
at exit zero, `python3 .hexaemeron/design-probes/clone_verdict.py` printing
`"e001": 14`, `python3
plugins/hexaemeron/skills/protasis/scripts/design_evidence.py
.hexaemeron/design-evidence.json --transition integration` at exit zero,
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
scripts docs` at exit zero, `python3 -m unittest discover -s tests` at exit
zero and `python3 plugins/hexaemeron/tests/run_tests.py` at exit zero on the
committed tree.

**Files.** `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`,
`plugins/hexaemeron/skills/ephoros/SKILL.md`,
`plugins/hexaemeron/tests/test_ephoros_checker.py`,
`plugins/hexaemeron/tests/fixtures/ephoros/telemetry-keys/interpolated-message.ts`,
`plugins/hexaemeron/tests/fixtures/ephoros/telemetry-keys/constant-message.ts`,
`.hexaemeron/reports/span-index-clone-verdict-e001.json`, `.horos/boundary.json`,
`.horos/census.json`. The Horos scan and census write run before the commit.
`lint-ephoros` runs the script this step edits, so a non-zero result is triaged
against this diff before it is read against the file it names, and the checker
is never edited to make its own lint pass. `DEMONSTRATION.md` pins
`alert-labels.yaml`, which this step does not touch, so no digest is re-pinned;
if that changes, the re-pin lands in this commit and `python3 -m unittest
tests.test_demonstrations -v` proves it. `SOURCES.md` is not edited.

**Tests.** `plugins/hexaemeron/tests/test_ephoros_checker.py` gains
`TypeScriptInterpolatedMessageTests`: `interpolated-message.ts` reports exactly
one E001 at the call's line; `constant-message.ts`, holding a backtick message
with no `${}` beside a logger call with fields, reports nothing; a template
literal inside a block comment and one inside a string literal each report
nothing; a `console.log` with the same interpolated argument reports nothing; a
reasoned `// ephoros: allow <why>` comment on the finding line and on the line
above each suppress it while a bare pragma suppresses nothing; and a file the
shared lexer cannot terminate still reports E000 alone and no E001. Expect
eight cases. One existing case changes: the `logger-message.ts` assertion
becomes one E001 and no E005. Step audit runner contract is test command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file
`.hexaemeron/reports/conformance/fiat-1420-step-2.json`.

**Disciplines.** phylax: the recogniser adds work behind the untrusted-read
boundary the checker already opened, so the 1 MiB cap, the E000 fail-closed
path and the rule that no pragma suppresses E000 are all asserted here.
ephoros: the E001 message is the only output a reader gets, so it names the
shape and the remedy in one sentence, as the existing five do. metron: the
recogniser reads from the span index rather than scanning a span forward, which
is the shape the study's budget and the three prior audit findings are about;
`python3 .hexaemeron/design-probes/runtime.py span-index` and a timed run over
the extracted clone are recorded as the median of three runs. elenchus: the two
moved expectations land as guard tests observed red before the recogniser, with
the red observation recorded in the commit message. hypomnema: the
constant-template divergence from Python is expensive to reverse once other
tools read the counts, and it is stated in `SKILL.md` here and given its
decision record in step 5.

## Step 3: E002 on TypeScript, without reopening the E005 split

**Goal.** Report an unbounded key inside a metric label, tag or attribute
container on the TypeScript surface, leaving the address-shaped subset to E005.

**Entry.** Step 2's exit state.

**Exit.** `ephoros.py` reports E002 from `check_typescript` when a key in a
container `_label_container` already finds, meaning the array or object literal
after a `labels`, `labelNames`, `label_names`, `tags` or `attributes` property
or the argument of a `.labels(...)` call, matches an unbounded word that E005
has not already claimed. A key that is address-shaped reports E005 alone, as it
does on the Python surface. The vocabulary matches the same word set E005
already splits out of `walletAddress` and `wallet_address`, so `addresses` and
`hashes` are ordinary words on this surface and the Python `s?` plural gap is
not carried across; `SKILL.md` states that asymmetry. The fixture
`plugins/hexaemeron/tests/fixtures/ephoros/telemetry-keys/unbounded-label.ts`
was observed red before the recogniser landed, and the failing output is
recorded in the step's commit message before the fix commit. Proved by `python3
-m unittest plugins.hexaemeron.tests.test_ephoros_checker -v` at exit zero,
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
scripts docs` at exit zero, `python3 -m unittest discover -s tests` at exit
zero and `python3 plugins/hexaemeron/tests/run_tests.py` at exit zero on the
committed tree.

**Files.** `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`,
`plugins/hexaemeron/skills/ephoros/SKILL.md`,
`plugins/hexaemeron/tests/test_ephoros_checker.py`,
`plugins/hexaemeron/tests/fixtures/ephoros/telemetry-keys/unbounded-label.ts`,
`plugins/hexaemeron/tests/fixtures/ephoros/telemetry-keys/bounded-label.ts`,
`.horos/boundary.json`, `.horos/census.json`. The Horos scan and census write
run before the commit. `lint-ephoros` runs the script this step edits, so a
non-zero result is triaged against this diff first and the checker is never
edited to make its own lint pass. `DEMONSTRATION.md` pins `alert-labels.yaml`,
untouched here, so no digest is re-pinned; if that changes, the re-pin lands in
this commit under `python3 -m unittest tests.test_demonstrations -v`.
`SOURCES.md` is not edited.

**Tests.** `plugins/hexaemeron/tests/test_ephoros_checker.py` gains
`TypeScriptUnboundedLabelTests`: `unbounded-label.ts` reports exactly one E002
for a request-id key inside a `labels` object literal;
`bounded-label.ts`, holding `market`, `chain` and `status` keys in the same
container shape, reports nothing; a `walletAddress` key in that container
reports E005 and no E002, so the existing split is preserved; the same
unbounded word inside a comment and inside a string reports nothing; the
`.labels(...)` call form is found as well as the property form; and a reasoned
pragma suppresses on the line and the line above while a bare one suppresses
nothing. Expect seven cases. No existing test's assertions change. Step audit
runner contract is test command `python3 plugins/hexaemeron/tests/run_tests.py
--elenchus-report {report}`, report format `elenchus.unittest.v1`, report file
`.hexaemeron/reports/conformance/fiat-1420-step-3.json`.

**Disciplines.** phylax: the new key reading stays inside the same bounded read,
so the cap and the E000 path are asserted again against this recogniser.
ephoros: the E002 message names the container and the remedy in one sentence.
metron: the container keys come from the tables the file already built, so no
new pass is added and the specimen timing is re-recorded rather than assumed.
elenchus: the new fixture lands as a guard observed red before the recogniser,
with the red observation in the commit message. hypomnema: the vocabulary
choice binds a published code, so the plural asymmetry against Python is
written into `SKILL.md` rather than left for a reader to discover.

## Step 4: E003 on TypeScript, for a duration reduced to a mean

**Goal.** Report a declaration or assignment that takes a mean over something
named as a duration on the TypeScript surface.

**Entry.** Step 3's exit state.

**Exit.** `ephoros.py` reports E003 from `check_typescript` when a declaration
or assignment whose target name or right-hand expression carries a duration
word takes a mean, meaning a call to `mean`, `average`, `avg` or `fmean`, or
the reduce-over-length idiom. This is the one recogniser the current pass does
not already produce a shape for, and it is added as one indexed pass keyed to
the same bracket tables rather than as a forward scan. Sentence lengths, layout
positions and prices stay clean. The fixture
`plugins/hexaemeron/tests/fixtures/ephoros/telemetry-keys/mean-duration.ts` was
observed red before the recogniser landed, and the failing output is recorded
in the step's commit message before the fix commit. Proved by `python3 -m
unittest plugins.hexaemeron.tests.test_ephoros_checker -v` at exit zero,
`python3 .hexaemeron/design-probes/runtime.py span-index` reporting at most
2,000 milliseconds on the 64 KiB specimen as the median of three runs, `python3
plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests scripts
docs` at exit zero, `python3 -m unittest discover -s tests` at exit zero and
`python3 plugins/hexaemeron/tests/run_tests.py` at exit zero on the committed
tree.

**Files.** `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`,
`plugins/hexaemeron/skills/ephoros/SKILL.md`,
`plugins/hexaemeron/tests/test_ephoros_checker.py`,
`plugins/hexaemeron/tests/fixtures/ephoros/telemetry-keys/mean-duration.ts`,
`plugins/hexaemeron/tests/fixtures/ephoros/telemetry-keys/histogram-duration.ts`,
`.horos/boundary.json`, `.horos/census.json`. The Horos scan and census write
run before the commit. `lint-ephoros` runs the script this step edits, so a
non-zero result is triaged against this diff first and the checker is never
edited to make its own lint pass. `DEMONSTRATION.md` pins `alert-labels.yaml`,
untouched here, so no digest is re-pinned; if that changes, the re-pin lands in
this commit under `python3 -m unittest tests.test_demonstrations -v`.
`SOURCES.md` is not edited.

**Tests.** `plugins/hexaemeron/tests/test_ephoros_checker.py` gains
`TypeScriptMeanDurationTests`: `mean-duration.ts` reports exactly one E003 for
a named mean over a duration and one for the reduce-over-length idiom;
`histogram-duration.ts`, recording the same durations into buckets, reports
nothing; a mean over sentence lengths, one over a layout position and one over
a price each report nothing; the same shape inside a comment and inside a
template literal report nothing; and a reasoned pragma suppresses on the line
and the line above while a bare one suppresses nothing. Expect eight cases. No
existing test's assertions change. Step audit runner contract is test command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file
`.hexaemeron/reports/conformance/fiat-1420-step-4.json`.

**Disciplines.** phylax: this is the one added pass, so the bounded read, the
E000 path and the rule that no pragma suppresses E000 are asserted against it
directly. ephoros: the E003 message names the mean and the histogram remedy in
one sentence. metron: the added pass is the only place this run could
reintroduce the quadratic class the audit closed three times, so the specimen
timing is re-measured here as the median of three runs against the study's
2,000 millisecond budget, and the clone timing against its two second budget.
elenchus: the new fixture lands as a guard observed red before the recogniser,
with the red observation in the commit message. hypomnema: the duration
vocabulary and the dataflow non-goal bind a published code, so both are written
into `SKILL.md`.

## Step 5: Move the ledger, record the divergence, and run the demo path

**Goal.** Record the completed frontier advance in the ephoros ledger, give the
Python-to-TypeScript E001 divergence its decision record, reconcile the prose
that describes the skill, and run the study's demo path end to end.

**Entry.** Step 4's exit state.

**Exit.** `plugins/hexaemeron/skills/ephoros/EVOLUTION.md` carries exactly one
new history row, `ephoros-v1.3.0`, axis `evolution`, with a new frontier
revision and the SHA-256 of the exact UTF-8 line
`{status}|{frontier revision}|{current frontier}|{next Fiat job}` including its
final newline, and the held frontier bullets are rewritten to match. The row
states the three rules' TypeScript scope, the constant-template boundary, the
camel-case word vocabulary, and the verdict of 14 true E001 findings over
`wildcat-app-v2` at `564a189b` with the fact that they are true rather than
suppressed. `plugins/hexaemeron/skills/ephoros/SKILL.md` frontmatter version
becomes `1.3.0`, and its constant-template sentence becomes a pointer to the
new record. That record is added under `docs/decisions/` with its number picked
immediately before this branch is pushed, checked against the default branch at
that moment. The plugin version is propagated in the four places
`tests/test_version_propagation.py` reads: `plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`
and `.agents/plugins/marketplace.json`, with the pinned value in that test file
moved to match. `plugins/hexaemeron/AGENTS.md` and
`plugins/hexaemeron/README.md` are cold-read against the tree and reconciled
where they describe what ephoros checks; the `marketplace-context` block in
both is left as it stands, because it carries the Hexaemeron plugin frontier
rather than the ephoros skill frontier and this run did not complete that job.
`FUTUREPROOFING.md` drops "TypeScript parity for Ephoros rules E001 to E003"
from its contribution list, because this run closes it. The shipped copies at
`docs/ephoros-typescript-rule-parity-study.md`,
`docs/ephoros-typescript-rule-parity-runbook.md` and
`docs/ephoros-typescript-rule-parity/` are refreshed to the bytes receipted at
this step's entry, so they carry every amendment recorded up to that point and
the shipped record holds no row the controller has since resolved. Proved by
running the study's demo path in order on the committed tree: `python3 -m
unittest plugins.hexaemeron.tests.test_ephoros_checker` at exit zero, `python3
plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests scripts
docs` at exit zero, `python3 .hexaemeron/design-probes/clone_verdict.py`
printing `"e001": 14`, `python3 plugins/hexaemeron/tests/run_tests.py` at exit
zero and `python3 -m unittest discover -s tests` at exit zero. Also proved by
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py
.hexaemeron/design-evidence.json --transition integration` at exit zero and
`python3 scripts/run_checks.py --full` at exit zero.

**Files.** `plugins/hexaemeron/skills/ephoros/EVOLUTION.md`,
`plugins/hexaemeron/skills/ephoros/SKILL.md`,
`docs/decisions/ADR-<next free number>-<slug>.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`tests/test_version_propagation.py`, `plugins/hexaemeron/AGENTS.md`,
`plugins/hexaemeron/README.md`, `FUTUREPROOFING.md`,
`docs/ephoros-typescript-rule-parity-study.md`,
`docs/ephoros-typescript-rule-parity-runbook.md`,
`docs/ephoros-typescript-rule-parity/design-evidence.json`,
`docs/ephoros-typescript-rule-parity/reports/*.json`,
`tests/test_ephoros_typescript_parity.py`, `.horos/boundary.json`,
`.horos/census.json`. The Horos scan and census write run before the commit,
and this step adds the most tracked files of any. `lint-ephoros` runs the
script the three earlier steps changed, so a non-zero result is still triaged
against this run's diff first. `DEMONSTRATION.md` pins `alert-labels.yaml` and
is not touched, because the demo lane is a separate frontier that does not move
here; if a pinned fixture moves, the digest is re-pinned in this commit and
`python3 -m unittest tests.test_demonstrations -v` proves it. `SOURCES.md` is
generated and is not hand-edited, and ephoros is not one of the four skills
whose completed frontier job owes the coverage refresh.

**Tests.** `tests/test_ephoros_typescript_parity.py` gains `LedgerRowTests` and
`ShippedCopyRefreshTests`: the ephoros ledger holds exactly one row for
`ephoros-v1.3.0`; that row's recorded digest equals the SHA-256 of the ledger's
own canonical frontier line, computed from the file rather than restated; the
`SKILL.md` frontmatter version equals the ledger's current version; the ledger
row names the clone commit `564a189b` and the count 14; `FUTUREPROOFING.md`
carries no line offering TypeScript parity for E001 to E003; and each shipped
copy carries the same count of `### Amendment --` headings as its
`.hexaemeron/` source, written into the test as a literal so a fresh clone can
run it without reading anything outside the repository. Expect six cases. No
existing test's assertions change, and `tests/test_version_propagation.py`
changes one pinned version value rather than an assertion. Step audit runner
contract is test command `python3 plugins/hexaemeron/tests/run_tests.py
--elenchus-report {report}`, report format `elenchus.unittest.v1`, report file
`.hexaemeron/reports/conformance/fiat-1420-step-5.json`.

**Disciplines.** phylax: none, this step changes no reader and opens no path;
the clone is read by the demo path exactly as the earlier steps read it.
ephoros: none, the ledger and the prose are read by people rather than emitted
by a running system. metron: the demo path's timed run over the extracted clone
is reported against the study's two second budget, as the median of three runs
with its spread. elenchus: none, no failure is in hand at this point. hypomnema:
the decision record for the Python-to-TypeScript E001 divergence and the ledger
row stating a non-clean verdict over a real tree are both here, and both are
expensive to reverse once other tools cite the codes and read the counts.
