# Dokimasia: proposed dispositions

Assuming, unless corrected:

1. The starting ref is `main` at `f3af97e9fde2be6cbd1d831d010a212b0c379f01`, and
   the run integrates back into `main`.
2. Python 3 from the repository's own pin, standard library only, as the four
   existing `dokimasia_lib` modules already practise. No new runtime dependency.
3. The root suite is `python3 scripts/run_checks.py`. Bare
   `python3 -m unittest discover` is not a suite command in this repository: it
   raises `ImportError` on the plugin trees and reads as a clean run.
4. ADR-001's three dispositions are fixed. Confirmation is a separate axis on an
   entry, not a fourth state, so this run does not reopen that record.
5. The reviewed workbook's bytes stay uncommitted, so any check that needs them
   reads `DOKIMASIA_PINNED_WORKBOOK` and skips without it, as the existing pinned
   regeneration test does.
6. No GitHub task issue governs this run; the frontier ledger's held job is the
   requirement.

I will proceed on these unless corrected.

## 1. Problem statement

Dokimasia can compile a denominator and it cannot help anybody decide against
it. The first scrutiny of a real release, `wildcat-app-v2` at `bb9685fb`
against workbook `9da2f2e8`, scoped 261 items: 59 compiled from the application
(23 page routes, 35 API handlers, one guard) and 202 imported from the
workbook. Every one of the 261 carries no disposition, and the closure ratio is
0 over 261.

That zero is not a defect in the compiler. It is the cost of the interface. A
reviewer facing this tool is asked to author 261 entries from nothing, in a JSON
file, in a vocabulary they have to learn first, and the tool offers no starting
point. Nobody does that, so the denominator sits unused and the release goes
back to being declared tested by a spreadsheet.

**Who this is for.** The person who has to sign off a frontend release and
would rather correct a draft than write one. They know which routes are
admin-only, which cases are theirs to walk by hand, and which parts of the
application are somebody else's problem. What they do not want to do is type
that out 261 times.

**What a working prototype means here.** `dokimasia propose` reads the same
inventory and workbook the reconciler reads and writes a complete disposition
set: every scoped item present, every entry `manual` or `excluded`, every entry
carrying a reason drawn from what the compiled item or imported row actually
says, and every entry marked unconfirmed. A reviewer then edits that file. The
reconciler admits an entry only where a person confirmed it, so a freshly
generated set closes at zero and a reviewed one closes at what the person
actually decided. Regenerating the proposal after the inventory moves preserves
every entry a person touched.

`covered` is not proposed, ever, and no code path in the proposal surface can
construct it. ADR-001 reserves that state to a person holding an item to a
reviewed oracle, and a tool that could draft it would be a tool that could
widen a coverage number on its own.

**The demo path that proves it.** Against the pinned release, with a confirmed
subset written by hand:

```bash
python3 plugins/dokimasia/scripts/dokimasia.py propose --check
python3 plugins/dokimasia/scripts/dokimasia.py reconcile --check
python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check
python3 scripts/run_checks.py --scope dokimasia
```

Success is checkable and each condition below names how:

- A generated set is complete over the scoped item list and every entry is
  `manual` or `excluded` with a non-empty reason: asserted by `propose --check`
  against the committed fixtures.
- No proposal path emits `covered`: proved by a test that reads the proposal
  module's own source for the literal and by a test that drives every generator
  branch and asserts the emitted vocabulary is a subset of `{manual, excluded}`.
  The absence is a property of the code, so the test asserts it of the code.
- The reconciler admits no unconfirmed entry: asserted by `reconcile --check`
  against a fixture whose entries are all unconfirmed, which must produce a
  closure ratio of zero and name every entry as unconfirmed.
- A reviewer's edits survive regeneration: asserted by `propose --check`, which
  generates, edits two entries, regenerates against a moved inventory, and
  requires both edited entries byte-identical afterwards.
- The pinned scrutiny reports a closure ratio above zero drawn only from
  confirmed entries: asserted by `demonstrate --check` and recorded in the
  committed scrutiny evidence.

## 2. Prior art

**In this repository.** Everything this run extends shipped six commits ago.
The last merged pull request that changed the subject is
[#1094](https://github.com/wildcat-finance/skills/pull/1094), merged as
`f3af97e9`, which carried the whole five-step run from `dokimasia-v0.1.0` to
`dokimasia-v1.1.0`. The merged pull request before it that touched the subject
is [#1091](https://github.com/wildcat-finance/skills/pull/1091), step 5 of that
same run, which ran the pinned scrutiny and opened the ledger. Both were read.

#1094 carries its unfinished work as a prose section headed `## What is owed`
rather than as a fenced `carryover` block, because that run was halted before
`done integrate` and its stack was merged by hand. Its two items, and what this
run does with each:

- **The RS-40 router-selection regrade.** #1094 changed Dokimasia's marketplace
  description and the router row naming it, and the regrade needs one isolated
  context per request, which that session could not open. This run also changes
  the marketplace description, because the frontier line moves. Carried forward
  as a named open item, not answered here: the same isolation constraint holds,
  and manufacturing a regrade from a non-isolated context would be worse than
  recording that it is owed.
- **The pinned regeneration test needs two environment variables and skips
  without them.** Accepted and unchanged. Assumption 5 above states the reason:
  the workbook's bytes are deliberately not committed. Every check this run adds
  that needs the reviewed workbook follows the same convention.

The controller refusal that halted #1094 is filed as
[#1085](https://github.com/wildcat-finance/skills/issues/1085) and is a Fiat
defect, not a Dokimasia one. It is out of scope here and is named so a reader
does not mistake this run's clean integration for a fix to it.

**The audit record.** `audit/rounds/fiat-dokimasia-frontend-coverage-skill.md`
is the only in-scope audit source, and it was read at source: all 330 lines, not
its synopsis. `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py
--check .` was run from the target root and exits 0 with `committed=match` on
every pair including this one, so the synopsis was available and current; the
source was read anyway because this study needs every finding's status and every
lead, and the 21-line view is lossy by design. No other plugin's `audit/AUDIT.md`
is in scope: this run touches only `plugins/dokimasia/` and the root check map.

The record holds 20 rounds across five steps, 21 findings, all fixed or
accepted. Six items are open and each is answered here:

| Item | Where it stands in this run |
| --- | --- |
| S1-R1-01: 18 selection reports name a command path that resolves only inside the gitignored run directory | **Fixed for this run's own evidence.** This run's generator is committed at `plugins/dokimasia/docs/design/build_proposal_design_evidence.py` and every report names that repository-relative path, which runs from a fresh clone. The prior record's reports are immutable and stay as they are. |
| `read_json` tests only the supplied path for a symlink, not its parents | Accepted, unchanged. The inputs stay operator-supplied record paths. This run adds one more such path and applies the same rule, stated rather than repaired. |
| An empty scoped set reports zero over zero as not closed | Deliberate and unchanged, and this run depends on it: a generated-but-unconfirmed set is the same conservative reading applied to confirmation. |
| The schema checker is a bounded draft-07 subset; an unsupported keyword refuses | Unchanged, and it constrains this run: the new schema this run commits uses only keywords `schema.py` already supports, or `schema.py` grows with it in the same step. |
| `render` recomputes each item's kind prefix twice per row | Accepted at this scale. No performance claim is made, so metron records no budget for it. |
| A commit-time check that refuses a stale Horos boundary | Belongs to Horos or the commit path, not to a Dokimasia step. Named, not taken. |

One lead in the record is now a requirement rather than a lead. Rounds 2 and 3
of step 3 both recorded that the workbook's status and source vocabularies are
unpinned, and both deferred it to "the step that reconciles". Step 4 reconciled
and did not pin them. This run does not pin them either, and states why: the
proposal surface reads a status only to write a reason a person will read, never
to decide a disposition, so a renamed status changes drafted prose and cannot
change a coverage figure. The item stays open against the reconciler and is
recorded here so the third deferral is visible as a deferral.

**A gap this run inherits and must close for its own artefact.** Finding
S5-R4-01 established that every record the plugin *emits* is validated against
its committed schema at runtime, and four schemas ship. `dokimasia-dispositions/v1`
is not among them, because nothing emitted it: the disposition set was a
hand-written input. `propose` emits one, which brings it inside S5-R4-01's rule
and requires a committed `schemas/dispositions-v1.json` validated on the way
out.

**Outside this repository.** Nothing found that answers this shape. Coverage
tools report what a test executed, which ADR-001 rejects as a different
question. Test-management systems hold cases and statuses without a compiled
denominator. Neither drafts a decision for a person to correct, which is the
whole of this job.

## 3. Constraints and non-goals

**Constraints.**

- Starting ref `f3af97e9fde2be6cbd1d831d010a212b0c379f01` on `main`.
- Python 3 standard library only. No new runtime dependency; the design record
  counts that as a criterion.
- Root suite `python3 scripts/run_checks.py`; plugin scope
  `--scope dokimasia`. A step exit naming bare `unittest discover` is not an
  exit, per assumption 3.
- ADR-001's vocabulary is fixed at three states. Confirmation is a field on an
  entry.
- The reviewer's artefact stays a hand-editable text file. A binary store, a
  database, or a format that needs a tool to read would defeat the purpose.
- Dokimasia reads a target checkout and never writes to it; it spawns no
  subprocess and opens no socket during a scrutiny. The proposal surface
  inherits both.
- Every path written stays below a declared root and is never followed through
  a symlink.

**Non-goals.**

- Proposing `covered`. Structurally excluded, not merely avoided.
- Judging whether a proposed reason is right. The tool drafts prose from what
  the record says; the reviewer owns the claim.
- Executing the application or holding an oracle. Both stay outside this skill.
- Pinning the workbook's status and source vocabularies, per section 2.
- Regrading RS-40, per section 2.
- Reporting anything as passed. A closure ratio above zero means somebody
  decided, never that anything works.

## 4. Design options

The record at `.hexaemeron/design-evidence.json` selects one candidate from a
checked matrix of three candidates by eight criteria. The prose below explains
what each candidate is; it decides nothing.

**`confirmed-flag`.** One artefact. Each entry in the disposition set carries a
required `confirmed` boolean and the digest of the proposal it came from.
`propose` regenerates the file in place, carrying every confirmed or edited
entry forward byte for byte and replacing only entries no person has touched.
*The trade:* the reviewer maintains one file and pays one edit per item, which
is the cheapest of the three, and in exchange the whole risk of the design sits
in one place: a regeneration that rewrites the file a person has been editing.
That risk is answered by a conformance gate rather than by prose.

**`proposal-overlay`.** Two artefacts, one direction. `propose` writes a
proposals file it owns outright and never reads back; the reviewer confirms by
copying entries into the dispositions file, which the generator never opens.
*The trade:* edit survival is free, because nothing can rewrite a file nothing
opens, and the reviewer pays twice per item, once to copy and once to confirm,
which is the cost this run exists to remove.

**`two-file-merge`.** Two artefacts, joined at read time. `propose` owns the
proposals file; the reviewer owns a confirmations file naming the ids they
accept and any reason they replaced. The reconciler reads both.
*The trade:* one edit per item and no rewrite risk, paid for with a second
artefact the reviewer maintains and a second digest binding to keep current,
so a stale confirmations file becomes a new way to be wrong.

The two gates that could remove a candidate, that no path emits `covered` and
that a confirmed entry's bytes survive, are met by all three, because each can
be built that way. The choice is therefore made by what the reviewer pays, and
`confirmed-flag` is the only candidate no other candidate dominates: one action
and one artefact, against two and two for `proposal-overlay` and one and two for
`two-file-merge`. The checker computes that frontier; the record records it.

**One reading recorded rather than resolved silently.** The held job says a
proposed set is "refused by the reconciler wherever a reviewer has not confirmed
it". Two readings are available. The whole set could refuse, which would make a
partially reviewed file unreconcilable and force the reviewer to confirm all 261
entries before seeing a single number. Or the unconfirmed *entry* could be
refused as a disposition, leaving its item undisposed and named. This run takes
the second: an unconfirmed entry is admitted into no disposition, appears in a
new `unconfirmed` list in the coverage record, and holds the ratio down exactly
as an absent entry does. The reason is that incremental review is the only
review that will happen at this scale, and the conservative direction is
preserved either way, because an unconfirmed entry can never raise a number.

## 5. Risk register seed

The proposal surface is the first code in this plugin that writes a file a
person then edits, and the first that generates prose a person may trust
without reading. Both are new classes here. The regeneration path is where a
reviewer's work can be destroyed, and the reason templates are where a drafted
sentence can assert more than the record supports.

```risk-register
proposal-covered-path | the proposal generator's emitted vocabulary | no branch constructs `covered`, proved against the module source and by driving every branch
regeneration-clobber | the disposition file during a regeneration | a confirmed or edited entry's bytes survive a regeneration against a moved inventory
confirmation-forgery | the `confirmed` field on a generated entry | a freshly generated entry is never confirmed, and generation cannot set the field true
emitted-set-unvalidated | the disposition set on the way out of `propose` | the emitted set validates against a committed `dispositions-v1.json` before it is written
reason-overclaim | the drafted reason text | a reason states only what the inventory item or workbook row says, and never that anything passed
partial-write | the disposition file during a write | a killed regeneration leaves either the previous file or the new one, never a half-written set
path-traversal | the proposal output path and the record paths it reads | every path stays below its declared root and no path is followed through a symlink
cap-exhaustion | the scoped set and the reason text | the declared disposition and reason caps bind the generated set as they bind a written one
target-repository-write | the application checkout during a proposal | nothing is written to the target checkout
subprocess-and-network | the proposal run | no subprocess is spawned and no socket is opened
evidence-digest-binding | the proposal's recorded inventory and workbook digests | a set generated against moved records is stale and refuses
disposition-closure | the closure ratio under confirmation | the ratio counts confirmed entries only, and an unconfirmed set closes at zero
```

## 6. Glossary seeds

- **Scoped item.** One entry in the union of compiled inventory items and
  imported workbook cases; the thing a disposition is owed for.
- **Disposition.** One of ADR-001's three states, recorded against one scoped
  item by a person.
- **Proposal.** A disposition entry this tool drafted, marked unconfirmed,
  carrying a reason drawn from the record.
- **Confirmation.** A person's mark on one entry, which is the only thing that
  admits it as a disposition.
- **Unconfirmed entry.** A drafted entry no person has marked; refused as a
  disposition and named in the coverage record.
- **Regeneration.** Rewriting the proposal for a moved inventory or workbook,
  preserving every entry a person touched.
- **Closure ratio.** Confirmed dispositions over scoped items. One means
  nothing is unaccounted for; it never means anything passed.

## 7. Sources

- `plugins/dokimasia/skills/dokimasia/SKILL.md` and `EVOLUTION.md`:
  contract, the five promises, and the held frontier job at
  `dokimasia-v1.1.0`.
- `plugins/dokimasia/docs/decisions/ADR-001-one-disposition-per-scoped-item.md`
  states the three states, the ratio, and the sentence reserving `covered` to a
  person.
- `plugins/dokimasia/scripts/dokimasia_lib/reconcile.py`: the module this run
  extends; `covered` currently requires an inventory-side item, an oracle the
  workbook holds, and a status that is present, non-blank and not `Not Run`.
- `plugins/dokimasia/schemas/`: `coverage-v1.json`, `inventory-v1.json`,
  `scrutiny-v1.json`, `workbook-v1.json`. No `dispositions-v1.json`; section 2
  records why and this run commits one.
- `plugins/dokimasia/docs/evidence/wildcat-app-v2-scrutiny.md` and
  `wildcat-app-v2.coverage.json`: the pinned scrutiny, 261 scoped, 0 disposed,
  288ms against a 120,000ms budget.
- `audit/rounds/fiat-dokimasia-frontend-coverage-skill.md`: read at source, 330
  lines, 20 rounds.
- [#1094](https://github.com/wildcat-finance/skills/pull/1094) and
  [#1091](https://github.com/wildcat-finance/skills/pull/1091): the last two
  merged pull requests touching the subject.
- [#1085](https://github.com/wildcat-finance/skills/issues/1085): the Fiat
  merge-base defect that halted the prior run; out of scope.
- `plugins/dokimasia/docs/coverage-contract.md`, `docs/inventory-rules.md`,
  `docs/workbook-lineage.md`: the declared rules the proposal reads under.

## 8. Signals, and the questions behind them

[ephoros](../../hexaemeron/skills/ephoros/SKILL.md) owns what a signal must carry. This runs from a
terminal, on demand, and never unattended, so there is no on-call rotation and
no alert. What there is instead is a person reading a generated file and
deciding whether to trust it, which is the same question asked at a different
hour. Three questions, and where each is answered:

1. *Did this proposal get generated against the tree I am looking at now?*
   Answered by the recorded inventory and workbook digests in the emitted set,
   and by the reconciler refusing a set whose digests have moved. Step 2 emits
   them; step 3 enforces them.
2. *How much of this file did a person actually decide, and how much is still
   a draft?* Answered by the coverage record's counts: confirmed dispositions,
   unconfirmed entries, and undisposed items as three separate figures. Step 3
   emits them.
3. *What did the last regeneration change, and did it touch anything I wrote?*
   Answered by the regeneration reporting, per run, how many entries it
   preserved, replaced and added, and by the conformance gate proving a touched
   entry is never in the replaced set. Step 4 emits it.

## 9. Boundaries, per capability

[phylax](../../hexaemeron/skills/phylax/SKILL.md) owns the boundary list and the controls. Four
boundaries, three inherited and one new:

- **Reading two operator-supplied record paths.** Worth taking: an inventory
  and a workbook record, both JSON, both possibly truncated or mistyped.
  Controlled by the existing `read_json`, which requires a non-symlink regular
  file under a byte cap holding one JSON object, and by the shape check that
  made S4-R3-01 a named
  refusal rather than a stack trace. Unchanged, and the parents of a supplied
  path are still not walked, as section 2 records.
- **Writing the disposition file.** New, and the only boundary this run opens.
  Worth taking: a file a person owns and edits. Controlled by a declared output
  root, one safe path segment for the file name, which is the control S5-R2-01
  added after `--label ../../../../tmp/pwned` wrote outside the evidence root, a
  staged write renamed into place, and the regeneration rule that a touched
  entry's bytes are carried forward rather than rewritten.
- **Generating prose a person may trust.** Worth taking: a reason sentence
  drawn from an inventory item's kind and source, or a workbook row's sheet and
  identifier. Controlled by templates that quote only fields the record holds,
  the declared reason byte cap applied before the write, and the rule that no
  template asserts a status, an outcome or a judgement.
- **The target checkout.** Unchanged: read-only, no subprocess, no socket, no
  chain access, no key material.

Always: the plugin suite and the root suite before a commit; the imprimatur
lint on every shipped document; a recorded before and after for any change made
for speed. Ask first: a new dependency, a change to any committed schema, a
change to the disposition vocabulary, a wider trust boundary, a rewritten
released digest. Never: commit key material or the reviewed workbook's bytes;
edit a vendored tree; delete a failing test to green a suite; emit `covered`
from a generator; claim a command ran when it did not.

## 10. The budget, or its absence

[metron](../../hexaemeron/skills/metron/SKILL.md) owns what a budget carries and how it is checked.
One budget, inherited and extended. The pinned scrutiny declares 120,000ms and
was measured at 288ms over 261 items. Generating a proposal walks the same
scoped set once and writes one file, so it belongs inside the same budget
rather than getting one of its own:

```bash
python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check
```

The demonstration records its duration beside the declared budget, as it does
now. That figure is one observation on one machine and is not a benchmark; the
existing record already says so and this run does not upgrade the claim. No
change in this run is made in the name of speed, so no before-and-after
measurement is owed under metron's rule.

## 11. The fail-closed posture

[elenchus](../../hexaemeron/skills/elenchus/SKILL.md) owns the triage order and the guard rule.
What stops a run, in the direction that never widens a number:

- A proposal generated against records whose digests have moved is stale and
  refuses rather than being carried forward.
- An unconfirmed entry is admitted as no disposition, so a generated file
  closes at zero rather than at whatever it drafted.
- An emitted set that breaches `dispositions-v1.json` refuses before the write,
  so no invalid set reaches the reviewer's disk.
- A reason over the declared cap refuses; a template that would emit an empty
  reason refuses.
- A regeneration that cannot preserve a touched entry refuses and writes
  nothing, leaving the reviewer's file intact.
- Any attempt to construct `covered` in the proposal surface is a defect, not a
  runtime condition: there is no branch to take, and a test asserts the absence.

Every fix follows the guard convention already in this plugin: the fix lands
with a test that fails without it, driving the exact condition through the real
entry point rather than a helper. The audit record shows the convention working
and shows it slipping twice, because S3-R1-03 and S2-R1-01 are the same
mutated-global pattern, once in library code and once reintroduced in a test, so
a cap this
run adds is a parameter, never a module-level value a caller can lower.

## 12. Decisions and their homes

[hypomnema](../../hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a record and where
each lives.

- **Confirmation as a field rather than a fourth disposition.** Expensive to
  reverse: it changes the shape of every recorded set and the meaning of every
  ratio. Home: a new
  `plugins/dokimasia/docs/decisions/ADR-002-confirmation-is-not-a-disposition.md`,
  which also records the reading taken in section 4 on what "refused" means for
  an unconfirmed entry, and states the migration for the sets already written,
  of which there are none, which is the cheapest moment to make this change.
- **The selected candidate and its trade.** Home: the committed design record
  and its reports under `plugins/dokimasia/docs/`, bound by the runbook's
  `design-lock` block.
- **The reason templates.** Moderately expensive: a changed template changes
  every drafted reason on the next regeneration, and a reviewer who confirmed
  the old wording keeps it, so two vintages coexist. Home:
  `plugins/dokimasia/docs/proposal-rules.md`, beside the existing
  `inventory-rules.md` and `workbook-lineage.md`, which is where this plugin
  already puts a declared rule set.
- **The committed `dispositions-v1.json`.** Home: `plugins/dokimasia/schemas/`,
  with its runtime validation in the same step, under S5-R4-01's rule.
- **The frontier ledger row.** Home:
  `plugins/dokimasia/skills/dokimasia/EVOLUTION.md`, one row, written once in
  the last step, with the marketplace description and README frontier prose
  moved to match.
