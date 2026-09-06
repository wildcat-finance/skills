# Dokimasia: attributed confirmation, runbook

Derived from [the study](dokimasia-attribution-study.md). Four steps, in
dependency order. Each is one pull request against the step below it, green at
both ends on the plugin suite and on the repository root suite.

The order is fixed by the design record, not by preference. Its three
conformance cells for `rule-table` block `step:2`, `step:3` and `integration`,
and Fiat runs the checker at `step:N` immediately before opening step N. The
report a cell needs is therefore produced by the step before the one it blocks:
the reconciler's refusal is built in step 1, because `reconcile --check` admits
step 2; the proposal surface is built in step 2, because `propose --check`
admits step 3; and the attributed scrutiny is demonstrated in step 3, because
`demonstrate --check` admits integration. Step 4 moves the ledger and runs the
demo path from the study's section 1. Every conformance report is written below
the record's own directory, at the path the record names.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 69a258165bf3fa02efd13c6b634584865de862adcb2bd5dd4afe1d09d94b0846
candidate | rule-table
```

## Step 1: Commit the specification and make the reconciler refuse an unattributed confirmation

**Goal.** Land the study, runbook, design record and ADR-003, and make the
reconciler require `confirmed_by` on every confirmed entry, resolve `rule`
against a set-level `rules` table, and emit a `confirmations` block, with the
pinned set attributed under assumption 6 so the committed evidence stays green.

**Entry.** The run branch
`fiat/1352-dokimasia-3-a-reconciler-that-refuses-a-con` at
`0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`, with the study receipted,
`.hexaemeron/design-evidence.json` at SHA-256
`69a258165bf3fa02efd13c6b634584865de862adcb2bd5dd4afe1d09d94b0846` with its 21
selection reports present, the design checker admitting `design-lock` and
`step:1` with nothing due, the commit gate active through
`git config core.hooksPath .githooks`, and `DOKIMASIA_PINNED_APP` and
`DOKIMASIA_PINNED_WORKBOOK` set to the detached `bb9685fb` extraction and the
`9da2f2e8` workbook.

**Exit.** The study, runbook, design record, its 21 selection reports and its
generator are committed under `plugins/dokimasia/docs/` with links that resolve
from that directory; the generator regenerates the committed record byte for
byte; ADR-003 records that a person is required, that a rule is a table row,
the two readings in the study's section 4, the identifiers staying at `/v1`,
and the migration with no defaulting; `dispositions-v1.json` declares
`confirmed_by`, `rule` and the set-level `rules` table, and `coverage-v1.json`
declares `confirmations` with `people`, `by_person`, `by_rule` and
`individual`, both using only keywords `schema.py` already supports and both
digests re-bound in `tests/promise_machine_coverage.json`; the reconciler
refuses by name a confirmed entry with no, blank or non-string `confirmed_by`,
a `rule` id the table does not hold, a rule row with blank `text` or blank
`stated_by`, a `rules` value that is not an object, and an unconfirmed entry
carrying either field, and it refuses a set confirmed under `dokimasia-v2.1.0`
on its first confirmed entry naming the item and the missing field; the
`confirmations` block reconciles with `disposed` three ways and the canonical
coverage digest covers it; every new cap is a parameter with a default; the
pinned disposition set carries one `rules` row `row-author-owns-walking-it`
stated by `Laurence Day` and 202 entries naming that person and that rule, the
coverage, scrutiny and rendered records are regenerated from the pinned inputs
and still close at 202 over 261 with `covered` zero, the four DEMONSTRATION.md
source digests and the root README front-door marker follow the files that
moved, and the Horos boundary and census match a fresh scan. Proved by
`python3 scripts/run_checks.py --scope dokimasia --scope root && python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py plugins/dokimasia/docs/attribution-design-evidence.json --transition design-lock && python3 plugins/dokimasia/docs/design/build_attribution_design_evidence.py && git diff --exit-code -- plugins/dokimasia/docs/attribution-design-evidence.json plugins/dokimasia/docs/reports/selection && python3 scripts/promise_machine.py coverage --check && python3 scripts/demonstrations.py check --root . && python3 scripts/check_public_front_door.py && python3 plugins/dokimasia/scripts/dokimasia.py reconcile --check --candidate rule-table --criterion unattributed-confirmation-refused --report .hexaemeron/reports/conformance/rule-table-unattributed-confirmation-refused.json`.

**Files.** `plugins/dokimasia/docs/dokimasia-attribution-study.md`;
`plugins/dokimasia/docs/dokimasia-attribution-runbook.md`;
`plugins/dokimasia/docs/attribution-design-evidence.json`, this run's own
record, with the prior two records untouched; its 21 reports in the existing
`plugins/dokimasia/docs/reports/selection/`, the path the record declares
relative to itself, named by this run's candidate ids so none collides with the
prior runs' 33; `plugins/dokimasia/docs/design/build_attribution_design_evidence.py`,
untracked at entry;
`plugins/dokimasia/docs/decisions/ADR-003-attribution-names-a-person-and-a-stated-rule.md`;
`plugins/dokimasia/docs/coverage-contract.md`, one new "Attribution" section
beside "Confirmation"; `plugins/dokimasia/schemas/dispositions-v1.json`;
`plugins/dokimasia/schemas/coverage-v1.json`;
`plugins/dokimasia/scripts/dokimasia_lib/reconcile.py`;
`plugins/dokimasia/scripts/dokimasia.py`, only if the check surface or the
report identity needs it;
`plugins/dokimasia/tests/fixtures/dispositions/build.py` and the fixtures it
emits, extended rather than replaced; `plugins/dokimasia/tests/test_reconcile.py`;
`plugins/dokimasia/tests/test_demonstration.py`, where the workbook-prose test
now also covers a rule's text;
`plugins/dokimasia/docs/evidence/wildcat-app-v2.dispositions.json`, attributed
as one reviewed edit of the reviewer's file, never by a default in code;
`plugins/dokimasia/docs/evidence/wildcat-app-v2.coverage.json`,
`wildcat-app-v2.scrutiny.json` and `wildcat-app-v2-scrutiny.md`, regenerated
with `demonstrate --write-evidence`;
`plugins/dokimasia/skills/dokimasia/DEMONSTRATION.md`, the source digests of
every one of its four files this step changed, with the demo frontier line
unchanged; the root `README.md` `front-door:demo` marker for
`dokimasia-wildcat-app-v2-scrutiny`, whose digest follows the demonstration
record; `tests/promise_machine_coverage.json`, the `runtime` bindings of
`dokimasia-disposition-closure` and `dokimasia-drafted-dispositions` re-bound to
the two changed schema digests; `.horos/boundary.json` and `.horos/census.json`,
regenerated last by
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` and
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`
after every other file has landed and before the commit.

**Tests.** Extend `test_reconcile.py`, which starts this run at 55 tests, with
one test per refusal: a confirmed entry with no `confirmed_by`, a blank one and
a non-string one; a `rule` id the table does not hold; a rule row with blank
`text` and one with blank `stated_by`; a `rules` value that is not an object;
an unconfirmed entry carrying `confirmed_by` and one carrying `rule`; and the
committed `dokimasia-v2.1.0` shape refusing on its first confirmed entry with
the item and field named and no coverage record produced. Add the arithmetic:
`confirmations.people` equals the count of distinct `confirmed_by` values,
`by_person` sums to `disposed`, `individual` plus every `by_rule.*.applied`
equals `disposed`, a `rules` row nobody applied reports `applied` zero rather
than refusing, and a changed attribution changes the canonical coverage digest.
Add the mixed fixture asserting the numerator counts attributed confirmations
only, the refusal driven through the command line as well as `reconcile()`,
each cap at its bound and one over it, `confirmed_by` and `stated_by` at 128
bytes, a rule id at 64 bytes in one safe segment, rule text at the 512-byte
reason cap and the table at 256 rows, and the emitted record validating against
the committed schema. In `test_demonstration.py`, the existing
`test_the_committed_record_carries_no_workbook_prose` gains the rule text and
the five column names are still refused. Elenchus runner:
`python3 plugins/dokimasia/scripts/dokimasia.py reconcile --check --candidate rule-table --criterion unattributed-confirmation-refused --report {report}`;
report format `protasis-design-report/v1`; report file
`.hexaemeron/reports/conformance/rule-table-unattributed-confirmation-refused.json`.

**Disciplines.** phylax: this step opens the one new boundary, a person's name
and a rule's text read from a reviewer-supplied file into the committed record,
and the parameter caps, the workbook-prose refusal and the rule that no code
path writes either field are its controls; the unverifiable identity is stated
in ADR-003 rather than closed. ephoros: the `confirmations` block answers the
study's first two on-call questions, and this is the step that emits it.
metron: none, every new count is a dictionary increment inside the pass the
reconciler already makes, and no change is made for speed. elenchus: none, no
failure in hand; every refusal lands with a test that fails without it.
hypomnema: this is the step that exists for it, and ADR-003, the committed
design record, the coverage contract's new section and the attributed pinned
set are four of the six homes the study's section 12 names.

## Step 2: Carry attribution through a proposal regeneration

**Goal.** Make `propose` carry every attributed entry and the `rules` table
forward byte for byte, draft no attribution on any branch, and refuse before
writing when either cannot be preserved.

**Entry.** Step 1 is merged. The design checker admits `step:2` by consuming
the passing `rule-table-unattributed-confirmation-refused` report.

**Exit.** A regeneration against a moved inventory carries every attributed
entry and the `rules` table forward byte for byte and reports the preserved
count on stderr; a regeneration that cannot carry an attributed entry or the
table forward refuses and writes nothing; no branch of the proposal surface
writes `confirmed_by` or `rule`, asserted against the module source and by
driving every branch; a drafted set carrying either field breaches its schema
check before the write; and the regenerated pinned set is byte-identical to the
committed one. Proved by
`python3 scripts/run_checks.py --scope dokimasia --scope root && python3 scripts/demonstrations.py check --root . && python3 scripts/check_public_front_door.py && python3 plugins/dokimasia/scripts/dokimasia.py propose --check --candidate rule-table --criterion attribution-preserved-on-regeneration --report .hexaemeron/reports/conformance/rule-table-attribution-preserved-on-regeneration.json`.

**Files.** `plugins/dokimasia/scripts/dokimasia_lib/propose.py`;
`plugins/dokimasia/scripts/dokimasia.py`, only if the check surface needs it,
in which case its DEMONSTRATION.md `program` digest and the root README marker
move in this step; `plugins/dokimasia/tests/test_propose.py`;
`plugins/dokimasia/tests/fixtures/dispositions/build.py` and the fixtures it
emits; `plugins/dokimasia/docs/proposal-rules.md`, its "Regeneration" and "What
a proposal never does" sections; `.horos/boundary.json` and
`.horos/census.json`, regenerated last by the two `horos.py scan .` commands
step 1 names.

**Tests.** Extend `test_propose.py`, which starts this run at 24 tests, with:
an attributed entry surviving a regeneration byte for byte; the `rules` table
surviving byte for byte, including a row nobody applies; a regeneration that
cannot preserve an attributed entry refusing and leaving the previous file
intact; the module source carrying no `confirmed_by` or `rule` literal in the
drafting surface, beside the existing `covered` assertion; every driven branch
emitting neither field; a drafted set carrying either field refusing at the
schema check before the write; and the pinned set regenerating against its own
inventory and workbook to identical bytes. Elenchus runner:
`python3 plugins/dokimasia/scripts/dokimasia.py propose --check --candidate rule-table --criterion attribution-preserved-on-regeneration --report {report}`;
report format `protasis-design-report/v1`; report file
`.hexaemeron/reports/conformance/rule-table-attribution-preserved-on-regeneration.json`.

**Disciplines.** phylax: the boundary here is inherited, the file the tool
writes and a person then edits, and the control that matters is that a
generator never writes an attribution, asserted against the source. ephoros:
the preserved count and the carried table answer the study's third on-call
question, and this step emits them. metron: none, the regeneration walks the
scoped set once as before. elenchus: none, no failure in hand. hypomnema: none,
the proposal rules committed by the previous run are the home and this step
fills in two sections rather than relocating them.

## Step 3: Report confirmations by attribution in the scrutiny record and its prose

**Goal.** Carry the coverage record's `confirmations` figures into the scrutiny
record and the rendered prose, and make `demonstrate --check` assert that the
committed prose states the people count and every rule.

**Entry.** Step 2 is merged. The design checker admits `step:3` by consuming
the passing `rule-table-attribution-preserved-on-regeneration` report.

**Exit.** The scrutiny record carries the `confirmations` figures and validates
against `scrutiny-v1.json`; the rendered scrutiny carries a section stating how
many people decided, each rule's id, text, author and applied count, and the
individual count; the committed-evidence check refuses prose that omits the
people count or any rule; a second scrutiny of the same inputs agrees; the
pinned scrutiny is regenerated from the pinned inputs, closes at 202 over 261
attributed to one person under one rule, and records its duration beside the
declared 120,000ms budget; the changed source digests and the observation line
in DEMONSTRATION.md and the root README marker follow; and the schema set is
still five. Proved by
`python3 scripts/run_checks.py --scope dokimasia --scope root && python3 scripts/demonstrations.py check --root . && python3 scripts/check_public_front_door.py && python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check --candidate rule-table --criterion pinned-confirmations-attributed --report .hexaemeron/reports/conformance/rule-table-pinned-confirmations-attributed.json`.

**Files.** `plugins/dokimasia/scripts/dokimasia_lib/demonstrate.py`;
`plugins/dokimasia/scripts/dokimasia.py`, its committed-evidence check;
`plugins/dokimasia/schemas/scrutiny-v1.json`;
`plugins/dokimasia/tests/test_demonstration.py`;
`plugins/dokimasia/docs/evidence/wildcat-app-v2.scrutiny.json` and
`wildcat-app-v2-scrutiny.md`, regenerated;
`plugins/dokimasia/skills/dokimasia/DEMONSTRATION.md`, the `scrutiny`, `report`
and `program` digests and the `check` observation line if the message changed,
with the demo frontier line unchanged; the root `README.md` marker and its
quoted observation line; `.horos/boundary.json` and `.horos/census.json`,
regenerated last by the two `horos.py scan .` commands step 1 names.

**Tests.** Extend `test_demonstration.py`, which starts this run at 32 tests,
with: the scrutiny record carrying the same `confirmations` figures as the
coverage record beside it; the rendered prose naming the people count, every
rule id, its text, its author and its applied count, and the individual count;
the prose regenerating byte for byte; the committed-evidence check refusing a
prose file that omits the people count and one that omits a rule; the pinned
regeneration test, still skipped without the two environment variables,
asserting 202 over 261 with `confirmations.people` one and
`by_rule.row-author-owns-walking-it.applied` 202; and the committed scrutiny
validating against the changed schema. Elenchus runner:
`python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check --candidate rule-table --criterion pinned-confirmations-attributed --report {report}`;
report format `protasis-design-report/v1`; report file
`.hexaemeron/reports/conformance/rule-table-pinned-confirmations-attributed.json`.

**Disciplines.** phylax: the step reads the pinned checkout and the reviewed
workbook under the existing read-only, no-subprocess, no-socket boundary and
commits neither's bytes; the only new prose in the record is the name and rule
text step 1 already bounded. ephoros: the rendered section is where the
study's first question is answered for a reader of the prose rather than the
JSON. metron: the declared 120,000ms budget is measured here, as it was at
288ms in the prior run; one observation on one machine, not a benchmark, and
no change is made for speed. elenchus: none, no failure in hand. hypomnema:
the regenerated scrutiny beside the attributed set is the fifth home the
study's section 12 names.

## Step 4: Move the ledger, reconcile the marketplace prose and run the demo path

**Goal.** Record the frontier row at `dokimasia-v3.1.0`, move every surface
that states the version or the frontier, cold-read the plugin's mutable
marketplace prose against the tree, and prove the study's demo path end to
end.

**Entry.** Step 3 is merged. The design checker admits `step:4` with nothing
further due, the `integration` report already written at
`.hexaemeron/reports/conformance/rule-table-pinned-confirmations-attributed.json`.

**Exit.** The ledger carries exactly one new row at `dokimasia-v3.1.0`,
incrementing evolution and retaining generation and epoch, whose digest is the
SHA-256 of the canonical `{status}|{frontier revision}|{current frontier}|{next
Fiat job}` line, with either one evidenced next job or `mature` with its
evidence; the `**Current frontier.**` line is identical across
`plugins/dokimasia/README.md`, `AGENTS.md` and `skills/dokimasia/SKILL.md`,
and the README's `Next Fiat job` line reads `Use /hexaemeron:fiat to
<topic>.` followed by the fixed cold-read sentence, or `None -- mature.`; the
README's "remain to be implemented" paragraph and the `AGENTS.md` "What this
plugin does not yet do" section describe the tree as it is; both host
manifests, both marketplace entries, the skill metadata, `test_scaffold.py`
and `test_version_propagation.py` name `3.1.0`; the `dokimasia-disposition-closure`
promise text names attribution and the coverage bindings still check; and the
four demo commands from the study's section 1 exit zero in order. Proved by
`python3 scripts/run_checks.py --scope dokimasia --scope root --scope marketplace --scope promise-machine && python3 -m unittest tests.test_evolution_contract tests.test_marketplace_prose tests.test_version_propagation && python3 scripts/promise_machine.py coverage --check && python3 plugins/dokimasia/scripts/dokimasia.py selftest --candidate rule-table --criterion frontier-row --report .hexaemeron/reports/conformance/rule-table-frontier-row.json && python3 plugins/dokimasia/scripts/dokimasia.py reconcile --check && python3 plugins/dokimasia/scripts/dokimasia.py propose --check && python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check && python3 scripts/run_checks.py --scope dokimasia`.

**Files.** `plugins/dokimasia/skills/dokimasia/EVOLUTION.md`, one row, written
once; `plugins/dokimasia/skills/dokimasia/SKILL.md`, its metadata version, its
marketplace block and the `dokimasia-disposition-closure` promise;
`plugins/dokimasia/README.md`; `plugins/dokimasia/AGENTS.md`;
`plugins/dokimasia/.claude-plugin/plugin.json`;
`plugins/dokimasia/.codex-plugin/plugin.json`; `.claude-plugin/marketplace.json`;
`.agents/plugins/marketplace.json`; `plugins/dokimasia/tests/test_scaffold.py`;
`tests/test_version_propagation.py`; `tests/promise_machine_coverage.json`,
only if the changed promise text moves a bound digest;
`plugins/dokimasia/skills/dokimasia/DEMONSTRATION.md` and the root `README.md`
marker, only if `scripts/dokimasia.py` changes for the version;
`.horos/boundary.json` and `.horos/census.json`, regenerated last by the two
`horos.py scan .` commands step 1 names. No private repository, branch or path
is named in any of them; the programme note and surveys are named only as held
by the maintainer, by date.

**Tests.** Extend `test_scaffold.py`, which starts this run at 37 tests, so the
ledger's latest row is `dokimasia-v3.1.0` with a digest that recomputes from
its canonical line and the version agrees across the ledger, both manifests,
both marketplace entries, the skill metadata and the README. The repository's
own `tests/test_evolution_contract.py`, `tests/test_marketplace_prose.py` and
`tests/test_version_propagation.py` are the gates for the row, the prose and the
propagated version, and are extended only where their pinned maps name the
version. Elenchus runner:
`python3 plugins/dokimasia/scripts/dokimasia.py selftest --candidate rule-table --criterion frontier-row --report {report}`;
report format `protasis-design-report/v1`; report file
`.hexaemeron/reports/conformance/rule-table-frontier-row.json`.

**Disciplines.** phylax: none new, this step changes prose and version
strings and opens no input path. ephoros: none, nothing here runs unattended
and no signal is added. metron: none, no runtime change. elenchus: none, no
failure in hand. hypomnema: the ledger row and the maturity judgement are the
sixth home the study's section 12 names, and the cold-read of the README and
`AGENTS.md` is the obligation "What every frontier run owes" places on this
step.
