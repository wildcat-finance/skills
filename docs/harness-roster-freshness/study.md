# Study: separate harness roster content from observation age

Assuming, unless corrected:

1. Public roster surfaces should omit `recorded.host`, `recorded.date`, and
   `recorded.base_ref`; the linked manifest remains the provenance record.
2. A manifest is current through 30 completed calendar days and stale on day
   31. A future observation date is invalid for freshness purposes.
3. Freshness is a hard, separately named repository check. A report-only
   warning would preserve the current incentive to leave an old manifest
   untouched.
4. The existing `harness-classification/v1` schema and probe observations stay
   unchanged. This work changes consumers, checks, and documentation only.

These assumptions resolve the decisions issue #1247 deliberately left open.
They follow its stated objective: a metadata-only re-probe should change the
manifest without forcing a 2.7 MB PDF rebuild, while an old manifest must stop
passing unnoticed.

## 1. Problem statement

The harness roster renderer currently embeds the manifest's observation host,
date, and base commit in `README.md`, `docs/how-to-help-shoggoth.md`, and the
contributor-guide PDF. Its drift check then compares those values as if they
were roster facts. A re-probe with no changed harness observation therefore
rewrites all three surfaces, while a six-month-old manifest passes when those
surfaces still match it.

The prototype separates two questions. `harness-roster-check` answers whether
the three public surfaces match the manifest's harness content.
`harness-roster-freshness` answers whether `recorded.date` is no more than 30
days old and not in the future. The demonstration at
`docs/harness-roster-freshness/demonstration.md` proves both paths.

Success is:

- `python3 -m unittest tests.test_harness_manifest` passes with a case showing
  that changing only all three `recorded` fields changes no rendered surface;
- `python3 scripts/render_harness_roster.py --check` passes on content-matching
  surfaces regardless of metadata-only manifest movement;
- `python3 scripts/render_harness_roster.py --check-freshness` passes at age 30
  and fails at age 31 or for a future date; and
- `python3 scripts/run_checks.py --base origin/main` selects and passes both
  declared harness checks for the final repository delta.

## 2. Prior art

Issue [#1247](https://github.com/wildcat-finance/skills/issues/1247) preserves
the live reproduction: zero of 59 per-harness fields changed, while the three
surfaces and the 2,702,681-byte PDF were tied to moving metadata. It also shows
that the old `stale-manifest` risk row duplicated roster drift instead of
measuring age.

The machinery was introduced by the only merged pull request that has changed
these newly created paths, [#1268](https://github.com/wildcat-finance/skills/pull/1268),
merged as `5bc2494c4f5802efcd8a92e58554809ac4b9f147`. There is no second merged pull
request touching them. Its carryover explicitly files #1247 as
`roster-observation-metadata`; every other carryover row is outside this
delivery or gives a reason it stayed closed.

The source at the starting commit shows four coupling sites in
`scripts/render_harness_roster.py`: `_provenance`, `readme_block`,
`guide_block`, and `pdf_label`. `write` also rebuilds the PDF unconditionally,
so removing visible metadata without changing that path would leave the main
churn intact. `tests/test_harness_manifest.py` currently requires each
`recorded` field to redden the content drift check, encoding the defect as a
test.

The whole audit-synopsis currency check passed before this study. The in-scope
source is
`audit/rounds/fiat-856-framework-13-test-the-remaining-atlas-hand-o.md`; its
verified reading view is the sibling `.synopsis.md`, checked at source digest
`d8434e51355b2d701f3df6ac6219fa708f6ec14e5857f64c33a1ea32261a8b9c`.
The synopsis retains all 78 findings, their statuses, `Covered`, `Not checked`,
Elenchus verdicts, and leads not pursued. Its `stale-manifest` rounds establish
surface-to-manifest coupling, not elapsed age. No in-scope plugin skill is
changed, so there is no plugin audit record to add.

Repository practice supplies the remaining parts: `tests/check-map-v1.json`
is the execution authority for declared checks, `scripts/run_checks.py` plans
them by scope, `datetime.date.fromisoformat` already validates the manifest's
calendar date, and ADR-077 requires new decision records to remain numberless
under `docs/decisions/drafts/` until integration assigns a number.

## 3. Constraints and non-goals

The run starts from clean `main` at
`5bc2494c4f5802efcd8a92e58554809ac4b9f147`, using the repository's Python
pin and standard-library `unittest`. The existing ReportLab dependency remains
only on the PDF write path. The renderer's read-only checks stay standard
library only.

The change does not alter the six-harness roster, probe commands,
classification vocabulary, earned-class rules, authentication observations,
schema, or the meaning of the manifest's provenance fields. It does not make a
network request, install a client, or claim that any client ran. It does not
rewrite the historical issue-856 study or audit record.

Always: run the focused module and the repository check plan before each
delivery boundary; lint every shipped Markdown document; measure any claimed
performance change before and after. Ask first: adding a dependency, changing
the manifest schema, touching hosted rulesets, or widening what a probe reads.
Never: delete a failing test, weaken credential refusal, hand-edit a generated
surface, commit a secret, or describe an unrun check as passing.

## 4. Design options

`separate-hard-freshness` removes observation metadata from all rendered
strings, compares only harness content, skips a PDF build when its roster text
already matches, and adds a separate 30-day hard check. It keeps provenance in
the linked manifest and gives each failure one meaning.

`normalised-metadata-comparison` keeps the visible metadata but teaches the
check to ignore or normalise those substrings. It gives readers a convenient
date, but the writer still regenerates changing bytes, the PDF still churns,
and the comparison must know which part of its own output it does not protect.

`separate-report-only-freshness` removes metadata from surfaces but emits only
a warning for an old manifest. It avoids churn, but it leaves stale evidence
green and does not reverse the incentive identified by #1247.

The checked `protasis-design-evidence/v1` record selects
`separate-hard-freshness`. All three candidates preserve the schema. The
normalised design is dominated on comparison branches and surface metadata;
the report-only design fails the recovery gate because stale state does not
block its declared check.

## 5. Risk register seed

```risk-register
metadata-content-coupling | the recorded block crossing into generated Markdown and PDF text | mutating host, date, and base_ref together leaves every rendered body and expectation byte-identical
stale-manifest | the manifest date against the local calendar date | age 30 passes, age 31 fails, and a future date fails under a separately declared check
no-op-pdf-build | the renderer write path when only observation metadata moved | a matching harness page skips the ReportLab subprocess and leaves the PDF bytes untouched
manifest-validation | provenance fields that no public surface renders | malformed host, date, or base_ref remains refused before either check or write proceeds
roster-drift | names, classes, observations, blockers, and PDF roster text | a real harness-content change still reddens every surface it reaches
check-graph | tests/check-map-v1.json and scope selection | both roster content and freshness checks are reachable and selected for the docs scope
clock-boundary | the host calendar read used by the freshness command | tests inject exact dates around zero, 30, 31, and future-day boundaries
generated-surface-atomicity | a content change that needs a PDF rebuild and Markdown writes | the PDF build still completes before either Markdown surface is replaced
```

## 6. Glossary seeds

- Roster content: the harness array and the fields public surfaces derive from
  it, excluding the top-level `recorded` object.
- Observation metadata: `recorded.host`, `recorded.date`, and
  `recorded.base_ref` in the manifest.
- Content drift: a public surface differing from the text derived from roster
  content.
- Manifest age: completed calendar days from `recorded.date` to the date the
  freshness check evaluates.
- Freshness budget: at most 30 calendar days, inclusive.
- Metadata-only re-probe: a valid manifest change confined to the three
  observation metadata fields.

## 7. Sources

- `scripts/render_harness_roster.py` at starting commit `5bc2494c`.
- `scripts/probe_harnesses.py` at starting commit `5bc2494c`.
- `tests/test_harness_manifest.py` and `tests/check-map-v1.json` at that commit.
- `docs/harness-classification.json` and
  `schemas/harness-classification-v1.json` at that commit.
- `docs/decisions/ADR-079-generate-the-harness-roster-from-one-probed-manifest.md`.
- `docs/atlas-harness-handoff/{study,runbook,demonstration}.md`.
- Verified synopsis
  `audit/rounds/fiat-856-framework-13-test-the-remaining-atlas-hand-o.synopsis.md`.
- GitHub issue #1247 and merged pull request #1268, read live on 2026-09-05.
- Python standard-library `datetime.date` API used by the current source.

## 8. Signals, and the questions behind them

The implementation follows [Ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md).
This is a bounded repository check, not an unattended service, so it adds no
metrics or alerts. Its command output answers: how old is the manifest, what
budget applied, did it come from the future, and which named surface carries
content drift. Step 2 owns those messages; Step 3 captures them in the demo.

## 9. Boundaries, per capability

The implementation follows [Phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md).
The existing manifest and operator-selected paths remain untrusted local
inputs, held by bounded reads, type checks, calendar validation, credential
sweeps, and fixed subprocess argv. The new clock boundary takes one local date
and compares it without network access. No dependency, secret, or new process
boundary is introduced.

## 10. The budget, or its absence

The freshness budget is semantic rather than a speed claim: at most 30
completed calendar days. `python3 scripts/render_harness_roster.py
--check-freshness` measures it. The no-op path also has a zero-write budget:
metadata-only movement may write the manifest but must write no public surface
and must not invoke the PDF builder. No runtime optimisation is claimed, so
[Metron](../../plugins/hexaemeron/skills/metron/SKILL.md) has no before-and-after
performance measurement to require.

## 11. The fail-closed posture

The implementation follows [Elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md).
Malformed provenance, a future date, age above 30, missing surfaces, content
drift, a failed PDF build, and any existing credential-shaped rendered text
all stop their command at exit 1. A discovered failure is reproduced in the
focused module, reduced to one fixture mutation, fixed at cause, and left with
a guard that fails without the fix.

## 12. Decisions and their homes

The durable decision follows
[Hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md) and lives as the
numberless draft
`docs/decisions/drafts/separate-harness-roster-content-from-observation-age.md`.
It records the dropped surface date, the 30-day hard budget, the separate check
identities, and the no-op PDF write. It supersedes only ADR-079's surface
provenance and unconditional-regeneration consequences; the manifest schema,
probe, classifications, and evidence rules remain accepted.

The check graph keeps the two checks as separate nodes. The issue-856 study
and audit stay historical; this study's `stale-manifest` row is the corrected
risk contract. No governed skill frontier or version changes.

### Amendment -- 2026-09-05

**What changed.** The selected design is now bound explicitly to its standing
decision record.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | separate-hard-freshness
record | docs/decisions/drafts/separate-harness-roster-content-from-observation-age.md
```

**Why.** Hypomnema requires a shipped study to join the selected Protasis
candidate to exactly one durable home; section 12 named that home but did not
carry the machine-readable bridge.

**Steps touched.** Step 1 copies this amended study and writes the named record.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Step 1 now repairs Hypomnema's H008 study-mode contract so
the explicit design bridge accepts the repository's established numberless ADR
draft home, while retaining every refusal on unsafe paths, invalid stable
identities, malformed records, and duplicate homes. The repair is a Hypomnema
generation change from `hypomnema-v5.7.0` to `hypomnema-v5.8.0`; it preserves
the open `duplicate-home-discovery` frontier byte for byte and adds a regression
observed red on the unfixed checker.

**Why.** The receipted study names the only repository-valid pre-integration
home, `docs/decisions/drafts/<slug>.md`, but H008 currently accepts only an
already-numbered ADR or governed-skill ledger. That makes Hypomnema reject the
authoring lifecycle its own contract requires and blocks Step 1 before the
issue-1247 implementation can begin.

**Steps touched.** Step 1 owns the Hypomnema contract repair, version ledger,
portable copies, and regression evidence. Steps 2 and 3 keep their existing
product scope.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Step 1 also rebinds the Promise Machine coverage inventory
to the reviewed Hypomnema bytes and repairs the root self-test that mistakes an
unrelated active Fiat design-evidence record for its own closed candidate set.
The prover now consumes a live record only when it contains exactly its four
declared candidates; every unrelated, absent, malformed, duplicate, empty, or
oversized record takes the existing closed fallback.

**Why.** The exact repository delta plan exposed both integration failures.
The digest failure is the intended review gate for a changed Promise Machine
surface. The candidate failure occurs in every unrelated Fiat worktree because
the repository self-test runs beside that run's valid but unrelated
`.hexaemeron/design-evidence.json`; accepting those ids makes the prover reject
its own `digest-neutral-corpus` test candidate.

**Steps touched.** Step 1 owns both bounded integration repairs and their
regressions. Steps 2 and 3 keep their existing product scope.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.
