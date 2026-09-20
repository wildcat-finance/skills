# Study: a Promise-bound transition gate for every Fiat mutation

Task issue: [skills#871](https://github.com/wildcat-finance/skills/issues/871).
Starting commit: `aededf66434ed4b4e3994bbaab5f1005fe10b453` on `main`.
Design record: `.hexaemeron/design-evidence.json`, SHA-256
`d991b74e649768433f1e50a403702ea9e3c0e276a6d43e97329f5d1dcc32d438`, selected
candidate `dispatcher-grant-wal`.

Assuming, unless corrected:

1. The same-ledger audit loop (`start-audit-loop`, responsibility 3 and
   specimen 8 of the issue) is in scope for this run. The issue words it as a
   later Promise, and
   [ADR-028](https://github.com/wildcat-finance/skills/blob/aededf66434ed4b4e3994bbaab5f1005fe10b453/docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md)
   already accepted it on 2026-08-27. The design record binds it: the
   conformance cell `product-appends-loop-two` blocks `step:5`. Cutting the
   loop after the study receipt needs a new run, not an amendment.
2. Replacement admission stays. It and the same-ledger loop are two separate
   exits from an exhausted loop, each under its own Promise.
3. The exact #622 preimage bytes are not in the repository. A search for state
   digest `b00a2001...f816` and sidecar digest `de2a7a40...0303` found no file.
   Specimens 1 and 2 therefore run against a synthetic preimage of the same
   shape: 43 ledger entries, step 2 halted after round 8, 30 findings open. If
   the archived checkpoint is supplied, Step 3 adds a digest-checked replay.
4. "Generic `resume`" in specimen 2 means a `resume` that names no exit. At an
   exhausted-loop halt a bare `resume --note ...` refuses. `resume --to
   audit-verdict` is granted because it exposes only the directive the halt
   covered. Everywhere else a bare `resume` keeps working, which specimen 7
   requires. Reason: on `main` a halted run must `resume` before `done audit
   --no-further-leads`, so an unconditional refusal would remove an exit the
   issue says must stay available.
5. Main's stricter configuration rule stands. The issue would allow
   `audit.max_rounds` to be set before the first audit receipt; ADR-047 froze
   it after `init`, and this run does not loosen that.
6. Python is the interpreter in `.python-version`, `3.14.6`, with the standard
   library only.
7. The Shoggoth Interceptor's `verify-gate.py` and `install-guardrails.sh` are
   not in this repository. Responsibility 5 is built from the issue's
   description of them.
8. This run was initialised without `--frontier`. Fiat's held job stays
   [skills#1212](https://github.com/wildcat-finance/skills/issues/1212) and is
   not edited.

## 1. Problem statement

In run #622 an agent raised `audit.max_rounds` from 8 to 16 at an exhausted
loop, resumed, and published the recipe in PR #681. `hexctl verify` had passed.
No declared Promise authorised any of it, and the user caught it by reading.

The build is for a Fiat operator, and for an agent driving `hexctl`, who must
not be able to move a run by a command the declared Promises do not authorise.
Every mutation must carry this join, checked before either file changes:

```text
verified preimage state and ledger -> stable Promise id -> exact authorised
transition -> exact current next or named recovery directive -> normalised
command and evidence -> one atomic state and ledger write
```

The delivery has seven modules in one study, because the issue files them as
one governed packet and each depends on the one before it.

| Module id | Responsibility | Depends on |
| --- | --- | --- |
| gate | Pure closed decision engine, `transition_gate.py` | none |
| wiring | One dispatcher, grant-required writers, labelled write-ahead commit | gate |
| loop | `start-audit-loop` and the `fiat-audit-loop-continuation` Promise | wiring |
| handover | Controller-generated checkpoint handover, `handover.py` | loop |
| integrity | `verify_transition_gate.py`, installer wrapper, handler discovery | wiring |
| publication | Wrapper that checks controller commands in prose before `gh` runs | gate, handover |
| demonstration | The ten hostile specimens run end to end | all |

Build order: gate, wiring, loop, handover, integrity, publication,
demonstration.

A working prototype means all ten specimens from the issue hold against the
tree's own controller on disposable runs. Each has a command:

| Specimen | Check |
| --- | --- |
| 1, 2, 3, 6, 7 | `python3 -m unittest plugins.hexaemeron.tests.test_transition_gate_wiring` |
| 3 (pure rules) | `python3 -m unittest plugins.hexaemeron.tests.test_transition_gate` |
| 8 | `python3 -m unittest plugins.hexaemeron.tests.test_audit_loop_continuation` |
| 4, 9 | `python3 -m unittest plugins.hexaemeron.tests.test_handover` |
| 5 | `python3 -m unittest plugins.hexaemeron.tests.test_verify_transition_gate` |
| 10 | `python3 -m unittest plugins.hexaemeron.tests.test_transition_gate_discovery` |
| publication | `python3 -m unittest plugins.hexaemeron.tests.test_publication_gate` |

The proving demo path is the last step: one script initialises a disposable
run with the tree's `hexctl.py`, drives it to an exhausted loop, runs every
hostile command, compares state and ledger bytes before and after each
refusal, starts loop 2, generates a handover, restores it elsewhere and reruns
the three read-only commands. It reports bounded positive and negative
observations. It does not claim the criteria are sufficient.

Self-hosting limit. The gate ships inside the artefact it gates. This run is
driven by the installed Hexaemeron 1.6.64 controller, not by the tree it
edits, so nothing built here gates this run. Hash pins checked by a process
under the same OS account are tamper evidence and deterministic refusal. They
are not privilege isolation, and no document from this run may say otherwise.

## 2. Prior art

### What `main` already does

Read at the starting commit in
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` (31,196 lines):

- One dispatcher exists. `main()` takes the run lock for all 19 names in
  `MUTATING` and runs `gate_recovery_preflight` for 14 of them. It checks no
  Promise and no directive.
- `config set` accepts only `audit.log_path`, `git` and paths below `git`
  (`config_path_is_mutable`, ADR-047). The refusal precedes any write.
  `test_audit_log_path.py` guards the whole-section form. Specimen 1's
  command already refuses; nothing yet proves the bytes unchanged against an
  exhausted preimage or reports a Promise id.
- `cmd_resume` clears any halt and records a free-text note. `cmd_halt` sets
  one. Neither consults `_next_directive`.
- `commit()` appends the ledger line, then replaces `state.json`, with no
  `fsync` and no label. The design resolver drove this real function and
  stopped it between the two writes: the ledger held entry 44, the state was
  the preimage, and nothing on disk said so.
- Five state or ledger writes bypass `commit()`: lines 19325, 19427, 19436,
  20515 and 20540. Three transaction writers have their own pending records:
  `write_amendment_pending`, `write_version_resolution_pending` and
  `_append_no_known_ledger_entry`.
- No `transition_gate.py`, `handover.py`, `verify_transition_gate.py`,
  `start-audit-loop` or publication wrapper exists.

### Satisfied differently: the exhausted-loop exit

ADR-028 decided that continuation is a new bounded loop on the same ledger and
that a controller without that transition leaves the run halted. Main did not
build it. Main built `carryover.py` and `replacement.py`: cumulative carryover
custody at the exhausted `audit-verdict` boundary, then replacement admission
into a fresh run at the current base. Promises
`fiat-cumulative-carryover-custody` and `fiat-replacement-admission` declare
both. That path changes ledgers and needs a native proof repository. It is a
valid exit and stays, but it is not specimen 8, which requires loop 2 round 1
on the same ledger with loop 1 byte-identical.

One defect follows from the gap. `cmd_checkpoint_archive` sets the boundary's
`loop` field to `len(rounds)` (line 29100), so an exhausted loop 1 archives as
`loop-8`. The name format in `references/checkpoint-archive.md` reads it as a
loop ordinal. Step 4 must make it the ordinal for new archives and keep old
archives readable.

### Checkpoints and pins

`checkpoint export`, `restore`, `inspect`, `identity` and `archive` exist and
accept two boundaries, `done:push` and the exhausted loop. A handover can be
built on them. Protasis's `gate_commands.py` pins eight CLI modules in
`MODULE_BINDINGS`; `hexctl.py` is not one of them, and nothing pins the
controller's own enforcement path.

### The earlier #871 run

Branches `origin/fiat/871-implement-checkpoint-bound-audit-loop-contin*` and
open PRs #1168 and #1169 (2026-09-03) sit 1,303 commits behind `main`,
stopped at Step 1 audit round 1. Read through `git show` only; this run does
not build on, edit or close them. Their study chose `append-only-loop-kernel`
over `nested-loop-state-v2` and `continuation-sidecar`.

Carried forward: the append-only `audit.continuations` layout with legacy
rounds as loop 1, staged publication with a durable label, and the 20-id risk
list as a seed. Refused by name: its ADR number, because `ADR-069` on `main` is
now "reinstate the distributed checkpoint layer"; its loop-first step order,
because the loop transition must itself pass the gate; and its candidate set,
which predates replacement admission and never compared against it. Its audit
round recorded that the #622 checkpoint bytes were not an established
fixture. That is still true.

### Last two merged pull requests on the controller

- [#1785](https://github.com/wildcat-finance/skills/pull/1785), merged
  2026-09-20: names the recorded controller when a registered module's pin was
  taken at another commit. Not a Fiat run; no carryover block.
- [#1784](https://github.com/wildcat-finance/skills/pull/1784), merged
  2026-09-20, run 1676: 27 carryover rows. None names #871. Two touch this
  work and stay open under their own issues: `controller-fences` at
  [#864](https://github.com/wildcat-finance/skills/issues/864), the external
  acceptance fence of ADR-072, a non-goal here; and `design-amendment` at
  [#1524](https://github.com/wildcat-finance/skills/issues/1524), the reason
  this design record cannot change after receipt.

[#1775](https://github.com/wildcat-finance/skills/pull/1775) was read as well.
Its `controller-registry-refusal` row is #1715, which #1785 closed.

### Audit records

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exited 0 from the target root, so synopses were the reading view. Nothing under
`audit/` was opened whole.

| Source | View read | How |
| --- | --- | --- |
| `plugins/hexaemeron/audit/AUDIT.md` | `AUDIT_SYNOPSIS.md` | search `config set`, `max_rounds`; row F-01 extracted |
| `audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.md` | its `.synopsis.md` | same search; row S2-R1-01 extracted |
| `audit/rounds/fiat-622-carryover-3-implementation-continuation.md` | its `.synopsis.md` | headings and the last `Leads not pursued` |
| earlier run's `audit/rounds/fiat-871-implement-checkpoint-bound-audit-loop-contin.md` | the source, by `git show` | field lines only |

F-01 (medium, fixed): `verify` proved the ledger chain but not the state; every
entry now carries a state fingerprint. The gate's preimage check relies on it.
S2-R1-01 (high, fixed): `cmd_config` guarded only the exact leaf, and a
whole-section write passed; ADR-047 and its test closed it. The #622 synopsis
shows Step 2 reaching round 8 on 2026-08-27 and records no round 9. Its rounds
list controller mutation under `Not checked`. The earlier #871 round found no
defect in a documents-only step, with `Elenchus verdict: null` and no leads.
Synopsis fields marked `[missing legacy field: ...]` stay unknown.

Searches over synopses, by pattern: `config set|config-set|max_rounds`;
`resume|halt`; `save_state|append_ledger|partial write|torn|crash|fsync|atomic`.
The second and third returned 17 and 11 files, none from a run on this surface. They were
not opened.

No known-failure inventory is carried. Both named failures are fixed and
guarded on `main`, and no record names an unguarded failure in this scope.

### Outside the repository

The Shoggoth Interceptor's verifier and installer are the model the issue
names; they were not available to read. Write-ahead logging with a staged
postimage and a durable label is the standard construction for the two-file
write.

## 3. Constraints and non-goals

- Starting ref `main` at `aededf66434ed4b4e3994bbaab5f1005fe10b453`. Python
  `3.14.6`. Standard library only. No new dependency.
- Hexaemeron plugin `1.6.64`, Fiat `6.70.1`. Under
  `plugins/hexaemeron/skills/VERSIONING.md` this is a generation change, not a
  frontier advance: one new Fiat `EVOLUTION.md` history row with the frontier
  tuple unchanged, the matching `SKILL.md` version, and the held `Next Fiat
  job` untouched. The runbook should declare it with a `version-relations` row
  and write no concrete Fiat version token.
- `scripts/plugin_release.py` requires every stacked step pull request that
  touches `plugins/hexaemeron` to raise the plugin version itself.
- Per-step pin obligations found by digest search. The runbook names each in
  the step that moves it:
  - `tests/promise_machine_coverage.json` pins the `hexctl.py` SHA-256
    (`5a69457a...a729` now). Any `hexctl.py` or Fiat `EVOLUTION.md` edit starts
    the coverage re-pin cascade.
  - `tests/fixtures/agent-instruction-v1/manifest.json` and the
    `fiat-study-runbook-phase` fixture (`model.json`, `source-spans.json`,
    `compact.wai`) pin the Fiat `SKILL.md` SHA-256 (`f53dc950...427c` now) and
    a governed byte range ending at 29736. `tests/test_demonstrations.py` reads
    the same range. New Promise text belongs after that range.
  - `MODULE_BINDINGS` pins `scripts/run_checks.py` and
    `plugins/hexaemeron/tests/run_tests.py`. Step 6 must reference the verifier
    from CI without editing either, or re-pin in the same step.
  - `.horos/census.json` tracks byte counts and changes with any tracked file.
  - A new Promise needs its `tests/promise_machine_coverage.json` entry and
    promise-case fixtures in the step that declares it.
- Tests: `NO_COLOR=1 python3 plugins/hexaemeron/tests/run_tests.py` and
  `NO_COLOR=1 python3 scripts/run_checks.py --format json`. `unittest
  discover` in that directory raises ImportError and reads as clean. Three
  checkpoint-authority tests are red on this host for lack of `cosign` before
  any change; a step proves its own reds against a snapshot of its entry.
- The decision record ships as an unnumbered draft under
  `docs/decisions/drafts/` and takes its number at integration.

Non-goals: privilege isolation or a broker under another OS identity; the
external acceptance fence of ADR-072; a design-amendment transition (#1524);
any mutation, verdict or approval of the live #622 run or its 30 findings;
changes to replacement admission or carryover custody beyond passing the gate;
editing the earlier #871 branches; moving audit history (#1212).

Boundaries:

- Always: both suites before a commit; the Imprimatur lint on every shipped
  document; byte comparison of state and ledger in every refusal test; a guard
  test that fails without its fix.
- Ask first: changing the state container version; changing a stored archive
  or checkpoint field; touching `.github/workflows`; editing a pinned module in
  `MODULE_BINDINGS`; widening what `config set` accepts.
- Never: weaken or delete a test to pass; let the delivering agent re-pin the
  gate's own integrity pins without the separately reviewed change the issue
  requires; represent a round 9 in any state, log heading, directive, handover
  or file name; claim privilege isolation; claim a command ran when it did not.

## 4. Design options

The record at `.hexaemeron/design-evidence.json` selects; this prose explains.
Selection cells were measured by `.hexaemeron/design/resolve_gate.py` over a
disposable synthetic preimage. Its procedures model the constructions; they
are not the product.

### `dispatcher-grant-wal` (selected)

`main()` stays the single entry. Under the run lock it verifies gate
integrity, loads and verifies the state and ledger preimage, recomputes
`_next_directive`, and asks the pure `transition_gate.evaluate` for a grant
keyed by handler and subcommand. The grant names the Promise id, consequence,
transition, directive, state digest and ledger tail. `commit()` and every
other writer refuse without the live grant. `commit()` stages both postimages
and the grant, publishes a durable label, replaces the ledger and then the
state, and retires the label; recovery completes a labelled transaction or
reports the exact preimage. The five direct writes move behind it, and the
three existing pending-record writers are registered as named recovery
directives, not rewritten. Exhausted loops continue through
`audit.continuations`, append-only, with legacy rounds as loop 1.

Trade: the largest edit to `hexctl.py`, about 25 writer call sites, and the
coverage re-pin in each step that touches it. It buys one place to prove
ordering from source.

### `per-handler-gate`

Each of the 19 handlers calls the gate itself, and `commit()` stays as it is.
Trade: small, local diffs. It fails `crash-window-labelled`: the real
`commit()` left an unlabelled ledger-ahead state. It needs 19 ordering proofs
where the selected design needs one.

### `external-writer-broker`

A broker process under another OS identity owns the writer and the pins.
Trade: the only construction that could support a prevention claim. It fails
`runs-under-one-account-stdlib`, because the run environment has no second
identity and a restored checkpoint would not carry one, and it fails
`added-processes-per-mutation` with 1 against a ceiling of 0. The issue defers
it, and it stays a non-goal.

### `gate-with-replacement-exit`

The selected gate and writer, with no same-ledger loop. Trade: the smallest
delivery, and no second representation of audit history. It fails
`appends-loop-two-same-ledger`, which is specimen 8 and ADR-028.

### Result

| Candidate | Failed selection gates | `gate-call-sites` |
| --- | --- | ---: |
| `dispatcher-grant-wal` | none | 1 |
| `per-handler-gate` | `crash-window-labelled` | 19 |
| `external-writer-broker` | `runs-under-one-account-stdlib`, `added-processes-per-mutation` | 1 |
| `gate-with-replacement-exit` | `appends-loop-two-same-ledger` | 1 |

One candidate survives, so the rule is `unique-frontier`. All four passed
`refuses-622-widening`, `legacy-loop-one-bytes-identical` and
`max-grant-bytes` (493 bytes or fewer against 65,536). The
`runs-under-one-account-stdlib` cell is a declared property of each
construction checked against the process's effective user. It is the weakest
measurement in the matrix.

Pending conformance, for the selected candidate. Each resolver is
`python3 .hexaemeron/design/conform_gate.py --candidate dispatcher-grant-wal
--criterion <id> --out .hexaemeron/design/reports/dispatcher-grant-wal-<id>.json`.
It writes a report only when its module is green and never overwrites one.

| Criterion | Module | Stop point |
| --- | --- | --- |
| `product-refuses-622-specimens` | `test_transition_gate_wiring` | `step:4` |
| `product-appends-loop-two` | `test_audit_loop_continuation` | `step:5` |
| `product-every-mutator-mapped` | `test_transition_gate_discovery` | `step:7` |

These fix the step order: wiring is complete by the end of Step 3, the loop by
the end of Step 4, and handler discovery by the end of Step 6. No cell blocks
`integration`.

Proposed steps, for the runbook to derive: (1) scaffold and record the study,
runbook, design record and draft decision; (2) the pure gate and its rule
table; (3) dispatcher wiring, grant-required writers, write-ahead commit and
typed `resume`; (4) `start-audit-loop`, its Promise and loop-aware `next`,
`audit-round`, `verify`, `status` and archive naming; (5) `handover.py`; (6)
`verify_transition_gate.py`, the installer wrapper and handler discovery; (7)
the publication wrapper; (8) demonstration, the Fiat ledger row and the final
decision record. Steps 3 and 4 are the large ones, an estimated 600 to 900
changed product lines each before tests; the rest are 300 to 600.

## 5. Risk register seed

```risk-register
grant-preimage-binding | the grant passed from dispatcher to writer | a grant is refused when the state digest, ledger tail or directive it names differs from the bytes on disk at write time
writer-discovery-drift | every call that writes state.json or ledger.jsonl | a source check finds each writer, proves it requires the grant, and fails on a new one
unmapped-handler | the MUTATING set and the gate's rule table | a handler without a rule, a Promise id and a hostile specimen fails the discovery test
gate-purity | transition_gate.py | it imports only the standard library, opens no file, spawns nothing and interprets no prose
transaction-crash-window | the staged write-ahead commit | a stop at each boundary leaves the exact preimage or one labelled transaction that recovery completes
pending-writer-coexistence | the amendment, version-resolution and no-known pending records | each remains recoverable under the gate and none can run while another label is live
transaction-concurrency | the run lock around verify, gate and write | no second process can change the preimage between the grant and the write
generic-resume-overreach | resume at an exhausted-loop halt | a bare resume refuses with Promise id, consequence 2, blocked transition and recovery, and bytes are unchanged
config-container-bypass | config set on a leaf, a section or a nested path | every path outside the ADR-047 allowlist refuses against the exhausted preimage
round-nine-alias | state, log headings, directives, handovers and file names | no representation of a ninth round exists in either loop
legacy-loop-preservation | steps[*].audit.rounds of a legacy state | the canonical bytes of loop 1 are identical before and after loop 2 opens and closes
loop-number-continuity | the append-only continuations array | the next loop is the predecessor plus one and every prior loop digest is fixed
finding-carryover-omission | the open-finding identities bound into a new loop | a missing or altered finding identity refuses the transition
authority-as-evidence | the recorded user authority for a new loop | it is recorded as an operator declaration and never described as authenticated identity
archive-loop-field | the checkpoint archive boundary loop value and directory name | new archives carry the loop ordinal and archives written with a round count still inspect and restore
replacement-exit-regression | carryover custody and replacement admission | their fixtures still reach only their own directives under the gate
handover-prose-divergence | the human paste block | it is rendered from the accepted JSON envelope and has no independent field
handover-hostile-input | a checkpoint or supplied handover read by handover.py | no symlink is followed, sizes are capped, and an unsupported transition or round 9 refuses
gate-integrity-bootstrap | verify_transition_gate.py and its pins | a modified, symlinked, oversized, non-executable, unpinned, reordered or unreferenced component refuses before any writer runs
same-account-tamper | every document and refusal message about the pins | the claim is tamper evidence and deterministic refusal, never privilege isolation
self-repin | the delivering agent and the gate's own pins | no step re-pins the integrity pins outside the separately reviewed change the issue requires
publication-command-smuggling | controller commands inside prose given to the wrapper | every command is read-only or granted against a named fixture state, with no shell and no command inferred from prose
installer-fail-open | the installer wrapper | set -eu, verification first, and failure aborts
self-hosting-confusion | tests and the demonstration | they drive the tree's hexctl.py on disposable runs and never this run's state
pin-cascade-drift | the coverage digest, agent-instruction fixtures, census and plugin version | each step that moves a pinned byte re-pins it in the same step and both suites stay green
```

The resolver's reference gate is a model. Warden should not treat a passing
selection cell as evidence about product code.

## 6. Glossary seeds

- **Grant:** the closed object the gate returns for one command against one
  preimage; it names the Promise, the transition and the digests it holds for.
- **Preimage:** the verified `state.json` and `ledger.jsonl` bytes a mutation
  starts from.
- **Transition rule:** one row of the gate's closed table: handler, Promise
  id, consequence, admitted directives and required evidence.
- **Labelled transaction:** staged postimages plus a durable marker that
  recovery can complete.
- **Loop:** a bounded series of at most eight audit rounds. Legacy flat rounds
  are loop 1.
- **Continuation:** one append-only loop object bound to its predecessor's
  digest, checkpoint, open findings and recorded authority.
- **Exhausted loop:** a loop at its ceiling with findings open; `next` returns
  `audit-verdict`.
- **Handover envelope:** the closed JSON a verified checkpoint yields, from
  which the paste block is rendered.
- **Tamper evidence:** a pin mismatch that refuses, under the same OS account.

## 7. Sources

Opened whole: the issue body; Protasis `SKILL.md` at plugin 1.6.64;
`ADR-047`; `docs/fiat-carried-step-commits/design/conform_carry.py`.

Read in part, by line range or search, at the starting commit:
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` (the `MUTATING` set at line
2813, `save_state`, `append_ledger` and `commit` at 3004 to 3042, `cmd_config`
at 7895, the audit directive at 29515 to 29550, `cmd_halt` and `cmd_resume` at
29971, `main` at 31173); Fiat `SKILL.md` (phase notes, carryover, replacement,
hard rules, six Promise declarations); `ADR-028` lines matching `loop`;
`ADR-072` and `ADR-088` opening sections;
`plugins/hexaemeron/skills/VERSIONING.md` lines 1 to 44; Fiat `EVOLUTION.md`
frontier block; `design_evidence.py` selection and report rules.

By `git show` from
`origin/fiat/871-implement-checkpoint-bound-audit-loop-contin-step-1-record-the-architecture-and-scaf`:
`docs/fiat-transition-gate-study.md` headings and candidate lines, and the
runbook's step headings; from its `--audit` branch, the round's field lines.

By `gh`: issue 871; pull requests 1168, 1169, 1775, 1784 and 1785.

By digest: `hexctl.py` `5a69457aef6871eb639fbac6334240bf84ce19fd71dd500d5004c4d73748a729`
and Fiat `SKILL.md`
`f53dc950b2edb40746ec97d624075bf18edd7925c8855111c31bf40d39d4427c`, each
searched across the tree to find its pins.

Not established: the #622 checkpoint bytes; the Interceptor's scripts; the
name of the test that enforces the Horos census; whether `resume --to` suits
the maintainers.

## 8. Signals, and the questions behind them

1. Why did this mutation refuse? Every refusal prints one closed
   `fiat-transition-refusal/v1` object: Promise id, consequence, blocked
   transition, stable code, recovery. Steps 2 and 3 emit it.
2. Is a half-finished write on disk, and which one? `status` and `verify` name
   a live label and its transition. Step 3.
3. Which loop and round is this run in, and what authorised the loop? `next`,
   `status` and the ledger event `audit-loop-start` carry the loop ordinal, the
   predecessor digest and the recorded authority. Step 4.
4. Has the enforcement path changed since it was pinned?
   `verify_transition_gate.py` exits non-zero and names the component. Step 6.

Each granted mutation's ledger entry carries the grant digest, so a refusal
and a write can be correlated afterwards. Ephoros owns what each signal must
carry: see the [Ephoros contract](https://github.com/wildcat-finance/skills/blob/aededf66434ed4b4e3994bbaab5f1005fe10b453/plugins/hexaemeron/skills/ephoros/SKILL.md).

## 9. Boundaries, per capability

- The command line into the gate: an agent can submit any argv. Control: a
  closed table; unknown commands, fields, Promise ids and directive shapes
  refuse.
- State and ledger files under one account: an agent can edit them. Control:
  the verified preimage and the fingerprint chain refuse the next mutation.
  This detects; it does not prevent.
- Checkpoints and supplied handovers read by `handover.py`: hostile input.
  Control: no-follow opens, size caps, closed JSON, digest checks before use.
- Prose given to the publication wrapper, and the `gh` argv it guards. Control:
  commands are extracted by a closed grammar, checked against a named fixture
  state, and `gh` is run without a shell only after every command passes.
- The installer wrapper, a shell script: `set -eu`, verification first, abort
  on failure.
- The integrity pins: the delivering agent can rewrite them. Control: a
  mismatch refuses, and the process rule that a re-pin is a separately
  reviewed change. The rule is not mechanically enforced.

Phylax owns the boundary list and controls: see the
[Phylax contract](https://github.com/wildcat-finance/skills/blob/aededf66434ed4b4e3994bbaab5f1005fe10b453/plugins/hexaemeron/skills/phylax/SKILL.md).
Every new Python file passes
`python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py <file>`.

## 10. The budget, or its absence

Two budgets, both already gates in the design record. The gate adds no process
to a mutation: `added-processes-per-mutation` at most 0. A grant is at most
65,536 bytes: `max-grant-bytes`, measured at 493. Command: `python3
.hexaemeron/design/resolve_gate.py --candidate dispatcher-grant-wal
--criterion added-processes-per-mutation --out <new report>`.

No wall-clock budget is claimed. The gate is a dictionary lookup and two
SHA-256 digests over files that `load_state` already reads. The write-ahead
commit adds `fsync` calls whose cost depends on the disk, so a number here
would be a guess. If a step finds `hexctl` mutations slower in use, Metron's
baseline-first rule applies: see the
[Metron contract](https://github.com/wildcat-finance/skills/blob/aededf66434ed4b4e3994bbaab5f1005fe10b453/plugins/hexaemeron/skills/metron/SKILL.md).

## 11. The fail-closed posture

A missing, stale, malformed, over-broad or unsupported link refuses before
either file changes, and the refusal test compares bytes. A gate integrity
failure stops every writer and the publication wrapper. A live label blocks
every mutation except its own recovery. An exhausted loop stays halted unless
`start-audit-loop`, `done audit --no-further-leads`, `halt`, `reset` or
replacement admission is granted. `verify`, `status`, `next`, checkpoint
inspection and exact rollback stay available after any refusal.

A red suite stops the step. Each audit fix lands with a guard test that fails
without it. The runbook's Elenchus line for every step is `python3
plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, format
`unittest-json-v1`. On this host the runner has returned an inconclusive
verdict under the worker boundary; when it does, the counterfactual is done by
hand and recorded as such. Elenchus owns the triage order and the guard rule:
see the [Elenchus contract](https://github.com/wildcat-finance/skills/blob/aededf66434ed4b4e3994bbaab5f1005fe10b453/plugins/hexaemeron/skills/elenchus/SKILL.md).

## 12. Decisions and their homes

Expensive to reverse:

1. One dispatcher gate with grant-required writers and a labelled write-ahead
   commit, with the three rejected constructions and the same-account limit.
2. Audit history as loops, append-only, legacy rounds as loop 1, no round 9,
   beside replacement admission and not instead of it.
3. The typed `resume --to` at an exhausted-loop halt.
4. The handover envelope and grant schemas, `fiat-transition-grant/v1` and its
   siblings, which checkpoints and published prose will bind to.

Decisions 1 to 3 go in one record,
`docs/decisions/drafts/gate-fiat-mutations-and-continue-audit-loops.md`,
written in Step 1, completed in Step 8 and numbered at integration. It states
how it relates to ADR-028 and ADR-047 and edits neither. Decision 4 goes in
`plugins/hexaemeron/skills/fiat/references/transition-gate.md`, the reference
the refusal messages point at. The study, runbook, design record, resolvers and
reports are committed under `docs/fiat-transition-gate/` in Step 1. The new
Promise is declared in Fiat's `SKILL.md`, after the governed range. Hypomnema
owns which decisions earn a record and where each lives: see the
[Hypomnema contract](https://github.com/wildcat-finance/skills/blob/aededf66434ed4b4e3994bbaab5f1005fe10b453/plugins/hexaemeron/skills/hypomnema/SKILL.md).

### Amendment -- 2026-09-20

**What changed.** The study gains its design bridge to the draft decision record that Step 1 authors.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | dispatcher-grant-wal
record | docs/decisions/drafts/gate-fiat-mutations-and-continue-audit-loops.md
```

**Why.** Hypomnema study mode reports H008 when a study names no record for its selected design, and the record is the home section 12 names for decisions 1 to 3.
**Steps touched.** Step 1's exit, which already requires this bridge.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds. Step 8: entry holds; exit holds.
