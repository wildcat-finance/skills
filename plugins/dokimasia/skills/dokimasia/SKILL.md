---
name: dokimasia
description: >
  Inspect or build the scaffold that compiles a frontend's routes, actions and
  access guards into a coverage denominator and reconciles a reviewed UAT
  workbook against it, so every scoped item carries exactly one disposition.
  A closure ratio states that nothing is unaccounted for, never that anything
  passed, and no item may be reported as covered without a reviewed oracle a
  person named. Horos decides what an agent does not read; Hexaemeron Fizz
  fuzzes contracts. Neither compiles a frontend inventory or holds an oracle.
metadata:
  version: "1.1.0"
---

# Dokimasia

## Frontier

Dokimasia owns the frontend release-coverage frontier, not Hexaemeron's
delivery or Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run another
frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Dokimasia compiles a frontend's routes, actions and guards into a coverage denominator and reconciles a reviewed UAT workbook against it, so every scoped item carries exactly one disposition.

**Current frontier.** Dokimasia compiles a pinned checkout, imports a reviewed workbook, reconciles both into dispositions, and has run one scrutiny of `wildcat-app-v2` at `bb9685fb`: 261 scoped items, none carrying a disposition. No code path helps a reviewer write one, and 261 entries by hand is the whole cost of using this.
<!-- marketplace-context:end -->

Never report an item as covered without a reviewed oracle.

The name comes from *dokimasia*, the scrutiny an Athenian faced before taking
office. The question is fitness to proceed, asked before the fact, by somebody
whose job is to look.

## The problem this exists for

A release is declared tested because a spreadsheet says so. The spreadsheet
lists the paths somebody thought to walk. Nothing joins it to the application,
so three different things look identical from outside: a route that passed, a
route nobody thought of, and a row that stopped matching the product a year ago.

Adding more rows does not fix that. The missing thing is a denominator: a
compiled list of what the application can actually do, against which the
reviewed rows can be placed. Everything left over is the answer.

## What a scrutiny says, and what it never says

A scrutiny states that, for one pinned application commit and one workbook
digest, every scoped route, action and guard and every workbook row carries
exactly one disposition, and it names every item that has no reviewed oracle.

It never states that the application works. A covered item is one a person
wrote an oracle for and a test or a reviewer was held to; whether that oracle
was right is a human judgement this skill does not make and cannot check. A
closure ratio of one means nothing is unaccounted for. It does not mean
anything passed.

It also never claims more than it read. Coverage is reported over the compiled
inventory and the imported rows, never over the application's reachable state
space, which is unbounded and which no static compile enumerates.

## The pieces

| Piece | What it does |
|---|---|
| inventory | compiles routes, API handlers, actions and guards from a pinned checkout |
| workbook | imports a reviewed spreadsheet, preserving every row's identity |
| propose | drafts an unconfirmed disposition set a reviewer edits rather than authors |
| reconcile | joins both sides and assigns exactly one disposition per scoped item |
| demonstrate | runs one complete scrutiny and emits its digest-bound record |
| selftest | proves the packaging and the contract agree, and emits its report |

Every declared verb is built.

## Boundaries

Dokimasia reads a target checkout and never writes to it. It spawns no
subprocess and opens no socket during a scrutiny. It holds no wallet, no
signing key and no chain access, and it does not execute the application: the
harness that does belongs to the application repository. A spreadsheet is an
untrusted zip archive and is read under caps on member count, member size,
name shape and nesting depth. Every path a scrutiny reads or writes stays
below its declared root, and no path this skill writes is followed through a
symlink.

A person owns every disposition. The skill drafts `manual` and `excluded`
entries and marks every one unconfirmed; only a person's confirmation admits an
entry as a disposition. It never drafts `covered`, and holds no code path that
constructs it.

## Promises

`dokimasia-scaffold-identity`, `dokimasia-source-inventory`,
`dokimasia-workbook-lineage`, `dokimasia-drafted-dispositions`,
`dokimasia-disposition-closure` and
`dokimasia-pinned-scrutiny` below are the promises this version keeps. A
promise with no case that could support it is the overclaim the root law
refuses, so nothing else is declared.

Every declared verb is built and every declared promise is kept. A reviewer
no longer authors a disposition set from nothing: `propose` drafts one covering
every scoped item, and the reconciler admits only the entries a person
confirmed, so drafting cannot move a coverage figure.

## Promise Machine contract

### dokimasia-scaffold-identity

- Promise: A successful `dokimasia selftest` establishes that both host manifests, the canonical contract, the ledger and the command surface declare one version, that this plugin's installed law copy is byte-identical to the root law, and that the declared verb table matches the verbs the command surface answers on.
- Evidence: Bounded reads of both `plugin.json` files, the canonical `SKILL.md` and its `EVOLUTION.md`, a byte comparison against the root `PROMISE_MACHINE.md`, the declared verb table, and the emitted `protasis-design-report/v1` report.
- Evidence classes: checked, recorded
- Boundary: The report establishes that the packaging, the contract and the command surface agree on one version and one verb table. It does not establish that any inventory, workbook, disposition or scrutiny operation is correct; each of those has its own promise and its own evidence.
- Authorises: Recording that the plugin is installed and internally consistent at the version it declares.
- Consequence: 1
- Refuses: A version that differs between any two declarations, a drifted installed law copy, an undeclared verb, an unsafe or oversized report path, and a report the design checker cannot consume.
- Recovery: Read the named disagreement, restore the exact bytes or the declared version, and rerun `dokimasia selftest`.
- Exceptions: none

### dokimasia-source-inventory

- Promise: A successful `dokimasia inventory` establishes that one declared root compiled to one closed, digest-bound inventory of page routes, API handlers, server actions and named guards under the stated rules and caps, and that two compiles of the same tree produce the same digest.
- Evidence: The resolved declared root, bounded non-symlink reads of every source file under it, the scanner's token stream with comments and string bodies excluded from recognition, the sorted item set, the declared caps, the canonical digest over schema, rules, caps and items, and the six exercised refusals.
- Evidence classes: checked, recorded
- Boundary: The record establishes what the declared rules recognised in the tree that was read. It does not establish that the rules are complete for a framework, that an item is reachable at runtime, that a route renders, or that anything was tested. Client-side gates are found by name, so a gate the declared list does not name is absent from the inventory rather than proved absent from the application.
- Authorises: Using the inventory as the coverage denominator, and opening the runbook step that imports a reviewed workbook against it.
- Consequence: 2
- Refuses: A symlink root, a root that is not a directory, an absolute or parent-directory path, a path escaping the declared root, a file over the byte cap, a tree over the depth cap, a tree over the file-count cap, and a compile whose two runs disagree.
- Recovery: Read the refusal, which names the rule or cap and the path that breached it, correct the input or the declared root, and rerun `dokimasia inventory`.
- Exceptions: none

### dokimasia-workbook-lineage

- Promise: A successful `dokimasia workbook` establishes that one reviewed spreadsheet imported to a closed record in which every case keeps the sheet and row it came from, the identifier it was filed under and every column the header named, that every sheet is accounted for including the ones that contributed no case and why, that a declared split carries the whole source row onto each atomic case, and that the record rebuilds every source row it read.
- Evidence: The checked archive members, the bounded reads under the declared member, total and expansion caps, measured against bytes delivered rather than bytes declared, the resolved sheet parts, the shared and inline string tables, the cached cell values with no formula consulted, the header row and its first-occurrence column map, the per-sheet accounting with a named condition for every sheet that produced no case, the case rows, the rebuilt source-row map, and the canonical digest over the cases.
- Evidence classes: checked, recorded
- Boundary: The record establishes what the workbook said. It does not establish that a recorded status is correct, that a passing row was right to pass, that the cases cover anything, or that a row a reviewer never split describes one thing. Splitting is a declaration this importer applies, not a judgement it makes. The per-sheet accounting establishes which sheets contributed nothing and under which condition; it does not establish that the condition was the right one for that sheet to meet.
- Authorises: Using the imported cases as one side of a reconciliation, and opening the runbook step that assigns dispositions.
- Consequence: 2
- Refuses: An archive over the member, total or expansion caps, a member delivering more bytes than the cap allows whatever size it declares, a member carrying a document type or entity declaration, a member name that is absolute or holds a parent-directory segment, a file that is not a zip archive, a sheet naming a missing or absent part, a cell reference past the column cap, a cell reference naming no column, a shared string index the table does not hold, an identifier appearing twice, a workbook over the case cap, a declared split matching no row in the workbook, and a split whose atomic cases disagree about the row they came from.
- Recovery: Read the refusal, which names the cap, member or identifier that caused it, correct the workbook or the declared split, and rerun `dokimasia workbook`.
- Exceptions: none

### dokimasia-drafted-dispositions

- Promise: A successful `dokimasia propose` establishes that one drafted disposition set covered every scoped item exactly once, that every entry it emitted was `manual` or `excluded`, carried a reason drawn from the record it was built from and was marked unconfirmed, that the set validated against its committed schema before it was written, and that a regeneration carried every confirmed or edited entry forward byte for byte while replacing only entries no person had touched.
- Evidence: The two bounded record reads, the scoped set built from both sides, the declared inventory and workbook digests carried onto the set, the per-kind reason templates and the declared reason cap, the emitted state vocabulary measured against the draftable pair, the recorded per-entry draft digest, the preserved, replaced, added and dropped counts, the schema check before the write, the staged write and rename, the one-segment label under the declared evidence root, and the committed fixtures the contract check drives.
- Evidence classes: checked, recorded
- Boundary: The record establishes what was drafted, not that a draft is right. It does not establish that an item belongs in the state it was drafted as, that a reason is a good reason, that a reviewer read it, or that anything was tested. A drafted set answers for nothing: it closes the ratio at zero until a person confirms an entry, and confirmation is the only thing this verb cannot do.
- Authorises: Handing a reviewer a complete draft to edit, and regenerating it against moved records without losing what they already decided.
- Consequence: 2
- Refuses: An existing set declaring the wrong schema, answering for one item twice, or holding an entry that is not an object or names no item; a template producing an empty reason or one over the declared cap; a scoped set over the item cap; a drafted set breaching its committed schema; a label that is not one safe path segment under the declared evidence root; and a write through a symlink or onto anything that is not a regular file.
- Recovery: Read the refusal, which names the entry, the cap or the label that caused it, correct the existing set or the label, and rerun `dokimasia propose`; the reviewer's file is left exactly as it was.
- Exceptions: none

### dokimasia-disposition-closure

- Promise: A successful `dokimasia reconcile` establishes that every scoped item, drawn from both the inventory and the workbook, carried exactly one disposition from the closed set, that each covered item named an oracle the workbook holds and that a person has acted on, that each manual and excluded item carried a reason, and that the disposition set was written against the exact inventory and workbook digests in front of it.
- Evidence: The two bounded record reads, the declared inventory and workbook digests compared against the records, the scoped set built from both sides, each declared disposition with its reason or oracle, the resolved oracle status, the separately stated numerator and denominator of the closure ratio, the gap list, the undisposed list, and the canonical digest over everything but the subject.
- Evidence classes: checked, recorded
- Boundary: The record establishes that the deciding was done and by whom it was declared. It does not establish that a covered item works, that its oracle was a good oracle, that a recorded status was right, or that an excluded item was correctly excluded; it establishes that somebody said so and wrote down why. A closure ratio of one means nothing is unaccounted for, never that anything passed.
- Authorises: Reporting the closure ratio and the gap list for a named inventory and workbook pair, and opening the runbook step that demonstrates against a pinned application.
- Consequence: 2
- Refuses: A disposition set declaring the wrong schema or no digest, a set naming an inventory or workbook digest that has moved, two dispositions on one item, a disposition naming an item outside the scoped set, a state outside the closed vocabulary, a covered item naming no oracle, a covered item naming an oracle the workbook does not hold, a covered item naming an oracle nobody has acted on, a manual or excluded item with an empty reason, a reason over the byte cap, a symlink or oversized input, and a scoped set over the item cap.
- Recovery: Read the refusal, which names the item and the condition it breached, correct the disposition set or recompile the record whose digest moved, and rerun `dokimasia reconcile`.
- Exceptions: none

### dokimasia-pinned-scrutiny

- Promise: A successful `dokimasia demonstrate` establishes that one scrutiny of one pinned application commit and one reviewed workbook produced a digest-bound coverage record with its closure ratio, scoped count and gap count stated as separate fields, that two scrutinies of the same inputs agree, and that a result differing from an earlier scrutiny names which of the application commit, the workbook digest or the skill version moved.
- Evidence: The pinned application commit, the workbook label and sha256, the inventory, workbook and coverage digests, the scoped count and its two sides, the separately stated numerator and denominator, the gap and undisposed counts, the measured duration beside its declared budget, and the canonical digest over everything but the subject and the timing.
- Evidence classes: checked, recorded, measured
- Boundary: The record establishes what was examined and what carries no disposition. It does not establish that the application works, that any item was tested, or that a closure ratio of one would mean anything passed. The duration is one observation on one machine and is not a benchmark. A cause names which identity moved, not why somebody moved it.
- Authorises: Publishing a scrutiny of a named commit and workbook pair, and comparing it against a later scrutiny with each difference attributed.
- Consequence: 2
- Refuses: An application commit that is not a full forty-character object name, a workbook or checkout that any earlier promise refuses, a disposition set the reconciler refuses, and a comparison whose result moved with no identity moved, which is reported as unattributed rather than as a change.
- Recovery: Read the refusal or the named cause, repin the input that moved, and rerun `dokimasia demonstrate`.
- Exceptions: none
