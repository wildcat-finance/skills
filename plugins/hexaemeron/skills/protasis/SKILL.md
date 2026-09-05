---
name: protasis
description: >-
  Hold a Fiat study and runbook to a content contract before any code is
  written: stated assumptions, testable success criteria, a chosen design with
  its trade named, the five discipline questions answered before any build, and
  steps that are discrete, green at both ends, sized for the audit loop and
  explicit about the gates they incur, including a source-bound known-failure
  inventory when audit history names one. Use when a topic is about to enter
  the study or runbook phase, when a requirement arrives vague or bundles
  several capabilities, or when deciding whether a runbook is ready to build from. Do
  not use it to run the controller or write a receipt, which belong to fiat,
  and do not use it to record a decision after the fact, which belongs to
  hypomnema.
metadata:
  version: "5.11.0"
---

<p align="center">
  <img src="../../assets/characters/protasis.png" width="1200">
</p>

# Protasis

From *protasis*, the proposition laid down before the argument runs. Nothing is
built from a topic; things are built from a proposition about a topic.

## Where this sits

Protasis owns the content contract for the `study` and `runbook` phases: what
those two documents must answer before implementation is allowed to start. It
owns no state, writes no receipt and gates nothing itself.

Surveyor may write the study packet, while Fiat keeps the artefact paths and
receipt commands. Mason and Warden later receive the exact source-bound
runbook step. Phylax, Ephoros, Metron, Elenchus, and Hypomnema answer the five
discipline questions Protasis requires; Protasis cites their contracts rather
than copying them. A decision made after the study belongs to Hypomnema's
recording rules.

Synkrisis proposes a next owner from a validated series of run observations.
That finding still needs a scoped proposition before it can become a study,
runbook, or framework change.

Its version, held frontier, next job, and maturity state live in
[EVOLUTION.md](EVOLUTION.md).

**Current state.** Protasis checks the fixed mechanical shape of study and
runbook prose, one source-bound known-failure inventory, and one closed
candidate-by-criterion design record at the transition where each item of
evidence becomes due.

## Refuse these six

1. No study, no runbook. A runbook derived from conversation instead of a
   written study is not a runbook.
2. No runbook, no implementation. A step that does not exist in the runbook
   does not get built, however small it looks.
3. No criterion, no success. A study whose success condition cannot be checked
   by a command or a named demo path is unfinished.
4. No stated assumption, no spec. Assumptions go on the page before the
   content they support.
5. No checked design record, no design lock. A preferred construction in prose
   does not authorise implementation.
6. No closed known-failure inventory, no production edit. Missing, stale, or
   unassigned entries cannot be repaired by treating an empty list as clean.

Report a refusal in three parts: what is missing, where you looked, and the one
action that clears it. Say plainly that the phase is blocked rather than
in progress. None of the four is a suggestion to proceed carefully.

If the gap is an ambiguity rather than an absence, ask one literal question
instead of picking a reading.

## Assumptions go first

List what you are assuming before writing any spec content, and say plainly
that you will proceed on them unless corrected.

```
Assuming, unless corrected:
1. Foundry, not Hardhat; the repo has foundry.toml and no hardhat.config.
2. Solidity 0.8.x with checked arithmetic; unchecked blocks are opt-in per site.
3. The exact interpreter in the repository's `.python-version`, with stdlib unittest.
4. An archive RPC is available for the capture step; without one, step 3 changes.
```

An unstated assumption is the failure this phase exists to catch. On the page,
a wrong one costs a sentence. Buried in step 4, it costs the step.

## Vague requirement, testable criterion

Restate the request as conditions a command can check, then confirm the
restatement before building on it.

```
Requirement: "make the harvester faster"

Restated:
- A full Ethereum USDC interval harvest finishes inside 20 minutes on a warm cache.
- The digest of the produced release is byte-identical to the current one.
- Peak resident memory stays under 2 GB.
Measured by metron, before and after. Are these the right targets?
```

"Faster", "cleaner", "more robust" and "production-ready" are not criteria.
Neither is a criterion that can only be checked by asking someone whether they
are happy.

## What a study must answer

1. **Problem statement.** What is being built, for whom, and what a working
   prototype means here. Name the demo path or the check that proves it.
2. **Prior art.** What exists already, in this repo, in the organisation's
   other repos, and outside. Name files, packages and standards by identifier.
   Where the topic touches something that has shipped before, read the last two
   merged pull requests that changed it before writing anything else. A run
   that could not finish something records it in the body of the last pull
   request it lands, so that is where the unfinished work of the previous run
   is written down. Carry each item forward as content here, as a stated
   non-goal, or as a named reason it stays open. Read the audit records of
   every in-scope skill the same way, before design options are drawn. Every
   discovered audit source remains authoritative. A verified synopsis is its
   normal reading view only after
   `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check
   <target-root>` runs from the target root and the whole-set currency check
   exits zero. `**/audit/AUDIT.md` maps to its sibling `AUDIT_SYNOPSIS.md`. A
   direct child `audit/rounds/<run>.md` maps to
   `audit/rounds/<run>.synopsis.md`. The root pair covers only the root source;
   it does not cover per-run or plugin records.

   Missing, stale, unsupported, or unavailable view means: read the
   authoritative source directly and record its source path and the reason.
   If the whole-set check fails, do that for every in-scope source rather than
   guessing which view remains current. A target without the renderer or a
   committed synopsis can still be studied when its source is available. If
   neither view nor source is available, readiness stops on that evidence gap.

   Keep every finding id and status, `Covered`, `Not checked`, `Elenchus
   verdict`, and `Leads not pursued`; `[missing legacy field: ...]` remains
   unknown. Then name every in-scope source, which synopsis or source was
   actually read, and the evidence for that choice. Do not claim the source
   was read when only its synopsis was read. The run's audit file, at its
   `config audit.log_path`, holds what each round found, what was fixed, and
   the leads accepted with the reason nobody pursued them. Fiat derives one
   such file per run under `audit/rounds/`, so the records of several runs are
   several files; a target that kept a shared log before that change has the
   rest of its history in `audit/AUDIT.md`. A study that cannot find the real
   reason for a decision supplies a plausible one, and the plausible one then
   governs the build: a rejected option gets rejected for the wrong cause, an
   accepted risk gets quietly reopened, and the round that already judged the
   question reads afterwards as though it never happened. Found in the study
   it costs a sentence; found in step four it costs the step.
3. **Constraints and non-goals.** The starting ref, toolchain and version pins,
   what the user ruled out, what is deferred past the prototype.
4. **Design options.** Two to four candidate constructions, each with the trade
   it makes. The prose explains the candidates; the design-evidence record
   below selects one from checked gates and comparative measurements.
5. **Risk register seed.** What the audit loop should look hardest at. In
   Solidity: trust boundaries, external calls, arithmetic, upgrade paths, key
   custody. In Python: untrusted input, subprocess and filesystem handling,
   secret material, partial writes, and what happens when a long run is killed
   halfway. The concerns go in a fenced block the audit loop can enumerate,
   info string `risk-register`, one concern per line as three pipe-separated
   fields -- a kebab-case id stable within the study, the boundary the concern
   sits at, and what the audit loop checks:

   ```risk-register
   subprocess-input | the argv of the spawned compiler | inputs are pinned and no shell is used
   partial-write | the release directory during a long harvest | a killed run leaves no half-written file that verifies
   ```

   A round then logs each id as reviewed or not applicable, so the look is an
   enumerable obligation rather than a judgement call nobody can verify
   afterwards. Prose around the block carries what a line cannot, and the ids
   are how a round cites it.
6. **Glossary seeds.** Terms the runbook and implementation will reuse, one
   line each.
7. **Sources.** Enough of a pointer to find each one again.

The five that follow are the disciplines the build will be held to. Answering
them here costs a sentence each; leaving them to the audit loop costs a step.

8. **Signals, and the questions behind them.** Two to four questions someone
   will ask at three in the morning once this runs unattended, and which steps
   emit the signals that answer them.
   [ephoros](../ephoros/SKILL.md) owns what a signal must carry.
9. **Boundaries, per capability.** Each boundary this opens, what is worth
   taking at it, and the control that closes it. This feeds item 5 rather than
   replacing it. [phylax](../phylax/SKILL.md) owns the boundary list and the
   controls.
10. **The budget, or its absence.** Any performance budget this must hold, with
    the exact command that measures it.
    [metron](../metron/SKILL.md) owns what a budget carries and how it is
    checked.
11. **The fail-closed posture.** What stops the run, and the guard-test
    convention a fix will follow.
    [elenchus](../elenchus/SKILL.md) owns the triage order and the guard rule.
12. **Decisions and their homes.** The decisions expected to be expensive to
    reverse, and the file each record will live in.
    [hypomnema](../hypomnema/SKILL.md) owns which decisions earn a record and
    where each one lives.

For items 8 through 12, "none, and here is why" is a complete answer. A lint
invoked from a terminal has no on-call question; a step that reads two files
has no budget. What is not a complete answer is silence, because silence cannot
be told apart from not having looked.

Cite those five contracts, never restate them. Each owns its own rules and each
evolves on its own ledger, so a copy here is stale the moment it is written.

### Known-failure inventory

When audit history names failures that implementation must guard before product
work starts, the study carries exactly one fenced
`known-failure-inventory` JSON object under schema
`protasis-known-failure-inventory/v1`. Each `source_views` entry names a
portable synopsis path and the SHA-256 of both that view and the authoritative
source named by its header. Each finding has one unique id, a source reference
whose prefix names a checked view, bounded non-empty locator text, a failure
statement, closed guard-path set, structural test command, report format and
path, exact expected verdict `guarded`, fixed-tree command, and one consuming
runbook step. The locator text is recorded but not interpreted as a line or
claim proof. The inventory fence is column-zero and blank-line isolated.

The test command is a bounded six-argument invocation: `python3`, one declared
Python reporter path, `--case`, the finding id, `--report`, and exactly one
argv equal to `{report}`. Its fixed-tree counterpart differs only in the report
argument. Each report and derived green path is unique under `.elenchus/`.
Filesystem-backed uniqueness uses Unicode NFC plus case folding for portable
alias detection.
Admitted report formats are `unittest-json-v1`, `forge-junit-v1`, and
`node-test-json-v1`. The caller supplies an independent expected-id set, or the
checker uses ids in visible assignment records; each record names a real
positive, column-zero runbook Step, and the inventory's consuming Steps must
match. Each assignment belongs to a contiguous nonblank block containing
assignment lines only, so adjacent prose, image labels, link titles, and
reference definitions cannot supply one. The only authoritative assignment is
a visible full line of the form
``Known-failure assignment: `kf-453-N` -> Step S`` outside fences. Raw HTML,
comments, and malformed HTML-like bytes outside one-line code spans refuse at
the runbook boundary. Every square-bracket byte outside a complete one-line
code span or fenced block also refuses there. The study keeps its separate
surface rules. Its inventory discovery tolerates unmatched inline-backtick runs
in ordinary prose, but never uses them to mask bytes. It processes or refuses
each column-zero fence candidate before that tolerance. Raw HTML, image openers,
indented fences, bad fence information, unclosed fences, and anything other
than one isolated inventory block still refuse. Fenced examples use column-zero
fences. Nested or indented fence candidates refuse. At most 128 findings, 4,096
aggregate guard paths, 1,024 bytes per path, 4,096 bytes per source reference,
failure statement, or command, and 16 command arguments are checked. Paths are
root-relative portable paths without shell metacharacters or Unicode
whitespace. The checker opens source paths through no-follow, nonblocking
directory handles. It rereads the study, runbook, views, and sources together
before returning success.

A non-empty finding set requires `no_known_findings: null`. An empty set needs
a non-null claim that repeats every checked source id and both digests, names
one real consuming step, and carries the exact Surveyor assertion
`no-known-findings`. An empty array alone never establishes readiness. The
checker reports K000 through K012 and writes no controller state or ledger.
It establishes structure and current bytes, not that Surveyor found every
failure or that any guard has run.

### Design evidence and progressive gates

The study writes one closed record to `.hexaemeron/design-evidence.json` under
schema `protasis-design-evidence/v1`. The record is the selection interface;
prose is not. It contains two to four candidate ids, one to 32 criteria, the
exact candidate-by-criterion result matrix, and one selection.

Every criterion names one of five concerns: `correctness`, `time`, `space`,
`compatibility`, or `recovery`. The complete set must be covered. A criterion
also names its owner and one of two forms:

- A hard gate has stage `selection` or `conformance`, compares a typed value by
  `equals`, `at-most`, or `at-least`, and blocks `design-lock`, `step:N`, or
  `integration`.
- A comparative metric has stage `selection`, minimises or maximises `bytes`,
  `count`, `milliseconds`, or `ratio`, and blocks `design-lock`.

The record uses these exact object forms; this excerpt is not a complete
matrix:

```json
{
  "schema": "protasis-design-evidence/v1",
  "candidates": [{"id": "streaming", "summary": "Process one bounded window."}],
  "criteria": [{
    "id": "peak-space", "concern": "space", "kind": "metric",
    "stage": "selection", "owner": "metron", "unit": "bytes",
    "comparator": "minimise", "threshold": null, "blocks": "design-lock"
  }],
  "results": [{
    "candidate": "streaming", "criterion": "peak-space", "state": "pass",
    "report": {"path": "reports/streaming-peak-space.json", "sha256": "<64 lowercase hex>"}
  }, {
    "candidate": "streaming", "criterion": "restart-safe", "state": "pending",
    "resolver": "python3 tests/prove_restart.py",
    "report": "reports/streaming-restart-safe.json", "blocks": "step:2"
  }],
  "selection": {"candidate": "streaming", "rule": "unique-frontier", "policy_ref": null}
}
```

The abbreviated example shows both result forms; an accepted record still has
two to four candidates, all five concerns, and every matrix cell.

A resolved matrix cell is `pass` or `fail` and names a report path plus its
SHA-256. The report is one closed `protasis-design-report/v1` object containing
`candidate`, `criterion`, typed `value`, `unit`, `command`, and integer `exit`;
exit must be zero. Paths are relative to the record directory and may not cross
a symlink. A pending cell instead names the exact resolver command, future
report path, and stop point it blocks. Selection evidence may be pending while
the record is drafted, but not when the design locks. Conformance evidence may
remain pending until its named step or integration transition. An unknown is
therefore a scheduled refusal, not a guessed score.

Selection is closed and mechanical. A failed selection gate removes a
candidate. The checker computes the non-dominated frontier from the selection
metrics. `unique-frontier` requires one survivor. `exact-tie-simplicity`
applies only when every checked comparative value is exactly equal across at
least two survivors. `user-policy` requires at least two survivors and a
bounded `policy_ref`. Simplicity has no other tie-breaking authority.

Run both checks before the study is receipted:

```bash
python3 "$PLUGIN_ROOT/skills/protasis/scripts/protasis.py" --study .hexaemeron/study.md
python3 "$PLUGIN_ROOT/skills/protasis/scripts/design_evidence.py" \
  .hexaemeron/design-evidence.json --transition design-lock
```

The runbook binds the accepted bytes before Step 1:

```design-lock
schema | protasis-design-evidence/v1
sha256 | <sha256 of .hexaemeron/design-evidence.json>
candidate | <selected candidate id>
```

P007 checks the block's closed shape and position. Fiat checks that its values
match the study receipt, then runs the design checker at `step:N` immediately
before opening that step and at `integration` before admitting the completed
stack. Each transition records the reports consumed there. Verification
replays every recorded transition against the unchanged record and report
bytes. A run created before the contract has no `contracts.design_evidence`
marker and remains on the legacy path; no evidence is fabricated for it.

A section reading "TBD" is a section to fill or cut. Where the request is
ambiguous, record the reading you chose and the reason for it. Never resolve an
ambiguity silently.

## What a runbook step must contain

A step is discrete: one pull request, one boundary. It is self-contained, so
someone holding only the study, the runbook and the repo at that step's entry
state can finish it. Both ends are green; no step hands the next a broken tree.
And it stays small enough to audit, because that phase dominates the clock.

```markdown
## Step N: <title>

**Goal.** One sentence.
**Entry.** The exact ref or state this step starts from.
**Exit.** Deliverables, plus the command or test that proves them.
**Files.** Paths created or changed.
**Tests.** What gets written or extended, and the expected count if known.
**Disciplines.** Which of the five apply to this step and why, or none with
the reason.
```

For a Fiat step, `Tests` also owns the runner contract used when its audit
claims a fix. It names the exact Elenchus test command with one `{report}`
argument, the report format, and the report file. Fiat sends the complete
source-bound step to Warden; Warden owns those three inputs and may not infer a
command from `Files` or replace one with a nearby suite.

The Disciplines line carries the study's items 8 through 12 down to the step
that actually incurs them. Name each discipline and the reason in one clause:

```text
**Disciplines.** phylax: this step opens the ingestion path. ephoros: it runs
unattended once deployed. metron: none, no performance claim. elenchus: none,
no failure in hand. hypomnema: the storage format is expensive to reverse.
```

A step that names a discipline without a reason has not answered; a step that
omits one has not been asked. Mason builds against the declared gates and
warden audits against them, so a gate named here is cheaper than the same gate
discovered in round three.

Three fixed points. Step 1 scaffolds: layout, toolchain pins, CI stub, licence,
and committed copies of the study and runbook. The last step demonstrates, by
running the demo path from the problem statement. Ordering is dependency order,
and a step may assume every earlier step's exit state and nothing else.

If a step's exit cannot be proved by a command, it is not an exit. "Reviewed",
"working" and "integrated" prove nothing on their own.

### Version relations

A runbook may carry one optional fenced `version-relations` block before Step
1. Absence preserves the literal-only contract. A present block carries at
most 32 physical rows, with no blank row, in this closed shape:

```version-relations
protasis | plugins/hexaemeron/skills/protasis/EVOLUTION.md | next-generation-after-integration-base
```

Each row is `skill id | EVOLUTION.md path | relation`. The skill id is
kebab-case. The path is repository-relative, contains no empty, `.` or `..`
segment, backslash or control character, ends in `EVOLUTION.md`, and has the
skill id as its parent directory. Ids and paths are unique. The sole admitted
relation is `next-generation-after-integration-base`; a partial target list is
valid because an omitted target may retain an intentional literal.

A declared target has no concrete
`<skill>-v<evolution>.<generation>.<epoch>` token outside the block. Prose,
examples, commands and amendments all count. P006
checks this shape and lexical identity. It does not open the ledger, decide
whether the relation suits the change, allocate a version, or establish what
the integration base will be.

## When one topic is several

Most topics are one capability and go straight to the study. Decompose first
only when a single request bundles capabilities that could ship and be verified
separately, or when one could be cut without rewriting the others.

The decomposition is a table and a build order, not a project plan:

| Module id | Responsibility | Depends on |
| --- | --- | --- |
| capture | Fixed-block RPC capture, digest-keyed | none |
| verify | Proof checks over a capture | capture |
| replay | Local replay boundary, no fallback | capture |
| fixture | Published fixture and its manifest | verify, replay |

Build order: capture, then verify and replay, then fixture.

Module ids are kebab-case, chosen once, never renamed mid-topic. Dependencies
point one way; if two modules each need the other, they are one module. An
interface belongs in the spec of the module that provides it. Each module then
gets its own study, and its modules become runbook steps in that order.

## Boundaries the study must state

Three tiers, each with concrete entries:

- **Always.** Both test suites before a commit. The imprimatur lint on every
  shipped document. A recorded measurement before any performance change.
- **Ask first.** Adding a dependency. Changing a storage layout or a public
  ABI. Touching CI. Widening a trust boundary. Rewriting a released digest.
- **Never.** Commit key material or an RPC credential. Edit a vendored
  directory. Delete a failing test to make a suite pass. Claim a command ran
  when it did not.

## The mechanical subset

Whether the twelve items are present, and whether items 8 through 12 carry an
answer, is settled by a parser; so is the runbook step schema. Run the bundled
check over each artefact and require exit 0:

```bash
python3 "$PLUGIN_ROOT/skills/protasis/scripts/protasis.py" --study <study>
python3 "$PLUGIN_ROOT/skills/protasis/scripts/protasis.py" <runbook>
python3 "$PLUGIN_ROOT/skills/protasis/scripts/known_failure_inventory.py" <study> <runbook> --repository <root> --expected-id <id> [--expected-id <id> ...]
python3 "$PLUGIN_ROOT/skills/protasis/scripts/design_evidence.py" <record> --transition <design-lock|step:N|integration>
```

The study mode reads items as `## N. Title` headings, 1 to 12, refuses
silence and a bare none on items 8 through 12, and reads item 5's
risk-register block against the shape above: S005 when no block names a
concern, S006 when a line does not split into the three pipe-separated
fields, S007 when a field is malformed. S008 reports a real study amendment
whose heading is not a calendar date, whose four fields are missing,
duplicated, reordered, unknown, or empty, or which is not final. A study with
no amendment and amendment examples inside fences remain unchanged. The
runbook mode reads the step
schema above, ends the last baseline step before a real amendment heading and
reports P005 when a runbook amendment does not carry the dated four-field
shape and complete replacement clauses below. It reports P006 when a present
version-relations block is open, misplaced, duplicated, oversized or malformed,
or when a declared target is also pinned to a concrete token outside that
block. P007 checks a present design-lock block's position, closed rows, schema,
digest and selected-candidate shape. Codes P000 to P007, S000 to S008, and
K000 to K012 are stable interfaces other tools cite. Deliberate exceptions
state a reason:
`<!-- protasis: allow <why> -->` on the heading line or the line above it.
Presence and shape are all the parser settles; whether an answer is any good
stays with the reviewer and the rest of this contract.

## The spec stays alive

When a decision changes, change the study first and the code second. When scope
moves, say so on the page. Both documents are committed and reviewed like any
other shipped artefact, and both go through the prose pass first.

A mid-run change is an amendment, and an amendment appends rather than edits,
so the run's earlier belief stays readable. It is a dated block at the end of
the study carrying four fields:

```markdown
### Amendment -- 2026-08-20

**What changed.** The capture step reads the header from the fixture, not RPC.
**Why.** The archive endpoint was withdrawn mid-run.
**Steps touched.** Step 3's entry and step 4's files.
**Still holding.** Steps 5 and 6 re-confirmed: each unbuilt step's entry and
exit hold as written. Step 3 does not; see below.
```

Every unbuilt step gets a verdict in the last field: its entry and exit hold,
or they do not. Do not proceed past a step whose entry the amendment broke;
report it as blocked in the contract's three parts and re-derive the runbook
from the amended study, or re-specify the step, before building on it. The
decision that forced the change is recorded where
[hypomnema](../hypomnema/SKILL.md)'s rules put it, and the amendment points at
that record rather than restating it.

A receipted runbook is amended by appending the same dated block, never by
editing or repeating a numbered step. Its `What changed` value is one or more
clauses with this exact shape:

```text
Complete replacement Exit: <the full replacement field, including its command>
```

Each clause names one of `Goal`, `Entry`, `Exit`, `Files`, `Tests` or
`Disciplines`, occurs once, and restates that entire field. More than one
changed field is written as more than one `Complete replacement <Field>:`
clause. The other three amendment fields remain `Why`, `Steps touched` and
`Still holding`, in that order. Replacement prose is still an operator claim:
the mechanical check establishes its shape and source bytes, not that the new
criterion is correct or its command will pass.

For machine-checked assignment authority, `What changed` is the first nonblank,
unfenced record after its amendment heading. Its first replacement header
begins that value. Each later header begins a column-zero paragraph after a
blank separator. Fenced and inline-code examples are not headers. A
replacement-like fragment at any other location refuses as ambiguous.

Known-failure assignment records outside every structurally valid complete
replacement `Exit` clause remain ordinary active authority and stay outside
generation comparison. Records inside those clauses form source-ordered
generations. Each generation first passes exact-line, assignment-only-block,
unique-id, and real-Step checks. Leading empty generations are allowed. The
first non-empty id-to-Step map locks assignment authority. Every later Exit
generation, including an empty one, must equal that map; pair order does not
matter. The lock cannot reset or fall back. Empty, partial, extra, or reassigned
post-lock generations refuse. A later replacement of another field creates no
generation. The final Exit generation is combined with the ordinary records,
while matching earlier generations remain readable history. Step headings come
only from the baseline before the first real amendment. Malformed amendment or
replacement boundaries, repeated clauses, and post-amendment Step headings
refuse before any generation can suppress a record.

The shared amendment scanner checks every real study or runbook amendment's
calendar date, four ordered non-empty fields, and final-section placement.
Fenced examples are not amendments. Runbook mode additionally checks the
complete-replacement syntax described above. The runbook checker treats the
first real `### Amendment -- YYYY-MM-DD`
heading as the end of the last baseline step, so amendment fields cannot answer
for a missing step field. Fiat owns exact-prefix continuity,
step topology, touched-step verdicts, receipts, recovery and the current-study
binding; Protasis does not duplicate those controller gates.

## Rationalisations

- "This is simple, it needs no spec." Simple topics need short specs, not none.
  Two lines and a checkable criterion is a spec.
- "I will write the study afterwards." Then it is documentation. The value here
  is forcing clarity before the code exists.
- "A spec slows us down." Fifteen minutes of study against hours of rework in
  the audit loop, which is the phase that already dominates the clock.
- "Requirements will change anyway." Which is why the study is edited rather
  than abandoned.
- "The user knows what they want." Every clear request carries implicit
  assumptions. This phase exists to surface them.
- "It is one feature, splitting it is overhead." If its criteria cluster into
  separately verifiable groups, every later step has to reason over the whole
  contract. A four-row table is cheaper.
- "I will decompose while planning." Planning slices steps inside a study.
  Module boundaries have to be settled before the study is written, not after.

## Red flags

- Code before any written requirement.
- Asking whether to start building before "done" has been defined.
- A step in flight that appears in no runbook.
- A design decision made and not written down.
- One study whose criteria span capabilities that could ship separately.
- Build order settled implicitly during implementation.

## Before the runbook is receipted

Report the count, then name every failure. A set reported as passed without the
count is not a report.

- [ ] The study answers all twelve items.
- [ ] Items 8 through 12 each carry an answer or a stated none with its reason.
- [ ] The last two merged pull requests touching the target were read, and
      anything they carried forward is answered, refused by name, or stated as
      still open. Say so plainly where there were none to read.
- [ ] Every discovered audit source remains authoritative. The study must name
      every in-scope source, which synopsis or source was actually read, and
      the evidence for that choice. Do not claim the source was read when only
      its synopsis was read.
- [ ] A verified synopsis was used only after
      `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check
      <target-root>` ran from the target root and the whole-set currency check
      exits zero. `**/audit/AUDIT.md` maps to its sibling
      `AUDIT_SYNOPSIS.md`. A direct child `audit/rounds/<run>.md` maps to
      `audit/rounds/<run>.synopsis.md`. The root pair covers only the root
      source.
- [ ] Missing, stale, unsupported, or unavailable view means: read the
      authoritative source directly and record its source path and the reason.
      If the whole-set check failed, every in-scope source was read directly;
      if the source was also unavailable, readiness stopped on that evidence
      gap.
- [ ] The chosen read mode retains every finding id and status, `Covered`,
      `Not checked`, `Elenchus verdict`, and `Leads not pursued`;
      `[missing legacy field: ...]` remains unknown.
- [ ] No discipline core is restated where a citation belongs.
- [ ] Assumptions are on the page and were confirmed or corrected.
- [ ] Every success criterion names a command, a test or a demo path.
- [ ] The design record covers correctness, time, space, compatibility and
      recovery with one exact result per candidate and criterion.
- [ ] Every resolved result binds a zero-exit report; every pending result names
      its resolver, future report and exact blocking transition.
- [ ] The design-lock check exits zero, and the chosen candidate is on the
      mechanically computed frontier under its declared rule.
- [ ] The runbook's design-lock block matches the record digest and selected
      candidate before Step 1.
- [ ] When known failures exist, the inventory checker exits zero against the
      independent expected-id set, exact runbook, and current source views.
- [ ] Always, ask-first and never each carry concrete entries.
- [ ] Each step carries goal, entry, exit, files, tests and disciplines.
- [ ] Every discipline a step names carries the reason it applies.
- [ ] No exit rests on anything but a command.
- [ ] Step 1 scaffolds and the last step demonstrates.
- [ ] Steps are in dependency order.
- [ ] If the topic was decomposed, every step traces to a module id.

## Hand back

Lead with the state: ready to build, or blocked on a named gap. Then give the
count of checks passed out of the total, and name each one that failed.

Keep three things apart. What the study establishes, what it assumes, and what
could not be settled. An assumption that changes the build order or the chosen
design gets said out loud, not buried in a section.

End with one action, and make it something the reader can do in a couple of
minutes: confirm an assumption, answer one question, or approve the runbook.
Name the open question rather than closing it with a guess. Corrected here, an
assumption costs a sentence. Found in the audit loop, it costs a step.

## Promise Machine contract

### protasis-known-failure-inventory

- Promise: A clean inventory result establishes that one closed `protasis-known-failure-inventory/v1` object matches an independent exact id set, current source and synopsis bytes, portable guard paths, structurally bound commands, admitted reports, and real consuming runbook steps, or carries one digest-bound no-known-findings claim.
- Evidence: The exact study and runbook bytes, caller or effective runbook expected ids, source and synopsis paths and SHA-256 values, finding fields and assignments, parsed argv, path and count caps, locked replacement-Exit map, stable K000 to K012 result, and focused hostile cases.
- Evidence classes: checked
- Boundary: This result establishes bounded structure and byte currency. A `source_ref` prefix selects a checked source view, but its locator text is opaque and does not prove that a cited line, range, or statement supports the failure. The result does not discover unknown failures, judge Surveyor's completeness, execute a guard, classify Elenchus output, write a receipt, or authorise a product edit by itself.
- Authorises: Carrying the exact checked inventory into runbook derivation and the later Fiat inoculation boundary without inferring an omitted entry or an empty success.
- Consequence: 1
- Refuses: An absent, duplicated, open, malformed, non-finite, oversized, stale, unsafe, unassigned, command-drifted, id-mismatched, bracket-bearing runbook, replacement-ambiguous, post-lock generation-drifted, or unbound empty inventory.
- Recovery: Repair the named K000 to K012 cause in the study, runbook, expected-id set, or source view, then rerun the complete read-only check.
- Exceptions: none

### protasis-study-readiness

- Promise: A study accepted by Protasis states the problem, assumptions, current state, boundaries, failure and recovery model, affected versions and success criteria, and locks one candidate through a complete checked `protasis-design-evidence/v1` matrix without predicting evidence that is not yet available.
- Evidence: The exact study, source inventory, explicit unknowns and exclusions, answered discipline questions, design record and report digests, mechanical frontier result, named future resolvers and completed study checklist.
- Evidence classes: checked, inferred, recorded
- Boundary: Readiness establishes the closed record, the reports checked at design lock and the declared stop points for later evidence. It does not establish that the selected design is correct, that pending conformance will pass, that implementation exists, or that later receipts are true.
- Authorises: Derivation of a discrete runbook from the accepted study without silently adding a new design decision.
- Consequence: 1
- Refuses: Hidden assumptions, an unstated boundary, solution-first prose, an incomplete candidate matrix, missing required concern, unresolved selection evidence, a selected dominated candidate, unsupported tie-break, untestable success language or a topic still containing several independent deliveries.
- Recovery: Name the missing question or decision, gather the required evidence, amend the study and repeat the complete Protasis review.
- Exceptions: none

### protasis-runbook-readiness

- Promise: A runbook accepted by Protasis binds the exact selected design and decomposes the study into ordered steps whose entry, modules, exit commands, files, tests and discipline effects are discrete and provable, and any optional governed-skill version relation has one closed source without a competing concrete target token. When the study carries a known-failure inventory, Fiat must join this result to the clean `protasis-known-failure-inventory` result before product work.
- Evidence: The accepted study, design-evidence digest and selected candidate, exact runbook and matching design-lock block, `protasis.py` structural result, per-step commands and files, dependency order, optional version-relations block, version boundary, completed pre-receipt checklist and, when present, the clean known-failure inventory result.
- Evidence classes: checked, inferred, recorded
- Boundary: Runbook readiness establishes buildable specification content, the design lock, and the lexical shape of a declared version relation. It does not establish correct implementation, later conformance evidence, command success, relation suitability, a selected version or integration base, audit closure or delivery completion. When an inventory is present, runbook readiness alone never authorises a product edit.
- Authorises: Entering controller-governed runbook execution at the first step and, when an inventory is present, its required inoculation gate.
- Consequence: 1
- Refuses: A missing or mismatched design lock, a step with no executable exit, mixed independent outcomes, missing affected files or tests, forward references to an undecided design, receipt language with no evidence command, an applicable inventory without a clean joined result, or a malformed, ambiguous or concretely contradicted version relation.
- Recovery: Split or reorder the failing step, supply its exact evidence and rerun both the mechanical check and the full content review.
- Exceptions: none
