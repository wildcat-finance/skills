---
name: janus
description: >
  Check a contract hook at the threshold it controls: what it may observe and
  change before a host action, what it may change after, and what it must never
  touch. Use when someone has a host protocol that calls hooks and wants to
  state and enforce the permitted effects, when reviewing a new hook against a
  host's economic contract rather than only its ABI, or when a hook must be
  shown safe on its exit and revert paths, not only its entry. Do not use it to
  fuzz one repository for generic Solidity defects; that is fizz. Never report a
  hook as conformant on a delta the recorder did not fully capture.
metadata:
  version: "0.1.0"
---

# Janus

## Frontier

Janus owns the hook-conformance frontier, not Hexaemeron's delivery or Solidity
frontier. Its version, held target, next job, and maturity state live in
[EVOLUTION.md](EVOLUTION.md). Do not recommend or run another frontier pass
after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Janus checks a contract hook at the host threshold it crosses: the observations and changes the host permits before and after the action, plus the state it must never touch.

**Current frontier.** Janus ships the Wildcat v2.5 host adapter and its seven gates against modeled hooks, and no second host adapter yet shows the manifest format holds for another callback model.
<!-- marketplace-context:end -->

Pandects supplies economic laws when the host transition needs them. Hermes
measures gas changes, and the Pashov suite audits the contracts. Janus
alone owns the declared hook-effect boundary. Conformance to one manifest is
not a whole-protocol security verdict.

Janus is named for the Roman god of gates and passages, shown looking in both
directions. A hook sits on exactly that boundary and inspects or alters an
action as it enters and leaves its host. An interface says which function runs.
It does not say whether the hook may move value, write host state, consume all
remaining gas, change an authorisation result, or leave a user unable to exit.
That policy is otherwise spread across implementation code, comments, and the
assumptions of whoever wrote the first hook, so a new module can satisfy the
ABI and still break the host's economic contract.

## What it is

A host adapter exposes a host's actions, the state that matters, and its
economic roles. A hook manifest declares, in JSON checked against a schema:

- the entry points and the host actions each threshold runs around;
- the calls and callbacks the hook may make;
- the host, hook, and external storage it may change;
- the assets and recipients it may cause to move;
- the required behaviour on hook revert, host revert, and partial batch failure;
- the gas budget, and whether failure is fail-open or fail-closed;
- the liveness conditions for withdrawal, uninstall, and emergency paths.

A stateful Foundry harness drives ordinary and hostile sequences through the
adapter, records the real storage writes, call targets, value movements, and
gas across each threshold, and compares the observed delta against the manifest.
A deterministic unit mode runs the same checks over fixed sequences.

## The seven gates

1. Permitted effects are enumerated. An omitted storage write, call target, or
   value movement is forbidden, not implicitly accepted.
2. Value conservation is independent of return values. The harness checks
   balances and claims even when every call reports success.
3. Exit gets a liveness property. Credential expiry, provider removal, sanctions
   changes, and hook failure are tested on the exit path, not only on entry.
4. Revert behaviour is part of conformance. State and value after nested or
   partial failure must match the host's declared rollback rule.
5. Gas grief is exercised. The suite includes hooks that consume gas, expand
   return data, and create expensive callback paths.
6. Re-entry crosses actions. Tests enter a different host action from a
   callback, not only the function that invoked the hook.
7. A host adapter limits every result. Passing the Wildcat suite makes no claim
   about an ERC-7579 account or another protocol's callback model.

## What ships

- the hook-manifest JSON schema and a stdlib Python validator;
- the Solidity host-adapter interface and the state-delta recorder;
- the stateful Foundry harness and the deterministic unit mode;
- five hostile reference hooks: callback re-entry, gas grief, value redirection,
  storage mutation, and stale authorisation;
- the Wildcat host adapter, a faithful model of the v2.5 market-to-hook seam
  with an honest hook that passes every applicable gate; and
- human and SARIF reports linking each violation to a manifest rule and a trace.

## Run it

The harness is a Foundry project under `harness/` with no external Solidity
dependency; it declares the minimal cheatcode interface it needs in
`harness/src/Vm.sol`. The validator and reporter sit in one stdlib Python
file, `scripts/janus.py`.

```text
cd harness && forge build && forge test -vv
python3 ../scripts/janus.py validate manifests/*.json
python3 ../scripts/janus.py report --findings ../examples/findings.sample.json \
  --md report.md --sarif report.sarif
```

Running the suite against a host adapter compiles and executes that host's
modeled code in a local EVM. Treat a target repository as the user's, and obey
its own instructions before writing anything into it.

## What it refuses

- No conformance verdict on an incompletely recorded delta. An effect the
  recorder cannot classify is a violation, not an ignored unknown.
- No gate weakened to let a hostile hook pass, and no hostile reference hook
  committed that its owning gate does not catch.
- No exit liveness reported as a proof. A bounded run holds a property over the
  sequences it drove; it does not prove an exit always completes.
- No claim that a hook is safe. The suite says a hook stayed inside a declared
  boundary under a described search, for one host adapter.
- No cross-host claim. Passing one adapter's suite says nothing about another
  host's callback model.

If a build, a test, a validation, or a report did not run, say so plainly and
do not describe its result.

## Promise Machine contract

### janus-manifest-validation

- Promise: A successful `janus.py validate` establishes that each named hook manifest satisfies the shipped schema and enumerates the threshold, effects, rollback, gas and liveness fields the format requires.
- Evidence: The exact manifest bytes, shipped JSON schema, stdlib validator diagnostics and zero exit status.
- Evidence classes: checked
- Boundary: Schema acceptance does not establish that a hook obeys the manifest, that the manifest matches a host, or that its permitted effects are safe.
- Authorises: Use of the validated manifest as input to the matching host-adapter conformance harness.
- Consequence: 1
- Refuses: Running or reporting conformance from a malformed, incomplete, escaped or schema-unknown manifest.
- Recovery: Repair the named manifest field, validate the complete manifest set again and then restart the harness run.
- Exceptions: none

### janus-bounded-conformance

- Promise: A green harness run establishes that observed hook behaviour stayed within the validated manifest for the named host adapter, manifest revision, recorder coverage and bounded deterministic or stateful search.
- Evidence: The validated manifest, adapter identity, compiled harness, search configuration, complete recorded storage, call, value and gas deltas, hostile-hook guards and passing Foundry results.
- Evidence classes: checked, measured, recorded
- Boundary: The result is bounded conformance, not hook safety, complete exit liveness, coverage of unrecorded effects, another adapter or every possible execution.
- Authorises: Reporting the exact hook and adapter as conformant under the recorded search and using that bounded result in an authorised security or release decision.
- Consequence: 3
- Refuses: A verdict on an unknown delta, absent hostile-hook guard, failed gate, incomplete recorder, unnamed search or cross-host generalisation.
- Recovery: Inspect the violating trace or unknown effect, repair the hook, manifest, adapter or recorder without weakening a gate and rerun the full bounded search.
- Exceptions: none

### janus-report-rendering

- Promise: A successful `janus.py report` renders the supplied finding records into Markdown and SARIF without adding, removing or strengthening a conformance result.
- Evidence: The exact findings JSON, deterministic reporter output, linked manifest rule and trace for each violation and successful render status.
- Evidence classes: recorded, checked, recomputed
- Boundary: Rendering establishes format and trace linkage only; it does not validate a manifest, execute a harness, complete a recorder or create a conformance verdict.
- Authorises: Publication or hand-off of the rendered report only with the originating harness scope and result intact.
- Consequence: 1
- Refuses: Reporting an absent run, dropping a violation, changing adapter scope or presenting a rendered sample as observed conformance evidence.
- Recovery: Restore the originating findings record, rerun the reporter and attach the validated manifest and harness receipt separately.
- Exceptions: none
