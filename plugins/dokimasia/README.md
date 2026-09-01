# Dokimasia

<!-- marketplace-context:start -->
## In one line

Dokimasia compiles a frontend's routes, actions and guards into a coverage denominator and reconciles a reviewed UAT workbook against it, so every scoped item carries exactly one disposition.

**Current frontier.** Dokimasia compiles a pinned checkout, imports a reviewed workbook, reconciles both into dispositions, and has run one scrutiny of `wildcat-app-v2` at `bb9685fb`: 261 scoped items, none carrying a disposition. No code path helps a reviewer write one, and 261 entries by hand is the whole cost of using this.

**Next Fiat job.** Use /hexaemeron:fiat to propose a disposition set a reviewer can edit rather than author from nothing: draft `manual` and `excluded` entries with reasons for every scoped item, and never propose `covered`, which ADR-001 reserves to a person holding an item to a reviewed oracle. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
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
| `reconcile` | built: gives every scoped item exactly one disposition |
| `demonstrate` | built: runs one scrutiny and names why a number moved |

```bash
python3 plugins/dokimasia/scripts/dokimasia.py selftest
python3 plugins/dokimasia/scripts/dokimasia.py inventory --check
python3 plugins/dokimasia/scripts/dokimasia.py inventory --root <a-pinned-checkout>
python3 plugins/dokimasia/scripts/dokimasia.py workbook --check
python3 plugins/dokimasia/scripts/dokimasia.py workbook --source <a-reviewed-workbook>
python3 plugins/dokimasia/scripts/dokimasia.py reconcile --check
python3 plugins/dokimasia/scripts/dokimasia.py reconcile \
  --inventory <inventory.json> --workbook <workbook.json> \
  --dispositions <a-reviewed-disposition-set.json>
python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check
python3 plugins/dokimasia/scripts/dokimasia.py demonstrate \
  --app <a-pinned-checkout> --workbook <a-reviewed-workbook> \
  --commit <the-40-character-commit> --label <name> --report-timing
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
