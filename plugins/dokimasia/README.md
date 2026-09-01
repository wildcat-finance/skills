# Dokimasia

<!-- marketplace-context:start -->
## In one line

Dokimasia defines the boundary for compiling a frontend's routes, actions and guards into a coverage denominator and reconciling a reviewed UAT workbook against it; its current scaffold compiles nothing.

**Current frontier.** Dokimasia ships its contracts, packaging and a self-test. No inventory is compiled, no workbook is imported and no disposition is recorded, so nothing yet establishes what a release left unexamined.

**Next Fiat job.** Use /hexaemeron:fiat to compile one pinned application checkout into a closed, digest-bound inventory of routes, API handlers, actions and access guards, refusing every cap breach, symlink and parent-directory path by name and spawning no subprocess. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Start here

A release gets declared tested because a spreadsheet says so. The spreadsheet
lists the paths somebody thought to walk. Nothing joins it to the application,
so three different things look identical from outside: a route that passed, a
route nobody thought of, and a row that stopped matching the product a year ago.

Dokimasia is the planned home for the missing half of that picture. Compile
what the application can actually do from a pinned commit, import the reviewed
rows without losing what each one says, put them side by side, and read off
what is left over.

That comparison does **not** run today. The plugin ships its contract,
packaging, and a self-test. Inventory compilation, workbook import,
reconciliation and the coverage record remain to be implemented; substantive
requests refuse and name the runbook step that owes them.

## Intended boundary

The unit of the answer is a disposition. Every scoped route, action, guard and
workbook row ends up marked covered, manual or excluded, with a reason for the
last two, and the closure ratio says whether anything is unaccounted for. That
ratio reaches one when the deciding is finished. It never says anything passed,
because a covered item only means a person wrote an oracle and something is
held to it.

What the skill will not do is as important. It reads a checkout and never
writes to it. It runs no browser, holds no signing key and reaches no chain.
The harness that executes a release belongs to the application repository,
where the study for one already exists. A person owns every disposition; the
skill may propose one and can never mark an item covered on its own.

## The pieces

| Verb | State |
| --- | --- |
| `selftest` | built: proves the packaging, contract and ledger agree on one version |
| `inventory` | built: compiles a pinned checkout into a digest-bound inventory |
| `workbook` | built: imports a reviewed spreadsheet without losing a row |
| `reconcile` | refuses; step 4 owes it |
| `demonstrate` | refuses; step 5 owes it |

```bash
python3 plugins/dokimasia/scripts/dokimasia.py selftest
python3 plugins/dokimasia/scripts/dokimasia.py inventory --check
python3 plugins/dokimasia/scripts/dokimasia.py inventory --root <a-pinned-checkout>
python3 plugins/dokimasia/scripts/dokimasia.py workbook --check
python3 plugins/dokimasia/scripts/dokimasia.py workbook --source <a-reviewed-workbook>
```

## What is committed here

[The study](docs/dokimasia-study.md) states the proposition and its twelve
answers. [The runbook](docs/dokimasia-runbook.md) states the five steps.
[ADR-001](docs/decisions/ADR-001-one-disposition-per-scoped-item.md) fixes the
disposition vocabulary and the closure ratio.

[design-evidence.json](docs/design-evidence.json) is the locked design record.
It selects `inventory-first` over two lighter candidates and ships with the 18
selection reports behind that choice, so the selection can be rechecked here:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py \
  plugins/dokimasia/docs/design-evidence.json --transition design-lock
```

The conformance half is deliberately absent. Each report is produced by the
step that earns it, so asking for a later transition refuses until that step
has run. `docs/design/` holds the candidate inputs and the generator that
reproduces the record and its reports.

Each selection report records a `command` naming the generator at
`.hexaemeron/design/build_design_evidence.py`, which is where it sat in the run
that produced the record. That directory is the controller's own and is not
committed, so run the copy at `docs/design/build_design_evidence.py` instead.
The path cannot be corrected in place: it is inside the digest-bound record,
which is immutable once the study receipt pins it.

The committed runbook differs from the receipted original in one relative link,
retargeted to the filename the copy is committed under. The committed study is
byte-identical.
