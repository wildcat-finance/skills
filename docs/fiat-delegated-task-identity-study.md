# Study: bind delegated task identity to step and role

Topic: `bind delegated task identity to step and role`. Task issue:
[skills#363](https://github.com/wildcat-finance/skills/issues/363), the held
`Next Fiat job` on Fiat's own ledger
(`plugins/hexaemeron/skills/fiat/EVOLUTION.md:13`). Starting ref
`97b74e5d1adda5d86f59c8936e32d5af6840e0d0` on `main`. Every `file:line` below
is read at that ref unless it says otherwise.

Assuming, unless corrected:

1. The controller is `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at
   `97b74e5d`, digest
   `0c7b3fca99db6927be802e867715d457037826fbe17991655716319a730afeb1`, driven
   by Python 3.14.6 (`.python-version`) with stdlib `unittest`.
2. A host spawns a delegate and names it; the controller cannot rename a
   host's agent. In this session's host the spawn call takes a short
   `description` and the host assigns the agent's ID and name, and a later
   message continues that agent by ID or name. That is observed from the host's
   tool schema in this session, not from a repository file.
3. Fiat's `next` stays read-only and deterministic over `state.json`
   (`hexctl.py:16839-16866`), and the four brief key sets pinned in
   `plugins/hexaemeron/tests/test_hexctl.py:388-392`,
   `test_hexctl.py:3149`, `test_fiat_skill.py:249-270` and
   `test_version_relations.py:2874-2925` stay as they are.
4. The dependency [skills#453](https://github.com/wildcat-finance/skills/issues/453)
   is `OPEN` (checked with `gh issue view 453` on 2026-09-13). The issue body
   says delegation identity work begins only after known-failure guards can be
   injected and proved against the unfixed parent. This run was initialised
   with #453 open. The reading taken: each fix in this run lands with a guard
   test proved red on its step parent and green on the step tree, under the
   Elenchus convention in section 11, which is the property #453 wants
   receipted generically. The controller decides whether that reading holds
   for the run; it does not change the design below.
5. A Warden keeps one handle across the rounds of one step. `warden_continuity`
   says `same-agent` on every later round of a step (`hexctl.py:13810-13820`),
   so the handle must be stable across rounds and must change across steps.

## 1. Problem statement

Fiat delegates four phases to workers: `surveyor` for `study`, `mason` for
`implement`, `warden` for `audit-round`, `scribe` for `prose`
(`hexctl.py:13728-13847`). The `next` envelope carries `state_sha256`, an
`agent` role string and a source-bound `brief`, and nothing else names the
delegation (`hexctl.py:13730-13735`). Only the Warden brief carries a `step`
field (`hexctl.py:13818`); the Surveyor brief carries `topic`
(`hexctl.py:13741`); the Mason and Scribe briefs carry the step number inside
`runbook_step.number` and `pr_draft_path` respectively. No field says which
issue or topic, step and role the spawned task should be named for, so the
orchestrator picks a name, and on the issue 320 run it continued a Mason under
the older handle `issue318_step2` (issue #363, Observed failure).

Built here: a deterministic `task_identity` in every delegated `next` envelope,
and a controller refusal for an observed handle that names another issue,
step or role. The user is the orchestrator running Fiat and the person reading
its status. A working prototype means:

1. `hexctl next` for issue N at step S with agent R prints
   `task_identity.handle` equal to `fiat-N-step-S-R` (`fiat-N-study-surveyor`
   for the study phase, `fiat-<topic-slug>-...` for a run with no task issue).
2. `hexctl next --task-handle <observed>` exits 0 with byte-identical stdout
   when `<observed>` equals that handle, and exits 2 before printing any packet
   when it does not, naming both values.
3. Two `next` processes over the same `state.json`, and a `next` after a
   checkpoint restore, print the same `task_identity`.
4. `plugins/hexaemeron/skills/fiat/SKILL.md` and the four agent files require
   the handle to be the spawned task's visible name and require the check
   before any existing handle is continued, and a test asserts those sentences.

Demo path: `python3 -m unittest
plugins.hexaemeron.tests.test_hexctl.TestTaskIdentity`, whose case
`test_stale_handle_from_another_issue_is_refused` initialises a run bound to
issue 320, advances it to step 2 `implement`, and shows `next --task-handle
issue318_step2` exits 2 while `next --task-handle fiat-320-step-2-mason` exits
0 with the same stdout as bare `next`. The names above are the contract the
runbook binds; they do not exist at `97b74e5d`.

Acceptance from issue #363, restated as checks:

| # | Issue text | Check |
| --- | --- | --- |
| 1 | issue N cannot visibly retain issue M | the emitted handle for N contains `N` and no other task segment; any observed handle not equal to it is refused at the controller before spawn or continuation |
| 2 | identities include issue or topic, step, role | handle grammar `fiat-<task>-<phase>-<role>` with `<phase>` `study` or `step-<n>`; asserted for all four roles |
| 3 | resume and post-compaction return the same identity | `task_identity` derives from `state.json` alone; asserted across two processes and a checkpoint restore |
| 4 | stale reused handle rejected, executable regression | `TestTaskIdentity`, red at the step parent, green on the step tree |

Boundary stated plainly: the controller emits a packet. Whether a host names
the spawned task with the emitted handle is outside the controller. The design
does not rename another runtime's handle; it makes the mismatch detectable and
refusable at the one point the controller is consulted, and Fiat's contract
requires the orchestrator to consult it before continuing any existing handle.

## 2. Prior art

In the repository:

- `hexctl.py:13728-13847`, `delegation_packet`, is the only builder of the
  `agent` and `brief` fields and the only caller site is `cmd_next`
  (`hexctl.py:16850`). `--brief-out` diverts the brief body to a scoped file
  and leaves the rest of the envelope readable (`hexctl.py:16851-16866`).
- The directive already carries `step` and `title` for step phases and
  `round` for audit rounds (`hexctl.py:16979-17023`), and the run anchor
  carries `task` as `{"kind": "github-issue", "number": N}`, `external` with a
  digest, or the none shape (`hexctl.py:13026-13042`). `slug()` at
  `hexctl.py:1224` and `init_preflight` at `hexctl.py:2545-2557` already build
  the run branch as `fiat/<issue>-<topic-slug>` under a 48-character limit.
  Everything a deterministic identity needs is in state today.
- `warden_continuity` (`hexctl.py:13810-13820`) is the one field that tells
  the controller which agent to continue, and its tests
  (`test_hexctl.py:5768-5846`) are the nearest shape to the regression this
  study asks for.
- Fiat `SKILL.md:751-765`, `Delegation and context`, promises `state_sha256`,
  an explicit `agent` and a source-bound `brief`, says to delegate the exact
  packet, and says that after compaction `next` reconstructs the packet from
  state. It says nothing about the visible name of the spawned task.
- The four agent files carry `- Delegation role: <role>.` at line 7 and a
  generated marketplace-context block at lines 3-5 whose current-frontier
  sentence names this very gap. Their brief key sentences are read by
  `test_fiat_skill.py:249-270`.
- `state_fingerprint` (`hexctl.py:2298`) is the canonical state digest every
  envelope already carries; `validate_state_shape` (`hexctl.py:1724-1770`)
  admits the version-1 spine and would have to admit any new state container,
  which is one reason the chosen design adds none.
- `FUTUREPROOFING.md:83` lists the reused-handle exposure as Fiat's one
  `Missing` item.

Last two merged pull requests that changed the subject, read in full:

- [#1158](https://github.com/wildcat-finance/skills/pull/1158), merged
  2026-09-03 at `bacb34c0d49a83dea0c4463a61b2cf1525fec60b`: gave Surveyor and
  Mason `plugin_root` and made each agent file the reader of its contracts. It
  names four places that pin brief shapes and records that the fourth,
  `test_version_relations.test_no_block_preserves_the_legacy_receipt_and_packet_shape`,
  compares the whole emitted directive against a literal dict. Carried
  forward here: an envelope-level `task_identity` moves that literal test and
  none of the brief key sets. Left open by name: #1122's third acceptance
  check, the digest-bound `fiat/SKILL.md` edit blocked on #1098, is not this
  run's work and stays open.
- [#1156](https://github.com/wildcat-finance/skills/pull/1156), merged
  2026-09-03 at `239880128e6fe18aba3b9f737e98ca5a663f4fc9`: added
  `warden_continuity` and `step` to the Warden brief with six tests, five of
  which fail against the unmodified controller. Carried forward: the same
  red-then-green proof pattern and the rule that `same-agent` decides
  delegation without claiming what an agent has read. Left open by name:
  #1066 items 4 and 5, blocked on #1030 and #1098, not this run's work.

Also read: [#365](https://github.com/wildcat-finance/skills/pull/365), merged
2026-08-21 at `6980aef4c33ece8614b21e4ef8ff32dd19c3e7fc`, the issue 320 run
that created the packets. Its `Carried forward` section names #363 as this
exact observation and says future packets or orchestration must bind the
visible task name to the current issue or topic, step and role across resume
and compaction. It also states that automatic spawning is an explicit product
boundary of that study, not unfinished work; this study keeps that boundary.

Audit records. `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py
--check .` ran from the target root on 2026-09-13 and exited 0 with every
committed synopsis matching its fresh render, so the verified synopsis is the
reading view. In-scope sources and what was read:

- `audit/AUDIT.md` via `audit/AUDIT_SYNOPSIS.md`, entries `Fiat delegation
  packets` step 1 rounds 1-3, step 2 rounds 1-2, step 3 rounds 1-4, the
  post-push merge incident and the integration sync closure
  (`AUDIT_SYNOPSIS.md:275-288,300`). Step 1 round 1 keeps its three findings
  `I320-S1-R1-01`, `I320-S1-R1-02`, `I320-S1-R1-03`, all resolved on the audit
  branch, with `Leads not pursued: none`. Every entry carries
  `[missing legacy field: audit-schema]`, `covered`, `not-checked` and
  `elenchus-verdict`, and every entry after step 1 round 1 also carries
  `[missing legacy field: leads-not-pursued]` with no table in the synopsis;
  those remain unknown here. PR #365's body records what those rounds closed
  and states no finding was accepted or left open.
- `audit/rounds/*.md`: no run file exists for #1156 or #1158, because both
  were pull requests without a Fiat run. Ten round synopses match the word
  `delegat`; none concerns task naming. No in-scope finding is carried
  forward or refused; there is none to carry.

Organisation and outside. No other Wildcat repository carries a Fiat
controller. Outside, the nearest analogue is a job scheduler's deterministic
job key derived from its inputs, which is the shape chosen; no standard is
cited because none governs an agent host's task name.

## 3. Constraints and non-goals

- Start `97b74e5d1adda5d86f59c8936e32d5af6840e0d0`; run branch
  `fiat/363-bind-delegated-task-identity-to-step-and-rol`; integration base
  `main`.
- Python 3.14.6 per `.python-version`; stdlib only; the Hexaemeron suite runs
  through `python3 plugins/hexaemeron/tests/run_tests.py --jobs 8`, and the
  repository checks through `python3 scripts/run_checks.py --scope hexaemeron
  --format json` (`tests/check-map-v1.json`).
- `hexctl.py`'s whole-file SHA-256 is pinned at
  `tests/promise_machine_coverage.json:4148-4149`; the obligation-gate records
  under `docs/promise-machine/obligation-gates/` bind digests over a set that
  includes that file. Any controller edit re-pins them in their own commit.
- `next` stays read-only. No new ledger event, no new state container, no
  new receipt field. The brief key sets stay as pinned.
- Ruled out: renaming, killing or inspecting a host's agent from the
  controller; a registry of issued handles; putting the identity inside the
  brief.
- Deferred past the prototype: a host-side hook that names the spawned task
  automatically; carrying the observed handle into any receipt; identity for
  the inline (`agent: null`) directives, which have no delegate.
- The frontier row in `plugins/hexaemeron/skills/fiat/EVOLUTION.md` is owed at
  integration and is not touched by the study.

Tiers the build holds to. Always: both suites before a commit; the imprimatur
lint on every shipped document; a recorded measurement before any performance
change. Ask first: adding a dependency; changing a receipt or state layout;
touching CI; widening a trust boundary; rewriting a released digest. Never:
commit key material or a credential; edit a vendored directory; delete a
failing test to make a suite pass; claim a command ran when it did not.

## 4. Design options

The record at `.hexaemeron/design-evidence.json` selects; this prose explains.
Selection values come from `.hexaemeron/resolve_design.py`, whose `FACTS`
table declares each candidate's refusal point and durable additions and
measures the bytes of the object each adds. Those are recorded design facts,
not test results; the conformance cells are the test results and stay pending
until their step.

1. `envelope-identity` (selected). `next` adds one `task_identity` object
   beside `agent` on every delegated envelope: `schema`
   `fiat-task-identity/v1`, `handle`, `task` (the run anchor's task, or the
   48-character topic slug when there is no issue), `step`, `round`, `role`.
   Handle grammar `fiat-<task>-<phase>-<role>` with `<phase>` `study` or
   `step-<n>`; `round` is in the object and out of the handle so a Warden's
   `same-agent` continuity is the same handle. `next --task-handle <observed>`
   compares by exact equality and exits 2 before printing when they differ,
   or when the directive has no delegate. Trade: the controller can only
   refuse what it is shown, so the guarantee rests on Fiat's contract that the
   orchestrator runs the check before continuing any handle; a host that never
   asks is not caught, and the refusal leaves no durable record because `next`
   writes none. Adds 148 bytes per envelope, zero durable schema, and detects
   before any phase runs.
2. `receipt-bound-handle`. Each phase receipt records the handle the work ran
   under; `done` refuses a handle naming another issue, step or role. Trade:
   the whole delegated phase completes before the mismatch is seen, and every
   receipt shape plus `verify` replay changes, which is two durable additions
   and a legacy-run compatibility question.
3. `prose-contract`. Fiat `SKILL.md` and the agent files require a fresh,
   correctly named handle; nothing mechanical. Trade: nothing refuses a stale
   handle and the identity is whatever the orchestrator typed, so acceptance
   4 has no executable case. It fails the correctness gate and is removed.
4. `ledger-registry`. A mutating `hexctl delegate --handle` mints and records
   each handle and refuses one already issued for another step or role.
   Trade: strongest refusal, but it adds a state registry, a ledger event and
   a `verify` replay rule, `next` stops being the whole story after
   compaction, and it gains nothing over candidate 1 because the expected
   handle is already a pure function of state.

Frontier: `prose-contract` fails `stale-handle-refused-mechanically`.
`envelope-identity` scores 0 phases before detection and 0 durable additions;
`receipt-bound-handle` scores 1 and 2; `ledger-registry` scores 0 and 3. One
survivor, rule `unique-frontier`. `python3
plugins/hexaemeron/skills/protasis/scripts/design_evidence.py
.hexaemeron/design-evidence.json --transition design-lock` printed `clean` and
exited 0 on 2026-09-13.

Conformance owed later, all on the selected candidate: at `step:3`,
`stale-handle-regression-guarded`, `resume-identity-reproducible` and
`next-wall-clock-bound` (median of five `next` runs at most 1000 ms); at
`integration`, `delegation-prose-bound` and `hexaemeron-suite-green`. Their
resolver is `.hexaemeron/resolve_conformance.py`, which runs the named check
as a no-shell subprocess and writes only to `--out`.

## 5. Risk register seed

```risk-register
untrusted-handle-input | the --task-handle argv string supplied by the host | at most 200 bytes, no control or whitespace characters, exact equality only, never echoed unbounded in a diagnostic
warden-round-continuity | one Warden handle across the rounds of one step | round stays out of the handle so same-agent continuity is accepted and a step change is refused
envelope-determinism | the next envelope across processes, after compaction and after checkpoint restore | identical bytes for identical state; no clock, pid, hostname or absolute path in task_identity
brief-shape-pins | the four pinned brief key sets and the literal directive dict at test_version_relations.py:2900 | brief keys unchanged; the envelope gains one key and the literal test moves in its own commit
controller-digest-cascade | tests/promise_machine_coverage.json:4148 and the obligation-gate digests | the hexctl.py digest and every downstream digest re-pinned in their own commit, recomputed from committed answers, never a fresh model run
topic-only-runs | a run initialised without --task-issue or with an external task | the handle uses the 48-character topic slug and never fabricates an issue number
inline-directive-handle | --task-handle on a directive whose agent is null | refused with a named diagnostic rather than silently accepted
host-rename-boundary | the host's own agent name or ID | the controller never claims to rename or read a host handle; it accepts or refuses the one it is shown
```

Prose the block cannot carry: the whole guarantee for acceptance 1 is a
contract plus a refusal, not a rename. Warden should look hardest at what
happens when the orchestrator skips the check, and confirm the SKILL.md
sentence makes the check unconditional before any continuation.

## 6. Glossary seeds

- `task_identity`: the envelope object naming the task, step, round and role of
  one delegation, schema `fiat-task-identity/v1`.
- `handle`: the string `fiat-<task>-<phase>-<role>` the orchestrator uses as
  the spawned task's visible name.
- `<task>`: the run anchor's GitHub issue number, or the 48-character topic
  slug when the run has none.
- `<phase>`: `study` for the Surveyor, `step-<n>` for Mason, Warden and Scribe.
- observed handle: the name of an existing agent the orchestrator is about to
  continue, passed as `--task-handle`.
- stale handle: an observed handle not equal to the emitted one.
- inline directive: an envelope with `agent: null` and `brief: {}`, executed by
  the controller session itself.
- `warden_continuity`: `new` or `same-agent`, which Warden a round is
  delegated to (`hexctl.py:13810-13820`).

## 7. Sources

- Issue: `gh issue view 363`, body digest recorded in state at
  `receipts.task_issue_contract.sha256`
  `7882fb4d42e1b47108e86550ede2e1a416dc3acd4d4e468a7eb3c302e5df2da3`.
- Dependency: `gh issue view 453`, state `OPEN` on 2026-09-13.
- Controller: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at
  `97b74e5d`, lines 1224, 1724-1770, 2298, 2545-2557, 13026-13042,
  13728-13847, 16839-16866, 16934-17023.
- Contract: `plugins/hexaemeron/skills/fiat/SKILL.md:751-765` and
  `:145-175`; `plugins/hexaemeron/agents/{surveyor,mason,warden,scribe}.md`.
- Tests: `plugins/hexaemeron/tests/test_hexctl.py:386-435,751-781,5768-5846`;
  `test_fiat_skill.py:51-54,249-270`; `test_version_relations.py:2874-2925`;
  `hexctl_harness.py:763-790`.
- Pull requests: #1158 (`bacb34c0`), #1156 (`23988012`), #365 (`6980aef4`),
  read with `gh pr view <n>`.
- Audit: `audit/AUDIT_SYNOPSIS.md:275-288,300`; synopsis check exit 0.
- Ledger and frontier: `plugins/hexaemeron/skills/fiat/EVOLUTION.md:1-14`;
  `FUTUREPROOFING.md:83`.
- Design record: `.hexaemeron/design-evidence.json`, reports under
  `.hexaemeron/design-reports/`, resolvers `.hexaemeron/resolve_design.py` and
  `.hexaemeron/resolve_conformance.py`.
- Check graph: `tests/check-map-v1.json`; digest pin
  `tests/promise_machine_coverage.json:4148`.
- Protasis: `plugins/hexaemeron/skills/protasis/SKILL.md` version 5.10.0.

## 8. Signals, and the questions behind them

The controller runs attended in an orchestrator's session, so the questions
are the ones an operator asks when a run looks wrong, not an alert at three in
the morning.

1. Which handle should this step's worker be running under? Answered by
   `hexctl next`, whose `task_identity.handle` the step that adds the field
   emits on every delegated envelope.
2. Was the handle I am about to continue refused, and why? Answered by the
   `next --task-handle` exit code and its one stderr line naming the expected
   and observed values, emitted by the same step.
3. Did a refusal happen earlier in this run? Not answerable from durable
   state: `next` writes nothing, by design, so a refusal is visible only in
   the session that saw it. That gap is accepted and stated in section 12.

[ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what those two
signals must carry.

## 9. Boundaries, per capability

One boundary opens: `--task-handle` takes a string from the host. Worth taking
at it: a long or control-laden value that reaches a diagnostic or a log.
Controls: length bound of 200 bytes, refusal of control and whitespace
characters through the existing `clean` convention (`hexctl.py:17029`),
exact-equality comparison, and a diagnostic that prints the expected handle
and a bounded copy of the observed one. No subprocess, no file and no network
is added; the topic slug already passes `slug()` and the issue number already
passes `task_issue_number` (`hexctl.py:1228`).
[phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list
and its controls; the untrusted-handle-input row in section 5 feeds the audit.

## 10. The budget, or its absence

No performance claim is made and none is needed: the identity is a string
derived from values already in memory. A sanity bound is kept so the change
cannot regress `next` by accident. Baseline on 2026-09-13, this machine, three
consecutive runs of `python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py
--dir . next`: 0.18 s, 0.48 s, 0.47 s wall. Bound: the median of five runs
stays at most 1000 ms, measured by `python3
.hexaemeron/resolve_conformance.py --candidate envelope-identity --criterion
next-wall-clock-bound`, due at `step:3`.
[metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns what a budget
carries and how it is checked.

## 11. The fail-closed posture

What stops the run: `next --task-handle` exits 2 before printing any packet
when the observed handle differs from the emitted one, when it is malformed,
or when the directive has no delegate. A refused check is a stop condition for
the orchestrator: spawn fresh under the emitted handle, never continue the
refused one. Guard convention: every fix lands with a test that fails on its
step parent and passes on the step tree, proven the way #1156 did by reverting
the controller and re-running; the runner contract is `python3
plugins/hexaemeron/tests/run_tests.py --jobs 8 --elenchus-report {report}`
and the report is the runner's `wildcat.hexaemeron-run.v1` JSON.
[elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage
order and the guard rule.

## 12. Decisions and their homes

Expensive to reverse, because anything that names tasks by it will depend on
it:

1. The handle grammar `fiat-<task>-<phase>-<role>`, with `round` outside the
   handle. Home: one decision record under `docs/decisions/`, drafted
   unnumbered and numbered at integration by the repository's allocator.
2. Identity lives at the envelope level, not in the brief, and `next` stays
   read-only, so a refusal leaves no durable record. Home: the same record,
   with the accepted signal gap from section 8 written down.
3. The study and runbook are run inputs and are committed under
   `docs/<run>/` by Step 1, as the issue 320 run's round 1 resolution
   established (`AUDIT_SYNOPSIS.md:275`, `I320-S1-R1-03`).
4. The Fiat frontier row in `plugins/hexaemeron/skills/fiat/EVOLUTION.md` is
   owed at integration and names this issue.

[hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which
decisions earn a record and where each one lives.

### Amendment -- 2026-09-13

**What changed.** Three statements are corrected. The selected candidate and the design record are unchanged.

1. `<task>` for a run with no task issue is the 48-character topic slug, except that a slug of digits alone takes the prefix `topic-`: topic `363` derives `topic-363` (sections 4 and 6).
2. The Elenchus runner contract in section 11 is `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}` with report format `unittest-json-v1`. That runner writes an `elenchus.unittest.v1` report; `wildcat.hexaemeron-run.v1` is its run event, not an Elenchus format. A guard under the root `tests/` uses `python3 tests/run_tests.py --elenchus-report {report}` with the same format.
3. Decision 12.3's copies are the flat files `docs/fiat-delegated-task-identity-study.md` and `docs/fiat-delegated-task-identity-runbook.md`, byte-identical to `.hexaemeron/study.md` and `.hexaemeron/runbook.md`, the form the issue 320 run used for `docs/fiat-delegation-packets-study.md`.

**Why.** Step 1 audit round 1 recorded all three in `audit/rounds/fiat-363-bind-delegated-task-identity-to-step-and-rol.md`. S1-R1-02: a topic slug of digits alone equals the task segment of the issue with that number, so the two runs would accept each other's handles; commit `370866012205b6d0378e656ecc089b390b435db4` fixed it. S1-R1-05: Elenchus accepts only `unittest-json-v1`, `forge-junit-v1` and `node-test-json-v1`, so under the old contract every fix classifies `inconclusive` and assumption 4's guard reading cannot be recorded as `guarded`. S1-R1-06: no step created the copies, and a flat copy keeps this study's `../plugins/` links resolving from `docs/`.

**Steps touched.** Step 1, Step 2 and Step 3.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-09-14

**What changed.** Section 9's controls for `--task-handle` are corrected to match `task_handle_refusal` as built. It refuses a value longer than 200 bytes and any whitespace or non-printable character, lone surrogates included, and it does not use the `clean` convention. Comparison is exact equality. The length and character refusals name the expected handle and never echo the refused value; the equality refusal names both handles, the observed one having passed both checks. A handle checked against a directive with no delegate is refused before its value is read.

**Why.** Step 1 audit round 2 and Step 2 audit round 1 recorded the section 9 wording as leads in `audit/rounds/fiat-363-bind-delegated-task-identity-to-step-and-rol.md`: the `clean` convention and "a bounded copy of the observed one". The reader was built stricter than that sentence, in commit `370866012205b6d0378e656ecc089b390b435db4` for S1-R1-01 and S1-R1-03. Step 3 refreshes this study's committed copy, so the correction lands before it.

**Steps touched.** Step 3

**Still holding.** Step 3: entry holds; exit holds.
