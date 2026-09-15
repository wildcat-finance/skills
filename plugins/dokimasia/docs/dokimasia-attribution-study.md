# Dokimasia: attributed confirmation

Assuming, unless corrected:

1. The starting ref is `main` at `0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`,
   on branch `fiat/1352-dokimasia-3-a-reconciler-that-refuses-a-con`, and the
   run integrates back into `main`.
2. Python from the repository's `.python-version` (3.14.6), standard library
   only, as every `dokimasia_lib` module already practises. No new runtime
   dependency.
3. The suite command is `python3 scripts/run_checks.py`; the plugin scope is
   `--scope dokimasia`. Bare `unittest discover` is not a suite command here,
   because it raises `ImportError` on plugin trees and reads as clean.
4. ADR-001's three dispositions and ADR-002's `confirmed` boolean are fixed.
   Attribution is added beside the boolean, not in place of it.
5. The pinned scrutiny of `wildcat-app-v2` at `bb9685fb` against workbook
   `9da2f2e8` is regenerated, not migrated by hand. Both inputs are present on
   this machine and reach the tests through `DOKIMASIA_PINNED_APP` and
   `DOKIMASIA_PINNED_WORKBOOK`, as the existing regeneration test requires. The
   application checkout's head has moved past `bb9685fb`, so the app input is
   a detached extraction of that commit, not the live working tree.
6. The 202 confirmed entries are attributed to `Laurence Day` under one rule,
   id `row-author-owns-walking-it`, text "the reviewer who wrote a row owns
   walking it, which holds by construction of the workbook". That is what
   pull requests #1113 and #1111 recorded about how the 202 were confirmed.
   The name is the display form those bodies use. This does not change the
   design; it changes one evidence file.
7. Task issue #1352 governs the run. Its live body is withdrawn; the entry it
   carries names this job as Dokimasia desire D.1, kickoff entry 3 of 59, tier
   0, and refers to a programme note dated 5 September 2026 and four surveys,
   all held by the maintainer. Nothing here names where they are held.

I will proceed on these unless corrected.

## 1. Problem statement

A confirmed entry and a drafted one differ by one boolean. `confirmed: true`
is what admits an entry to the closure ratio, and anything with write access
to the file can set it. The committed record of `wildcat-app-v2` says 202 of
261 were confirmed and cannot say by whom or under what rule. It cannot tell a
reviewer who worked through 261 items from a script that flipped a field, and
producing those 202 required halting the previous run to ask a person by name,
because there was nowhere to write the answer down.

**Who this is for.** The person who has to cite a closure ratio for the
counterparty-history panel: a release note, a dashboard, app copy. The task
issue refuses any such citation until the figure states whose judgement it is.
The other reader is the reviewer, who wants confirming an entry to cost one
edit and wants a rule they applied to 202 rows written once.

**What a working prototype means here.** A confirmed entry carries
`confirmed_by`, a person. It may carry `rule`, an id into a set-level `rules`
table holding that rule's text and who stated it. The reconciler refuses, by
name, a confirmed entry with no person, a rule id the table does not hold, a
rule with blank text or no stated author, and an unconfirmed entry carrying
either field. The coverage record gains a `confirmations` block: how many
people decided, how many entries each confirmed, which rules were applied and
how many times, and how many entries were confirmed individually with no rule.
The scrutiny record and its rendered prose carry the same figures. `propose`
drafts no attribution and carries every attributed entry and the `rules` table
forward byte for byte. The pinned scrutiny closes at the same 202 over 261, now
attributed to one person under one rule, with `covered` still zero.

**The demo path that proves it.** Against the pinned release:

```bash
python3 plugins/dokimasia/scripts/dokimasia.py reconcile --check
python3 plugins/dokimasia/scripts/dokimasia.py propose --check
python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check
python3 scripts/run_checks.py --scope dokimasia
```

Success is checkable, one condition per acceptance clause of the held job and
one per frontier obligation:

- A confirmed entry carrying no `confirmed_by` refuses by name and is never
  counted: `reconcile --check` against a `confirmed-without-person.json`
  fixture, and a test asserting the refusal names the item and that no
  coverage record was produced.
- A rule-based confirmation records the rule, not only its result: `reconcile
  --check` against a fixture whose entries name a rule the table holds, with
  the record's `confirmations.by_rule` carrying the rule's text, its author and
  its applied count; a fixture naming an unknown rule id refuses by name.
- The coverage record reports confirmations by attribution: `reconcile
  --check` asserts `confirmations.people` equals the number of distinct
  `confirmed_by` values, `by_person` sums to `disposed`, and `individual` plus
  the sum of `by_rule.*.applied` equals `disposed`. `demonstrate --check`
  asserts the committed prose states the people count and every rule.
- A test proves an entry confirmed with no attribution is refused rather than
  counted: `test_reconcile.py` drives such an entry through `reconcile()` and
  the command line, asserts `ReconcileError`, and asserts the mixed fixture's
  numerator equals the count of attributed confirmations only.
- Frontier obligations: the ledger carries one row at `dokimasia-v3.1.0`
  whose digest matches the canonical frontier line (`test_scaffold.py`,
  `tests/test_evolution_contract.py`); every mutable marketplace surface names
  the same frontier and version (`tests/test_marketplace_prose.py`); the
  demonstration ledger's four source digests and the root README front-door
  marker match the regenerated evidence (`python3 scripts/demonstrations.py
  check --root .` and `python3 scripts/check_public_front_door.py`); the
  promise-coverage bindings for `coverage-v1.json` and `dispositions-v1.json`
  carry the new schema digests (`python3 scripts/promise_machine.py coverage
  --check`); and the Horos boundary and census match a fresh scan
  (`tests/test_demonstrations.py::HorosCensusCurrencyTests`).

## 2. Prior art

**In this repository.** The subject shipped in one run five days ago.
[#1113](https://github.com/wildcat-finance/skills/pull/1113), merged as
`27b555e0`, is the run-level pull request that carried
`dokimasia-v1.1.0` to `dokimasia-v2.1.0`;
[#1111](https://github.com/wildcat-finance/skills/pull/1111), merged as
`15400778`, is its step 4, which confirmed the 202 and moved the ledger. Both
were read in full. Two later pull requests touched `plugins/dokimasia/` without
touching the subject:
[#1279](https://github.com/wildcat-finance/skills/pull/1279) added the
demonstration ledger `skills/dokimasia/DEMONSTRATION.md`, and
[#1303](https://github.com/wildcat-finance/skills/pull/1303) recased the
README headings. Neither carries Dokimasia work forward; both add pins this
run must move, recorded in section 3.

#1113's `carryover` block holds six rows. What this run does with each:

| Row | Where it stands in this run |
| --- | --- |
| `rs40-regrade`, filed as [#1112](https://github.com/wildcat-finance/skills/issues/1112) | Still open. This run changes the marketplace description again, because the frontier line moves, and the regrade still needs an isolated context per request. Carried forward by name, not answered. |
| `venues-ownership`, none | Settled on `main`; nothing to do. |
| `step2-post-audit-commit`, none | A recorded evidence gap in the previous run, not work. Nothing to do. |
| `confirmation-attribution`, none | This run. The ledger's held job is the requirement, and #1352 is its issue. |
| `unconfirmed-59-items`, none | Unchanged. The 59 compiled items stay unconfirmed and undisposed; deciding them is the reviewer's, and an attribution shape does not decide anything. Stated as a non-goal in section 3. |
| `generated-by-unverifiable`, none | Partly answered, and the remainder stated. `confirmed_by` and `rules.*.stated_by` are claims the file makes, with no signature behind them, exactly as `generated_by` is. What changes is that the claim now exists to be checked by a reader; making it checkable by a machine needs a key this skill deliberately does not hold, and section 9 says so. |

**The audit records.** Two in-scope sources, both direct children of
`audit/rounds/`, both read at source rather than through their views:
`audit/rounds/fiat-dokimasia-proposed-dispositions.md` (129 lines, 8 rounds
across 4 steps, 6 findings S1-R1-01, S1-R1-02, S2-R1-01, S3-R1-01, S3-R1-02,
S4-R1-01, all `fixed`) and
`audit/rounds/fiat-dokimasia-frontend-coverage-skill.md` (330 lines, 20 rounds
across 5 steps, 26 finding ids, all fixed or accepted, as the previous study
already tabulated). `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py
--check .` was run from the target root and exits 0 with `committed=match` on
every pair including both of these; the sources were read anyway because this
study needs every lead, and a synopsis is lossy by design. No plugin
`audit/AUDIT.md` is in scope: `plugins/dokimasia/` has none, and this run
touches no other plugin's code. Every `Covered`, `Not checked` and `Elenchus
verdict` line was kept; no legacy field is missing from either record.

The leads in the proposed-dispositions record that bear on this run, each
carried or refused by name:

- *The 202 confirmations were applied mechanically under a rule a person
  stated, and the record cannot distinguish the two* (step 4, round 1). This
  run's requirement. The rule gets a table row with its author; the 202 entries
  name it.
- *`generated_by` records what the writing process claimed and nothing signs
  it* (step 4, round 1). Carried forward as stated above; attribution is the
  same class of claim and section 9 draws the boundary.
- *`proposed_sha256` is in the reviewer's own file, so a hand-recomputed digest
  makes an edit read as untouched* (step 3, round 1). Accepted and unchanged.
  Attribution fields are outside `entry_digest` for the same reason
  `confirmed` is: a person adding them has not edited what the entry says.
  Because `_touched` reads `confirmed` first, an attributed entry is always
  preserved whatever its digest.
- *Regeneration counters go to stderr, not into the set* (step 3, round 1).
  Unchanged; the coverage record is where figures a reader needs live, and
  the `confirmations` block is added there.
- *The workbook's status and source vocabularies are unpinned* (deferred in
  both runs). Deferred a fourth time, and the deferral is visible: nothing in
  attribution reads a workbook status.
- *The canonical coverage digest covers the `unconfirmed` list, so moved
  confirmations move the digest* (step 2, round 1). Extended deliberately: the
  digest now also covers `confirmations`, so a changed attribution is a changed
  record, which is the point.
- *Two quadratic scans in one run, S2-R1-01 and S3-R1-01* (steps 2 and 3).
  Constraint, not lead: the by-person and by-rule counts are dictionary
  increments in the one pass the reconciler already makes over entries, and no
  new lookup walks a list.
- *The committed set carries sheet names, row numbers and identifiers but no
  workbook prose* (step 4, round 1). Constraint: a person's name and a rule's
  text are new prose in the record, and `test_the_committed_record_carries_no_workbook_prose`
  refuses the workbook column names `Test step`, `Expected result`, `Comments`,
  `Tx hash` and `Tester` anywhere in the coverage record. A rule's text may not
  contain them.

From the first run's record, the items the previous study left open stand as
it left them: `read_json` does not walk a supplied path's parents; an empty
scoped set reports zero over zero as not closed; the schema checker is a
bounded draft-07 subset; `render` recomputes a kind prefix twice per row; a
stale-boundary commit check belongs to Horos. This run's schema changes use
only keywords `schema.py` already supports: `additionalProperties` with an
object schema is already used by `coverage-v1.json` for `by_disposition`, and
that is how the `rules` table and the per-person counts are declared.

**Outside this repository.** Nothing answering this shape. Signed review
attestations (in-toto layouts, Sigstore-style attestations) record who signed
a statement and are the right tool once a key exists, and Ariadne in this
marketplace already binds artefacts that way; Dokimasia deliberately holds no
key, so the attribution here is a named claim in a reviewed file, not a
signature, and the study says so rather than borrowing the word.

## 3. Constraints and non-goals

**Constraints.**

- Starting ref `0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a` on `main`.
- Python 3.14.6 from `.python-version`, standard library only.
- Suite `python3 scripts/run_checks.py`, plugin scope `--scope dokimasia`.
  Every step exit names the root suite through the checked runner, never three
  lints alone. The commit gate in `.githooks` runs the suite; activate it with
  `git config core.hooksPath .githooks` in the worktree.
- Any tracked-file edit changes the byte counts `HorosCensusCurrencyTests`
  checks. Before every commit, after every other file has landed:
  `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` for the
  boundary and `python3 plugins/horos/skills/horos/scripts/horos.py scan .
  --census --write` for the census; both are the commands the tests name.
- `plugins/dokimasia/skills/dokimasia/DEMONSTRATION.md` pins the SHA-256 of
  `docs/evidence/wildcat-app-v2.coverage.json`, `.scrutiny.json`,
  `-scrutiny.md` and `scripts/dokimasia.py`, and one exact stdout line of
  `demonstrate --check`. All four files change in this run, so the four digests
  are re-pinned in the step that changes them, and the observation line is
  re-pinned if the message changes. `python3 scripts/demonstrations.py check
  --root .` refuses a stale digest with `D026`.
- The root `README.md` carries a `front-door:demo` marker for
  `dokimasia-wildcat-app-v2-scrutiny` binding the demonstration record's
  digest and displaying its non-claim. Re-pinning the record moves that digest;
  `python3 scripts/check_public_front_door.py` reports `FD19` until the marker
  follows, and `FD25` if the non-claim text on the card stops matching.
- `tests/promise_machine_coverage.json` binds `coverage-v1.json` and
  `dispositions-v1.json` by SHA-256 under the `runtime` bindings for
  `dokimasia-disposition-closure` and `dokimasia-drafted-dispositions`. Both
  schemas change, so both digests move; `python3 scripts/promise_machine.py
  coverage --check` is the gate.
- `tests/test_marketplace_prose.py` requires the `**Current frontier.**` line
  to be identical across `plugins/dokimasia/README.md`, `AGENTS.md` and
  `skills/dokimasia/SKILL.md`, and the README's `Next Fiat job` line to
  read `Use /hexaemeron:fiat to <topic>.` followed by the fixed cold-read
  sentence, unique across plugins, or `None -- mature.` when the ledger is
  mature.
- `test_scaffold.py` asserts the schema set by name and count: five schemas.
  `rule-table` adds no schema, so the set stays five.
- ADR-001's vocabulary and ADR-002's boolean are fixed. Attribution is added
  beside `confirmed`; a record identifier does not change, exactly as ADR-002
  kept `dokimasia-dispositions/v1` when it added the boolean.
- The reviewer's artefact stays one hand-editable JSON file.
- Dokimasia reads a target checkout and never writes to it; spawns no
  subprocess; opens no socket. Every path written stays below a declared root
  and no path is followed through a symlink.
- Prose written in this run names the programme note and surveys only as held
  by the maintainer, by date. No private repository, branch or path is named
  in the study, the design record, a report, an ADR or a pull request body.

**Non-goals.**

- Crawling the UAT spreadsheets with a browser. The maintainer has stated it as
  the direction after this job. This run builds nothing toward it and does not
  foreclose it: `confirmed_by` is a string a crawler could fill from a
  reviewed cell, and `rule` names a row whose `stated_by` is the person who
  stated the crawler's rule, so a crawler's confirmations would be attributed
  to the person whose rule it applied, never to the crawler.
- Verifying an attribution. No signature, no identity lookup, no key.
- Deciding the 59 unconfirmed compiled items. They stay undisposed.
- Pinning the workbook's status and source vocabularies.
- Regrading RS-40 (#1112).
- Reporting anything as passed. A closure ratio above zero means somebody
  decided, and now says who.

## 4. Design options

The record at `.hexaemeron/design-evidence.json` selects one candidate from a
checked matrix of three candidates by ten criteria, seven at selection and
three at conformance. The prose below explains the candidates; it decides
nothing.

**`rule-table`.** One artefact. A confirmed entry carries `confirmed_by`, a
person, and may carry `rule`, an id into a set-level `rules` object whose
values hold `text` and `stated_by`. A confirmed entry with no `rule` was
decided individually by the named person. *The trade:* a rule applied to 202
rows is written once and its author named once, so a reworded rule is
corrected in one place and a count of distinct rules is a count of table rows;
in exchange an entry read on its own shows a rule id, not its wording, and the
reconciler acquires one more join to refuse, a dangling id.

**`inline-attribution`.** One artefact. A confirmed entry carries
`confirmed_by` and `rule_text`, the wording written out on the entry. *The
trade:* every entry is self-contained and there is no join to refuse; in
exchange the same rule is written 202 times on the pinned set, two entries
meant to share a rule can drift by a character and count as two rules, and
"how many rules were applied" becomes a question about string equality.

**`attestation-ledger`.** Two artefacts. Entries keep `confirmed`; a separate
confirmations file holds attestations, each naming a person, a rule and the
items it covers. *The trade:* the rule is stated once and the disposition file
is untouched; in exchange the reviewer maintains two files and two digest
bindings, confirming one item is two edits, and a dropped item leaves a
dangling attestation, which is a second staleness to refuse.

The four selection gates are met by all three: a generator that drafts no
attribution, three states untouched, a set confirmed before this version
refusing by name, and a confirmed entry's bytes carried forward. The choice is
made by three metrics. Two count what the reviewer pays, as the previous run
counted them: `rule-table` and `inline-attribution` cost one action and one
artefact, `attestation-ledger` two and two. The third is measured, not
declared: the generator builds each candidate's shape over the committed
261-entry set with its 202 confirmations under the one stated rule and counts
how many places the rule's text is written. `rule-table` 1,
`inline-attribution` 202, `attestation-ledger` 1. `rule-table` is the only
candidate no other dominates. The checker computes that frontier; the record
records it.

**One reading recorded rather than resolved silently.** The topic says the
reconciler refuses an entry "carrying no person and no stated rule". Read one
way, either a person or a rule would suffice. This run takes the other: a
person is always required, and a rule is the additional thing a rule-based
confirmation must record. The reason is the held job's own sentence, that a
coverage figure must state whose judgement it is, and ADR-001's, that a person
owns every disposition. A rule with no person would attribute a judgement to a
sentence. A rule row therefore carries `stated_by` too, so an entry confirmed
under a rule names two people at most and one at least.

**A second reading.** Whether `rules` may hold a row no entry applies. It may;
the record reports it as a rule applied zero times rather than refusing, since
a stated rule nobody used is information about the review, not a defect in
the file.

## 5. Risk register seed

Attribution is the first field in this plugin that names a person, and the
first whose absence changes a number that was previously counted. The refusal
path is where a count could be widened by an entry that says nothing about who
decided it, and the regeneration path is where an attribution could be lost.

```risk-register
unattributed-admission | the reconciler's admission of a confirmed entry | a confirmed entry with no `confirmed_by`, or a blank or non-string one, refuses by name and is never counted
rule-dangling | the `rule` id on a confirmed entry | an id absent from the `rules` table refuses by name, and a table row with blank `text` or blank `stated_by` refuses
attribution-on-draft | an unconfirmed entry | an entry with `confirmed` false carrying `confirmed_by` or `rule` refuses, so a draft cannot pre-name a confirmer
attribution-drafted | the proposal generator's emitted entries | no branch writes `confirmed_by` or `rule`, asserted against the module source and by driving every branch
attribution-clobber | the disposition file during a regeneration | an attributed entry and the `rules` table survive a regeneration byte for byte
prior-set-migration | a set confirmed under `dokimasia-v2.1.0` | it refuses by name on its first confirmed entry rather than defaulting a person, and the pinned set is regenerated rather than defaulted
counts-by-attribution | the `confirmations` block | `people`, `by_person`, `by_rule` and `individual` reconcile with `disposed` three ways, and the canonical digest covers the block
workbook-prose | a person's name and a rule's text in the coverage record | no workbook column name or row content enters the record; the existing prose test still refuses the five column names
cap-exhaustion | `confirmed_by`, rule ids, rule text and the `rules` table | each is bound by a declared cap that is a parameter, never a module-level value a caller can lower
partial-write | the disposition file and the evidence files during a write | a killed write leaves either the previous file or the new one
path-traversal | the record paths read and the evidence root written | every path stays below its declared root and no path is followed through a symlink
subprocess-and-network | a reconcile, propose or demonstrate run | no subprocess is spawned and no socket is opened
target-repository-write | the application checkout during a scrutiny | nothing is written to the target checkout
evidence-digest-binding | the recorded inventory and workbook digests | a set generated against moved records is stale and refuses
disposition-closure | the closure ratio under attribution | the ratio counts attributed confirmations only, and an unattributed confirmation lowers nothing and raises nothing
repository-pins | the demonstration ledger, front-door marker, promise bindings, boundary and census | every pin that binds a changed file is re-pinned in the same step, and its checker exits zero before the commit
```

## 6. Glossary seeds

- **Attribution.** The person a confirmed entry names in `confirmed_by`, and
  the rule it names in `rule` if it was confirmed under one.
- **Confirmer.** The person `confirmed_by` names. A claim the file makes, not
  a verified identity.
- **Rule.** One row of the set's `rules` table: an id, its `text`, and
  `stated_by`, the person who stated it.
- **Rule-based confirmation.** A confirmed entry naming a rule. Its judgement
  is the rule author's; its application may have been mechanical.
- **Individual confirmation.** A confirmed entry naming no rule. The named
  person decided that entry on its own.
- **Confirmations block.** The coverage record's `confirmations` object:
  `people`, `by_person`, `by_rule` and `individual`.
- **Unattributed confirmation.** An entry with `confirmed` true and no
  `confirmed_by`. Refused, never counted.
- **Re-pin.** Replacing a recorded digest with the digest of the file as it
  now is, in the same change that moved the file.

## 7. Sources

- `plugins/dokimasia/skills/dokimasia/EVOLUTION.md`: the held job at
  `dokimasia-v2.1.0`, frontier revision `attributed-confirmation`.
- `plugins/dokimasia/skills/dokimasia/SKILL.md`: the six promises and the
  marketplace block this run rewrites.
- `plugins/dokimasia/skills/dokimasia/DEMONSTRATION.md` and
  `plugins/hexaemeron/skills/DEMONSTRATIONS.md`: the four pinned source digests
  and the refusal catalogue.
- `plugins/hexaemeron/skills/VERSIONING.md`, section "What every frontier run
  owes": the cold-read obligation and the maturity judgement.
- `plugins/dokimasia/docs/decisions/ADR-001-one-disposition-per-scoped-item.md`
  and `ADR-002-confirmation-is-not-a-disposition.md`.
- `plugins/dokimasia/docs/dokimasia-proposal-study.md` and
  `dokimasia-proposal-runbook.md`: the previous run's specification and its
  four amendments.
- `plugins/dokimasia/docs/coverage-contract.md` and `proposal-rules.md`.
- `plugins/dokimasia/scripts/dokimasia_lib/reconcile.py`, `propose.py`,
  `demonstrate.py`, `schema.py`, and `scripts/dokimasia.py`.
- `plugins/dokimasia/schemas/dispositions-v1.json` and `coverage-v1.json`.
- `plugins/dokimasia/docs/evidence/`: the four committed evidence files; 202
  confirmed `manual` entries, 59 unconfirmed drafted `excluded`.
- `plugins/dokimasia/tests/`: 264 tests, 1 skipped without the pinned inputs.
- `audit/rounds/fiat-dokimasia-proposed-dispositions.md` and
  `fiat-dokimasia-frontend-coverage-skill.md`, read at source.
- [#1113](https://github.com/wildcat-finance/skills/pull/1113),
  [#1111](https://github.com/wildcat-finance/skills/pull/1111),
  [#1279](https://github.com/wildcat-finance/skills/pull/1279),
  [#1303](https://github.com/wildcat-finance/skills/pull/1303).
- [#1352](https://github.com/wildcat-finance/skills/issues/1352), the task
  issue; [#1112](https://github.com/wildcat-finance/skills/issues/1112), the
  open RS-40 regrade.
- `tests/promise_machine_coverage.json`, `tests/test_marketplace_prose.py`,
  `tests/test_demonstrations.py`, `scripts/check_public_front_door.py`: the
  repository pins listed in section 3.
- The programme note of 5 September 2026 and its four surveys, held by the
  maintainer; referenced by the task issue, not read here.

## 8. Signals, and the questions behind them

[ephoros](../../hexaemeron/skills/ephoros/SKILL.md) owns what a signal must
carry. This runs from a terminal, on demand, never unattended, so there is no
alert. The questions are a reader's, asked of a committed record:

1. *Whose judgement is this number?* Answered by `confirmations.people` and
   `by_person` in the coverage record and by the rendered scrutiny's new
   section. The reconciler step emits them; the demonstration step renders
   them.
2. *Was this rule applied by the person who stated it, and to how many
   entries?* Answered by `by_rule.<id>.stated_by` and `applied`, beside the
   rule's text. The reconciler step emits it.
3. *Did the last regeneration keep every attribution?* Answered by the
   preserved count on stderr, by the `rules` table carried forward, and by the
   conformance gate proving an attributed entry is never in the replaced set.
   The proposal step emits it.

## 9. Boundaries, per capability

[phylax](../../hexaemeron/skills/phylax/SKILL.md) owns the boundary list and
the controls. One boundary is new and three are inherited:

- **Reading a person's name and a rule's text from a reviewer-supplied file.**
  New. Worth taking: strings that reach the committed coverage record and the
  rendered prose. Controlled by caps that are parameters, `confirmed_by` and
  `stated_by` at 128 bytes, a rule id at 64 bytes matching one safe segment, a
  rule's text at the existing 512-byte reason cap, and the `rules` table at
  256 rows; by the existing prose test refusing the five workbook column
  names anywhere in the record; and by the rule that no template or code path
  writes either field. What is not controlled, and stated: nothing verifies
  that the named person exists or agreed. The field is a claim the file makes
  under a person's name, the same class as `generated_by`, and making it a
  proof needs a key this skill does not hold.
- **Reading two operator-supplied record paths and one disposition set.**
  Inherited and unchanged; the parents of a supplied path are still not
  walked.
- **Writing the disposition file and the evidence files.** Inherited: a
  declared root, one safe path segment, a staged write renamed into place.
- **The target checkout.** Unchanged: read-only, no subprocess, no socket, no
  key material.

Always: the plugin scope and the root suite through `run_checks.py` before a
commit; the imprimatur lint on every shipped document; the Horos boundary and
census regenerated last; every pin in section 3 re-checked. Ask first: a new
dependency; a change to any committed schema beyond the fields named here; a
change to the disposition vocabulary or the `confirmed` boolean; a wider trust
boundary; rewriting a released digest other than the four evidence files this
run regenerates. Never: commit key material or the reviewed workbook's bytes;
edit a vendored tree; delete a failing test to green a suite; write
`confirmed_by` or `rule` from a generator; name a private repository, branch
or path; claim a command ran when it did not.

## 10. The budget, or its absence

[metron](../../hexaemeron/skills/metron/SKILL.md) owns what a budget carries
and how it is checked. One budget, inherited. The pinned scrutiny declares
120,000ms and was measured at 288ms over 261 items. Attribution adds a
dictionary increment per confirmed entry inside the pass the reconciler already
makes, and one pass over the `rules` table bounded at 256 rows, so it belongs
inside the same budget:

```bash
python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check
```

The demonstration records its duration beside the declared budget. That figure
is one observation on one machine and is not a benchmark. No change in this
run is made for speed, so no before-and-after measurement is owed; the two
quadratic scans the previous run recorded are the reason every new count is a
dictionary lookup, which is a constraint rather than a claim.

## 11. The fail-closed posture

[elenchus](../../hexaemeron/skills/elenchus/SKILL.md) owns the triage order
and the guard rule. What stops a run, in the direction that never widens a
number:

- A confirmed entry with no `confirmed_by`, or a blank or non-string one,
  refuses by name before any count is taken.
- A `rule` id the table does not hold refuses; a table row with blank `text`
  or blank `stated_by` refuses; a `rules` value that is not an object refuses.
- An unconfirmed entry carrying `confirmed_by` or `rule` refuses.
- A set confirmed under `dokimasia-v2.1.0` refuses on its first confirmed
  entry, naming the item and the missing field. No default is supplied,
  because defaulting a person is the exact forgery this run exists to make
  impossible.
- A regeneration that cannot carry an attributed entry or the `rules` table
  forward refuses and writes nothing.
- A drafted set that carries either attribution field breaches its schema
  check before the write.
- Any code path writing `confirmed_by` or `rule` from a generator is a defect,
  asserted absent by a test against the module source.

Every fix follows the convention already in this plugin: the fix lands with a
test that fails without it, driving the exact condition through the real entry
point. A cap added here is a parameter with a default, never a module-level
value a caller can lower, which is the pattern S2-R1-01 and S3-R1-03 of the
first run both recorded.

## 12. Decisions and their homes

[hypomnema](../../hexaemeron/skills/hypomnema/SKILL.md) owns which decisions
earn a record and where each lives.

- **A person is required and a rule is a table row, not a fourth field of
  free text.** Expensive to reverse: it fixes the shape of every attributed
  set and what "how many people decided" means. Home: a new
  `plugins/dokimasia/docs/decisions/ADR-003-attribution-names-a-person-and-a-stated-rule.md`,
  which also records the two readings in section 4, the identifiers staying at
  `/v1`, and the migration: no defaulting, and the pinned set regenerated.
- **The selected candidate and its trade.** Home: the committed design record
  `plugins/dokimasia/docs/attribution-design-evidence.json`, its 21 selection
  reports under `plugins/dokimasia/docs/reports/selection/`, and its
  generator `plugins/dokimasia/docs/design/build_attribution_design_evidence.py`,
  bound by the runbook's `design-lock` block.
- **The attribution rules a reviewer writes under.** Home: a new section of
  `plugins/dokimasia/docs/coverage-contract.md`, beside its existing
  "Confirmation" section, since the contract is where the reconciler's
  refusals are already stated for a reader.
- **Who confirmed the pinned 202 and under what rule.** Home: the regenerated
  `plugins/dokimasia/docs/evidence/wildcat-app-v2.dispositions.json`, whose
  `rules` table and 202 `confirmed_by` fields are the record, and the
  rendered scrutiny beside it.
- **The frontier ledger row and the maturity judgement.** Home:
  `plugins/dokimasia/skills/dokimasia/EVOLUTION.md`, one row at
  `dokimasia-v3.1.0`, written once in the last step, with the marketplace
  block, README, `AGENTS.md`, both manifests and the marketplace entry moved
  to match, and the README's stale scaffold prose ("Inventory compilation,
  workbook import, reconciliation and the coverage record remain to be
  implemented") and the plugin `AGENTS.md`'s stale "What this plugin does not
  yet do" section reconciled with the tree under the cold-read obligation.
- **The demonstration ledger's re-pin.** Home:
  `plugins/dokimasia/skills/dokimasia/DEMONSTRATION.md`, four source digests
  and the observation line, with its demo frontier line unchanged, since the
  demonstration still shows the same claim over the same three files.
