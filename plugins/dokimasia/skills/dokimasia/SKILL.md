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

Only `selftest` is built. Every other verb refuses with the step that owes it.

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

## Promises, and why three of them are not here

`dokimasia-scaffold-identity` below is the only promise this version can keep,
so it is the only one declared. A promise with no case that could support it is
the overclaim the root law refuses.

Three more are named here so the runbook has a real interface to build against,
and so a reader can tell an unbuilt transition from one nobody thought of.
`dokimasia-source-inventory` will establish that one pinned checkout compiled to
one closed, digest-bound inventory under declared caps; step 2 owes it.
`dokimasia-workbook-lineage` will establish that a reviewed spreadsheet imported
without losing a row's id, status, comment, evidence or source label; step 3
owes it. `dokimasia-disposition-closure` will establish that every scoped item
carried exactly one disposition against an exact inventory and workbook digest
pair; step 4 owes it. None of the three is declared as a contract section,
because this version establishes none of them.

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
