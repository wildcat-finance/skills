# Dokimasia: a coverage skill for frontend release testing

Δοκιμασία was the scrutiny an Athenian faced before taking office. This study
proposes a skill of that name: the examination a frontend release passes before
anybody claims it was tested.

It applies the checked design-selection and progressive conformance model from
[ADR-061](https://github.com/wildcat-finance/skills/blob/c5e9bdd02022373805f833dfebe8ed41cdb94ab5/docs/decisions/ADR-061-lock-designs-with-progressive-checked-evidence.md).

Assuming, unless corrected:

1. The target is `wildcat-finance/skills` at
   `51fb586e41f67bff1cd53bed8414e3fc63ff48cb`, and the deliverable is one new
   plugin under `plugins/dokimasia/`.
2. Python stays at `==3.14.*` with no third-party dependency, matching every
   sibling plugin and `pyproject.toml`.
3. The first application read is `wildcat-finance/wildcat-app-v2` at
   `bb9685fb7dbe9cd2f5b7683a9b3f164509dc2de9`. The skill reads that checkout
   and never writes to it.
4. The UAT workbook is a reviewed oracle whose bytes are not republished. Its
   SHA-256 is `9da2f2e8bbdb0271fac8d9a71f3f4129ca2d4ad79a4c1ee2f46412e831212a25`.
   Committed fixtures are synthetic.
5. Browser, wallet and chain execution is out of scope for this skill and stays
   in the application repository.

## 1. Problem statement

Wildcat engineers decide whether a frontend release was tested by reading a
spreadsheet. The spreadsheet lists the paths somebody thought to walk. Nothing
joins it to the application, so a route, an action or a guard that nobody
thought of is indistinguishable from one that passed, and a row that stopped
matching the product reads exactly like a row that still does.

The skill serves release engineers and UAT reviewers. Its bounded claim is:

> For one pinned application commit and one reviewed workbook, every compiled
> route, action and guard and every workbook row carries exactly one
> disposition, and every item without a reviewed oracle is named.

That is a denominator and a gap list, not a pass. The prototype is proved by
`python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check`, which
compiles the inventory from the pinned application checkout, imports the
workbook, reconciles both, and emits one digest-bound coverage record. The run
passes only if that command exits zero and every scoped item has a disposition.

## 2. Prior art

The frontend UAT assessment and its Protasis review already pinned the release
bundle, the workbook facts and the design of an execution harness. They live in
the private `wildcat-finance/skills-braintrust` repository under
`frontend-uat-agent/`, at commit `b2c91c154e0bbfeb7dcc3bc582339dc1799813df`.
The assessment found 23 page routes, 35 API handlers, 107 Jest files, 12
Storybook files and no existing Playwright, Cypress or Synpress harness at the
application snapshot. Its runbook targets the application repository, which is
why it is prior art here and not this runbook.

[PR #851](https://github.com/wildcat-finance/skills/pull/851) landed Homologia
and is the closest precedent for the mechanics of landing a plugin. Its body
records the work it could not finish: landing a plugin forces a router row,
because the promise machine requires the router to reach every plugin runtime
contract once; a router row must be graded by a corpus case; adding that case
moves `corpus_sha256`; and the recorded grading run is then bound to a stale
digest. That pull request refused to synthesise the regrade and said so. This
run inherits the same obligation and carries it as Step 1 work rather than as a
surprise.

[PR #1002](https://github.com/wildcat-finance/skills/pull/1002) introduced the
design-evidence contract this study writes against.
[PR #1003](https://github.com/wildcat-finance/skills/pull/1003) rewrote the
contributor guides and is the current statement of house voice.

Horos already lexes TypeScript for its outline maps under
`plugins/horos/tests/test_ts_lexer.py` and `test_ts_outline.py`, with a
JavaScript oracle at `plugins/horos/dev/ts_oracle.mjs`. That is the reusable
prior art for reading an application's sources without a Node toolchain. Horos
decides what an agent does not read; it compiles no route inventory and holds
no oracle, so this is borrowing a technique, not a job.

Three merges since that review bear on this run.
[PR #1038](https://github.com/wildcat-finance/skills/pull/1038) integrated
issue #949 and moved the generated payload out of this repository, so the
ADR-054 footprint figure that constrained a new plugin's size is gone and
`git ls-files .agents` reports four files.
[PR #1024](https://github.com/wildcat-finance/skills/pull/1024) landed
Anamnesis, which took router-selection case `RS-39` and added its own router
row, so this run takes `RS-40`. Anamnesis is also the nearest sibling by
subject: it preserves audit findings and the changes that answered them, where
this skill records which product behaviour has no reviewed oracle. Neither
reads the other's records, and the boundary sentence has to say so.

[framework-73](https://github.com/wildcat-finance/skills/issues/1036) records
that `RS-33` has failed in every recorded grading run. The corpus expects an
ambiguous refusal between `elenchus` and `metron`, and graded contexts answer
`elenchus`. A regrade in this run is expected to reproduce that failure. Doing
so is not evidence of a defect here.

Audit records were read as synopses. The whole-set currency check,
`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`,
exits zero at this commit, so each committed synopsis is the current reading
view of its source. The in-scope sources are `audit/AUDIT.md` through
`audit/AUDIT_SYNOPSIS.md`, and `plugins/hexaemeron/audit/AUDIT.md` through
`plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`. No skill audit record covers a
plugin that does not exist yet, so nothing further was in scope. Historical
records carry `[missing legacy field: ...]` for `Covered`, `Not checked` and
`Elenchus verdict`, which remains unknown rather than absent.

## 3. Constraints and non-goals

The starting ref is `main` at `51fb586e41f67bff1cd53bed8414e3fc63ff48cb`.
Python is `==3.14.*` and the standard library is the whole toolchain: no
sibling plugin adds a dependency and `pyproject.toml` declares none. A
spreadsheet is therefore read as a zip archive of XML by `zipfile` and
`xml.etree`, and an application's TypeScript is read by a bounded lexer, not by
a Node process.

`python3 scripts/run_checks.py` refuses a changed path with no declared owner,
so `tests/check-map-v1.json` gains a check, a scope, a dependency edge and an
owner row in the same change. The plugin also owes both host manifests, the
marketplace entries, the root registrations that name every sibling, a
byte-identical `PROMISE_MACHINE.md`, an `EVOLUTION.md` opening at generation
one, and router-selection case `RS-40` with a recorded 40-case regrade, because `RS-39` is taken.

The skill does not execute the application, drive a browser, hold a wallet or a
signing key, reach a chain, judge whether a passing row was right to pass, infer
business intent from source, or write anything into the application checkout it
reads. It replaces neither exploratory testing nor human review; it says what
has no reviewed oracle. Producing the execution harness itself stays with the
application repository and with the runbook already written for it.

## 4. Design options

The checked record is [design-evidence.json](design-evidence.json). Selection
values are measured from the candidate artefacts under `design/candidates/` by
`design/build_design_evidence.py`; no value in the record is asserted by hand.

| Candidate | Construction | Trade |
|---|---|---|
| `inventory-first` | Compile the inventory, import the workbook, reconcile both into dispositions; execution stays in the application repository | Answers the coverage question and nothing else, so somebody still has to build and run the tests |
| `harness-emitter` | Emit a Playwright harness, manifest schema and reporter into the application repository | Cheapest useful output, but it supplies a place to write tests rather than a denominator or a disposition for any item |
| `resident-driver` | Drive the browser, the wallet extension and the Safe lanes from this repository | Would answer everything, at the cost of a browser, a signing key and shared testnet state inside the distribution repository |

Selection evidence:

| Candidate | Coverage gate | Browser-free gate | Signer gate | Kill-resumable gate | Steps (minimise) | Runtime deps (minimise) | Eligible |
|---|---:|---:|---:|---:|---:|---:|---:|
| `inventory-first` | Pass | Pass | Pass | Pass | 5 | 0 | Yes |
| `harness-emitter` | Fail | Pass | Pass | Pass | 3 | 0 | No |
| `resident-driver` | Pass | Fail | Fail | Fail | 7 | 4 | No |

`inventory-first` is selected by `unique-frontier`. It loses both comparative
metrics to `harness-emitter`. It wins because `harness-emitter` fails a gate
that is not negotiable: a harness with no inventory and no dispositions leaves
the spreadsheet problem exactly where it was found.

The following conformance evidence is intentionally pending. Each report is due
only after the step that can produce it:

| Criterion | First blocked transition |
|---|---|
| scaffold contract check | Step 2 |
| inventory determinism | Step 3 |
| workbook round-trip | Step 4 |
| disposition closure | Step 5 |
| pinned demonstration | integration |

## 5. Risk register seed

This is the inventory the audit loop enumerates, not a claim that an audit has
happened.

```risk-register
workbook-bytes | the spreadsheet parser reading an untrusted zip archive | member counts sizes names and nesting are capped and no member escapes the extraction root
workbook-lineage | the import to record boundary | every source id status comment evidence and source label survives a round trip
inventory-fidelity | the pinned application reader | routes actions and guards come from a pinned commit through a bounded lexer never a network fetch or an eval
disposition-closure | the reconciliation boundary | every inventory item and workbook row carries exactly one disposition and an unreviewed or stale item refuses
target-repository-write | the application checkout under examination | the skill reads that tree and never writes creates checks out or fetches in it
partial-write | the output directory during a long compile | a killed run leaves no half-written record that verifies
path-traversal | every declared input and output path | paths stay below their declared root and no symlink is followed
subprocess-and-network | the skill process boundary | no subprocess is spawned and no socket is opened during a compile import or reconcile
cap-exhaustion | file counts byte sizes and recursion depth | every bounded limit refuses before the memory or time is spent
router-corpus-drift | the promise machine router corpus | the new plugin row carries its own graded case and the recorded run block matches the current corpus digest
evidence-digest-binding | the emitted coverage record | identities digests units and commands are recomputed rather than copied from an earlier run
marketplace-boundary | the sixteen sibling descriptions | the new skill's job does not restate a sibling's and its row names the deciding sentence
```

## 6. Glossary

- **Inventory item.** One route, API handler, user action or access guard
  compiled from the pinned application commit.
- **Workbook row.** One reviewed case imported from the UAT spreadsheet, with
  its source id, status, comment, evidence and source label preserved.
- **Reviewed oracle.** A recorded statement of what an item should do, written
  by a person, that a test or a human check can be held to.
- **Disposition.** Exactly one of covered, manual, or excluded, with a reason
  for the last two.
- **Closure ratio.** Scoped items carrying a disposition, over scoped items.
  One is the only passing value.
- **Coverage record.** The digest-bound output joining inventory, workbook and
  dispositions for one pinned commit.
- **Scrutiny.** One complete compile, import and reconcile against one pinned
  application commit and one workbook digest.

## 7. Sources

- Frontend UAT assessment and Protasis review,
  `wildcat-finance/skills-braintrust` at
  `b2c91c154e0bbfeb7dcc3bc582339dc1799813df`, private; read directly.
- `wildcat_v25_uat_v2-jack.xlsx`, SHA-256
  `9da2f2e8bbdb0271fac8d9a71f3f4129ca2d4ad79a4c1ee2f46412e831212a25`; read
  locally and not republished.
- [Pinned application](https://github.com/wildcat-finance/wildcat-app-v2/tree/bb9685fb7dbe9cd2f5b7683a9b3f164509dc2de9).
- [PR #851](https://github.com/wildcat-finance/skills/pull/851),
  [PR #1002](https://github.com/wildcat-finance/skills/pull/1002) and
  [PR #1003](https://github.com/wildcat-finance/skills/pull/1003).
- `AGENTS.md`, `PROMISE_MACHINE.md`, `plugins/hexaemeron/skills/VERSIONING.md`
  and `tests/check-map-v1.json` in this repository.
- `plugins/homologia/`, the closest scaffold precedent, and `plugins/horos/`
  for bounded TypeScript reading.
- `docs/router-selection/study.md` and `docs/router-selection/runbook.md` for
  the corpus and the recorded run block.
- `audit/AUDIT_SYNOPSIS.md` and `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`,
  current at this commit by the whole-set check.
- [ECMA-376](https://ecma-international.org/publications-and-standards/standards/ecma-376/)
  for the spreadsheet container this parser reads.

## 8. Signals and questions

The [Ephoros contract](https://github.com/wildcat-finance/skills/tree/51fb586e41f67bff1cd53bed8414e3fc63ff48cb/plugins/hexaemeron/skills/ephoros)
owns signal design. Four questions govern this prototype:

1. **What exactly was examined?** Steps 2 through 5 emit the application
   commit, the workbook digest, the inventory digest, the reconciliation digest
   and the scoped item count in one record.
2. **Which items have no reviewed oracle?** Step 4 emits the gap list by
   disposition, with a reason for every manual and excluded item.
3. **Why did a scrutiny refuse?** Steps 2 through 4 name the failing cap, path,
   parser position or unreviewed item rather than reporting a total.
4. **Did the answer change because the product changed, or because the skill
   did?** Step 5 emits the inventory digest beside the skill version, so a
   moved number has one of two explanations rather than none.

## 9. Boundaries per capability

The [Phylax contract](https://github.com/wildcat-finance/skills/tree/51fb586e41f67bff1cd53bed8414e3fc63ff48cb/plugins/hexaemeron/skills/phylax)
owns the boundary inventory and controls.

| Capability | Worth taking | Closing control |
|---|---|---|
| Spreadsheet ingestion | reviewed cases and their history | member count, size, name and depth caps; no member written outside a temporary root; no formula or macro evaluated |
| Application source reading | routes and guards a crawler cannot see | a pinned commit, a bounded lexer, read-only access, no fetch and no eval |
| Output writing | a record somebody can recheck | declared root, no symlink followed, temporary file and atomic rename |
| Plugin registration | the checked runner accepts the change | ownership declared in the same change; the router row carries its own graded case |
| Agent assistance | drafting dispositions and reasons | a person owns every disposition; the skill can propose one and can never mark an item covered on its own |

Always pin the subject, bound every input, write atomically, and publish the
gaps. Ask first before adding a dependency, widening a cap, changing a
disposition vocabulary, or reading a repository the user did not name. Never
write to the application under examination, never open a socket, never spawn a
subprocess during a scrutiny, and never report an item as covered without a
reviewed oracle.

## 10. Budget

The [Metron contract](https://github.com/wildcat-finance/skills/tree/51fb586e41f67bff1cd53bed8414e3fc63ff48cb/plugins/hexaemeron/skills/metron)
owns measurement and comparison.

The design-lock metrics are narrow on purpose: declared step count and declared
runtime dependencies, both measured from the candidate artefacts by
`python3 .hexaemeron/design/build_design_evidence.py`.

One runtime budget applies. A complete scrutiny of the pinned application and
the workbook must finish within 120,000 milliseconds on a developer machine,
measured by
`python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check --report-timing`.
There is no memory or output-size target yet, because no inventory has been
compiled and a target invented before the first measurement would be a guess.
Step 5 records the observed timing and peak record size; a later decision may
set budgets from those observations without reopening the locked selection.

## 11. Fail-closed posture

The [Elenchus contract](https://github.com/wildcat-finance/skills/tree/51fb586e41f67bff1cd53bed8414e3fc63ff48cb/plugins/hexaemeron/skills/elenchus)
owns failure localisation and guard tests.

A scrutiny stops on a workbook digest mismatch, an application commit that is
not the one declared, a zip member that breaches a cap or escapes its root, a
parser position it cannot explain, an unsafe path, a symlink, an item with no
disposition, an item whose disposition names an oracle that is absent, a
reconciliation that would write over a record it did not read, and any
conformance evidence due at the next transition. Covered, manual, excluded and
unreviewed stay terminally distinct; nothing collapses into a total.

Every defect fix begins with a reducing case that fails for the intended
reason, then proves the fixed tree and the plugin suite pass. An expected
progressive refusal is a model test, not a harness failure.

## 12. Decisions and homes

The [Hypomnema contract](https://github.com/wildcat-finance/skills/tree/51fb586e41f67bff1cd53bed8414e3fc63ff48cb/plugins/hexaemeron/skills/hypomnema)
owns durable decision placement.

| Decision | Home |
|---|---|
| Select `inventory-first` and keep execution in the application repository | this study and `design-evidence.json`, committed under the plugin's `docs/` |
| Name the skill Dokimasia and state the boundary against every sibling | `plugins/dokimasia/AGENTS.md` and the root `AGENTS.md` marketplace paragraph |
| Fix the disposition vocabulary and the closure ratio | `plugins/dokimasia/docs/decisions/ADR-001-one-disposition-per-scoped-item.md` |
| Fix the inventory rules for one application framework | the skill contract, with the rules and their caps stated in one place |
| Read spreadsheets with the standard library rather than a dependency | the same ADR, with the caps it introduces |
| Set timing or size budgets after the first measurement | a later decision record citing the Step 5 report |
| Change what an existing disposition means | a decision record plus the reviewer, never a silent edit |

The checked design record is immutable after lock. Changing its candidates,
criteria, selection or report identities requires a new run, because the
current model has no design-amendment transition.
