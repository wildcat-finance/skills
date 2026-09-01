# Dokimasia: proposed dispositions, runbook

Derived from [the study](dokimasia-proposal-study.md). Four steps, in dependency order. Each is one
pull request against the step below it, green at both ends.

The order is not a preference. The design record's three conformance gates each
block a named transition, and Fiat runs the checker immediately before opening
that step, so the evidence a gate needs is produced by the step before it. That
fixes the sequence: the reconciler learns about confirmation first, because
`reconcile --check` admits step 3; the proposal surface is built second, because
`propose --check` admits step 4; and the pinned demonstration is last, because
`demonstrate --check` admits integration.

```design-lock
schema | protasis-design-evidence/v1
sha256 | a27b3d090ab1f6e3d50627d3b38509f64949fc70d693a778637354825b6afdff
candidate | confirmed-flag
```

## Step 1: Commit the specification, the decision and the schema

**Goal.** Land everything this run decided before any behaviour changes, so the
three later steps are read against a committed spec rather than against a
conversation.

**Entry.** The run branch `fiat/dokimasia-proposed-dispositions` at
`f3af97e9fde2be6cbd1d831d010a212b0c379f01`, with the study receipted and the
design checker admitting `design-lock`.

**Exit.** The study, runbook, design record, its 15 selection reports and its
generator are committed under `plugins/dokimasia/docs/`; ADR-002 records
confirmation as a field rather than a fourth disposition, and the reading taken
on what refusal means for an unconfirmed entry; `schemas/dispositions-v1.json`
declares the disposition set including its `confirmed` field, using only
keywords `schema.py` already supports; `docs/proposal-rules.md` declares the
reason templates. No runtime behaviour changes. Proved by
`python3 scripts/run_checks.py --scope dokimasia && python3 plugins/dokimasia/scripts/dokimasia.py selftest --check && python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py plugins/dokimasia/docs/proposal-design-evidence.json --transition design-lock`.

**Files.** `plugins/dokimasia/docs/dokimasia-proposal-study.md`;
`plugins/dokimasia/docs/dokimasia-proposal-runbook.md`;
`plugins/dokimasia/docs/proposal-design-evidence.json`, which is this run's own
record; the prior frontier's `docs/design-evidence.json` is not touched. Its 15
reports land in the existing `plugins/dokimasia/docs/reports/selection/`, which
is the path the record declares relative to itself, and their names carry this
run's candidate ids so none collides with the prior run's;
`plugins/dokimasia/docs/design/build_proposal_design_evidence.py`;
`plugins/dokimasia/docs/decisions/ADR-002-confirmation-is-not-a-disposition.md`;
`plugins/dokimasia/docs/proposal-rules.md`;
`plugins/dokimasia/schemas/dispositions-v1.json`.

**Tests.** Extend `plugins/dokimasia/tests/test_selftest.py` so the committed
schema set is asserted to hold five schemas rather than four, and add a test
that `schema.py` accepts every keyword `dispositions-v1.json` uses, which is the
gate finding S5-R4-01 left behind for any fifth schema. No new behaviour is
under test because none ships here. Elenchus runner:
`python3 plugins/dokimasia/scripts/dokimasia.py selftest --check --report {report}`;
report format `protasis-design-report/v1`; report file
`.hexaemeron/reports/conformance/confirmed-flag-scaffold.json`.

**Disciplines.** phylax: none, the step opens no boundary and ships no code that
reads input. ephoros: none, nothing here runs unattended. metron: none, no
performance claim and no change made for speed. elenchus: none, no failure in
hand. hypomnema: this is the step that exists for it, and ADR-002, the proposal
rules and the committed schema are the three homes the study's item 12 named.

## Step 2: Admit a disposition only where a person confirmed it

**Goal.** Make the reconciler read the `confirmed` field, refuse an unconfirmed
entry as a disposition, and name every one it refused, so a generated set closes
at zero until somebody decides something.

**Entry.** Step 1 is merged. The design checker admits `step:2`, which has no
evidence due.

**Exit.** A disposition entry carries a required `confirmed` boolean; an entry
with `confirmed` false is admitted as no disposition, leaves its item in
`undisposed`, and appears in a new `unconfirmed` list in the coverage record
with its drafted state and reason intact; the counts block states confirmed
dispositions, unconfirmed entries and undisposed items as three separate
figures; a set whose entries are all unconfirmed produces a closure ratio of
zero over the scoped count; an entry missing the field refuses by name rather
than defaulting either way; the coverage record still validates against its
committed schema. Proved by
`python3 scripts/run_checks.py --scope dokimasia && python3 plugins/dokimasia/scripts/dokimasia.py reconcile --check --report .hexaemeron/reports/conformance/confirmed-flag-proposal-refused-unconfirmed.json`.

**Files.** `plugins/dokimasia/scripts/dokimasia_lib/reconcile.py`;
`plugins/dokimasia/schemas/coverage-v1.json`;
`plugins/dokimasia/schemas/dispositions-v1.json`;
`plugins/dokimasia/tests/fixtures/dispositions/`;
`plugins/dokimasia/tests/test_reconcile.py`;
`plugins/dokimasia/docs/coverage-contract.md`.

**Tests.** Cover an all-unconfirmed set closing at zero and naming every entry;
a mixed set closing at exactly the confirmed count; an entry missing the
`confirmed` field refusing by name; an unconfirmed `covered` entry, which must
refuse for the reasons `covered` already refuses rather than being excused by
being unconfirmed; the three counts agreeing with the scoped set three ways as
the existing arithmetic tests require; and the emitted record validating against
the committed schema. Extend the committed fixtures rather than replacing them,
so the prior run's cases keep running. Every new cap is a parameter, never a
module-level value a caller can lower, which is the pattern S2-R1-01 and
S3-R1-03 both recorded. Elenchus runner:
`python3 plugins/dokimasia/scripts/dokimasia.py reconcile --check --report {report}`;
report format `protasis-design-report/v1`; report file
`.hexaemeron/reports/conformance/confirmed-flag-proposal-refused-unconfirmed.json`.

**Disciplines.** phylax: the step widens what the reconciler accepts from an
operator-supplied record, so the entry-shape check gains a field and keeps
S4-R3-01's named-refusal rule. ephoros: the three separate counts are the study's
second on-call question, and this is the step that emits them. metron: none, the
join walks the same scoped set once and no speed change is made. elenchus: none,
no failure in hand; the guard convention applies to any the round finds.
hypomnema: none, ADR-002 in step 1 already records the decision this implements.

## Step 3: Draft a set the reviewer edits rather than authors

**Goal.** Emit a complete disposition set from the inventory and workbook, every
entry `manual` or `excluded` with a reason drawn from the record and marked
unconfirmed, and regenerate it without touching anything a person changed.

**Entry.** Step 2 is merged. The design checker admits `step:3` by consuming the
passing `proposal-refused-unconfirmed` report.

**Exit.** `dokimasia propose` writes a set covering every scoped item; no branch
constructs `covered` and a test proves the absence against the module source and
against every driven branch; each reason is drawn from the item's kind and
source or the case's sheet and identifier, is non-empty and inside the declared
cap; the emitted set validates against `dispositions-v1.json` before it is
written; the write is staged and renamed so a killed run leaves one whole file;
the output path takes one safe segment under a declared root; regeneration
against a moved inventory carries every confirmed or edited entry forward byte
for byte, replaces only untouched entries, adds entries for new items, and
reports the three counts; a regeneration that cannot preserve a touched entry
refuses and writes nothing. Proved by
`python3 scripts/run_checks.py --scope dokimasia && python3 plugins/dokimasia/scripts/dokimasia.py propose --check --report .hexaemeron/reports/conformance/confirmed-flag-regeneration-preserves-edits.json`.

**Files.** `plugins/dokimasia/scripts/dokimasia_lib/propose.py`;
`plugins/dokimasia/scripts/dokimasia.py`;
`plugins/dokimasia/schemas/dispositions-v1.json`;
`plugins/dokimasia/tests/fixtures/propose/`;
`plugins/dokimasia/tests/test_propose.py`;
`plugins/dokimasia/docs/proposal-rules.md`;
`plugins/dokimasia/skills/dokimasia/SKILL.md`.

**Tests.** Cover a generated set being complete over the scoped list; every
emitted disposition being `manual` or `excluded`, asserted as a set membership
over every driven branch rather than by spot-checking; the module source
carrying no `covered` literal in the proposal surface; a reason at the cap and
one over it; regeneration preserving a confirmed entry and an edited unconfirmed
entry byte for byte; regeneration adding an entry for a new inventory item and
dropping one whose item is gone; a killed write leaving the previous file
intact; a path segment carrying a separator or a parent reference refusing, with
nothing written outside the root, which is S5-R2-01's case applied to this
verb's output; and the emitted set validating against its schema. Elenchus
runner:
`python3 plugins/dokimasia/scripts/dokimasia.py propose --check --report {report}`;
report format `protasis-design-report/v1`; report file
`.hexaemeron/reports/conformance/confirmed-flag-regeneration-preserves-edits.json`.

**Disciplines.** phylax: this is the step that opens the one new boundary, a
file the tool writes and a person then edits, so the declared root, the safe
path segment, the staged write and the template rules all land here. ephoros:
the regeneration counts are the study's third on-call question and this step
emits them. metron: none, the generator walks the scoped set once inside the
existing scrutiny budget and makes no speed claim. elenchus: none, no failure in
hand. hypomnema: none, the templates' home is the proposal rules committed in
step 1, which this step fills in rather than relocates.

## Step 4: Demonstrate against the pinned release and move the ledger

**Goal.** Run one scrutiny of `wildcat-app-v2` at `bb9685fb` against workbook
`9da2f2e8` with a confirmed subset, report a closure ratio above zero drawn only
from confirmed entries, and record the frontier row.

**Entry.** Step 3 is merged. The design checker admits `step:4` by consuming the
passing `regeneration-preserves-edits` report.

**Exit.** A proposal is generated for the pinned pair, a subset is confirmed by
hand and committed as evidence, and the scrutiny reports a closure ratio above
zero whose numerator counts confirmed entries only; the committed scrutiny and
coverage records carry the confirmed and unconfirmed counts and validate against
their schemas; a second scrutiny of the same inputs agrees; the ledger carries
exactly one new row at `dokimasia-v2.1.0`, incrementing evolution and retaining
generation and epoch, with the frontier line, its SHA-256 and either an
evidenced next job or a mature status; the SKILL.md marketplace block, the
README frontier prose and the version metadata all name the same version; the
Horos boundary is regenerated with its file count read back rather than piped
away, which is S5-R5-01's correction. Proved by
`python3 scripts/run_checks.py --full && python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check --report .hexaemeron/reports/conformance/confirmed-flag-pinned-closure-above-zero.json`.

**Files.** `plugins/dokimasia/docs/evidence/wildcat-app-v2.dispositions.json`;
`plugins/dokimasia/docs/evidence/wildcat-app-v2-scrutiny.md`;
`plugins/dokimasia/docs/evidence/wildcat-app-v2.coverage.json`;
`plugins/dokimasia/docs/evidence/wildcat-app-v2.scrutiny.json`;
`plugins/dokimasia/skills/dokimasia/EVOLUTION.md`;
`plugins/dokimasia/skills/dokimasia/SKILL.md`;
`plugins/dokimasia/README.md`;
`plugins/dokimasia/.claude-plugin/plugin.json`;
`.claude-plugin/marketplace.json`;
`.horos/boundary.json`.

**Tests.** Cover the pinned scrutiny reproducing byte for byte from the two
environment variables and skipping cleanly without them, as the existing pinned
regeneration test does; the closure numerator equalling the confirmed count and
never the drafted count; a scrutiny whose confirmed subset is empty reporting
zero rather than the drafted total; the committed evidence validating against
all five schemas; the version agreeing across the ledger, both manifests, the
skill metadata and the README; and the boundary matching a fresh scan. Elenchus
runner:
`python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check --report {report}`;
report format `protasis-design-report/v1`; report file
`.hexaemeron/reports/conformance/confirmed-flag-pinned-closure-above-zero.json`.

**Disciplines.** phylax: the step reads the pinned application checkout and the
reviewed workbook, both under the existing read-only, no-subprocess, no-socket
boundary, and commits neither's bytes. ephoros: the scrutiny record's three
identities answer the study's first on-call question, and this step is where a
moved number gets its cause. metron: the scrutiny's declared 120,000ms budget is
measured here, as it was at 288ms in the prior run, and the figure stays one
observation rather than a benchmark. elenchus: none, no failure in hand.
hypomnema: the ledger row is the record this step owes, and its home is the
skill's own `EVOLUTION.md`.

### Amendment -- 2026-09-01

**What changed.** Complete replacement Files: `plugins/dokimasia/docs/dokimasia-proposal-study.md`; `plugins/dokimasia/docs/dokimasia-proposal-runbook.md`; `plugins/dokimasia/docs/proposal-design-evidence.json`, which is this run's own record, while the prior frontier's `docs/design-evidence.json` is not touched, and whose 15 reports land in the existing `plugins/dokimasia/docs/reports/selection/` because that is the path the record declares relative to itself, their names carrying this run's candidate ids so none collides with the prior run's; `plugins/dokimasia/docs/design/build_proposal_design_evidence.py`; `plugins/dokimasia/docs/decisions/ADR-002-confirmation-is-not-a-disposition.md`; `plugins/dokimasia/docs/proposal-rules.md`; `plugins/dokimasia/schemas/dispositions-v1.json`; `plugins/dokimasia/tests/test_scaffold.py`.
Complete replacement Tests: Extend `plugins/dokimasia/tests/test_scaffold.py`, which is where this plugin's packaging and contract assertions already live, with an assertion that the committed schema set holds five schemas rather than four, so a dropped schema is caught rather than inferred from a passing suite. No second keyword test is written, because `test_schema.py`'s `test_no_committed_schema_uses_an_unsupported_keyword` globs `schemas/*.json` and therefore covers `dispositions-v1.json` from the moment it is committed, which is the gate finding S5-R4-01 left behind for any fifth schema; a duplicate would drift from it. No behaviour test ships, because no behaviour ships in this step. Elenchus runner: `python3 plugins/dokimasia/scripts/dokimasia.py selftest --check --report {report}`; report format `protasis-design-report/v1`; report file `.hexaemeron/reports/conformance/confirmed-flag-scaffold.json`.

**Why.** The receipted step named `plugins/dokimasia/tests/test_selftest.py`, which this plugin does not have: its selftest and contract assertions live in `test_scaffold.py`. The step also asked for a keyword test that `test_schema.py` already performs by glob, so writing one would have added a second copy of an existing gate rather than a new check.

**Steps touched.** Step 1's Files and Tests.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.

### Amendment -- 2026-09-01

**What changed.** Complete replacement Exit: The study, runbook, design record, its 15 selection reports and its generator are committed under `plugins/dokimasia/docs/`; ADR-002 records confirmation as a field rather than a fourth disposition, and the reading taken on what refusal means for an unconfirmed entry; `schemas/dispositions-v1.json` declares the disposition set including its `confirmed` field, using only keywords `schema.py` already supports; `docs/proposal-rules.md` declares the reason templates; the committed study and runbook carry links that resolve from the directory they are committed into rather than from the controller's state directory. No runtime behaviour changes. Proved by `python3 scripts/run_checks.py --scope dokimasia && python3 plugins/dokimasia/scripts/dokimasia.py selftest && python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py plugins/dokimasia/docs/proposal-design-evidence.json --transition design-lock`.
Complete replacement Tests: Extend `plugins/dokimasia/tests/test_scaffold.py`, which is where this plugin's packaging and contract assertions already live, with an assertion that the committed schema set holds five schemas rather than four, so a dropped schema is caught rather than inferred from a passing suite. No second keyword test is written, because `test_schema.py`'s `test_no_committed_schema_uses_an_unsupported_keyword` globs `schemas/*.json` and therefore covers `dispositions-v1.json` from the moment it is committed, which is the gate finding S5-R4-01 left behind for any fifth schema; a duplicate would drift from it. No behaviour test ships, because no behaviour ships in this step. Elenchus runner: `python3 plugins/dokimasia/scripts/dokimasia.py selftest --report {report}`; report format `protasis-design-report/v1`; report file `.hexaemeron/reports/conformance/confirmed-flag-scaffold.json`.

**Why.** Both fields named `selftest --check`, and `selftest` has no `--check` flag: it takes `--report` alone, because the verb is itself the check. Running the receipted command would have exited 2 on an argparse refusal, which is the shape step 5 round 5 of the previous run recorded when an exit-status sweep reported every check verb refusing and the cause was the invocation rather than the code. The Exit field also now names the link correction the committed copies need, which the hypomnema lint catches and which the controller's own copies do not have.

**Steps touched.** Step 1's Exit and Tests.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.
