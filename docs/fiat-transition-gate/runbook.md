# Runbook: a Promise-bound transition gate for every Fiat mutation

Derived from the receipted study `.hexaemeron/study.md`, SHA-256
`a282ca8aef5aacef2c70c6cc50835c461095f2f80a833b694cb47430c6b7e7b6` at its
receipt, for https://github.com/wildcat-finance/skills/issues/871. The run
branch is `fiat/871-promise-bound-transition-gate-for-every-fiat`, cut from
`main` at `aededf66434ed4b4e3994bbaab5f1005fe10b453`. Step 1 branches from the
run branch and every later step from the audited head of the step below it.

The selected design is `dispatcher-grant-wal` (study section 4). `main()` in
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` stays the single entry.
Under the run lock it checks gate integrity, verifies the state and ledger
preimage, recomputes `_next_directive`, and asks the pure
`transition_gate.evaluate` for one grant. Every writer refuses without the
live grant. `commit()` stages both postimages and the grant, publishes a
durable label, replaces the ledger, replaces the state, then retires the
label. An exhausted audit loop continues through an append-only
`audit.continuations` array, with legacy flat rounds as loop 1. The scope
confirmation for the same-ledger loop was given by the maintainer on
2026-09-20 (study assumption 1).

Self-hosting limit, carried from study section 1: the installed Hexaemeron
1.6.64 controller drives this run, so nothing built here gates this run. Every
test and the demonstration drive the tree's `hexctl.py` on disposable runs and
never this run's `.hexaemeron/`. Pins checked under the same OS account are
tamper evidence and deterministic refusal, not privilege isolation.

Conventions for every step:

- Exits run from the run worktree root on the committed step head, with
  `NO_COLOR=1` in the environment because this shell sets `FORCE_COLOR=3`.
  The runner is never started while a worker is still editing the tree. A bare
  `unittest discover` inside `plugins/hexaemeron/tests` raises ImportError and
  reads as clean, so it is not an exit.
- Three checkpoint-authority tests are red on this host for lack of `cosign`
  before any change. A step that sees them proves them on a detached snapshot
  of its own entry commit and compares failure sets; any other red stops the
  step.
- Steps 2 to 8 touch `plugins/hexaemeron/`, so each raises the package version
  on its six surfaces together: `plugins/hexaemeron/.claude-plugin/plugin.json`,
  `plugins/hexaemeron/.codex-plugin/plugin.json`, the hexaemeron entry in
  `.claude-plugin/marketplace.json` and in `.agents/plugins/marketplace.json`,
  the pin in `tests/test_version_propagation.py` and the pin in
  `plugins/hexaemeron/tests/test_phylax_model_proxy.py`. The number exceeds the
  step's own pull request base and every version any local or remote ref
  claims at the moment of the bump, re-scanned with `git ls-remote` and
  `git show <ref>:plugins/hexaemeron/.claude-plugin/plugin.json`. At drafting
  time 579 refs were scanned and the highest claim was `1.6.64`, so Step 2
  claims `1.6.65` and each later step the next number, through `1.6.71` at
  Step 8, unless the re-scan says otherwise.
  `python3 scripts/plugin_release.py --base <pull request base> --head HEAD`
  exits 0 before each push. Step 1 changes no plugin byte and claims no
  version.
- Every edit to `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` or to
  Fiat's `EVOLUTION.md` re-pins, in the same step: the controller SHA-256 in
  `tests/promise_machine_coverage.json` (`5a69457a...a729` at the starting
  commit), then `docs/promise-machine/obligation-gates/evaluation-run.json`
  through `tests/promise_evaluation_driver.py` with the recorded model and date
  kept, then `docs/promise-machine/obligation-gates/integration-projection.json`
  and `integration-projection.md`. No model, tokenizer or measurement process
  runs. Open this cascade before investigating any digest red.
- Fiat's `SKILL.md` is edited in Steps 4 and 8 only. Its whole-file SHA-256
  (`f53dc950...427c` at the starting commit) is pinned by
  `tests/fixtures/agent-instruction-v1/manifest.json` and the
  `fiat-study-runbook-phase` fixture (`model.json`, `source-spans.json`,
  `compact.wai`), and `tests/test_demonstrations.py` reads a governed byte
  range ending at 29736. New text goes after that range, and the fixture
  chain is rebuilt by its own builder in the same step, never by hand.
- `scripts/run_checks.py` and `plugins/hexaemeron/tests/run_tests.py` are
  registered CLI modules pinned by `MODULE_BINDINGS` in
  `plugins/hexaemeron/skills/protasis/scripts/gate_commands.py`. No step edits
  either. New test files are named `test_*.py` so the runner's existing
  discovery pattern finds them.
- Before a Mason starts, search the tree for the SHA-256 of every file the
  step will edit, and add any pin found to the step's work. Brief each Mason
  with the fix classes earlier steps' audit rounds landed.
- Stage every change, run `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`
  and `python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`,
  stage `.horos/boundary.json`, `.horos/candidates.json` and
  `.horos/census.json` together, then commit. Never hand-edit a `.horos`
  artefact.
- The design record `.hexaemeron/design-evidence.json` is immutable. Three
  conformance cells of `dispatcher-grant-wal` are due. Each is resolved by
  running `python3 .hexaemeron/design/conform_gate.py --candidate dispatcher-grant-wal --criterion <criterion> --out .hexaemeron/design/reports/dispatcher-grant-wal-<criterion>.json`
  from the worktree root on the committed step head, before that step's push
  receipt: `product-refuses-622-specimens` in Step 3 (blocks `step:4`),
  `product-appends-loop-two` in Step 4 (blocks `step:5`) and
  `product-every-mutator-mapped` in Step 6 (blocks `step:7`). The resolver
  writes a report only when its module is green and refuses an existing path.
  No existing report is rewritten, and `build_record.py` and `resolve_gate.py`
  are never run again.
- The study is amended once, in Step 1, through `hexctl amend study`, to add
  the `design-bridge` fence Hypomnema study mode requires. The committed study
  copy is taken after that receipt and stays byte-identical to it.
- No known-failure inventory is carried (study section 2): the two failures
  audit history names on this surface are fixed and guarded on `main`.
- Each audit fix lands with a guard test that fails without it. When the
  Elenchus runner returns an inconclusive verdict on this host, the
  counterfactual is done by hand and recorded as such.
- Never: represent a ninth round anywhere; weaken or delete a test to pass;
  change an existing integrity pin value once Step 6 has written it; claim
  privilege isolation; edit the earlier #871 branches; mutate the live #622
  run.

```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
```

The relation is not a reservation. The ledger row, the `SKILL.md` metadata
version, the compatibility-set entry in `hexctl.py` and the pins in
`tests/test_evolution_contract.py` are written in Step 8 and resolved against
the exact integration base at `done resolve-versions`. The held frontier
revision `delegated-task-identity`, its digest
`a54452aef0e415d7d17a548751178de0804d22af4829255b3c5d8bfe289581f1`, the
`Current frontier` line and the `Next Fiat job` line stay unchanged.

```design-lock
schema | protasis-design-evidence/v1
sha256 | d991b74e649768433f1e50a403702ea9e3c0e276a6d43e97329f5d1dcc32d438
candidate | dispatcher-grant-wal
```

## Step 1: Commit the specification and the draft decision

**Goal.** Put the receipted study, this runbook, the design record, its 32
reports and the three design scripts under `docs/fiat-transition-gate/`, author
the draft decision record, and bind the study to it.
**Entry.** The run branch at `aededf66434ed4b4e3994bbaab5f1005fe10b453` with a
clean tree. Module: none; this step scaffolds.
**Exit.** Each command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/871-promise-bound-transition-gate-for-every-fiat --scope root --scope hexaemeron --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-transition-gate/study.md docs/fiat-transition-gate/runbook.md docs/decisions/drafts/gate-fiat-mutations-and-continue-audit-loops.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-transition-gate/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-transition-gate/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/fiat-transition-gate docs/decisions/drafts
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study docs/fiat-transition-gate/study.md --design-evidence docs/fiat-transition-gate/design-evidence.json --repo-root .
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py docs/fiat-transition-gate/design
```

- `docs/decisions/drafts/gate-fiat-mutations-and-continue-audit-loops.md`
  exists with the heading `# Decision: ...`, the sections Status, Context,
  Decision, Alternatives and Consequences in that order, a dated status and no
  ADR number. It carries decisions 1 to 3 of study section 12, the three
  rejected constructions of study section 4 as alternatives, the same-account
  limit, and how it relates to ADR-028 and ADR-047. No inherited decision
  record changes by a byte.
- The receipted study carries one dated amendment whose `design-bridge` fence
  names schema `hypomnema-design-bridge/v1`, decision `dispatcher-grant-wal`
  and that draft's path, receipted through `hexctl amend study` with every
  step holding.
- `docs/fiat-transition-gate/study.md`, `runbook.md` and
  `design-evidence.json` are byte-identical to their `.hexaemeron/` sources;
  `docs/fiat-transition-gate/design/reports/` holds byte-identical copies of
  the 32 reports; and `docs/fiat-transition-gate/design/` holds byte-identical
  copies of `resolve_gate.py`, `conform_gate.py` and `build_record.py`.
- The three `.horos` artefacts equal a fresh scan. No file under
  `plugins/hexaemeron/` changed.

**Files.** `docs/fiat-transition-gate/study.md`,
`docs/fiat-transition-gate/runbook.md`,
`docs/fiat-transition-gate/design-evidence.json`,
`docs/fiat-transition-gate/design/reports/` (32 files),
`docs/fiat-transition-gate/design/resolve_gate.py`,
`docs/fiat-transition-gate/design/conform_gate.py`,
`docs/fiat-transition-gate/design/build_record.py`,
`docs/decisions/drafts/gate-fiat-mutations-and-continue-audit-loops.md`,
`.horos/boundary.json`, `.horos/candidates.json`, `.horos/census.json`.
**Tests.** None written; the root and Hexaemeron suites and the lints above are the gate.
Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-1.json`
**Disciplines.** hypomnema: the copies and the draft record are the homes study
section 12 names, and the design bridge joins them. phylax: the three script
copies enter the phylax lint walk and write only a caller-named output.
ephoros: none, nothing in this step runs. metron: none, no performance claim.
elenchus: none, no failure in hand.

## Step 2: Build the pure transition gate and its closed rule table

**Goal.** Add `transition_gate.py`, a standard-library decision engine that
returns one exact grant or one stable refusal for a command against a
verified preimage, with a rule for each of the 19 mutating handlers, and wire
it to nothing yet.
**Entry.** Step 1's exit state. Module: gate.
**Exit.** The command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/871-promise-bound-transition-gate-for-every-fiat --scope root --scope hexaemeron --format json
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins/hexaemeron/skills/fiat/scripts/transition_gate.py
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/references/transition-gate.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py plugins/hexaemeron/skills/fiat/references
```

- `transition_gate.evaluate` takes the state digest, the ledger tail digest
  and count, the canonical directive, the handler and subcommand, the
  normalised command and its evidence. It returns a closed
  `fiat-transition-grant/v1` object naming Promise id, consequence,
  transition, directive, state digest and ledger tail, or raises a closed
  `fiat-transition-refusal/v1` naming Promise id, consequence, blocked
  transition, stable code and recovery.
- The module imports only the standard library, opens no file, starts no
  process and reads no prose. A source test proves this from its AST.
- The rule table is closed: an unknown command, field, Promise id, directive
  shape, recovery path or consequence level refuses. Every name in `MUTATING`
  has a rule that names an existing declared Promise, except
  `start-audit-loop`, whose rule is added in Step 4.
- The rules encode the ADR-047 configuration allowlist and the typed
  `resume` of study assumption 4: at an exhausted-loop halt a `resume` that
  names no exit refuses, and a `resume` naming the `audit-verdict` exit is
  granted.
- `references/transition-gate.md` states the two schemas and every stable
  refusal code, and carries the same-account limit.
- `hexctl.py` is unchanged in this step.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/transition_gate.py`,
`plugins/hexaemeron/skills/fiat/references/transition-gate.md`,
`plugins/hexaemeron/tests/test_transition_gate.py`, the six package version
surfaces, `.horos/boundary.json`, `.horos/candidates.json`,
`.horos/census.json`.
**Tests.** New module `plugins/hexaemeron/tests/test_transition_gate.py`: one granted and one refused case per rule, the unknown-value refusals of specimen 3 at the pure level, the purity source test, and grant size at most 65,536 bytes. Expected count: at least 45.
Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-2.json`
**Disciplines.** phylax: the gate is the boundary every argv crosses, so its
table is closed and it touches no file or process. ephoros: the refusal object
is the signal for on-call question 1. metron: the grant-size budget of study
section 10 is asserted here. hypomnema: decision 4, the schemas, lands in the
reference. elenchus: none, no failure in hand.

## Step 3: Route every writer through the dispatcher grant and a labelled commit

**Goal.** Make `main()` evaluate the gate under the run lock before any
handler runs, make every state and ledger writer require the live grant,
replace the two-write `commit()` with the labelled write-ahead commit and its
recovery, and add the typed `resume`.
**Entry.** Step 2's exit state. Module: wiring.
**Exit.** The command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/871-promise-bound-transition-gate-for-every-fiat --scope root --scope hexaemeron --format json
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins/hexaemeron/skills/fiat/scripts/hexctl.py plugins/hexaemeron/skills/fiat/scripts/transition_gate.py
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins/hexaemeron/skills/fiat/scripts/hexctl.py
```

- For every name in `MUTATING`, `main()` holds the lock, verifies the state
  and ledger preimage, recomputes the directive, obtains the grant, and only
  then calls the handler. A refusal prints the closed refusal object and
  leaves state and ledger bytes unchanged.
- `save_state`, `append_ledger`, `commit` and the five direct writes the
  study lists (lines 19325, 19427, 19436, 20515 and 20540 at the starting
  commit) refuse without the live grant, and a grant whose digests differ from
  the bytes on disk at write time refuses. The three existing pending-record
  writers are registered as named recovery directives and keep their own
  formats; none runs while another label is live.
- `commit()` stages `state.next`, `ledger.next` and the grant, syncs them,
  publishes one durable label, replaces the ledger, replaces the state, and
  retires the label. A stop at each boundary leaves the exact preimage or one
  labelled transaction that recovery completes. `status` and `verify` name a
  live label and its transition. Each ledger entry written under a grant
  carries the grant digest.
- Against a synthetic exhausted preimage (43 ledger entries, step 2 halted
  after round 8, 30 findings open): `config set audit.max_rounds 16`, the
  whole-section `config set audit`, and a `resume` naming no exit each refuse,
  the report names Promise id, consequence 2, blocked transition and recovery,
  and byte comparison shows both files unchanged. A stale state digest, a
  forged directive, an unknown Promise id and a widened command refuse before
  mutation.
- Existing study, runbook, implementation, audit, prose, push, merge, halt,
  carryover, replacement and recovery fixtures still reach only their own
  directive, and a `resume` naming no exit still clears an ordinary halt.
- The conformance report for `product-refuses-622-specimens` exists at its
  recorded path with value true, produced by the resolver named in the
  conventions.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/scripts/transition_gate.py`,
`plugins/hexaemeron/skills/fiat/references/transition-gate.md`,
`plugins/hexaemeron/tests/test_transition_gate_wiring.py`,
`tests/promise_machine_coverage.json`,
`docs/promise-machine/obligation-gates/evaluation-run.json`,
`docs/promise-machine/obligation-gates/integration-projection.json`,
`docs/promise-machine/obligation-gates/integration-projection.md`, the six
package version surfaces, `.horos/boundary.json`, `.horos/candidates.json`,
`.horos/census.json`, and `.hexaemeron/design/reports/dispatcher-grant-wal-product-refuses-622-specimens.json`
(untracked, created once).
**Tests.** New module `plugins/hexaemeron/tests/test_transition_gate_wiring.py`, which the conformance resolver pins by name: specimens 1, 2, 3, 6 and 7, each refusal with a byte comparison, one injected stop per commit boundary with recovery, and the grant-mismatch refusal. Expected count: at least 40. Existing tests that call a writer directly are adapted to obtain a grant, never deleted.
Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-3.json`
**Disciplines.** phylax: state and ledger files are the boundary an agent under
the same account can edit, and the preimage check is the control. ephoros:
the label in `status` and the grant digest in the ledger answer on-call
questions 1 and 2. elenchus: the unlabelled ledger-ahead window measured in
the study is a failure in hand, and its guard is the injected-stop test.
metron: no process is added per mutation, asserted by test. hypomnema: the
reference gains the label layout and the recovery rule.

## Step 4: Continue an exhausted audit loop on the same ledger

**Goal.** Add `hexctl start-audit-loop` under its own declared Promise
`fiat-audit-loop-continuation`, store loops append-only with legacy rounds as
loop 1, and make `next`, `audit-round`, `status`, `verify` and the checkpoint
archive name loop-aware.
**Entry.** Step 3's exit state, with its conformance report present. Module: loop.
**Exit.** The command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/871-promise-bound-transition-gate-for-every-fiat --scope root --scope hexaemeron --format json
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins/hexaemeron/skills/fiat/scripts/hexctl.py
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/references/transition-gate.md plugins/hexaemeron/skills/fiat/references/audit-loop.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py plugins/hexaemeron/skills/fiat
```

- The gate grants `start-audit-loop` only when the run, step, ledger,
  controller version and worktree match the preimage; a verified
  exhausted-loop checkpoint and its digest are supplied; the predecessor loop
  ended at round 8 or its lower configured limit; the complete open-finding
  identities and unresolved leads are bound; one further bounded loop carries
  recorded user authority; and no label or unreceipted tree movement is
  pending. The authority is recorded as an operator declaration, never as
  authenticated identity.
- The transition appends loop N + 1 to `audit.continuations`, sets its next
  round to 1, binds it to the predecessor digest and checkpoint, clears the
  exhausted-loop halt, and appends one `audit-loop-start` ledger entry. `next`
  returns `audit-round` with loop 2 and round 1.
- The canonical bytes of `steps[*].audit.rounds` are identical before loop 2
  opens and after it closes. Each loop holds at most eight rounds. A ninth
  round refuses in either loop, and no state, log heading, directive or file
  name represents one. A missing or altered open-finding identity refuses.
- New checkpoint archives carry the loop ordinal in the boundary `loop` field
  and directory name. An archive written earlier with a round count in that
  field still inspects and restores.
- Carryover custody and replacement admission fixtures still reach only
  their own directives.
- Fiat's `SKILL.md` declares `fiat-audit-loop-continuation` after the
  governed range, adds the directive-table row and one hard rule, and points
  at `references/transition-gate.md`. The Promise has its coverage entry and
  promise cases, and the agent-instruction fixture chain is rebuilt by its
  builder.
- The conformance report for `product-appends-loop-two` exists at its
  recorded path with value true.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/scripts/transition_gate.py`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/references/transition-gate.md`,
`plugins/hexaemeron/skills/fiat/references/audit-loop.md`,
`plugins/hexaemeron/skills/fiat/references/checkpoint-archive.md`,
`plugins/hexaemeron/tests/test_audit_loop_continuation.py`,
`plugins/hexaemeron/tests/test_transition_gate.py`,
`tests/promise_machine_coverage.json` and the promise-case fixtures the new
Promise owes, `tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai`,
`docs/promise-machine/obligation-gates/evaluation-run.json`,
`docs/promise-machine/obligation-gates/integration-projection.json`,
`docs/promise-machine/obligation-gates/integration-projection.md`, the six
package version surfaces, `.horos/boundary.json`, `.horos/candidates.json`,
`.horos/census.json`, and `.hexaemeron/design/reports/dispatcher-grant-wal-product-appends-loop-two.json`
(untracked, created once).
**Tests.** New module `plugins/hexaemeron/tests/test_audit_loop_continuation.py`, which the conformance resolver pins by name: specimen 8 end to end, each refused precondition with a byte comparison, the ninth-round refusal in both loops, legacy byte identity, archive naming in both forms, and the replacement fixtures. Expected count: at least 30.
Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-4.json`
**Disciplines.** phylax: the supplied checkpoint and authority are outside
input and are checked by digest before use. ephoros: the loop ordinal,
predecessor digest and authority in `next`, `status` and the ledger answer
on-call question 3. hypomnema: decision 2 and the archive field change land
in the references and the new Promise in `SKILL.md`. elenchus: the archive
field that stores a round count is a defect in hand, guarded by the naming
test. metron: none, no performance claim.

## Step 5: Generate checkpoint handovers from verified controller evidence

**Goal.** Add `handover.py`, which reads a verified checkpoint without
following symlinks and emits one closed JSON envelope and a paste block
rendered only from it, and which refuses a supplied handover the installed
controller cannot express.
**Entry.** Step 4's exit state, with its conformance report present. Module: handover.
**Exit.** The command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/871-promise-bound-transition-gate-for-every-fiat --scope root --scope hexaemeron --format json
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins/hexaemeron/skills/fiat/scripts/handover.py
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/references/transition-gate.md
```

- The envelope `fiat-handover/v1` binds repository and worktree identity,
  controller version and digest, checkpoint and sidecar digests, state
  SHA-256, ledger count and tail, the exact `verify`, `status` and `next`
  commands, the current directive with its Promise id and permitted
  transition if any, open findings, unresolved recovery, and an explicit
  refusal when the controller cannot express a requested continuation.
- The paste block has no field the envelope lacks; a test renders it twice
  from the same envelope and compares bytes.
- A generated or supplied handover that names a ninth round, widens
  `audit.max_rounds`, or names a transition the gate's table lacks cannot be
  generated and fails verification when supplied. Reads use no-follow opens
  and size caps.
- A fresh restore of the checkpoint, followed by the envelope's three
  read-only commands, yields the same state digest and directive, and no
  command absent from the envelope is granted.
- `handover.py` writes no controller state and `hexctl.py` is unchanged.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/handover.py`,
`plugins/hexaemeron/skills/fiat/references/transition-gate.md`,
`plugins/hexaemeron/tests/test_handover.py`, the six package version
surfaces, `.horos/boundary.json`, `.horos/candidates.json`,
`.horos/census.json`.
**Tests.** New module `plugins/hexaemeron/tests/test_handover.py`: specimens 4 and 9, symlinked, oversized and digest-mismatched inputs, and render determinism. Expected count: at least 20.
Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-5.json`
**Disciplines.** phylax: a checkpoint or supplied handover is hostile input.
hypomnema: the envelope schema joins decision 4 in the reference. ephoros:
none, the tool is invoked by hand and its exit code is the signal. metron:
none, no performance claim. elenchus: none, no failure in hand.

## Step 6: Verify the enforcement path and discover every mutating handler

**Goal.** Add `verify_transition_gate.py`, its pin manifest and a fail-closed
installer wrapper, make the dispatcher run the verifier first, and fail the
suites when a mutating handler lacks a rule, a Promise, a hostile specimen or
the guarded writer path.
**Entry.** Step 5's exit state. Module: integrity.
**Exit.** The command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/871-promise-bound-transition-gate-for-every-fiat --scope root --scope hexaemeron --format json
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins/hexaemeron/skills/fiat/scripts/verify_transition_gate.py plugins/hexaemeron/skills/fiat/scripts/hexctl.py
```

- The verifier checks regular-file type, no symlink, a size cap, the
  executable bit where it applies, and exact SHA-256 pins for
  `transition_gate.py`, `handover.py`, the installer and itself, read from
  `transition-gate-pins.json`. For `hexctl.py` it pins the AST digests of
  `main`, `commit` and the grant check, and proves from source that the
  verifier precedes the gate, the gate precedes every write, and one writer
  path exists. It checks that the required test modules exist.
- A modified, symlinked, oversized, non-executable, unpinned, reordered or
  unreferenced component makes the verifier exit non-zero naming it, and the
  dispatcher then refuses before any writer runs.
- `install-transition-gate.sh` sets `set -eu`, runs the verifier first and
  aborts on failure.
- The discovery check finds every handler in `MUTATING` and every call that
  writes state or ledger, and fails on a handler without a rule, a Promise
  mapping or a negative specimen, and on a writer outside the guarded path.
  The root suite runs the same check through `tests/test_fiat_transition_gate.py`,
  which the existing repository workflow already discovers, so no workflow
  file changes.
- From this step on, no later step changes an existing pin value. Every
  message and document calls the pins tamper evidence.
- The conformance report for `product-every-mutator-mapped` exists at its
  recorded path with value true.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/verify_transition_gate.py`,
`plugins/hexaemeron/skills/fiat/scripts/transition-gate-pins.json`,
`plugins/hexaemeron/skills/fiat/scripts/install-transition-gate.sh`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/fiat/references/transition-gate.md`,
`plugins/hexaemeron/tests/test_verify_transition_gate.py`,
`plugins/hexaemeron/tests/test_transition_gate_discovery.py`,
`tests/test_fiat_transition_gate.py`, `tests/promise_machine_coverage.json`,
`docs/promise-machine/obligation-gates/evaluation-run.json`,
`docs/promise-machine/obligation-gates/integration-projection.json`,
`docs/promise-machine/obligation-gates/integration-projection.md`, the six
package version surfaces, `.horos/boundary.json`, `.horos/candidates.json`,
`.horos/census.json`, and `.hexaemeron/design/reports/dispatcher-grant-wal-product-every-mutator-mapped.json`
(untracked, created once).
**Tests.** New modules `plugins/hexaemeron/tests/test_verify_transition_gate.py` for the seven hostile component forms of specimen 5 and the installer abort, and `plugins/hexaemeron/tests/test_transition_gate_discovery.py`, which the conformance resolver pins by name, for specimen 10 with one planted unmapped handler and one planted unguarded writer. Expected count: at least 25 across both, plus one root test.
Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-6.json`
**Disciplines.** phylax: the pins and the shell installer are boundaries the
delivering agent can write, and the control is refusal plus the review rule,
stated as not mechanically enforced. ephoros: the verifier's exit and named
component answer on-call question 4. hypomnema: the pin rule and its limit
land in the reference. elenchus: none, no failure in hand. metron: none, the
verifier hashes five small files and no budget is claimed.

## Step 7: Check published mutation recipes against the same gate

**Goal.** Add `publication_gate.py`, a wrapper that extracts controller
commands from an ADR, handover, issue comment or pull request body by a closed
grammar, accepts each only when it is read-only or granted against a named
fixture state, and runs `gh` without a shell only after every command passes.
**Entry.** Step 6's exit state, with its conformance report present. Module: publication.
**Exit.** The command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/871-promise-bound-transition-gate-for-every-fiat --scope root --scope hexaemeron --format json
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins/hexaemeron/skills/fiat/scripts/publication_gate.py
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/references/transition-gate.md
```

- A body that tells a successor to run `config set audit.max_rounds 16`, to
  resume into a ninth round, or to run a transition the table lacks refuses
  before `gh issue create`, `gh issue comment`, `gh pr create` or `gh pr edit`
  starts. A body whose commands are read-only or granted passes, and the
  wrapper runs the verifier first.
- Tests replace `gh` with a recording stub on a private path; no network call
  is made and nothing is published.
- The reference states that the wrapper does not make prose true.
- The pin manifest gains one entry for `publication_gate.py`, and no existing
  pin value changes. `hexctl.py` is unchanged.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/publication_gate.py`,
`plugins/hexaemeron/skills/fiat/scripts/transition-gate-pins.json`,
`plugins/hexaemeron/skills/fiat/references/transition-gate.md`,
`plugins/hexaemeron/tests/test_publication_gate.py`, the six package version
surfaces, `.horos/boundary.json`, `.horos/candidates.json`,
`.horos/census.json`.
**Tests.** New module `plugins/hexaemeron/tests/test_publication_gate.py`: three refused recipes, two admitted bodies, command smuggling through quoting, fences and line continuation, the four guarded `gh` forms, and the unchanged-pin assertion. Expected count: at least 20.
Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-7.json`
**Disciplines.** phylax: prose is untrusted input and `gh` is a subprocess with
publishing credentials, so the grammar is closed and no shell is used.
hypomnema: the wrapper's boundary lands in the reference. ephoros: none, the
wrapper is invoked by hand and its refusal object is its output. metron:
none, no performance claim. elenchus: none, no failure in hand.

## Step 8: Demonstrate the ten specimens and record the release

**Goal.** Run the ten hostile specimens end to end against the tree's own
controller on disposable runs, commit the recorded observations, complete the
decision record, and write the Fiat generation row.
**Entry.** Step 7's exit state. Module: demonstration.
**Exit.** The command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/871-promise-bound-transition-gate-for-every-fiat --scope root --scope hexaemeron --format json
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py docs/fiat-transition-gate/demonstrate.py
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-transition-gate/demonstration.md docs/decisions/drafts/gate-fiat-mutations-and-continue-audit-loops.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/fiat-transition-gate docs/decisions/drafts plugins/hexaemeron/skills/fiat
```

- `docs/fiat-transition-gate/demonstrate.py` initialises a disposable run with
  the tree's `hexctl.py`, drives it to an exhausted loop, runs each hostile
  command with a byte comparison, starts loop 2, generates a handover,
  restores it elsewhere and reruns the three read-only commands. It reads and
  writes nothing under this run's `.hexaemeron/`.
- `docs/fiat-transition-gate/demonstration.md` names the controller path and
  digest, the source command, and one bounded positive or negative observation
  per specimen, 1 to 10. It states that the #622 bytes were synthetic unless
  the archived checkpoint was supplied, and it does not claim the criteria
  are sufficient.
- The draft decision record is complete, still unnumbered, and takes its
  number at integration through the repository's assignment process.
- Fiat's `EVOLUTION.md` gains exactly one generation row with the frontier
  tuple and digest unchanged; the `SKILL.md` metadata version, the
  compatibility-set entry in `hexctl.py` and `tests/test_evolution_contract.py`
  agree with it. No existing integrity pin value changes, because the
  verifier pins `hexctl.py` by function AST.
- The run pull request body carries every unfinished item in its carryover
  block, including the broker under another OS identity and the replay of the
  real #622 checkpoint if it was never supplied.

**Files.** `docs/fiat-transition-gate/demonstrate.py`,
`docs/fiat-transition-gate/demonstration.md`,
`docs/decisions/drafts/gate-fiat-mutations-and-continue-audit-loops.md`,
`plugins/hexaemeron/tests/test_transition_gate_demonstration.py`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`tests/test_evolution_contract.py`, `tests/promise_machine_coverage.json`,
`tests/fixtures/agent-instruction-v1/manifest.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json`,
`tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai`,
`docs/promise-machine/obligation-gates/evaluation-run.json`,
`docs/promise-machine/obligation-gates/integration-projection.json`,
`docs/promise-machine/obligation-gates/integration-projection.md`, the six
package version surfaces, `.horos/boundary.json`, `.horos/candidates.json`,
`.horos/census.json`.
**Tests.** New module `plugins/hexaemeron/tests/test_transition_gate_demonstration.py` runs the demonstration script in a temporary directory and asserts ten observations and an unchanged run state directory. Expected count: at least 3.
Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-8.json`
**Disciplines.** hypomnema: the decision record is completed and the
demonstration is the record of what was observed. phylax: the demonstration
script starts subprocesses and writes files, confined to a temporary
directory with no shell. ephoros: none, nothing new runs unattended. metron:
none, no performance claim. elenchus: none, no failure in hand.

### Amendment -- 2026-09-20

**What changed.** Complete replacement Exit: Each command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/871-promise-bound-transition-gate-for-every-fiat --scope root --scope hexaemeron --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-transition-gate/study.md docs/fiat-transition-gate/runbook.md docs/decisions/drafts/gate-fiat-mutations-and-continue-audit-loops.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-transition-gate/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-transition-gate/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/fiat-transition-gate docs/decisions
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study docs/fiat-transition-gate/study.md --design-evidence docs/fiat-transition-gate/design-evidence.json --repo-root .
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py docs/fiat-transition-gate/design
```

- `docs/decisions/drafts/gate-fiat-mutations-and-continue-audit-loops.md`
  exists with the heading `# Decision: ...`, the sections Status, Context,
  Decision, Alternatives and Consequences in that order, a dated status and no
  ADR number. It carries decisions 1 to 3 of study section 12, the three
  rejected constructions of study section 4 as alternatives, the same-account
  limit, and how it relates to ADR-028 and ADR-047. No inherited decision
  record changes by a byte.
- The receipted study carries one dated amendment whose `design-bridge` fence
  names schema `hypomnema-design-bridge/v1`, decision `dispatcher-grant-wal`
  and that draft's path, receipted through `hexctl amend study` with every
  step holding.
- `docs/fiat-transition-gate/study.md`, `runbook.md` and
  `design-evidence.json` are byte-identical to their `.hexaemeron/` sources;
  `docs/fiat-transition-gate/design/reports/` holds byte-identical copies of
  the 32 reports; and `docs/fiat-transition-gate/design/` holds byte-identical
  copies of `resolve_gate.py`, `conform_gate.py` and `build_record.py`.
- The three `.horos` artefacts equal a fresh scan. No file under
  `plugins/hexaemeron/` changed.

**Why.** The Hypomnema walk over the drafts directory alone reports two H009 findings on an inherited draft that cites two numbered records, because the numbered records sit one directory up and are never indexed. Walking the whole decisions directory indexes them and reads clean. The inherited draft stays untouched.
**Steps touched.** Step 1's exit.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds. Step 8: entry holds; exit holds.

### Amendment -- 2026-09-20

**What changed.** Complete replacement Exit: The command below exits 0, the checks runner reports outcome green, and the deliverables that follow hold:

```sh
python3 scripts/run_checks.py --base fiat/871-promise-bound-transition-gate-for-every-fiat --scope root --scope hexaemeron --format json
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py docs/fiat-transition-gate/demonstrate.py
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-transition-gate/demonstration.md docs/decisions/drafts/gate-fiat-mutations-and-continue-audit-loops.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/fiat-transition-gate docs/decisions plugins/hexaemeron/skills/fiat
```

- `docs/fiat-transition-gate/demonstrate.py` initialises a disposable run with
  the tree's `hexctl.py`, drives it to an exhausted loop, runs each hostile
  command with a byte comparison, starts loop 2, generates a handover,
  restores it elsewhere and reruns the three read-only commands. It reads and
  writes nothing under this run's `.hexaemeron/`.
- `docs/fiat-transition-gate/demonstration.md` names the controller path and
  digest, the source command, and one bounded positive or negative observation
  per specimen, 1 to 10. It states that the #622 bytes were synthetic unless
  the archived checkpoint was supplied, and it does not claim the criteria
  are sufficient.
- The draft decision record is complete, still unnumbered, and takes its
  number at integration through the repository's assignment process.
- Fiat's `EVOLUTION.md` gains exactly one generation row with the frontier
  tuple and digest unchanged; the `SKILL.md` metadata version, the
  compatibility-set entry in `hexctl.py` and `tests/test_evolution_contract.py`
  agree with it. No existing integrity pin value changes, because the
  verifier pins `hexctl.py` by function AST.
- The run pull request body carries every unfinished item in its carryover
  block, including the broker under another OS identity and the replay of the
  real #622 checkpoint if it was never supplied.

**Why.** The Hypomnema walk over the drafts directory alone reports two H009 findings on an inherited draft that cites two numbered records, because the numbered records sit one directory up and are never indexed. Walking the whole decisions directory indexes them and reads clean. The inherited draft stays untouched.
**Steps touched.** Step 8's exit.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds. Step 8: entry holds; exit holds.
