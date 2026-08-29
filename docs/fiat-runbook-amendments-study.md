# Study: runbook amendment receipts

Assuming, unless corrected:

1. Issue #554 is ordinary Fiat delivery. The controller state records
   `frontier: null`, so this run does not pass `--frontier`, increment either
   evolution counter, or replace either held frontier. It still makes
   meaningful behavioural changes to two governed skills, so VERSIONING.md
   requires one generation row for Fiat and one for Protasis.
2. The exact start is `84abae32d6d65b3a3ce27648ca144852a9e22e98`
   on `main`, where Fiat is `fiat-v5.20.1` and Protasis is
   `protasis-v4.6.0`. On an unchanged base, this delivery produces
   `fiat-v5.21.1` and `protasis-v4.7.0`. The isolated run branch is
   `fiat/554-runbook-amendment-receipts`.
3. The in-scope contracts are Protasis for the content of a runbook amendment
   and its mechanical last-step boundary, and Fiat for its receipt, recovery,
   blocking state, and delegated packet. Both changes count as generation,
   not prose-only edits.
4. A runbook amendment is accepted only after the study and runbook have been
   receipted and while build steps are active. It cannot add, remove, reorder,
   renumber, or rename steps, and it cannot rewrite a completed step.
5. The candidate keeps the currently receipted runbook bytes unchanged as its
   exact prefix and appends one final dated amendment. Earlier amendments stay
   in that prefix.
6. The amendment keeps the existing four fields: `What changed`, `Why`,
   `Steps touched`, and `Still holding`. For a changed runbook field, `What
   changed` restates the complete replacement field, including the exact
   command that proves a changed exit.
7. Every current or pending step receives one exact entry-and-exit verdict.
   A runbook amendment may repair a study-amendment block only when it is bound
   to the current study digest and restates the blocked current step.
8. Python 3 and the standard library remain the implementation boundary. No
   dependency, network call, state-version change, or CI change is assumed.
9. Existing interrupted `amend study` transactions must retain their current
   recovery path. Generalising the code must not strand their pending marker.
10. Issue #429's branch and controller state are not repaired by this run.
    They are evidence for the missing transition; #557 owns the lost-ledger
    problem that prevents applying the transition to that historical run as-is.
11. Elenchus uses two identifiers at different boundaries. The CLI report
    format is `unittest-json-v1`; the JSON report schema it produces is
    `elenchus.unittest.v1`. A runbook `Tests` contract must name the former as
    its report format and may name the latter only as the expected report
    schema. They are not aliases.
12. This study belongs only to issue
    `https://github.com/wildcat-finance/skills/issues/554`, controller state
    `49518dc37c1f9274e13a76ee518721bebbdc2ecb058713147dd4bcae3c83c5a1`,
    and this run's `.hexaemeron/study.md`. The earlier seven- and eight-entry
    ledgers are evidence, not receipts imported into this run.
13. Every step derived for this run's runbook must permit its mandatory
    append-only round record in `audit/AUDIT.md` through its `Files` scope. A
    docs-only implementation scope may remain narrow, but it cannot forbid the
    audit record that Fiat requires after implementation. This is a
    source-bound derivation and operator cold-review gate for this runbook, not
    a new Protasis rule, `hexctl` feature, or runtime checker behaviour.

## 1. Problem statement

Fiat binds a runbook path and SHA-256 at `done runbook`. Later Mason and Warden
packets reread that exact artefact, verify its digest, and select the current
`## Step N` block. Any later byte change is therefore ordinary drift and is
refused. There is no receipted way to correct an entry, exit, file list, test
command, or discipline clause after new evidence makes it stale.

Issue #554 supplies the live case. Issue #429's step 3 names Fiat v5.13.1,
while the current base at this study's start carries v5.20.1. The preserved
step-2 tip `4b78dfa` is 46 commits ahead of and 146 commits behind the current
base. Those counts will move, but the mismatch already makes the literal
v5.13.1 exit unreachable as written. Halting and starting another study loses
the accepted runbook's continuity; proceeding against the stale criterion
claims success against words everybody knows are wrong.

The working prototype adds `hexctl amend runbook --artifact <candidate>`. It
accepts only one append-only Protasis amendment, re-pins the runbook receipt,
records the old, new, and amendment digests, and carries the exact applicable
amendment beside the original step bytes in every later Mason and Warden
packet. A replacement exit is therefore genuinely actionable: the packet
contains the complete new criterion and its command, not merely a note that
the old criterion is stale.

A temporary-repository demonstration proves the useful path. It receipts a
two-step runbook whose current exit names `fiat-v1.0.0`, appends an amendment
that replaces that exit in full with a command checking `fiat-v2.0.0`, receipts
the amendment, and observes the exact replacement in both the Mason and Warden
source packets. A second demonstration starts from a broken study verdict and
shows that only a runbook amendment bound to that study digest and carrying a
holding replacement clears the block.

On the recorded base, the prototype also advances Fiat's generation from
`fiat-v5.20.1` to `fiat-v5.21.1` and Protasis's from `protasis-v4.6.0` to
`protasis-v4.7.0`. Each `SKILL.md` frontmatter value matches its ledger header
and new history row. Fiat retains frontier revision `state-shape-validation`
and digest `e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`;
Protasis retains frontier revision `amendment-block-check` and digest
`1014071026a149d38e7d79c222dfcfc25dd061d825fac9e7813a3a46b184cd29`.
Their current-frontier and next-job text remain byte-for-byte unchanged.

Acceptance is checked by:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill plugins.hexaemeron.tests.test_protasis_checker
python3 -m unittest discover -s tests -p 'test_evolution_contract.py'
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study .hexaemeron/study.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py .hexaemeron/study.md
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
```

The topic is one capability rather than several independent deliveries. The
content rule, durable transition, and source-packet overlay cannot be cut from
one another without producing either an unreceipted convention or a receipt
whose corrected criterion never reaches the builder and reviewer.

The first halted #554 run stopped before implementation after cold review found
that its runbook put the report schema `elenchus.unittest.v1` where the
Elenchus CLI contract required report format `unittest-json-v1`. Its
seven-entry controller ledger verified before the halt. The second halted run
made one signed, docs-only Step 1 commit and passed 349 root tests and 986
Hexaemeron tests. Warden then found that the literal Step 1 `Files` boundary
forbade the mandatory `audit/AUDIT.md` round record. It halted before any audit
append, audit receipt, push, or pull request, with an eight-entry controller
ledger verified. Neither run implemented issue #554. This study carries their
research and failure evidence only. The new runbook must state both Elenchus
identifiers beside their separate roles and permit each mandatory audit record
before its receipt can be submitted.

## 2. Prior art

The last two merged pull requests that changed the target Fiat controller,
canonical skill, and focused tests were read before choosing a design:

- [PR #579](https://github.com/wildcat-finance/skills/pull/579) added bounded
  run-observation receipt binding. It requires an exact source, a stable digest,
  a narrow Promise, and later recomputation without widening ordinary
  verification. Its `Carried forward` section leaves #508's runbook-gate work
  open; executable gate validation remains a non-goal here.
- [PR #562](https://github.com/wildcat-finance/skills/pull/562) added a bounded
  replacement for a failed integration sync. It retains the failed receipt,
  identifies the exact active subject, requires fresh evidence, and makes only
  the checked replacement usable. It carries no unfinished runbook-amendment
  work, but its repair pattern applies here: preserve the failed belief and
  bind the recovery rather than overwrite history.

[PR #474](https://github.com/wildcat-finance/skills/pull/474) is the direct
analogue. It integrated the append-only `amend study` transition and carried a
separate runbook-repair transition forward by name. It also carried general
transaction rewrites and the truth of operator prose forward; this issue
answers only the runbook repair and leaves those other boundaries open.

The analogous audit record at `audit/AUDIT.md` was read, including the two Fiat
study-amendment rounds. Round 1 found and fixed three mechanisms that govern
this design: an interrupted artefact/ledger/state update, a missing
consequence-2 Promise and terminal block, and a Markdown fence-length error.
Round 2 re-ran those mechanisms, found zero findings, and left runbook repair
as an explicit unpursued lead. The earlier Protasis amendment-contract rounds
found no defects and no unpursued leads; they fixed the append-only four-field
shape and the rule that a broken entry stops dependent work.

Current code supplies most of the construction:

- `done_runbook` already stores the canonical path, digest, step count, and
  titles under `receipts.runbook`.
- `receipted_source` verifies either study or runbook bytes before a packet is
  built.
- `cmd_amend_study` already implements exact-prefix selection, field and
  verdict parsing, bounded Protasis execution, a durable pending marker,
  atomic replacement, receipt history, ledger commit, and recovery.
- `source_runbook_step` selects one exact numbered and titled step, but stops
  only at the next step. A trailing `### Amendment` would otherwise be folded
  into the last step, and an amendment touching an earlier step would never
  reach that step's packet.
- `verify_run` currently recomputes a receipted study but not a receipted
  runbook. A runbook amendment therefore needs an explicit verification guard,
  not reliance on a later delegated action happening to reread it.

The existing tests in `plugins/hexaemeron/tests/test_hexctl.py` cover holding
and broken study amendments, exact prefix and field failures, fence decoys,
unsafe and oversized paths, checker refusal, concurrent writers, four
interruption windows, repeated amendments, legacy receipts, and later drift.
They are the source corpus to generalise. The current Protasis checker tests
also show that a level-three amendment heading is not a normal step boundary;
the runbook path needs a named boundary so amendment fields cannot answer for
the last step.

Two halted #554 runs are bounded prior art. The first reached a checked study
and draft runbook, then halted with a verified seven-entry ledger when cold
review caught an evidence-interface mismatch before implementation:
`elenchus.unittest.v1` identifies the report body's schema, while
`unittest-json-v1` is the Elenchus CLI report format the source-bound `Tests`
field must supply. The second made a signed docs-only Step 1 commit, passed 349
root tests and 986 Hexaemeron tests, and halted with a verified eight-entry
ledger when Warden found that Step 1 permitted only its documents while Fiat
required an append-only `audit/AUDIT.md` round record. That finding came before
an audit append, audit receipt, push, or pull request. The halts are red
examples for the runner and file-scope contracts. They do not prove that issue
#554 was implemented and do not widen its product design.

## 3. Constraints and non-goals

The build starts at the exact SHA named above and changes only the accepted
study/runbook copies; the Fiat and Protasis canonical skills, frontmatter, and
generation ledgers; `hexctl.py`; `protasis.py`; focused tests; Promise Machine
coverage; and the audit record required by later Fiat phases. State version 1,
the seeded step list, branch topology, completed-step receipts, and earlier
artefact bytes remain unchanged.

For this source-bound runbook, derivation treats `Files` as the permitted
surface for the whole Fiat round, not only Mason's implementation edit. Every
step therefore names `audit/AUDIT.md` as an append-only audit-record surface
alongside its bounded implementation files. A step whose implementation
changes only documentation may say so, but cannot say “only these documents”
in a way that excludes the Warden record. During cold review, the operator
refuses this runbook before `done runbook` if that permission is missing or
contradictory. Issue #554 does not add a controller or Protasis check for this
run-specific derivation rule; existing Protasis behaviour may remain unchanged
on this point.

The Fiat history row is a generation row from `fiat-v5.20.1` to
`fiat-v5.21.1` on the recorded base. It retains frontier revision
`state-shape-validation`, frontier digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`,
and the exact current-frontier and issue #363 next-job text. The Protasis row
is a generation row from `protasis-v4.6.0` to `protasis-v4.7.0`; it retains
revision `amendment-block-check`, digest
`1014071026a149d38e7d79c222dfcfc25dd061d825fac9e7813a3a46b184cd29`,
and its exact current-frontier and held amendment-check job text. Neither row
claims a frontier advance.

Those result labels are conditional on the recorded base. Immediately before
composition with an advanced `main`, reread each active ledger and matching
frontmatter. If a concurrent generation already used either result label while
the frontier revision, digest, status, current-frontier text, next-job text,
and compatibility boundary still hold, assign this delivery the next unused
generation for that skill and update its frontmatter, ledger header, and one
new history row together. If any held frontier field, evolution counter, epoch,
or compatibility premise changed, do not guess: amend the study and runbook or
halt before integration. A collision is never resolved by duplicating a label,
rewriting the other row, incrementing evolution, or passing `--frontier`.

The controller accepts the runbook amendment only in `steps`. It may run while
a study or runbook verdict has blocked the current step, because this is the
named recovery. The accepted candidate must preserve the current runbook as
its exact byte prefix, append one real final amendment outside Markdown fences,
pass the bundled Protasis runbook checker, name only current or pending steps,
and carry one verdict for every unbuilt step.

`What changed` must restate every superseded runbook field in full. A changed
`Exit` includes the replacement command; a changed `Tests` includes the exact
Elenchus `{report}` runner, format, and report file. The controller records and
transports those source bytes. It does not decide that the new criterion is
correct or that its command will pass on future implementation bytes.

For this run's own audit-fix runner, the corrected runbook must write
`unittest-json-v1` in the report-format position and
`elenchus.unittest.v1` in the expected-schema position. The exact command has
one `{report}` argument and names the report file separately. Cold review
compares those labelled roles before `done runbook`; mere presence of both
strings is not enough.

A runbook amendment cannot add, remove, reorder, rename, or renumber a step,
rewrite completed history, change a step branch, repair a lost controller
ledger, resolve target versions dynamically, validate every runbook command at
receipt time, edit a study, or act outside this repository. Issues #555, #556,
#557, and #508 retain those adjacent jobs.

**Always.** Preserve the old bytes and receipt history; bind the current study
and runbook digests; include the complete replacement field in the affected
source packet; keep completed steps immutable; add exactly one generation row
per changed governed skill with matching frontmatter and retained frontier
fields; run the focused and complete suites before a commit; run Imprimatur on
every shipped document; verify every Fiat-created signed commit before
publication; keep `unittest-json-v1` labelled as the Elenchus CLI report format
and `elenchus.unittest.v1` labelled as the generated report schema; permit an
append-only `audit/AUDIT.md` record in every step of this runbook's `Files`
scope.

**Ask first.** Change state version; add a dependency; change step count,
titles, order, branches, public receipt compatibility, or CI; broaden the
operation beyond active build steps; change a held frontier field, evolution
counter, epoch, or compatibility boundary; weaken an exact digest or checker
gate.

**Never.** Commit a credential, key, token, or raw signature; edit vendored
code; delete a failing test to make a suite pass; treat arbitrary runbook drift
as an amendment; erase a prior amendment or failed verdict; infer a holding
verdict from silence; claim a command, checker, recovery, test, audit, push, or
merge ran when it did not; substitute a report schema identifier for a CLI
report format or treat the two Elenchus identifiers as aliases; submit this
runbook when a step's literal `Files` boundary forbids the audit record its
Fiat round must append.

## 4. Design options

### Option A: halt and repeat the study and runbook phases

This uses existing commands but creates a new run rather than a correction. It
breaks continuity with pushed step receipts, cannot repair an in-place blocked
run, and makes the earlier accepted runbook disappear from the active evidence
chain.

### Option B: replace the runbook receipt with a generic digest update

This is small, but it cannot distinguish an append-only correction from an
arbitrary rewrite. It has no step-verdict coverage, no blocked-step recovery
rule, and no way to make the corrected field part of the exact source packet.

### Option C: a subject-aware append-only amendment transition (chosen)

Generalise the study-amendment helpers around a `study` or `runbook` subject
without weakening the existing study path. `amend runbook` proves the current
runbook is the candidate's exact prefix, parses the same dated four-field
suffix, runs Protasis in runbook mode, validates touched and unbuilt steps, and
records `amend:runbook` with the prior, new, and amendment digests plus the
current study digest.

Keep subject-specific pending markers behind shared recovery code. The existing
study marker remains recoverable; a runbook marker names its subject, canonical
path, prior state digest, and amendment record. Any pending marker blocks other
commands, and two markers at once refuse rather than choose one.

The runbook receipt keeps ordered amendment history. `source_runbook_step`
ends the original step at the first real amendment heading and returns the
original contiguous step bytes plus each exact amendment block whose `Steps
touched` names that step, in receipt order. Mason and Warden therefore receive
both the accepted baseline and the complete replacement field. No duplicate
`## Step N` block is appended or selected, so titles and branch identities stay
unambiguous.

The latest runbook verdict blocks when its current-step entry or exit is
broken. A holding runbook amendment clears a broken study verdict only when it
names the current step and records the current study digest. A later study
amendment changes that digest and makes an older repair inapplicable. This
gives the recovery an exact causal join without inventing a timestamp order
between two receipt histories.

Protasis states the runbook-amendment content rule and treats a real amendment
heading as the end of the last step for mechanical checking. Fiat states the
receipt, packet, refusal, and recovery rule and adds a separate
`fiat-runbook-amendment` Promise. `verify` recomputes both receipted artefacts.

Because this changes both skills' behaviour, the same implementation step
bumps Fiat's generation from 5.20.1 to 5.21.1 and Protasis's from 4.6.0 to
4.7.0 on the recorded base. Each row preserves its prior frontier revision,
digest, status, current-frontier text, and next job. The run does not pass
`--frontier`; VERSIONING.md generation arithmetic is verified by the ordinary
test suite and the focused evolution-contract command.

This is the cheapest construction that preserves the existing evidence model
and makes the new criterion usable. Its trade is a composite step source: a
consumer must read the original block and its ordered applicable amendments.
The packet makes that composition explicit and digest-bound, but the controller
still cannot prove that free-form replacement prose is a sound design choice.

### Option D: keep amendments in a second overlay file

This avoids changing the runbook bytes, but adds another artefact every packet
must discover and order. The overlay can drift from the runbook receipt and
does not follow the append-in-place choice already made for living specs.

## 5. Risk register seed

```risk-register
subject-confusion | shared study and runbook amendment helpers | every diagnostic pending marker receipt and ledger event names one exact subject and existing study recovery remains green
prefix-forgery | the boundary between receipted runbook bytes and the appended block | the exact prefix hashes to the current runbook receipt before any mutation
amendment-selection | the final dated block selected from Markdown | fenced decoys wrong fence lengths duplicate final blocks and trailing sections refuse
field-ambiguity | the four amendment fields | every field occurs once in order with bounded non-empty content and changed fields are restated in full
step-verdict-coverage | touched steps and Still holding text | only unbuilt steps are touched and every current or pending step has one exact entry-and-exit verdict
duplicate-step-source | original step headings beside amendment prose | no replacement Step heading is accepted and packet selection retains one numbered titled baseline block
effective-step-source | Mason and Warden source packets | each affected packet carries the exact baseline block and all applicable amendment blocks in receipt order with matching digests
repair-precedence | a runbook repair clearing a broken study verdict | the repair names the current study digest and current step and a later study digest makes it inapplicable
partial-write | runbook artefact ledger and state during amendment | a killed command leaves a labelled pending transaction that finishes or rolls back to matching durable evidence
pending-collision | study and runbook write-ahead markers | one marker blocks every other command and multiple markers refuse without deleting either
checker-binding | exact amended bytes passed to Protasis | a fixed argv-only checker receives captured bytes with bounded output and non-zero exit refuses mutation
post-amend-drift | runbook bytes after receipt | next status packets and verify recompute the current runbook digest and refuse later unreceipted edits
legacy-recovery | runs and pending study transactions created before this change | unchanged receipts read normally and the old study marker can still be recovered exactly once
evidence-overclaim | accepted structure digests and operator verdicts | the receipt claims checked continuity shape and source carriage not truth command success or plan correctness
generation-collision | in-scope skill labels when main advances before integration | each active ledger is reread and the next unused generation is chosen only while every held frontier field and compatibility premise still match
elenchus-identifier-swap | the runbook Tests contract handed to Warden | report format is exactly unittest-json-v1 expected report schema is exactly elenchus.unittest.v1 and a role-swapped specimen refuses before implementation
audit-record-scope | this runbook's derived Files boundaries against mandatory Warden output | operator cold review checks the current-run specimen and refuses this runbook before done runbook when audit/AUDIT.md is omitted or forbidden; no controller or Protasis product guard is added
```

## 6. Glossary seeds

- Receipted runbook: the canonical path and SHA-256 accepted by `done runbook`
  or the latest successful runbook amendment.
- Runbook amendment: one dated four-field block appended after the currently
  receipted runbook bytes.
- Baseline step block: the one original `## Step N: title` block whose number
  and title match controller state.
- Applicable amendment: a receipted runbook amendment whose touched-step list
  names the packet's step.
- Effective step source: the baseline block and its applicable amendments in
  receipt order, each carried as exact source bytes rather than rewritten into
  a synthetic step.
- Repair binding: the current study digest recorded by a runbook amendment that
  is allowed to clear a study-amendment block.
- Pending marker: the fsynced write-ahead record that identifies an interrupted
  amendment before canonical bytes are replaced.
- Generation row: one VERSIONING.md history entry that changes the second
  counter for meaningful non-frontier behaviour while retaining the active
  frontier revision and digest byte for byte.
- Elenchus CLI report format: `unittest-json-v1`, the format identifier the
  source-bound runner contract supplies to the Elenchus command.
- Elenchus report schema: `elenchus.unittest.v1`, the schema identifier expected
  inside the produced JSON report; it is not a CLI format value.
- Audit-record scope: the explicit permission in each step of this run's
  runbook `Files` field for Warden to append that round to `audit/AUDIT.md`,
  separate from the implementation files Mason may change and checked by the
  operator before receipt.

## 7. Sources

- [Issue #554](https://github.com/wildcat-finance/skills/issues/554), including
  both maintainer comments and the #429 handoff.
- [Issue #429](https://github.com/wildcat-finance/skills/issues/429), preserved
  step-2 tip `4b78dfa`, and current base
  `84abae32d6d65b3a3ce27648ca144852a9e22e98`.
- [PR #579](https://github.com/wildcat-finance/skills/pull/579) and
  [PR #562](https://github.com/wildcat-finance/skills/pull/562), the last two
  merged target changes.
- [PR #474](https://github.com/wildcat-finance/skills/pull/474) and its stacked
  implementation [PR #473](https://github.com/wildcat-finance/skills/pull/473).
- `audit/AUDIT.md`, “Fiat receipted study amendments” steps 1 and 2 and
  “Protasis amendment contract” steps 1 and 2.
- `docs/fiat-receipted-study-amendments-study.md` and
  `docs/fiat-receipted-study-amendments-runbook.md`.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`: pending-amendment state,
  `done_runbook`, `receipted_source`, amendment helpers,
  `source_runbook_step`, `delegation_packet`, `verify_run`, and CLI parsing.
- `plugins/hexaemeron/tests/test_hexctl.py`,
  `plugins/hexaemeron/tests/test_fiat_skill.py`, and
  `plugins/hexaemeron/tests/test_protasis_checker.py`.
- `plugins/hexaemeron/skills/fiat/SKILL.md`,
  `plugins/hexaemeron/skills/protasis/SKILL.md`, `PROMISE_MACHINE.md`, and
  `plugins/hexaemeron/AGENTS.md`.
- `plugins/hexaemeron/skills/VERSIONING.md` and the Fiat and Protasis
  `EVOLUTION.md` ledgers at the recorded base.
- The halted predecessor study at
  `/Users/c0rtexzer0/Documents/ChatGPT/Wildcat Skills-issue554/tmp/fiat/fiat-554-amend-a-runbook-the-way-a-study-can-already/.hexaemeron/study.md`
  and its verified seven-entry ledger and pre-implementation halt record.
- The second halted run's checked study at
  `/Users/c0rtexzer0/Documents/ChatGPT/Wildcat Skills-issue554/tmp/fiat/fiat-554-receipted-runbook-amendments/.hexaemeron/study.md`,
  its signed docs-only Step 1 test record, Warden file-scope refusal, and
  verified eight-entry ledger. No audit append, audit receipt, push, or pull
  request followed that commit.

## 8. Signals, and the questions behind them

This remains an interactive controller, not an unattended service. No metric,
trace, background log, or alert is added. Four operator questions are answered
by bounded command output, state, ledger, `status --json`, and the delegated
packet:

1. “Which runbook belief changed?” The receipt names the prior, new, and
   amendment digests, date, and touched steps.
2. “What exact criterion controls this step now?” The Mason and Warden briefs
   carry the baseline block and every applicable amendment in receipt order.
3. “Did this repair the recorded block?” State names the bound study digest
   and `next` either emits the amended packet or returns the exact broken
   verdict.
4. “Was the transaction interrupted?” The pending marker names the subject and
   recovery command until artefact, ledger, and state agree.

The amendment transition and packet construction emit these signals.
[Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) remains the signal
authority; this study cites its contract rather than copying it.

## 9. Boundaries, per capability

The candidate path and bytes are untrusted filesystem input. Their value is one
proposed append-only correction. Scoped regular-file reads, the source byte
cap, exact prefix hashing, UTF-8 decoding, fence-aware final-block selection,
and a complete Protasis runbook check close that boundary.

The amendment prose is untrusted structured input. Its value is a replacement
field and operator verdicts. Fixed field order, complete step coverage,
completed-step refusal, full replacement-field wording, and exact source
carriage close the usable boundary without treating the operator's claim as
truth.

The Protasis checker is an internal subprocess boundary. Its value is the
mechanical runbook-shape verdict. It runs by fixed sibling path through
`sys.executable`, an argv list with no shell, bounded time and output, and a
private captured file containing the exact candidate bytes.

The runbook, pending marker, ledger, and state are a durable-write boundary.
Validation finishes before mutation. The controller lock excludes another
writer. A subject-labelled fsynced marker, atomic artefact replacement,
non-duplicating ledger completion, state commit, cross-file verification, and
marker removal give each interruption a finish-or-rollback path.

The source packet is an authority boundary. It may carry only the receipted
baseline step and digest-matched amendments that name that step. Unrelated
amendments, duplicate step headings, stale study bindings, and unreceipted
runbook bytes refuse rather than being passed to Mason or Warden.

For this run, the derived runbook's `Files` field is a source-bound authority
boundary. It separates the implementation surface from the mandatory
append-only audit record without making them contradictory. The operator cold
review checks that boundary and refuses the runbook before `done runbook` when
a step omits `audit/AUDIT.md` or says no other file may change. This boundary
does not add a runtime refusal to `hexctl` or a new Protasis content check.

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) remains the boundary and
control authority; this study does not restate its general rules.

## 10. The budget, or its absence

No speed improvement is claimed, so there is no Metron before-and-after
performance budget. The operation retains the existing 2 MiB source class,
bounded checker output, and controller subprocess timeout as safety ceilings.
Parsing and digest work stay linear in the bounded runbook and amendment
history.

The repeatable functional check is:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_hexctl
```

If implementation adds caching, parallel work, or a latency claim, amend this
study before making that change. [Metron](../plugins/hexaemeron/skills/metron/SKILL.md)
remains the measurement authority.

## 11. The fail-closed posture

The red parent has no `amend runbook` parser subject. Appending a valid-looking
block changes the receipted digest, and the next Mason or Warden packet refuses
before source selection. The first guards preserve that reproduction before
implementation.

The fixed positive guard receipts a runbook amendment whose complete new exit
command appears in both packets. Negative guards cover prefix drift, a fenced
or duplicate heading, missing or reordered fields, a partial replacement
criterion, unknown or completed touched steps, missing and duplicate verdicts,
step-heading duplication, checker failure, unsafe path, oversize, wrong phase,
later drift, stale study binding, two pending markers, and each interruption
window. Removing the relevant check must make its named guard red on the
unfixed mechanism rather than error inside the harness.

Those product guards do not include the `audit-record-scope` row. That risk is
discharged for this run by operator cold review of the source-bound runbook and
the current-run specimen below, not by a new controller or Protasis negative
guard.

The corrected runbook also carries a red source specimen with the two Elenchus
identifiers swapped. Review must refuse that specimen before implementation,
then accept the exact roles `Report format: unittest-json-v1` and `Expected
report schema: elenchus.unittest.v1`. A check that merely finds both tokens does
not establish the mapping and is insufficient.

A second current-run review specimen scopes a docs-only step to its two tracked
documents and explicitly forbids every other path. The operator must refuse
that runbook before `done runbook` because Warden could not append
`audit/AUDIT.md`. The fixed specimen keeps the docs-only implementation
boundary while naming `audit/AUDIT.md` as the sole append-only audit-record
exception. This specimen is not a `hexctl` or Protasis regression test.

A valid amendment carrying a broken current-step verdict is recorded and stays
blocked. A holding repair that lacks the current study digest, omits the current
step, or fails to carry the complete replacement field does not clear an older
block. Recovery is inspection, rerunning the exact subject command to finish or
roll back a pending transaction, another valid runbook amendment, or an
explicit halt. No failure path edits ledger history to manufacture a pass.

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) remains the triage
and guard authority. Audit records must distinguish reproduction, red guard,
fix, and clean rerun.

## 12. Decisions and their homes

The append-only runbook content rule, complete replacement-field requirement,
and effective-step-source definition belong in
`plugins/hexaemeron/skills/protasis/SKILL.md`. The mechanical last-step boundary
belongs in `plugins/hexaemeron/skills/protasis/scripts/protasis.py`, with its
guards in `plugins/hexaemeron/tests/test_protasis_checker.py`.

The receipt, pending recovery, digest join, block-clearing rule, packet shape,
and evidence boundary belong in `plugins/hexaemeron/skills/fiat/SKILL.md` and
the new `fiat-runbook-amendment` Promise. Their implementation belongs in
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`; red-to-green behaviour
belongs in `plugins/hexaemeron/tests/test_hexctl.py` and structural contract
assertions in `plugins/hexaemeron/tests/test_fiat_skill.py`. Promise coverage
changes only for the exact new or changed Promise evidence.

Fiat's matching generation label, retained frontier fields, and issue #554
history entry belong in `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, with
frontmatter `version: "5.21.1"` on the recorded base. Protasis's matching row
belongs in `plugins/hexaemeron/skills/protasis/EVOLUTION.md`, with frontmatter
`version: "4.7.0"`. If integration collision recovery changes either result,
the active ledger, frontmatter, history row, tracked study, and runbook are
updated together before their checks rerun.

The accepted study and runbook are committed as byte-identical tracked copies
in step 1. Each step's `Files` field permits its round findings and dispositions
to append to `audit/AUDIT.md`, including a docs-only step. This source-bound
derivation rule lives only in this run's runbook, this study, and its
pre-receipt operator cold review. It does not broaden Mason's implementation
authority, alter existing Protasis behaviour, add a `hexctl` runtime refusal,
or require a new product test.

The append-only amendment product choice does not need a separate ADR: it
completes the recovery explicitly left open by PR #474 and its stable homes are
the two canonical skill contracts, their tests, this study, and the two
generation rows. The controller state correctly names no frontier delivery,
so no evolution counter moves and no `--frontier` gate is added.

The source-bound Elenchus runner mapping belongs in this run's runbook `Tests`
field: one `{report}` command, report format `unittest-json-v1`, its separate
report file, and expected JSON schema `elenchus.unittest.v1`. The halted
predecessor remains the durable reason for writing both labelled roles rather
than relying on an unlabelled pair of identifiers.

This study's receipt identity belongs only to branch
`fiat/554-runbook-amendment-receipts`, issue #554, controller state
`49518dc37c1f9274e13a76ee518721bebbdc2ecb058713147dd4bcae3c83c5a1`,
and the exact output path named by the controller. Future runbook and amendment
receipts must descend from this run's own accepted artefacts. The predecessor
ledgers remain cited evidence and are never copied into the new ledger.

If implementation needs a new state version, a second overlay artefact, a
step-graph rewrite, a dependency, CI work, or a generic transaction framework,
amend this study before code. [Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md)
remains the record-placement authority.
