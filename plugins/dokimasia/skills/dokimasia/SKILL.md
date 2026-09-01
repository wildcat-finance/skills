---
name: dokimasia
description: >
  Inspect or build the scaffold that compiles a frontend's routes, actions and
  access guards into a coverage denominator and reconciles a reviewed UAT
  workbook against it, so every scoped item carries exactly one disposition.
  The substantive operations have not shipped: the current surface self-tests
  and every other verb refuses, so never report coverage, a gap list or a
  closure ratio. Horos decides what an agent does not read; Hexaemeron Fizz
  fuzzes contracts. Neither compiles a frontend inventory or holds an oracle.
metadata:
  version: "0.1.0"
---

# Dokimasia

## Frontier

Dokimasia owns the frontend release-coverage frontier, not Hexaemeron's
delivery or Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run another
frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Dokimasia defines the boundary for compiling a frontend's routes, actions and guards into a coverage denominator and reconciling a reviewed UAT workbook against it. Its current scaffold compiles nothing.

**Current frontier.** Dokimasia ships its contracts, packaging and a self-test. No inventory is compiled, no workbook is imported and no disposition is recorded, so nothing yet establishes what a release left unexamined.
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
| reconcile | joins both sides and assigns exactly one disposition per scoped item |
| demonstrate | runs one complete scrutiny and emits its digest-bound record |
| selftest | proves the packaging and the contract agree, and emits its report |

`selftest`, `inventory` and `workbook` are built. Every other verb refuses
with the step that owes it.

## Boundaries

Dokimasia reads a target checkout and never writes to it. It spawns no
subprocess and opens no socket during a scrutiny. It holds no wallet, no
signing key and no chain access, and it does not execute the application: the
harness that does belongs to the application repository. A spreadsheet is an
untrusted zip archive and is read under caps on member count, member size,
name shape and nesting depth. Every path a scrutiny reads or writes stays
below its declared root, and no path this skill writes is followed through a
symlink.

A person owns every disposition. The skill may propose one and may never mark
an item covered on its own.

## Promises, and why one of them is not here

`dokimasia-scaffold-identity`, `dokimasia-source-inventory` and
`dokimasia-workbook-lineage` below are the promises this version keeps. A
promise with no case that could support it is the overclaim the root law
refuses, so nothing else is declared.

One more is named here so the runbook has a real interface to build against,
and so a reader can tell an unbuilt transition from one nobody thought of.
`dokimasia-disposition-closure` will establish that every scoped item
carried exactly one disposition against an exact inventory and workbook digest
pair; step 4 owes it. It is not declared as a contract section, because this
version does not establish it.

## Promise Machine contract

### dokimasia-scaffold-identity

- Promise: A successful `dokimasia selftest` establishes that both host manifests, the canonical contract, the ledger and the command surface declare one version, that this plugin's installed law copy is byte-identical to the root law, and that every unbuilt verb refuses with the step that owes it.
- Evidence: Bounded reads of both `plugin.json` files, the canonical `SKILL.md` and its `EVOLUTION.md`, a byte comparison against the root `PROMISE_MACHINE.md`, the declared verb table, the observed exit status of each unbuilt verb, and the emitted `protasis-design-report/v1` report.
- Evidence classes: checked, recorded
- Boundary: The report establishes that the packaging, the contract and the refusals agree. It does not establish that any inventory, workbook or disposition operation works, because none of them is built.
- Authorises: Recording that the scaffold is installed and consistent, and opening the runbook step that compiles the first inventory.
- Consequence: 1
- Refuses: A version that differs between any two declarations, a drifted installed law copy, an undeclared verb, a verb that answers instead of refusing, an unsafe or oversized report path, and a report the design checker cannot consume.
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
