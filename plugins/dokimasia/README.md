# DOKIMASIA

<!-- marketplace-context:start -->
## In one line

Dokimasia compiles a frontend's routes, actions and guards into a coverage denominator and reconciles a reviewed UAT workbook against it, so every scoped item carries exactly one disposition.

**Current frontier.** Dokimasia admits a confirmed entry only when it names the person who confirmed it and, where a rule was applied, a row in the set's `rules` table stating that rule and who stated it, and its coverage and scrutiny records report confirmations by person and by rule. The pinned scrutiny of `wildcat-app-v2` at `bb9685fb` still closes at 202 over 261 with `covered` at zero, now attributed to one person under one stated rule. Every one of those entries was drafted from the workbook; none records anything observed in the running application.

**Next Fiat job.** Use /hexaemeron:fiat to drive a browser over the reviewed UAT workbook's paths with Playwright so that a browser-driven pass over a pinned application checkout, not a hand-edited file, drafts the dispositions a person then confirms: every drafted entry names the route, action or guard it exercised and the oracle it observed, the walk is pinned by application commit and browser version, and the crawler cannot write `confirmed_by` or `rule`. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## START HERE

A release gets declared tested because a spreadsheet says so. The spreadsheet
lists the paths somebody thought to walk. Nothing joins it to the application,
so three different things look identical from outside: a route that passed, a
route nobody thought of, and a row that stopped matching the product a year ago.

Dokimasia is the missing half of that picture. It compiles what the
application can actually do from a pinned commit, imports the reviewed rows
without losing what each one says, puts them side by side, and reads off what
is left over.

That comparison runs today. Every verb below is built: the pinned scrutiny of
`wildcat-app-v2` at `bb9685fb` closes at 202 over 261, each counted entry
naming the person who confirmed it and the rule it was confirmed under. What
does not run is the application itself. Every disposition is drafted from the
workbook and confirmed by a person; nothing here has watched a route happen in
a browser, which is the held next job.

## INTENDED BOUNDARY

The unit of the answer is a disposition. Every scoped route, action, guard and
workbook row ends up marked covered, manual or excluded, with a reason for the
last two, and the closure ratio says whether anything is unaccounted for. That
ratio reaches one when the deciding is finished. It never says anything passed,
because a covered item only means a person wrote an oracle and something is
held to it. An entry counts only once a person has confirmed it under their
own name, and where a rule was applied to many entries at once the rule is
written down once, with who stated it, in the set's `rules` table.

What the skill will not do is as important. It reads a checkout and never
writes to it. It runs no browser, holds no signing key and reaches no chain.
The harness that executes a release belongs to the application repository,
where the study for one already exists. A person owns every disposition; the
skill may propose one and can never mark an item covered or confirmed on its
own. A name in the record is a claim the disposition set makes; nothing here
verifies that the named person agreed.

## THE PIECES

| Verb | State |
| --- | --- |
| `selftest` | built: proves the packaging, contract and ledger agree on one version |
| `inventory` | built: compiles a pinned checkout into a digest-bound inventory |
| `workbook` | built: imports a reviewed spreadsheet without losing a row |
| `propose` | built: drafts an unconfirmed `manual` or `excluded` entry for every scoped item, never `covered` |
| `reconcile` | built: gives every scoped item exactly one disposition, counting only entries a named person confirmed |
| `demonstrate` | built: runs one scrutiny and names why a number moved |

```bash
python3 plugins/dokimasia/scripts/dokimasia.py selftest
python3 plugins/dokimasia/scripts/dokimasia.py inventory --check
python3 plugins/dokimasia/scripts/dokimasia.py inventory --root <a-pinned-checkout>
python3 plugins/dokimasia/scripts/dokimasia.py workbook --check
python3 plugins/dokimasia/scripts/dokimasia.py workbook --source <a-reviewed-workbook>
python3 plugins/dokimasia/scripts/dokimasia.py propose --check
python3 plugins/dokimasia/scripts/dokimasia.py propose \
  --inventory <inventory.json> --workbook <workbook.json> --label <name>
python3 plugins/dokimasia/scripts/dokimasia.py reconcile --check
python3 plugins/dokimasia/scripts/dokimasia.py reconcile \
  --inventory <inventory.json> --workbook <workbook.json> \
  --dispositions <a-reviewed-disposition-set.json>
python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check
python3 plugins/dokimasia/scripts/dokimasia.py demonstrate \
  --app <a-pinned-checkout> --workbook <a-reviewed-workbook> \
  --commit <the-40-character-commit> --label <name> \
  --write-evidence --report-timing
```

## WHAT IS COMMITTED HERE

[The study](docs/dokimasia-study.md) states the proposition and its twelve
answers. [The runbook](docs/dokimasia-runbook.md) states the five steps.
[ADR-001](docs/decisions/ADR-001-one-disposition-per-scoped-item.md) fixes the
disposition vocabulary and the closure ratio. Two later runs each committed
their own study, runbook and design record beside it:
[the proposal study](docs/dokimasia-proposal-study.md) with
[ADR-002](docs/decisions/ADR-002-confirmation-is-not-a-disposition.md), which
makes confirmation a boolean on an entry rather than a fourth disposition, and
[the attribution study](docs/dokimasia-attribution-study.md) with
[ADR-003](docs/decisions/ADR-003-attribution-names-a-person-and-a-stated-rule.md),
which requires a person on every confirmed entry and makes a rule a table row.
[The coverage contract](docs/coverage-contract.md) states every refusal the
reconciler makes, and [the evidence directory](docs/evidence/) holds the pinned
scrutiny, its coverage record and its attributed disposition set.

[design-evidence.json](docs/design-evidence.json) is the first run's locked
design record. It selects `inventory-first` over two lighter candidates and
ships with the 18 selection reports behind that choice, so the selection can
be rechecked here; the later
[proposal](docs/proposal-design-evidence.json) and
[attribution](docs/attribution-design-evidence.json) records check the same way
against their own transition:

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
