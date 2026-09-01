# Dokimasia evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `dokimasia-v1.1.0`
- Frontier status: `open`
- Frontier revision: `proposed-dispositions`
- Current frontier: Dokimasia compiles a pinned checkout into a coverage denominator, imports a reviewed workbook without losing a row, reconciles both into dispositions, and has run one scrutiny of wildcat-app-v2 at bb9685fb against workbook 9da2f2e8. That scrutiny scoped 261 items and found none carrying a disposition, because no code path helps a reviewer write one and 261 entries by hand is the whole cost of using this.
- Next Fiat job: Propose a disposition set a reviewer can edit rather than author from nothing: draft `manual` and `excluded` entries with reasons for every scoped item, and never propose `covered`, which ADR-001 reserves to a person holding an item to a reviewed oracle. Accepted when a proposed set is refused by the reconciler wherever a reviewer has not confirmed it, when no proposal path can emit `covered` and a test proves no such path exists, when a reviewer's edits survive a regeneration of the proposal, and when the pinned scrutiny reports a closure ratio above zero drawn only from entries a person confirmed.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `dokimasia-v0.1.0` | baseline | `first-scrutiny` | `2b8aa0993df2c6313ea8ae66fc5f97577c75025a20ee4a61e7b5007f270c9231` | [the study](../../docs/dokimasia-study.md), [the design record](../../docs/design-evidence.json) | Versioning starts here. Dokimasia ships as a scaffold: both host manifests, the marketplace entries, the canonical contract with its four promises, this ledger, the committed study and runbook, the locked design record with its 18 selection reports, ADR-001, and a self-test that proves the packaging agrees with the contract. The held frontier is the first compiled inventory, and nothing here compiles one. |
| `dokimasia-v1.1.0` | evolution | `proposed-dispositions` | `624e18f65058b382b109ef69907e09ba11495b6de9f658dae0c392329afb99a3` | [the scrutiny](../../docs/evidence/wildcat-app-v2-scrutiny.md), [its coverage record](../../docs/evidence/wildcat-app-v2.coverage.json), [the coverage contract](../../docs/coverage-contract.md), [ADR-001](../../docs/decisions/ADR-001-one-disposition-per-scoped-item.md) | The held frontier is met. `inventory` compiles a pinned checkout under declared rules and caps; `workbook` imports a reviewed spreadsheet and accounts for every sheet including the ones that yield nothing; `reconcile` gives every scoped item exactly one disposition and refuses an unreviewed, ambiguous or stale one; `demonstrate` runs one scrutiny and names which of three identities moved when a number does. The first scrutiny of `wildcat-app-v2` at `bb9685fb` against workbook `9da2f2e8` scoped 261 items, 59 compiled and 202 imported, and reported a closure ratio of 0 over 261 in 288ms against a 120,000ms budget. That zero is the finding: the denominator now exists and nobody has decided against it. |
