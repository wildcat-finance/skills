# Study: bind companion run observations to Fiat receipts

Assuming, unless corrected:

1. The starting tree is `5d6fc67bb6c861f2be631eef2d7bef3c01c73e84`, the verified merge of issue #435.
2. `promise-machine-run-observation/v1` remains the event contract and
   `promise-machine-run-observation-capture/v1` remains the pre-persistence
   redaction contract; this run adds no third event format.
3. A selected receipt boundary means an operator explicitly records an
   observation binding after one existing Fiat ledger receipt. Fiat does not
   attach observations to every transition automatically.
4. A missing, failed, unknown, or unavailable observer blocks only an explicit
   observation-verification request. It does not block the controller's ordinary
   phase transition or strengthen completed delivery evidence.
5. Python 3.11 or newer and the standard library remain the implementation
   boundary. No dependency, service, database, dashboard, or CI workflow is
   added.
6. ADR-023 is reserved for an incoming decision. This run owns ADR-024 and
   must not create, rename, or modify ADR-023.
7. Signed local commit
   `6d0589ed813c4ec61184ed391caeff2d9572f638` is bounded prior art from the
   halted ADR-023 run: it contains the prefix validator, controller runtime,
   fixture manifest, and red-first focused guards. It is not a Fiat receipt or
   acceptance result. Mason may transplant those exact mechanisms before the
   complete ADR-024 tree is tested; it must not replay the halted run's partial
   gates as evidence.

## 1. Problem statement

Fiat needs a control receipt that identifies the exact companion observation
prefix available after a selected ledger receipt without moving observation
events into the controller ledger. A working prototype accepts one confined
run-local JSONL stream or records that capture was unavailable, associates the
result with the immediately preceding ledger entry, and later recomputes the
bound prefix without treating it as delivery evidence.

The normal demonstration is
`plugins.hexaemeron.tests.test_run_observation_binding.ObservationBindingTests.test_normal_prefix_binds_to_the_selected_receipt`.
It must show one validated prefix bound to the correct controller run and
receipt. The companion command
`hexctl verify --observations` must pass that fixture and return stable `FOB`
findings for missing, replaced, truncated, reordered, wrong-run, count-mismatched,
contract-mismatched, and failed-redaction cases.

Success requires all of the following:

- `python3 -m unittest plugins.hexaemeron.tests.test_run_observation_binding -v`
  passes the normal case and every issue-acceptance case.
- `python3 plugins/hexaemeron/tests/run_tests.py` passes with a non-empty
  `elenchus.unittest.v1` report when supplied its report path.
- `python3 -m unittest discover -s tests` passes.
- `python3 scripts/promise_machine.py sync --check`, `check`, and
  `coverage --check` pass with the new promise and exact runtime surface bound.
- `hexctl verify` remains green for a legacy state with no observation binding,
  while `hexctl verify --observations` refuses that dependent claim with its
  stable code and recovery.

## 2. Prior art

The event format and hostile-input controls shipped in issue #434 and merged
PR #513. ADR-015 deliberately left capture and Fiat receipt binding separate.
The final observable-record audit retained 1,258 inoculation cases and left
receipt binding assigned to #436. The capture and persistence boundary shipped
in issue #435 and merged PR #539. ADR-022 again left #436 separate, and the
zero-finding CARRYOVER-12 audit names receipt binding as an unpursued successor.

The last two merged pull requests changing Fiat's controller are PR #562 and
PR #550. PR #562 preserves exact product evidence while superseding only failed
integration evidence. PR #550 distinguishes an immutable starting commit from
the named integration base. This design keeps both distinctions: an observation
binding is evidence about one exact prefix at one ledger boundary, not a new
classification of the product or integration receipt.

Current repository contracts inspected before choosing the design:

- ADR-015, the v1 observation schema, validator, fixtures, reporter, and the
  final issue-434 audit rounds;
- ADR-022, the capture schema, runtime, writer, fixtures, reporter, and the
  issue-435 CARRYOVER-12 audit record;
- Fiat's state writer, hash-chained ledger, `record`, `verify`, status, and
  Promise Machine declarations at the starting ref; and
- the complete PR bodies and carried-forward sections for PRs #513, #539,
  #550, and #562.

Nothing in those records authorises treating observation as proof of delivery,
capture completeness, hidden model intent, or external truth. Their unresolved
receipt-binding boundary is the content of this run rather than a reason to
reopen either predecessor.

## 3. Constraints and non-goals

The run starts at `5d6fc67bb6c861f2be631eef2d7bef3c01c73e84`.
The controller remains state version 1. Existing ledgers with no observation
field remain verifiable; absence becomes a refused observation claim only when
the operator asks for one. Observation bytes live below `.hexaemeron/`, outside
the tracked product tree and outside ledger entries. Only bounded binding
metadata enters controller state and the ledger.

Always: validate the companion at the filesystem boundary, keep its events out
of state, bind the immediately preceding receipt hash, retain stable findings,
run both suites, and lint every shipped document. Ask first: a dependency, a
new network or host boundary, a write outside `.hexaemeron/`, a changed public
event schema, or a CI change. Never: coerce malformed events, follow symlinks,
echo rejected values, claim an unbound tail, weaken an existing receipt, or
make observation availability a precondition for delivery.

Non-goals are event capture, transcript storage, dashboards, cross-run search,
diagnosis, performance analysis, automatic issue creation, and the #437
handover report. The command does not prove that a host emitted every event or
that a recorded event is true.

## 4. Design options

### Option A: put every observation event in the Fiat ledger

This would reuse ordering and state fingerprints. It loses because event volume
and capture failure would enter the controller's critical path, changing the
ledger from a transition record into a telemetry store.

### Option B: add observation flags to every `done` transition

This gives direct per-phase attachment. It loses because every handler would
gain optional capture semantics, older phase receipts would need migration,
and an observer failure could be mistaken for a failed delivery transition.

### Option C: add an explicit non-authorising observation-binding receipt

Chosen. `hexctl observe` binds the current complete JSONL prefix to the
immediately preceding ledger receipt. It records the observation contract,
deterministic controller run id, event interval, event count, byte count,
SHA-256 digest, capture state, structural-validation result, and redaction-gate
result. The command appends `record:run-observation` without advancing the
workflow. Multiple selected boundaries produce multiple bindings to increasing
prefixes of the same stream.

`scripts/run_observation.py check-prefix` applies the existing v1 shape and
relation rules while allowing the final `run.finished` event to be absent.
It still requires one opening event, contiguous order, closed capabilities at
the receipt boundary, safe fields, and the existing final-byte check.
`hexctl observe` accepts an available prefix only after that check passes and
the run id matches Fiat's deterministic id. Unknown, unavailable, gapped,
refused, or failed-redaction states record no companion digest.

`hexctl verify` continues to establish only controller integrity. The new
`--observations` flag asks for the dependent observation claim: it recomputes
each bound prefix, verifies its receipt association, and reports any unbound
tail without adding that tail to the claim. Replacement, reordering, or
truncation inside a bound prefix refuses. Appending later events leaves the
earlier prefix valid and explicitly leaves the tail unbound until another
receipt is recorded.

The trade is one extra operator command and a separate claim flag. That is
cheaper to understand than hidden optional behavior on every phase and keeps
observation failure from becoming delivery failure.

## 5. Risk register seed

```risk-register
companion-path | the run-local JSONL path below .hexaemeron | regular no-follow confined reads reject symlinks escapes devices and races
prefix-drift | bytes covered by a recorded prefix digest | replacement reordering mutation and truncation refuse with stable recovery
unbound-tail | bytes appended after a bound prefix | verification preserves the earlier claim and names later bytes as unbound
run-association | observation run_id against the controller identity | wrong-run files and mixed-run prefixes refuse without echoing values
receipt-association | binding against the immediately preceding ledger entry | a missing reordered or edited receipt hash cannot satisfy the claim
contract-identity | event and capture contract identifiers | divergent or placeholder identities refuse before a binding is recorded
count-agreement | event interval count and byte count | recomputation detects mismatched counts boundaries and partial final lines
gate-status | capture validation and redaction results | failed unknown gapped refused or unavailable states stay visible and cannot pass the dependent claim
controller-independence | ordinary state verification and phase transitions | absent or failed observation never invalidates independent delivery receipts
legacy-state | version-1 states and ledgers without observation bindings | ordinary verification stays green and the explicit claim returns FOB001
partial-write | observation growth during bind or verify | bounded snapshot identity digest and final reread prevent a clean torn-prefix result
diagnostic-echo | malformed paths events and gate reasons | findings expose stable codes safe locations and recovery but no rejected values
binding-growth | repeated selected receipt boundaries | count caps monotonic prefixes and exact prior receipt hashes prevent unbounded or duplicate state
coverage-drift | Fiat Promise declarations and executable surface | generated copies and digest-bound coverage fail when docs runtime tests or selectors drift
```

## 6. Glossary seeds

- A companion stream is the run-local JSONL observation file outside controller state.
- A selected receipt is the existing ledger entry immediately before `hexctl observe`.
- A bound prefix is the exact first N companion bytes identified by count and SHA-256.
- An unbound tail contains later companion bytes not covered by the selected receipt.
- An observation claim is the result requested by `hexctl verify --observations`.
- A delivery claim is the independent result from ordinary `hexctl verify`.
- The controller run id is a deterministic safe identity derived from immutable run state.
- An unavailable binding records why no observation prefix can be claimed.

## 7. Sources

- [Issue #436](https://github.com/wildcat-finance/skills/issues/436)
- [PR #513](https://github.com/wildcat-finance/skills/pull/513)
- [PR #539](https://github.com/wildcat-finance/skills/pull/539)
- [PR #550](https://github.com/wildcat-finance/skills/pull/550)
- [PR #562](https://github.com/wildcat-finance/skills/pull/562)
- [ADR-015 at the starting ref](https://github.com/wildcat-finance/skills/blob/5d6fc67bb6c861f2be631eef2d7bef3c01c73e84/docs/decisions/ADR-015-define-the-promise-machine-run-observation-record.md)
- [ADR-022 at the starting ref](https://github.com/wildcat-finance/skills/blob/5d6fc67bb6c861f2be631eef2d7bef3c01c73e84/docs/decisions/ADR-022-define-the-run-observation-capture-profile.md)
- [Fiat controller at the starting ref](https://github.com/wildcat-finance/skills/blob/5d6fc67bb6c861f2be631eef2d7bef3c01c73e84/plugins/hexaemeron/skills/fiat/scripts/hexctl.py)
- [Observation validator at the starting ref](https://github.com/wildcat-finance/skills/blob/5d6fc67bb6c861f2be631eef2d7bef3c01c73e84/scripts/run_observation.py)
- [Repository audit log at the starting ref](https://github.com/wildcat-finance/skills/blob/5d6fc67bb6c861f2be631eef2d7bef3c01c73e84/audit/AUDIT.md)

## 8. Signals, and the questions behind them

This design follows [Ephoros](https://github.com/wildcat-finance/skills/blob/5d6fc67bb6c861f2be631eef2d7bef3c01c73e84/plugins/hexaemeron/skills/ephoros/SKILL.md).
The controller emits bounded command output rather than a new metrics or alert
surface. An operator needs to answer: which receipt the prefix covers; whether
capture, validation, and redaction passed; how many events and bytes are bound;
and whether a later tail remains unbound. The observation receipt and
`verify --observations` output answer those questions using the controller run
id, receipt hash, counts, digest, closed gate statuses, and stable finding code.
No event body, rejected value, high-cardinality metric label, or alert is added.

## 9. Boundaries, per capability

This design follows [Phylax](https://github.com/wildcat-finance/skills/blob/5d6fc67bb6c861f2be631eef2d7bef3c01c73e84/plugins/hexaemeron/skills/phylax/SKILL.md).
The companion file is untrusted input: bounded no-follow reads, confinement,
strict JSON, prefix validation, and final-byte identity close it. The operator's
status and reason arguments are closed enums and stable codes. The ledger
association is checked by hash against the existing chain. No subprocess shell,
network host, credential, dependency, or path outside `.hexaemeron/` is opened.
The audit classifies each control as exercised or merely asserted.

## 10. The budget, or its absence

No performance change or latency claim is in scope, so
[Metron](https://github.com/wildcat-finance/skills/blob/5d6fc67bb6c861f2be631eef2d7bef3c01c73e84/plugins/hexaemeron/skills/metron/SKILL.md)
has no measurement budget to apply. Existing observation limits of 1,048,576
bytes, 65,536 bytes per line, and 512 events bound work as hostile-input
ceilings, not performance targets. Tests assert the caps and totality rather
than benchmark speed.

## 11. The fail-closed posture

This design follows [Elenchus](https://github.com/wildcat-finance/skills/blob/5d6fc67bb6c861f2be631eef2d7bef3c01c73e84/plugins/hexaemeron/skills/elenchus/SKILL.md).
An unsafe file, malformed prefix, wrong run, wrong receipt, changed bound byte,
failed gate, or missing requested binding refuses the observation claim. It does
not advance or roll back the workflow. Every audit repair must preserve the
exact red invocation twice, add a test that fails on the unfixed parent, and
use `python3 plugins/hexaemeron/tests/run_tests.py {report}` with report format
`unittest-json-v1` and report file `.elenchus/fiat-run-observation-binding.json`
for the source-bound Elenchus verdict.

## 12. Decisions and their homes

This design follows [Hypomnema](https://github.com/wildcat-finance/skills/blob/5d6fc67bb6c861f2be631eef2d7bef3c01c73e84/plugins/hexaemeron/skills/hypomnema/SKILL.md).
The expensive choice is the public boundary between delivery receipts and
observation bindings. It will live in the next unused cross-repository record,
`docs/decisions/ADR-024-bind-run-observation-prefixes-to-fiat-receipts.md`.
Operator guidance will live in
`docs/fiat-run-observation-binding-v1.md`. The accepted study and runbook will
be copied byte-for-byte to `docs/fiat-run-observation-binding-study.md` and
`docs/fiat-run-observation-binding-runbook.md`. Interface docstrings will name
arguments, returns, stable findings, and the independence boundary next to the
code.

### Amendment -- 2026-08-24

**What changed.** Step 1 scope also includes `tests/test_evolution_contract.py`, solely to advance its existing Fiat version and evidence-parity assertions from `fiat-v5.19.1` to this run's required `fiat-v5.20.1` and issue #436 ADR-024 evidence.
**Why.** The receipted runbook already requires the Fiat `SKILL.md` and `EVOLUTION.md` generation bump plus the full root suite, but omitted the repository's exact guard for those required bytes. Leaving that guard stale would make the declared exit impossible.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds.

### Amendment -- 2026-08-24

**What changed.** Step 1 scope also includes `tests/test_run_observation_capture.py`, solely to bind issue #435's receipt-copy assertions to issue #435 controller state and to compare its inherited Fiat runtime coverage rows with the current controller bytes.
**Why.** The required root suite showed that those integration guards treated any later run's `.hexaemeron` study and runbook as #435 evidence, so a valid #436 receipt falsely invalidated the already merged #435 product tree. The same test pinned the prior Fiat runtime digest instead of checking the current covered source.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds.

### Amendment -- 2026-08-24

**What changed.** Step 1 scope also includes `plugins/hexaemeron/tests/run_tests.py`, solely to accept the receipted positional `{report}` argument as a backward-compatible alias for its existing `--elenchus-report PATH` interface; the binding coverage record must digest-bind that source-owned reporter and its guard.
**Why.** The receipted #436 study and runbook declare `python3 plugins/hexaemeron/tests/run_tests.py {report}` as the exact Elenchus command, while the current reporter refuses its positional argument before emitting a report. The existing command must become executable without rewriting the receipted runbook or weakening report-path confinement.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds.
