# Runbook: stop the marker rule excluding the classifier's own source

Derived from the receipted study at `.hexaemeron/study.md`. Task issue:
[wildcat-finance/skills#377](https://github.com/wildcat-finance/skills/issues/377).
The run branch is `fiat/377-stop-the-marker-rule-excluding-the-classifie`, cut
from `main` at `f1458dcefa24ac26a4a550178f43514bc775e4e8`. Step 1 branches
from the run branch; every later step branches from the step below it.

A host condition from the study's constraints applies to every suite command
in this runbook: this machine signs commits globally and the test helpers do
not neutralise signing, so each `unittest` invocation below carries
`GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false`,
written `<sign-off>` here for brevity. Expanding it is mandatory; fixing the
helpers instead is an ask-first item and no step here does it.

## Step 1: Commit the spec copies

**Goal.** Put the receipted study and this runbook where the repository keeps
them, so the branch carries its own specification.
**Entry.** The run branch at `f1458dcefa24ac26a4a550178f43514bc775e4e8`, clean
tree, both suites green as recorded in the study's constraints.
**Exit.** `plugins/horos/docs/marker-self-exclusion/study.md` and
`plugins/horos/docs/marker-self-exclusion/runbook.md` committed, then all of:
`python3 <imprimatur.py> plugins/horos/docs/marker-self-exclusion/study.md`
exit 0,
`python3 <imprimatur.py> plugins/horos/docs/marker-self-exclusion/runbook.md`
exit 0,
`<sign-off> python3 -m unittest discover -s tests` green, and
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
green (217 tests at this step).
**Files.** `plugins/horos/docs/marker-self-exclusion/study.md`,
`plugins/horos/docs/marker-self-exclusion/runbook.md`.
**Tests.** None written; the two existing suites are the gate. Elenchus
runner: `<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos 2> {report}`,
report format unittest text output, report file
`.hexaemeron/elenchus-step-1.txt`.
**Disciplines.** hypomnema: the committed spec copies are the record home the
study's section 12 names. phylax: none, documentation only. ephoros: none,
nothing here runs unattended. metron: none, no performance claim. elenchus:
none, no failure in hand.

## Step 2: Gate markers to comment-led lines

**Goal.** Bind a generated-file marker only when its occurrence sits on a
comment-led line, in both the prefix pass and the window pass, and regenerate
the committed boundary under the narrowed rule.
**Entry.** Step 1's exit tree.
**Exit.** All of, from the repository root:
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
green with the new tests counted,
`<sign-off> python3 -m unittest discover -s tests` green against the
regenerated `.horos/boundary.json`,
`python3 plugins/horos/skills/horos/scripts/horos.py check .` exit 0, and
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --json` emitting
no entry for `plugins/horos/skills/horos/scripts/horos.py` and none for
`plugins/horos/tests/test_classify.py` while keeping `CONTRIBUTORS.md` and
`plugins/horos/examples/fixture/gen/api.py` (pinned by a named test, checked
once by eye at exit). The five-run scan median before and after the change is
recorded in the run's audit log and the after-median stays within 10% of the
same-session before-median (study section 10).
**Files.** `plugins/horos/skills/horos/scripts/horos.py`,
`plugins/horos/tests/test_classify.py`, `.horos/boundary.json`, plus
`.horos/census.json` and `.horos/candidates.json` where the regeneration moves
them.
**Tests.** Extended in `plugins/horos/tests/test_classify.py`, observed red
against the unfixed rule before the fix lands (study section 11): near-miss
fixtures binding a banner under each leader family (`#`, `//`, `/*`, `*`
continuation, `<!--`, `--`, `;`, `%`) in the prefix pass and in the window
pass; markers inside a string literal, a call argument and a JSON value
staying readable in both passes; a banner straddling a window edge binding
through wholly contained lines only; a monotone-narrowing subset assertion
over the fixture corpus; the new evidence wording asserted, including the
existing `test_a_generation_marker_in_the_prefix_is_generated` wording pin
updated deliberately; a candidate directory corroborated only by
string-literal markers no longer excluding; and a repository-level
zero-self-exclusion test over this tree. Expected count: the horos suite grows
from 217; the exact count is recorded at exit. Elenchus runner:
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos 2> {report}`,
report format unittest text output, report file
`.hexaemeron/elenchus-step-2.txt`.
**Disciplines.** phylax: this step narrows the exclusion an untrusted
repository can buy with marker bytes (study section 9) and must not weaken the
security-review carve-out. ephoros: the evidence string must answer "why is
this file excluded" under the new condition (study section 8). metron: the
section 10 budget applies; both medians are recorded before the step closes.
elenchus: the near-miss guards are observed red against the unfixed rule
first. hypomnema: the comment-leader set gets its reasoning comment beside the
set in `horos.py`.

## Step 3: Reconcile the marketplace prose and write the ledger row

**Goal.** Cold-read every mutable first-party marketplace prose surface,
reconcile it with the tree and this run's outcome, and record the evolution
row that closes the held job.
**Entry.** Step 2's exit tree.
**Exit.** All of:
`<sign-off> python3 -m unittest tests.test_marketplace_prose` green,
`python3 <imprimatur.py> <file>` exit 0 for every prose file this step
touches, `plugins/horos/skills/horos/EVOLUTION.md` carrying exactly one new
history row (axis evolution, closing `marker-self-exclusion`) whose held next
job is the content-addressed object rule exactly as the v9.2.3 epoch row
names it, and both suites green:
`<sign-off> python3 -m unittest discover -s tests` and
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`.
**Files.** `plugins/horos/skills/horos/EVOLUTION.md`, and whichever of
`plugins/horos/README.md`, `plugins/horos/AGENTS.md`,
`plugins/horos/skills/horos/SKILL.md` and the root marketplace descriptors the
cold-read finds trailing the tree; the known finding is the frontier text
still saying content-addressed stores stand unclassified while the committed
boundary classifies them (study section 12).
**Tests.** None written; `tests.test_marketplace_prose` and the two suites are
the gate. Elenchus runner:
`<sign-off> python3 -m unittest discover -s tests 2> {report}`, report format
unittest text output, report file `.hexaemeron/elenchus-step-3.txt`.
**Disciplines.** hypomnema: the ledger row is the record of the
expensive-to-reverse semantics change (study section 12), and the accepted
losses are recorded in the run's audit log as reviewed risk-register ids.
phylax: none, prose and ledger only. ephoros: none, nothing runs unattended.
metron: none, no performance claim. elenchus: none, no failure in hand.

## Step 4: Demonstrate the fixed boundary

**Goal.** Run the study's demo path end to end at the run head and record the
result.
**Entry.** Step 3's exit tree.
**Exit.** From the repository root, in order, all green:
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --json` emitting
no entry for the two formerly self-excluded files and keeping
`CONTRIBUTORS.md` and `plugins/horos/examples/fixture/gen/api.py`,
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
green,
`<sign-off> python3 -m unittest discover -s tests` green,
`python3 plugins/horos/skills/horos/scripts/horos.py check .` exit 0, and
`<sign-off> python3 -m unittest tests.test_marketplace_prose` green. The
transcript lands in the run's audit log
(`audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.md`).
**Files.** `audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.md`
(demo record appended); no source file changes.
**Tests.** None written; the demo path is the gate. Elenchus runner:
`<sign-off> python3 -m unittest discover -s plugins/horos/tests -t plugins/horos 2> {report}`,
report format unittest text output, report file
`.hexaemeron/elenchus-step-4.txt`.
**Disciplines.** ephoros: the demo exercises the whole observable surface,
exit codes and evidence strings (study section 8). phylax: none, nothing new
opens. metron: none, the budget was settled in step 2. elenchus: none unless
the demo fails, which stops the line. hypomnema: the demo record's home is the
run's audit log.
