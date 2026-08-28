# Study: janus resolves the manifest's permitted effects into the gate inputs

Run: `fiat/329-janus-resolve-the-manifest-s-permitted-effec`, task issue
[wildcat-finance/skills#329](https://github.com/wildcat-finance/skills/issues/329).
Target: the `janus` skill (`plugins/janus/`), ledger `janus-v0.1.0`.

Assuming, unless corrected:

1. Foundry (forge 1.7.1, solc 0.8.25, evm `cancun`, per
   `plugins/janus/harness/foundry.toml`), offline, no external Solidity
   dependency. Python is the repository pin in `.python-version` (3.14.6),
   stdlib only.
2. This is a generation change under
   `plugins/hexaemeron/skills/VERSIONING.md`: exactly one new `EVOLUTION.md`
   history row, `janus-v0.1.0` to `janus-v0.2.0`, axis `generation`, retaining
   the frontier revision `second-host-adapter` and the frontier digest
   `c244247ec1071dda04c29206e52efe3eab264e8c323eaf15468f03e3a9688764`
   byte for byte. The held `Next Fiat job` text does not change.
3. The in-tree cheatcode declaration file `harness/src/Vm.sol` may be widened
   with signatures copied exactly from Foundry's canonical `Vm` interface
   (`keyExistsJson` is the one this design needs). That is an ordinary code
   change, not a new dependency: the file stays a declaration-only subset.
4. The manifest's `roleProvider.*` entries are intended, not stray: they
   describe the OpenTermHooks shape the honest hook models. The fix therefore
   wires a real role-provider path into the example rather than deleting the
   entries, so a non-empty resolved permit set is exercised on the honest
   path. If the maintainer would rather the honest example stay call-free and
   the entries be removed, the design still holds and one fixture moves.
5. `manifestVersion` stays `"1"`. Resolution gives existing fields a
   consumer; it does not change the format.

I will proceed on these unless corrected.

## 1. Problem statement

Gate 1 of the Janus conformance suite promises that an omitted storage write,
call target, or value movement is forbidden, not implicitly accepted. The
enforcement mechanism, however, takes hand-written Solidity `address[]`
literals from the test author, and the manifest that declares the permitted
effects is consulted for exactly one field. The manifest is a parallel
document: editing its permitted effects moves no verdict.

This wish is generation work on `janus`: resolve the manifest's symbolic
scopes and targets (`hook`, `roleProvider.getCredential`, and the rest of the
schema's vocabulary) into concrete addresses through the host adapter, and
build every conformance gate set from that resolution. It deliberately
precedes the held frontier job (`second-host-adapter`): a second host adapter
written against a manifest no gate consults would demonstrate nothing about
host-neutrality (wave-atlas review note of 26 Aug 2026, quoted in issue 329).

Who it is for: the janus maintainers now, and the author of the second host
adapter later, who will consume the resolution seam this run creates.

A working prototype means all of the following hold, each checkable by a
command from `plugins/janus/harness/` (Foundry commands) or `plugins/janus/`
(Python commands):

- `forge build && forge test` is green, and every conformance test that
  renders a manifest verdict builds its gate sets from
  manifest-through-adapter resolution rather than a hand-written literal.
  Engine-mechanics unit tests (attribution, laundering, JSON escaping) keep
  explicit arrays; see section 4 for that boundary.
- The gas gates read the budget of the action they drove, selected by action
  name, not `.thresholds[0]`.
- A new refusal test proves an omitted manifest entry is refused: a hook that
  calls the role provider, driven against a fixture manifest whose deposit
  threshold omits that call entry, fails gate 1.
- A new permit test proves a manifest-listed call is admitted: the
  provider-backed honest path passes gate 1 with the resolved set.
- A new fail-closed test proves an unresolvable symbol aborts the run
  (expectRevert), rather than shrinking or widening a gate set silently.
- `python3 scripts/janus.py validate manifests/*.json` exits 0, including any
  new fixture manifest; `python3 -m unittest discover -s tests` exits 0.
- The demo path: run the two suites above, then
  `python3 scripts/janus.py report --findings <emitted findings file> --md
  report.md --sarif report.sarif` over a findings file the harness emitted.

## 2. Prior art

In this repository, at the starting SHA
`6813bdb36ae27d23606f3449c019e5ab85520212`, every claim in issue 329 was
re-verified against the code:

- `plugins/janus/harness/test/WildcatConformance.t.sol:171` hands gate 1
  `new address[](0)` with the comment `// the honest hook calls nothing`,
  while `plugins/janus/harness/manifests/wildcat-open-term.json:16-19`
  declares two permitted calls (`roleProvider.getCredential`, staticcall;
  `roleProvider.validateCredential`, call) on that same deposit threshold.
  Confirmed: the shipped example disagrees with itself, and nothing notices
  because `HonestAccessHook` makes no external call
  (`plugins/janus/harness/src/wildcat/HonestAccessHook.sol:13-85`).
- The manifest is read for exactly one field anywhere in the harness:
  `vm.parseJsonUint(vm.readFile(MANIFEST), ".thresholds[0].gasBudget")` at
  `WildcatConformance.t.sol:184` and `HostileHooks.t.sol:55`. Confirmed by
  grep over `harness/src` and `harness/test`; the only other `readFile` calls
  read back findings files the harness itself wrote. Both reads are
  positional (`[0]`), correct today only because deposit happens to be the
  first threshold.
- Every other gate set is hand-written: `WildcatConformance.t.sol:171`
  (empty), `:223-224` (`[forwarder]`), `:242` (empty);
  `HostileHooks.t.sol:88` (empty calls), `:97-98` (`[hook]` write scope).
- The comments saying "the manifest lists" and "the manifest permits" are at
  `plugins/janus/harness/src/JanusHarness.sol:107` and `:112`; they describe
  an intention, not a mechanism. Confirmed.
- `WildcatConformance.t.sol:148` constructs the adapter with role provider
  `address(0)`; `WildcatHostAdapter.sol:23-28` stores it and `categoryOf`
  (`:52-58`) already classifies hook, host, asset, and role provider
  addresses, which is the natural seam for name resolution.
- The recorder (`StateDeltaRecorder.sol`) observes call targets, kinds,
  values, depths, and per-account storage writes. Gate granularity is the
  account: `_gate1_hookStorageWithinScopes` (`JanusHarness.sol:113-130`)
  checks written accounts, never slot names.
- The validator (`plugins/janus/scripts/janus.py:33-208`) enforces presence,
  enumerations (`J015`), and wildcard refusal (`J009`) over the same
  vocabulary; it never resolves anything to an address, and cannot, since
  addresses exist only at EVM runtime.

Last two merged pull requests that changed the subject: PR #723
(`agent/synkrisis-step-4`, merge `5b077bb6`) and PR #722
(`agent/synkrisis-step-3`, merge `45f4c5ea`) each touched only
`plugins/janus/PROMISE_MACHINE.md` and `README.md` prose from another run;
their bodies carry no unfinished janus work. The last substantive change to
the harness was PR #279 (merge `37ad3e4e`, "Build the Janus hook-conformance
suite against the Wildcat v2.5 hooks"); its body records no open work either.

Audit records. There is no `plugins/janus/audit/` source; the janus build
history lives in the shared-log era of the root `audit/AUDIT.md`. I ran
`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
from the target root; the whole-set currency check exits 0 over 25 mapped
pairs (root `audit/AUDIT.md` and its `AUDIT_SYNOPSIS.md`, the
`audit/rounds/*` pairs, and five plugin-local sources, none of them janus).
Because the root pair covers only the root source and the janus rounds
predate per-run logs, I read the authoritative source directly:
`audit/AUDIT.md`, sections "Run: create the janus skill in the Wildcat
Commons" (from line 4531) and "Run: build the Janus hook-conformance suite
against the Wildcat v2.5 hooks" (from line 4573). Findings carried forward,
all with status `fixed` in named commits: S2-R1-01 (validator enum hole,
J015), S3-R1-01..03 (recorder CREATE/SELFDESTRUCT, double-begin, delegatecall
double-count), S4-R1-01..03 (accessor attribution, value-kind filter, vacuous
pass), S5-R1-01..05 (over-attribution on host reads, ungated storage writes,
findings JSON injection, reentry invariant isolation, unpinned revert
reason). Leads not pursued, recorded as accepted limitations in Step 5 round
1: (a) no rate-band constraint on the value-returning hook, needing a
manifest field the format does not carry; (b) the hostile gas fixture
exercises deposit only. Both stay open by name here: (a) remains a manifest
format extension and is a non-goal of this run; (b) is partially narrowed by
this run, since budgets become per-action reads selected by name, but the
hostile gas fixture itself stays deposit-only and the lead stays open.

Outside the repository: Foundry's canonical `Vm` cheatcodes `parseJson*` and
`keyExistsJson` (Foundry book, cheatcode reference); the Wildcat v2.5
`OpenTermHooks` and `HooksConfig` sources at anchor commit `9716e78`, already
cited line-by-line in `WildcatHostModel.sol:37-57`; JSON Schema 2020-12 for
the manifest schema.

## 3. Constraints and non-goals

Constraints:

- Starting ref: `main` at `6813bdb36ae27d23606f3449c019e5ab85520212`, on run
  branch `fiat/329-janus-resolve-the-manifest-s-permitted-effec`. Work stays
  inside this worktree.
- Toolchain: forge 1.7.1, solc 0.8.25, evm `cancun`, optimizer 200 runs, as
  pinned by `harness/foundry.toml`; Python 3.14.6 per `.python-version`,
  stdlib only. Everything runs offline.
- Versioning: one new generation row in
  `plugins/janus/skills/janus/EVOLUTION.md` (`janus-v0.2.0`), retaining the
  prior frontier revision and digest byte for byte per
  `plugins/hexaemeron/skills/VERSIONING.md`. The `SKILL.md` frontmatter
  version moves to `0.2.0` to match. The held `Next Fiat job`
  (second-host-adapter) is not changed, started, or resumed by this run.
- `foundry.toml` `fs_permissions` stay as shipped (read `./manifests` and
  `./examples`, read-write `./out`); any new fixture manifest lives under
  `harness/manifests/` so no permission widens. `ffi` stays off.
- No external Solidity dependency is added; `Vm.sol` stays an in-tree
  declaration subset whose signatures match Foundry exactly.
- The five hostile reference hooks and the seven gates keep their semantics;
  no gate is weakened. The recorder is not the subject and is unchanged.

Non-goals, deferred past this prototype:

- Slot-level storage matching. The recorder yields written accounts and raw
  slots; manifest slot strings such as `lenderStatus[lender]` stay
  documentation. Resolution is to account granularity, stated openly in the
  schema text (section 12).
- ERC20 flow attribution beyond the existing gates. `permittedValueMovements`
  resolves to (asset, recipient) address pairs and an empty resolved list
  keeps meaning "the hook moves no fresh value" (`_hookValueMoved == 0`);
  token-transfer graph analysis is out.
- The second host adapter (the held frontier job), any manifest format
  change including a rate-band field, and any change to the Python reporter.

## 4. Design options

Option A, shared resolver plus adapter name table (chosen). A new
`harness/src/ManifestReader.sol` reads one manifest with the scoped
filesystem cheatcode, selects a threshold by action name (looping with
`keyExistsJson`, refusing a missing action), and resolves each symbolic
entry through a new `HostAdapter` virtual, `resolveAccount(string name)
returns (bool ok, address addr)`. `WildcatHostAdapter` implements the table
`hook`, `host`, `asset`, `roleProvider`, mirroring its existing `categoryOf`.
The account symbol of a call target or storage slot is the text before the
first `.`; the suffix (`getCredential`, a slot expression) stays
documentation. Storage scope `hook` resolves to the hook address, `host` to
the host, `external` to the resolved account symbol of its slot's prefix.
Only kinds `call` and `delegatecall` enter the state-changing allowed set;
a `staticcall` entry admits nothing, because gate 1 already never treats a
read as an effect, and letting it admit state-changing calls would widen the
permit beyond what the manifest said. The reader returns one
`ResolvedThreshold` (allowed call targets, allowed write accounts, value
pairs, gas budget) that conformance tests feed to the existing gate
functions unchanged. Trade: the in-tree `Vm` surface widens by one cheatcode
and JSON walking in Solidity is verbose; parsing per test costs milliseconds.
Bought: one resolver serves every future adapter, which is what the held
frontier job needs.

Option B, adapter-owned resolution. Each adapter parses the manifest and
returns resolved thresholds itself. Trade: every future adapter re-implements
JSON walking, and a second-adapter author can diverge from the format
semantics silently, the exact failure the frontier job exists to rule out.
Rejected.

Option C, test-local symbol tables. Each test maps names to addresses in a
local mapping and still hand-builds arrays. Cheapest to write, but resolution
stays outside the reusable harness, the manifest still moves no verdict on
its own, and the disagreement class survives wherever the next test author
hand-writes a set. Rejected.

(A Python-side pre-resolution pass was considered and discarded before
optioning: deployment addresses exist only at EVM runtime, so no offline tool
can produce the gate inputs.)

The pick is Option A: it is the cheapest to comprehend that still meets the
problem statement, because every piece sits where its knowledge lives: the
format walk in one reader, the name table in the adapter that already
classifies those addresses, the gates untouched.

One boundary inside Option A, stated so the runbook does not overreach:
conformance-verdict tests must build their sets through resolution;
engine-mechanics unit tests (the laundering forwarder at
`WildcatConformance.t.sol:212-229`, the host-read test at `:231-247`, the
JSON escaping tests) exercise attribution and reporting with deliberately
constructed sets and keep explicit arrays. The gate functions'
`address[]` parameters are the engine API and do not change. The example
disagreement resolves by wiring the declared role provider for real: a
minimal `MockRoleProvider` contract, the adapter constructed with its
address, and `HonestAccessHook` gaining an optional provider path that
makes the manifest's declared `validateCredential` call on deposit, so the
honest path exercises a non-empty resolved permit set. Gate 3's monotone
known-lender behaviour is preserved unchanged.

## 5. Risk register seed

```risk-register
unresolved-symbol-fail-closed | ManifestReader meeting a symbol the adapter cannot resolve, or a zero address | resolution reverts and the test aborts; no silent empty or partial set is returned
threshold-lookup-no-fallback | selecting a threshold by action name | a manifest without the driven action refuses; nothing falls back to thresholds[0]
staticcall-kind-not-permitting-writes | building the state-changing allowed set from permittedCalls | a kind staticcall entry never admits a state-changing call to its target
over-permit-by-category | the WildcatHostAdapter name table | only the named symbol's address enters a set; host and asset are never swept into a permit implicitly
vm-signature-drift | the widened in-tree Vm.sol declarations | each added signature matches Foundry's canonical Vm exactly and a test exercises it
fixture-manifest-validity | the omitted-entry fixture manifest | the fixture passes janus.py validate, so the refusal it proves comes from the gate, not a malformed file
hostile-set-regression | the five hostile hooks against resolved sets | each hostile hook is still caught once its gate set comes from the manifest
honest-liveness-regression | the provider-backed honest hook | gate 3 still passes after credential lapse and provider removal; the monotone known-lender bit is untouched
```

The first two lines are the same posture seen from both ends: the reader
refuses what it cannot ground. The over-permit line is the one false-pass
direction this change could introduce and deserves the hardest look; the
others are false-fail or drift risks that would erode trust in the suite
rather than let a hostile hook through.

## 6. Glossary seeds

- Resolution: mapping a manifest's symbolic names to concrete addresses
  through the host adapter at test runtime.
- Symbol: the account name before the first `.` in a manifest target or
  slot string, e.g. `roleProvider` in `roleProvider.getCredential`.
- Gate inputs / gate set: the `address[]` arguments the gate functions
  compare a recorded delta against.
- Threshold: one manifest entry declaring a hook's permitted effects around
  one host action.
- ResolvedThreshold: the struct the reader returns; allowed call targets,
  allowed write accounts, value pairs, and the gas budget for one action.
- Causal subtree: the depth-bounded run of recorded calls attributed to the
  hook (`JanusHarness.sol:56-79`).
- Role provider: the credential source the Wildcat hooks consult; modeled
  here by `MockRoleProvider`.
- Generation row: an `EVOLUTION.md` history entry that changes behaviour
  without advancing the frontier; it retains the prior frontier revision and
  digest byte for byte.

## 7. Sources

- `plugins/janus/harness/src/JanusHarness.sol` (gates; lines 94-130 the two
  gate-1 checks, 107 and 112 the intention comments).
- `plugins/janus/harness/test/WildcatConformance.t.sol` (lines 136, 148,
  171, 184, 223-224, 242) and `test/HostileHooks.t.sol` (lines 20, 55, 88,
  97-98).
- `plugins/janus/harness/manifests/wildcat-open-term.json` (deposit
  threshold lines 8-24) and `harness/schemas/hook-manifest.schema.json`.
- `plugins/janus/harness/src/HostAdapter.sol`,
  `src/wildcat/WildcatHostAdapter.sol` (categoryOf lines 52-58),
  `src/wildcat/HonestAccessHook.sol`, `src/wildcat/WildcatHostModel.sol`,
  `src/hostile/HostileHooks.sol`, `src/StateDeltaRecorder.sol`,
  `src/Vm.sol`.
- `plugins/janus/scripts/janus.py` (validator rules lines 33-208) and
  `plugins/janus/tests/`.
- `plugins/janus/skills/janus/EVOLUTION.md` and `SKILL.md`;
  `plugins/hexaemeron/skills/VERSIONING.md`.
- `audit/AUDIT.md` lines 4531-4790 (the two janus runs), read directly;
  whole-set synopsis check exit 0 recorded in section 2.
- Task issue wildcat-finance/skills#329 and the wave-atlas review note of
  26 Aug 2026 quoted there.
- `docs/janus-suite/study.md` and `runbook.md`, the anchor specification the
  `EVOLUTION.md` baseline row cites.
- Merged PRs #723, #722 (prose-only, plugins/janus), #279 (the suite).
- Foundry cheatcode reference for `parseJson*` and `keyExistsJson`; Wildcat
  v2.5 sources at anchor commit `9716e78` as cited in the host model.

## 8. Signals, and the questions behind them

None beyond what already ships, and here is why: the suite is invoked from a
terminal by a developer or CI, never unattended, so there is no three-in-the-
morning question ([ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md)
owns what a signal must carry, and its contract is for things that run
unattended). The questions that do get asked afterwards, "which manifest,
adapter, and search produced this verdict", are already answered by the
findings interchange file (`host`, `manifest`, `sequences`, findings), and
this run does not change that surface. A resolution refusal is a loud test
abort with a named error, which is the visibility a terminal run needs.

## 9. Boundaries, per capability

One boundary exists and none opens
([phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary
list and the controls). The manifest JSON is repo-local input read through
Foundry's scoped filesystem cheatcode; `fs_permissions` stays read-only over
`./manifests` and `./examples` and read-write over `./out`, `ffi` stays
off, and no network, subprocess, secret, or new dependency appears. What is
worth taking at the manifest boundary is a permit the author did not write;
the controls that close it are the existing validator (wildcard refusal
J009, enum enforcement J015, presence rules) plus this run's fail-closed
resolution: an unresolvable symbol aborts rather than widening or narrowing
a set. The widened `Vm.sol` adds parsing declarations only, no `ffi` or
environment surface. The Python validator and reporter are untouched.

## 10. The budget, or its absence

None, and here is why: the wish makes no performance claim, and the whole
harness suite completes in well under a second today (24 tests in about 91
ms wall time at the starting SHA). Manifest parsing per conformance test
adds milliseconds. If a budget were ever wanted, the measuring command is
`cd plugins/janus/harness && forge test`, timed the same way before and
after; [metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns what a
budget carries and how it is checked.

## 11. The fail-closed posture

What stops the run: a manifest that fails `janus.py validate`; a driven
action with no matching threshold; a symbol the adapter cannot resolve or
that resolves to the zero address; a recording misuse (`RecordingNotStarted`
and `RecordingAlreadyStarted` already revert); a conformance run that drove
nothing (`NoSequencesExercised`). Each aborts the test with a named error;
none returns a default set. The refusal test in section 1 pins the most
important one: the shipped example's own disagreement class must surface as
a failed gate, never as a quiet pass.

Guard convention, per
[elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md), which owns the
triage order and the guard rule: every defect fixed during this run lands
with a test that fails without the fix. The omitted-entry refusal test is
exactly such a guard for the disagreement this wish names, and the
fail-closed resolution test guards the unresolvable-symbol path the same
way.

## 12. Decisions and their homes

[hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which
decisions earn a record and where each lives. Three here are expensive to
reverse, because the second-adapter frontier job will consume them:

- The symbol grammar: the account symbol is the text before the first `.`;
  suffixes are documentation; scope `hook`/`host` resolve through the
  adapter, scope `external` resolves the slot prefix. Home: the
  `description` fields of `harness/schemas/hook-manifest.schema.json` (the
  format contract every adapter reads) and the `ManifestReader.sol` header
  comment.
- Account-granularity enforcement: gates compare written accounts and call
  targets, never slot expressions or function names. Home: the same schema
  descriptions, plus the gate comments in `JanusHarness.sol` rewritten so
  "the manifest lists" describes the mechanism it now is.
- The staticcall reading: a `staticcall` entry admits no state-changing
  call. Home: the schema `call.kind` description and the reader comment.

The honest hook's provider-backed path is cheaper to reverse (one example
contract) and is recorded in the `EVOLUTION.md` generation row's change text
and the `HonestAccessHook.sol` comment. The generation row itself is the
run's durable record that from `janus-v0.2.0` the gates consult the
manifest.

## Decomposition and build order

One capability, one study; the table is decomposition signal for the
runbook, not separate studies.

| Module id | Responsibility | Depends on |
| --- | --- | --- |
| resolution-core | `Vm.sol` widening (`keyExistsJson`), `ManifestReader.sol`: threshold lookup by action, symbol grammar, `ResolvedThreshold`, fail-closed errors | none |
| adapter-resolution | `HostAdapter.resolveAccount`, the Wildcat name table, `MockRoleProvider`, adapter wiring | resolution-core |
| gate-rewiring | conformance tests build sets from resolution; per-action gas budgets; provider-backed honest path; engine-unit tests stay explicit | adapter-resolution |
| disagreement-proof | fixture manifest with the omitted entry, refusal test, permit test, fail-closed test, hostile-set regression run | gate-rewiring |
| ledger-prose | `EVOLUTION.md` generation row, `SKILL.md` 0.2.0 and prose reconcile, README and schema text, imprimatur over shipped documents | disagreement-proof |

Build order: resolution-core, adapter-resolution, gate-rewiring,
disagreement-proof, ledger-prose. A scaffold step precedes them (commit the
study and runbook, suites green at entry) and a final step demonstrates the
demo path from section 1.

Boundaries the steps hold: always run both suites (`forge test`; `python3 -m
unittest discover -s tests`) plus `janus.py validate manifests/*.json`
before a commit, and the imprimatur lint on every shipped document. Ask
first before widening `fs_permissions`, adding any dependency, changing the
manifest schema's required shape, or touching CI. Never weaken a gate to
pass a hostile hook, never commit a hostile fixture its gate does not catch,
never edit the held `Next Fiat job` or the frontier digest, never claim a
command ran when it did not.
