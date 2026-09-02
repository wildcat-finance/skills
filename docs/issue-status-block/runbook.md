# Runbook: record an open issue's status where the census reads it

Three steps. The contract's bytes are fixed in a decision record before any
parser reads them, the reader lands in the one module that already reads issue
bodies, and the last step runs the demo path from the study's problem statement.

```design-lock
schema | protasis-design-evidence/v1
sha256 | d7d900ad246de9857aab9f43dd6d39a44be1621bd243ead448b1c4a05ecbe86f
candidate | extend-issue-check
```

## Step 1: Fix the marker contract and commit the spec

**Goal.** Record the exact delimiters and the one-block rule in a decision
record, and commit the study and runbook beside it, before any code matches
those bytes.
**Entry.** The run branch `fiat/1057-record-an-open-issue-s-status-where-the-cen`
at its cut from `main` `51fb586e41f67bff1cd53bed8414e3fc63ff48cb`.
**Exit.** `docs/issue-status-block/study.md`, `docs/issue-status-block/runbook.md`
and `docs/decisions/ADR-068-fix-the-issue-status-block-markers.md` committed,
with the ADR stating the delimiters, the one-block rule, the refusal of a
fenced-only occurrence, and the obligation the Atlas dependency extractor
inherits from issue #497. Proved by
`python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/issue-status-block/study.md`
and `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/ADR-068-fix-the-issue-status-block-markers.md`
both exiting zero, and `python3 -m unittest discover -s tests` no worse than its
recorded entry baseline.
**Files.** `docs/issue-status-block/study.md`,
`docs/issue-status-block/runbook.md`,
`docs/decisions/ADR-068-fix-the-issue-status-block-markers.md`.
**Tests.** No new test module. This step's deliverables are documents and the
two linters above are their check. Elenchus runner contract for any fix in this
step: `python3 -m unittest discover -s tests 2>&1 | tee {report}`, plain
unittest text output, report at `.hexaemeron/elenchus-step-1.txt`.
**Disciplines.** phylax: none, this step adds no boundary and reads no outside
input. ephoros: none, documents emit no signal. metron: none, no performance
claim. elenchus: none, no failure in hand at entry. hypomnema: the marker bytes
are expensive to reverse once another repository matches them, which is the
whole reason this step exists.

## Step 2: Read a status block in the issue contract

**Goal.** Teach the one module that already reads issue bodies to find and
refuse a status block, keeping a single parser of the contract.
**Entry.** Step 1's exit state on
`fiat/1057-record-an-open-issue-s-status-where-the-cen-step-1-fix-the-marker-contract-and-commit-the`.
**Exit.** `hexctl issue-check` reports a well-formed block, refuses an
unterminated one, refuses two opened blocks, and treats a body whose only
markers sit inside a fenced span as carrying no block. Every digest binding the
controller edit invalidates is reconciled. Proved by
`python3 -m unittest plugins.hexaemeron.tests.test_issue_filing_contract` and
`python3 scripts/promise_machine.py check` both exiting zero, and
`python3 -m unittest discover -s tests` no worse than its recorded entry
baseline.
**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_issue_filing_contract.py`,
`tests/promise_machine_coverage.json`,
`plugins/hexaemeron/tests/test_issue_429_recovery.py`.
**Tests.** `plugins/hexaemeron/tests/test_issue_filing_contract.py` gains one
case per risk-register concern that this step can reach: `fenced-decoy`,
`unclosed-block`, `duplicate-block` and `control-characters`, four cases, each
made to fail against the unfixed tree before it is kept. Elenchus runner
contract: `python3 -m unittest plugins.hexaemeron.tests.test_issue_filing_contract 2>&1 | tee {report}`,
plain unittest text output, report at `.hexaemeron/elenchus-step-2.txt`.
**Disciplines.** phylax: this step parses an issue body read from a local path
and from GitHub over REST, so the byte cap and the data-not-code treatment are
its controls. ephoros: none, the reader emits its findings to the caller and
runs no unattended path of its own. metron: none, the 134-millisecond host cost
is recorded in the design matrix as a trade taken, not a budget to hold.
elenchus: the four guard cases are this step's whole test contribution and each
must fail before it passes. hypomnema: none, the decision this step implements
is already recorded by step 1.

## Step 3: Report stale bodies and run the demo path

**Goal.** Emit a report-only count of open issues whose body carries no status
block, and prove the contract end to end on the issue this run was filed
against.
**Entry.** Step 2's exit state on
`fiat/1057-record-an-open-issue-s-status-where-the-cen-step-2-read-a-status-block-in-the-issue-contra`.
**Exit.** A report-only command lists open issues with no status block and never
gates, following ADR-053's posture. The demo path from the study's problem
statement runs: `hexctl issue-check --issue https://github.com/wildcat-finance/skills/issues/1057`
exits zero against the filed issue once its status block is added. Proved by
that command, by `python3 -m unittest plugins.hexaemeron.tests.test_issue_filing_contract`
exiting zero, and by `python3 -m unittest discover -s tests` no worse than its
recorded entry baseline.
**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_issue_filing_contract.py`,
`docs/issue-status-block/study.md`.
**Tests.** `plugins/hexaemeron/tests/test_issue_filing_contract.py` gains two
cases: the report-only command exits zero when every sampled body lacks a block,
and its output names each such issue exactly once. Elenchus runner contract:
`python3 -m unittest plugins.hexaemeron.tests.test_issue_filing_contract 2>&1 | tee {report}`,
plain unittest text output, report at `.hexaemeron/elenchus-step-3.txt`.
**Disciplines.** phylax: this step reads a list of open issues over REST, so the
existing bounded read and byte cap remain its controls and no new credential is
introduced. ephoros: this step emits the two signals the study named, the stale
count and the per-issue line, because it is the step that incurs them. metron:
none, the command runs once from a terminal and no budget is claimed. elenchus:
the two cases follow the same fail-first rule as step 2. hypomnema: none, the
report-only posture is ADR-053's and is cited rather than restated.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Exit: `docs/issue-status-block/study.md`, `docs/issue-status-block/runbook.md` and `docs/decisions/draft-fix-the-issue-status-block-markers.md` committed, with the record stating the delimiters, the one-block rule, the refusal of a fenced-only occurrence, and the obligation the Atlas dependency extractor inherits from issue #497. The record carries no number, because numbers are assigned at merge per issue #888. Proved by `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/issue-status-block/study.md`, `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/draft-fix-the-issue-status-block-markers.md` and `python3 -m unittest tests.test_decision_records` all exiting zero, and `python3 -m unittest discover -s tests` at no worse than its recorded entry baseline of 1110 passing and 0 failing. Complete replacement Files: `docs/issue-status-block/study.md`, `docs/issue-status-block/runbook.md`, `docs/decisions/draft-fix-the-issue-status-block-markers.md`.

**Why.** The runbook named ADR-068, and a number chosen now is stale before the run lands. Issue #888 records ADR-050 colliding exactly this way, and the ADR-024 duplicate that turned `main` red until #582 renumbered the Wave Delta chain. Measured against `tests/test_decision_records.py` on this tree, both `ADR-fix-the-issue-status-block-markers.md` and `ADR-XXX-fix-the-issue-status-block-markers.md` fail `test_every_filename_follows_the_convention`, because the guard globs `ADR-*.md` and then requires digits. A filename without that prefix passes. The unnumbered record therefore takes the `draft-` prefix, and #888 remains free to fix the draft form it lists as an open question.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Files: `docs/issue-status-block/study.md`, `docs/issue-status-block/runbook.md`, `docs/decisions/draft-fix-the-issue-status-block-markers.md`, `.horos/boundary.json`.

**Why.** The step adds three tracked files, and the Horos boundary describes the tracked tree it ships with, so adding them makes the committed boundary stale. Two suite modules caught it: `test_boundary_currency.test_the_committed_boundary_matches_a_fresh_scan` and `test_agent_instruction.test_horos_boundary_is_current_for_the_scaffold`, both green again after `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`. The Files field named only the three documents, so it did not describe what the step actually changes. Steps 2 and 3 edit files that are already tracked and add none, so neither is affected.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.
