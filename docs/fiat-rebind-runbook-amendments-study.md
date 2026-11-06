# Study: rebind runbook amendments across a study amendment

Task issue: [#1264](https://github.com/wildcat-finance/skills/issues/1264),
`framework-97: a study amendment silently unbinds every runbook amendment`.
Starting ref `b9f8e36b8b6210bcd023a68059ecb46da3e35769` on `main`.

Assuming, unless corrected:

1. The exact interpreter in `.python-version`, `3.14.6`, with stdlib
   `unittest` and no new dependency.
2. The fix lives in `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, its
   tests in `plugins/hexaemeron/tests/test_hexctl.py`, and the contract prose
   in `plugins/hexaemeron/skills/fiat/SKILL.md`; no other plugin changes.
3. The live-run figure of 17 runbook amendments bound to one study digest,
   and the 500-entry cap `AMENDMENT_HISTORY_MAX`, are the sizes the design
   is measured at.
4. The `fiat-runbook-amendment` promise stanza keeps its semantic fields; the
   phrase "current-study binding" is satisfied by a binding reached through
   recorded rebinds. If Warden reads it otherwise, the stanza edit and the
   `tests/promise_machine_id_history.json` re-pin join the build.
5. The rebind list is carried inside the existing `amend:study` event data
   rather than as a separate event kind, so the existing write-ahead marker
   and recovery path cover it. The constraint allows either.
6. The pull request that landed runbook amendment receipts, merged as
   commit `7e8a3f9f` for task #554 under number 584, cannot be opened on
   GitHub today, so its body was not read. Its content is taken from commit
   `a36768abf65d4afbcb310f1c231e98866798fbe7`.

## 1. Problem statement

`hexctl amend runbook` records the study digest current at write time in
each runbook amendment, at `_runbook_amendment_record` near `hexctl.py:11207`.
`source_runbook_step` near `hexctl.py:11653` admits an amendment into the
Mason or Warden packet only when that digest equals the current study digest,
and `amendment_block` near `hexctl.py:2362` applies the same equality when a
runbook repair is asked to clear a broken study verdict. Every
`hexctl amend study` changes the study digest, so every earlier runbook
amendment leaves the effective step at once. Nothing prints, nothing refuses,
`verify` and `status` stay clean, and only `next`'s
`brief.runbook_step.amendments` shows the loss. Run 856 reissued one step's
repaired fields five times; run 857 recorded the same loss as S1-R2-02.

The user is the Fiat controller session and its operator. The change is for
the controller itself: `amend study` decides, per effective runbook
amendment, whether the amendment is retained under the new study digest or
displaced, records that decision in the ledger, prints it, and the packet
builders follow the recorded decisions.

A working prototype means all five requirements of the issue hold on a
checked run, each mapped to a command:

1. Identification. `hexctl amend study` prints one `retained` or `displaced`
   line per effective runbook amendment naming its amendment digest, the
   steps it touches and its replaced field names. Proved by the guard test
   class `StudyAmendmentRebindTests` in `plugins/hexaemeron/tests/test_hexctl.py`,
   run by `python3 plugins/hexaemeron/tests/run_tests.py -k StudyAmendmentRebind`.
   Met by `verdict-rebind`; `refuse-then-reissue` prints the same list before
   refusing; `announce-only` prints it after the drop.
2. Atomic rebind or refusal, no stale intermediate packet. After one
   unrelated study amendment, `hexctl next` reports the same
   `brief.runbook_step.amendments` length and the same amendment bytes as
   before. Proved by the same test class. Met by `verdict-rebind`;
   `refuse-then-reissue` meets it by refusing; `announce-only` fails it, as
   the `stale-packet` gate in the design record shows.
3. A related change still needs review. A study amendment whose `Still
   holding` field marks step N `entry broken` or `exit broken` displaces
   every runbook amendment touching step N; the packet drops those bytes
   and `amendment_block` keeps step N blocked until a new runbook amendment
   is reviewed and receipted. Proved by the second specimen in the same test
   class. Met by `verdict-rebind` and by `refuse-then-reissue`, which
   reissues everything under review; `announce-only` meets it by retaining
   nothing.
4. Ledger retention. The `amend:study` event data carries, for each
   effective runbook amendment, `amendment_sha256`, `from_study_sha256`,
   `to_study_sha256` and `decision` in `retained` or `displaced`.
   `hexctl verify` recomputes the list from the two receipt histories and
   refuses a mismatch. Proved by the same test class and by
   `hexctl verify` exit 0 on a run built before the change. Met by
   `verdict-rebind` only; the other two record no decision because they
   retain nothing.
5. Regression coverage. One test creates a runbook amendment, applies two
   unrelated study amendments and proves the effective fields stay bound
   through two recorded `retained` rebinds; a second test applies a related
   study amendment and proves the `displaced` record, the printed line and
   the dropped packet bytes. Both fail on the starting ref and pass on the
   fix. Met by whichever candidate is built; the tests are written against
   the selected one.

The demo path is the last runbook step: on a scratch run, receipt one runbook
amendment, apply two unrelated study amendments, and show `hexctl next`
carrying the amendment with two retained rebinds in `.hexaemeron/ledger.jsonl`.

## 2. Prior art

### Merged pull requests

The two most recent merged pull requests whose commits changed the amendment
binding code in `hexctl.py`, found with
`git log -S'study_sha256' -- plugins/hexaemeron/skills/fiat/scripts/hexctl.py`:

- [PR #1069](https://github.com/wildcat-finance/skills/pull/1069), merged
  2026-09-02 as `f2770e006884b6399d0e9940465450513c1fa0ed`, carrying commit
  `482172e7`, "Rebuild the immutable run anchor and checkpoint identity on
  current main". Its body is the analytics block plus "Original was #560,
  moved to #860". It carries nothing forward about amendments; there was
  nothing to answer.
- The pull request for task #554, merged 2026-08-24 as
  `7e8a3f9f` "Merge pull request #584", carrying commit `a36768ab`
  "feat(fiat): receipt runbook amendments". This is the commit that wrote
  the equality at `source_runbook_step`. `gh pr view 584` returns "Could not
  resolve to a PullRequest", so its body was not read and any item it carried
  forward is unknown. Its commit message carries no open item.

Also read, as the most recent merged pull request titled about amendments
that touched `hexctl.py`: [PR #931](https://github.com/wildcat-finance/skills/pull/931),
merged 2026-08-30 as `21f97be370e9c861a41ed9c5fe64b9d0322284b7`, which made
Protasis the sole shape authority for study amendments. Its body carries
finding `S2-R1-01` fixed and no open item.

The `gh pr list --search "amend" --state merged` result also lists
[PR #474](https://github.com/wildcat-finance/skills/pull/474) and
[PR #473](https://github.com/wildcat-finance/skills/pull/473) of
2026-08-22, the study-amendment receipts; they predate the runbook binding
and their audit rows are carried below from the root record.

### Audit sources

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the target root on 2026-09-13 and exited 0: 81 source-and-synopsis
pairs, every one `committed=match`. Synopses were therefore the normal
reading view. In-scope sources, and what was read:

| Source | Read | Evidence for the choice |
| --- | --- | --- |
| `audit/AUDIT.md` with `audit/AUDIT_SYNOPSIS.md` | synopsis, plus source lines 8044 to 8134 | check exit 0; the legacy 2026-08-22 amendment runs carry `[missing legacy field: ...]` in the synopsis, so their risk tables were read in the source |
| `audit/rounds/fiat-856-framework-13-test-the-remaining-atlas-hand-o.md` | synopsis, plus source lines 133, 158 and 181 | check exit 0; the treadmill rows sit in `Leads not pursued`, read in the source for exact wording |
| `audit/rounds/fiat-857-framework-16-the-commit-gate-lives-in-one-cl.md` | synopsis, plus source lines 35, 55 and 109 | check exit 0; S1-R2-02 read in the source for its closing disposition |
| `audit/rounds/fiat-1098-make-a-bound-instruction-document-editable.md` | synopsis | check exit 0 |
| `audit/rounds/fiat-1345-*.md` | not present | `ls audit/rounds` lists no such file on the starting ref |
| `audit/rounds/fiat-1538-restore-main-root-suite-green-and-enforce-m.md` | synopsis | most recent controller run by commit date, 2026-09-12; check exit 0 |
| `audit/rounds/fiat-1420-ephoros-next-extend-e001-to-e003-to-the-typ.md` | synopsis | second most recent controller run, 2026-09-11; check exit 0 |
| `plugins/hexaemeron/audit/AUDIT.md` | synopsis | check exit 0; no line names an amendment |

Findings carried forward, by id and status:

- Run 856, `Leads not pursued`, step 2 rounds 1 to 3: "the study-digest
  treadmill is carried forward, not answered, and it is a controller defect
  rather than step 2 work". Carried here as the problem statement. S1-R1-04,
  accepted, and S1-R1-05, open, each "needs a controller amendment"; they
  belong to run 856's own artefacts and stay open there. S1-R2-04, accepted,
  is a Hypomnema bridge limit, out of scope.
- Run 857, S1-R2-02, medium, "closed for this run"; the round names the
  standing hazard: "any future study amendment unbinds every runbook
  amendment recorded before it" and assigns it to the Fiat frontier. Carried
  here as requirement 2. S1-R2-01, S1-R2-03 and the step 4 refresh are that
  run's own and stay closed there.
- Run 1098: S4-R1-01, high, open; S4-R2-02, medium, open; S4-R2-04, low,
  open. Each concerns the content of an amended step in that run, not the
  binding mechanism. Refused by name as out of scope; #1264's boundary keeps
  #837, #976 and #1117 separate and these sit with them.
- Runs 1538 and 1420: no finding names an amendment; nothing to carry.
- Root record, "Fiat receipted study amendments" step 2 rounds 1 and 2 of
  2026-08-22, audit schema unknown, `[missing legacy field: covered]`,
  `[missing legacy field: not-checked]`, `[missing legacy field:
  elenchus-verdict]`. Risk ids and final status: `prefix-forgery` clean,
  `amendment-selection` clean, `field-ambiguity` clean,
  `step-verdict-coverage` clean, `broken-step-transition` clean,
  `checker-binding` clean, `path-scope` clean, `partial-write` clean,
  `receipt-history` clean, `post-amend-drift` clean, `legacy-state` clean,
  `evidence-overclaim` clean. `Leads not pursued` is a missing legacy field
  for those rounds. The ids `partial-write`, `receipt-history`,
  `legacy-state` and `evidence-overclaim` reappear in item 5 because this
  change touches the same transitions.

### In the repository

- `hexctl.py`: `_runbook_amendment_record` near line 11207 records
  `study_sha256`; `cmd_amend_study` near line 11373 already computes
  `step_verdicts` for every unbuilt step through `_study_step_verdicts`
  near line 11018; `_receipted_runbook_amendments` near line 11598 replays
  offsets and digests; `verify_run` near line 17212 calls it; `amendment_block`
  near line 2359 holds the second equality.
- `plugins/hexaemeron/skills/fiat/SKILL.md` lines 519 to 531 document the
  current behaviour in prose: "every current-study-bound amendment" enters
  the packet and "a later study amendment changes that digest, so an older
  repair no longer applies". The second sentence becomes false under the
  chosen design and must be rewritten.
- `tests/promise_machine_coverage.json` binds `fiat-amendment-m`, `-o`,
  `-p` and `-r` to named tests in `test_hexctl.py` and `test_fiat_skill.py`.
- Six existing amendment tests in `test_hexctl.py`, none of which names
  `study_sha256`.

### Outside the repository

Append-only event ledgers that carry per-item decisions and replay to the
same state are the ordinary event-sourcing shape; nothing external is copied
here. No standard applies.

## 3. Constraints and non-goals

Constraints:

- Starting ref `b9f8e36b8b6210bcd023a68059ecb46da3e35769` on `main`; Python
  `3.14.6` per `.python-version`; stdlib `unittest`; no new dependency.
- No change to receipt shapes already recorded. The ledger is append-only;
  old runs must still verify. A new key on new study amendment records, or a
  new ledger event kind, is acceptable; editing history is not.
- The run pins `plugins/hexaemeron/skills/fiat/EVOLUTION.md` at
  `fiat-v5.54.1`, 59 rows. Integration owes exactly one new `generation` row
  and the hexaemeron plugin version bump in
  `plugins/hexaemeron/.claude-plugin/plugin.json`,
  `plugins/hexaemeron/.codex-plugin/plugin.json`, both `marketplace.json`
  files and the README. The held issue #363 job stays untouched.
- Editing `hexctl.py` starts a four-stage digest re-pin chain:
  `tests/promise_machine_coverage.json` carries the whole-file digest of
  `hexctl.py`; then `docs/promise-machine/obligation-gates/evaluation-run.json`
  is re-tallied with `tests/promise_evaluation_driver.py`; then
  `demonstration-run.json` and `demonstration-evidence.md` in the same
  directory; then `.horos/census.json`, `.horos/boundary.json` and
  `.horos/candidates.json`. Editing `fiat/SKILL.md` moves the digests in
  `tests/fixtures/agent-instruction-v1/manifest.json`, which binds that
  file once. Any edit to a promise stanza moves the semantic digests in
  `tests/promise_machine_id_history.json`. The design does not require a
  stanza edit; see assumption 4.
- Never write the decision-record identity token in study or runbook prose;
  describe the record by its path in words, as item 12 does.
- Every shipped document passes imprimatur, hypomnema and protasis before a
  receipt.

Boundaries, in three tiers:

- Always. Both suites before a commit: `python3 plugins/hexaemeron/tests/run_tests.py`
  and the root suite `python3 -m unittest discover -s tests -v`. The
  imprimatur lint on the study, the runbook, the draft decision record and
  the rewritten `SKILL.md` paragraph. A recorded measurement before any
  change made for speed.
- Ask first. Adding a dependency. Changing the shape of a receipt already
  recorded. Editing a promise stanza's semantic fields. Touching CI. Adding a
  ledger event kind rather than a key on the study amendment record.
- Never. Edit `ledger.jsonl` or `state.json` by hand. Delete or weaken an
  existing amendment test to make the suite pass. Claim a lint or suite ran
  when it did not. Write the decision-record identity token in prose.

Non-goals:

- Not removing the study-digest binding; a runbook amendment still records
  the digest it was reviewed against.
- Not rewriting completed steps or any frozen record.
- Not touching #837 frozen-record repair, #976 receipted link recovery or
  #1117 tracked-copy currency.
- Not retroactively rebinding amendments in runs that were displaced before
  this change; those were reissued by hand and their history stands.

## 4. Design options

Three candidates were measured on a stub model of the transition in
`.hexaemeron/measure_design.py`, with 17 effective runbook amendments for the
selection metric and 500 for the time gate. The design record
`.hexaemeron/design-evidence.json` selects mechanically; the prose here only
explains the candidates. The existing behaviour is not a fourth candidate:
the frontier needed none, and it fails the issue's requirement 1 on its face.

`verdict-rebind`. At `amend study`, for each runbook amendment effective under
the old study digest, read the new study amendment's verdicts. When every step
the runbook amendment touches has `entry holds; exit holds`, record
`{amendment_sha256, from_study_sha256, to_study_sha256, decision: retained}`;
otherwise record `displaced` and print the step and replaced fields. The list
lives in the study amendment record as `runbook_rebinds`, so it rides the
`amend:study` event, the pending marker and recovery unchanged.
`source_runbook_step` and `amendment_block` admit an amendment whose recorded
digest, followed through retained rebinds in study-history order, reaches the
current digest. `verify` recomputes each list from the two histories. The
trade: the ledger grows by one 288-byte record per effective amendment per
study amendment, and compatibility is inferred from the operator's own
verdicts rather than reviewed per amendment. Measured: 0 reissues.

`refuse-then-reissue`. `amend study` refuses while any effective runbook
amendment would be displaced and prints the exact list; the operator reissues
each amendment against the new digest first. Simplest change and no new
record. The trade: 17 reissues per unrelated study amendment on the live run,
each a full `amend runbook` with its own Protasis check, and the study cannot
be corrected until they are done. Measured: 17 reissues.

`announce-only`. Keep the drop but print the displaced count and fields at
`amend study` and at `next`. Smallest diff. The trade: the next packet after
an accepted study amendment is still built from baseline fields, which is
requirement 2's exact prohibition. Measured: 17 reissues and `stale-packet`
true, so the gate removes it.

Selection metric: `reissues-per-study-amendment`, minimised. Hard gates at
selection: `silent-drop` equals false, `stale-packet` equals false,
`related-change-reviewed` equals true, `ledger-replay` equals true,
`receipt-compat` equals true, `packet-bytes` at most 512, and
`amend-study-milliseconds` at most 1000 over 500 amendments. The time
criterion is a gate rather than a minimised metric because the study's only
budget is a threshold, and a sub-millisecond comparison over three loops
would let timer jitter pick the design. Conformance gate
`regression-coverage`, pending for every candidate, blocks `integration`
and is resolved by `python3 .hexaemeron/measure_design.py --resolve
regression-coverage --candidate <id> --out .hexaemeron/reports/<id>-regression-coverage.json`.
Result: `announce-only` fails `stale-packet`; `refuse-then-reissue` is
dominated on the metric; `verdict-rebind` is the unique frontier, and
`design_evidence.py --transition design-lock` exits 0.

## 5. Risk register seed

The audit loop reviews these at each round. The four ids shared with the
2026-08-22 root record are reused so a round can cite continuity.

```risk-register
silent-displacement | the packet builders after amend study | an effective amendment never leaves the packet without a printed line and a recorded decision
rebind-chain-forgery | state.json edited outside hexctl | verify recomputes every runbook_rebinds list from the two receipt histories and refuses a mismatch or an unknown decision value
partial-write | the amend study write-ahead marker | an interrupted amend study recovers to exactly one amend:study event whose rebind list equals the recomputed one, or rolls back
receipt-history | the study and runbook amendment histories | the rebind chain follows study-history order only, from prior_sha256 to new_sha256, and a gap or a fork is refused
legacy-state | a run started before this change | a study amendment record with no runbook_rebinds key means no rebinds, and such a run verifies and builds packets as before
verdict-inference | the Still holding verdicts of the new study amendment | an amendment touching any step not marked entry holds and exit holds is displaced, never retained
history-cap | AMENDMENT_HISTORY_MAX at 500 | the rebind loop is bounded by both histories and refuses beyond the cap rather than truncating
printed-fields | the retained and displaced lines on stdout | only step numbers, field names from the closed set and hex digests are printed; no amendment prose reaches stdout
digest-repin-chain | the four-stage re-pin after editing hexctl.py and the manifest re-pin after editing SKILL.md | every stage is re-tallied in the step that edits the file and the root suite is green at the step exit
skill-prose-currency | plugins/hexaemeron/skills/fiat/SKILL.md lines 519 to 531 | the sentence that an older repair no longer applies after a study amendment is rewritten in the same step as the code
evidence-overclaim | the fiat-runbook-amendment and fiat-study-amendment stanzas | the receipt establishes a recorded decision, not that a retained amendment is semantically compatible
```

## 6. Glossary seeds

- effective runbook amendment: a receipted runbook amendment that names the
  step and whose bound digest reaches the current study digest.
- bound digest: the study digest a runbook amendment recorded, followed
  through its retained rebinds in study-history order.
- rebind: one record `{amendment_sha256, from_study_sha256, to_study_sha256, decision}`.
- retained: the rebind decision when every touched step holds entry and exit.
- displaced: the rebind decision when any touched step is broken; the
  amendment leaves the packet until reissued.
- unrelated study amendment: one whose `Still holding` marks every unbuilt
  step holding.
- related study amendment: one whose `Still holding` marks a touched step
  broken.
- reissue: an operator `hexctl amend runbook` that restates fields already
  amended once, only because the study digest moved.
- rebind list: the `runbook_rebinds` array in one study amendment record.

## 7. Sources

- Issue #1264, read with `gh issue view 1264 -R wildcat-finance/skills`.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at
  `b9f8e36b8b6210bcd023a68059ecb46da3e35769`: lines 2359 to 2447, 11018
  to 11080, 11185 to 11236, 11373 to 11445, 11598 to 11720, 13655 to 13720,
  17212 to 17300.
- `plugins/hexaemeron/skills/fiat/SKILL.md` lines 458 to 531 and the
  `fiat-runbook-amendment` stanza at line 880.
- PR #1069, PR #931, commit `a36768abf65d4afbcb310f1c231e98866798fbe7`,
  merge commit `7e8a3f9f`.
- `audit/AUDIT.md` lines 8001 to 8134; the five round synopses and the
  source lines named in item 2.
- `tests/promise_machine_coverage.json` lines 1160 to 1182.
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md` line 78, `fiat-v5.54.1`.
- `.hexaemeron/measure_design.py` and `.hexaemeron/reports/*.json`, 24
  selection reports.
- Protasis contract at
  `plugins/hexaemeron/skills/protasis/SKILL.md`; Hypomnema mechanical subset
  at `plugins/hexaemeron/skills/hypomnema/SKILL.md`.

## 8. Signals, and the questions behind them

Questions someone asks after an unattended run:

1. Which runbook amendments did the last study amendment displace, and on
   which step and fields? Answered by the `displaced` lines `amend study`
   prints and by the `runbook_rebinds` list in the last `amend:study` ledger
   event.
2. Does step N's packet still carry repair X? Answered by
   `hexctl next` showing X's digest in `brief.runbook_step.amendments`, and
   by the retained chain for X in the ledger.
3. Did a recovery after an interrupted `amend study` keep the same rebind
   list? Answered by `hexctl verify` exit 0, which recomputes it.

The step that changes `cmd_amend_study` emits the lines; the step that
changes `verify_run` emits the recomputation refusal. Signal content follows
ephoros, `plugins/hexaemeron/skills/ephoros/SKILL.md`.

## 9. Boundaries, per capability

- The study amendment candidate file: already bounded by
  `read_bounded_source` and checked by Protasis before any record is built.
  What is worth taking: a crafted `Still holding` field that marks every
  step holding to carry a stale repair forward. Control: the verdicts are
  the operator's signed claim already receipted today; the rebind adds no
  new input, and a displaced decision is never inferred from history alone.
- `state.json` and `ledger.jsonl`: an edit outside hexctl could insert a
  `retained` record. Control: the state fingerprint in each ledger entry
  and the `verify` recomputation from both histories.
- stdout: the printed lines carry digests, step numbers and field names
  from the closed set `Goal`, `Entry`, `Exit`, `Files`, `Tests`,
  `Disciplines`; no free text from the amendment.
- No subprocess, network or credential is added. Controls follow
  phylax, `plugins/hexaemeron/skills/phylax/SKILL.md`.

## 10. The budget, or its absence

One budget: `hexctl amend study` with 500 effective runbook amendments, the
`AMENDMENT_HISTORY_MAX` cap, finishes its rebind loop under 1000
milliseconds. Measured now on the stub by
`python3 .hexaemeron/measure_design.py`, report
`.hexaemeron/reports/verdict-rebind-amend-study-milliseconds.json`, value 1
millisecond rounded up from 0.339. The build re-measures on the real
command in the step that changes `cmd_amend_study`, with the same 500-item
fixture. No other budget applies: `next` and `verify` already walk both
histories once. Measurement follows
metron, `plugins/hexaemeron/skills/metron/SKILL.md`.

## 11. The fail-closed posture

What stops the run: a rebind list that `verify` cannot recompute, a decision
value outside `retained` or `displaced`, a chain gap between study
amendments, a history beyond the cap, or an interrupted `amend study` whose
recovered record differs from the pending one. Each is a `die` with exit 1
before any durable write, on the existing pattern.

Guard-test convention: each fix lands with a test in
`plugins/hexaemeron/tests/test_hexctl.py` that fails on the starting ref and
passes with the fix, run through
`python3 plugins/hexaemeron/tests/run_tests.py`. The first guard is the
two-unrelated-amendments specimen of requirement 5; the second is the
related-change specimen. Triage follows
elenchus, `plugins/hexaemeron/skills/elenchus/SKILL.md`.

## 12. Decisions and their homes

Expensive to reverse: the rebind list's shape and its home inside the study
amendment record, because every later run's ledger carries it and `verify`
replays it. The record is a draft under `docs/decisions/drafts/`, named by
its stable slug, unnumbered until the integration composition assigns a
number through the assignment gate. It covers "rebind a runbook amendment on
a holding verdict rather than dropping it" and names the two losing
candidates. Runbook step 1 commits the draft with the study and runbook.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | verdict-rebind
record | docs/decisions/drafts/rebind-runbook-amendments-on-a-holding-verdict.md
```

The `fiat-v5.54.1` to next-generation row in
`plugins/hexaemeron/skills/fiat/EVOLUTION.md` is written at integration and
cites the same record. The rewritten paragraph in `fiat/SKILL.md` is the
contract home for the packet rule. Placement follows
hypomnema, `plugins/hexaemeron/skills/hypomnema/SKILL.md`.
