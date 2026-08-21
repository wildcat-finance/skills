# Procrustes: a fail-closed EIP-170 code-size optimiser beside Hermes

Assuming, unless corrected:

1. Procrustes ships as a second canonical-directory skill inside the existing
   `hermes` plugin, at `plugins/hermes/skills/procrustes/`, with its own
   `SKILL.md` and `EVOLUTION.md` and no marketplace-context block, matching how
   the thirteen Hexaemeron skills sit beside Fiat.
2. Foundry, not Hardhat. Targets carry `foundry.toml`; `forge 1.7.1` is present
   here and unit tests use a fake `forge` on `PATH`, as `test_hermes.py` does.
3. Python 3.11 and stdlib `unittest`, matching every other harness in the repo.
4. The run starts from `main` at `3c061c2e15df085cf300220250b421bbd03f664c`.
5. Hermes's harness is not edited. Procrustes imports from it and pins what it
   imports.
6. Solidity 0.8.x. Size classes are declared per run, one class per candidate,
   as Hermes declares gas classes.

## 1. Problem statement

A contract whose deployed runtime code exceeds 24576 bytes cannot be deployed.
EIP-170 makes the limit a consensus rule, so the failure arrives at deployment
rather than at compile time, and the moves that buy bytes back are not the moves
Hermes exists to make. Hermes measures gas and rejects any candidate whose
declared target shows no gas saving; most size reductions cost gas, so Hermes
refuses them by construction rather than by judgement.

Procrustes measures deployed bytecode instead. It seals a baseline of per-contract
runtime and initcode sizes and takes one declared size class at a time. A
candidate is accepted only when the bytes fell, the behaviour suites stayed
green, the protected layouts and selectors did not move, and the diff did not buy
its reduction by removing a check or by relocating code behind `delegatecall`
without saying so.

A working prototype means all of these hold:

- `python3 plugins/hermes/skills/procrustes/scripts/test_procrustes.py` exits 0.
- `python3 -m unittest discover -s tests` stays green over the added skill.
- `python3 scripts/promise_machine.py check` exits 0 with the Procrustes
  declarations counted in its inventory.
- On a fixture Foundry project held over the limit, one recorded run accepts a
  size class that brings the contract under 24576 bytes, and a second recorded
  run refuses a candidate that reaches the same number by deleting a `require`.

The last item is the demo path. A harness that cannot refuse the cheating
candidate has not been shown to work.

## 2. Prior art

**In this repository.** `plugins/hermes/skills/hermes/scripts/hermes.py` is 1138
lines carrying the whole evidence discipline Procrustes needs and does not need
to reinvent: `run_command`, `canonical_json`, `canonical_storage_layout`,
`inspect_layout`, `inspect_methods`, `snapshot_sources`, `source_diff`,
`artifact_hashes` and `mark_failure`. Its gates are Gate 1 baseline, Gates 2 to 6
in `verify`, then `promote` and `status`. `references/optimisation-catalogue.md`
already records the boundary this skill sits on: compiler settings are their own
experiment, and it names `forge build --sizes` as the place deployed size gets
recorded. Nobody built the loop around that sentence.

The last two merged pull requests touching the plugin are
[#291](https://github.com/wildcat-finance/skills/pull/291) and
[#287](https://github.com/wildcat-finance/skills/pull/287). The first bound
digest-backed runtime maps for all 29 promises at consequence 2 and 3, and
published the fourteen plugins at patch package versions. The second added the 43
standalone Promise Machine declarations and made the `contracts` component guard
the exact repository promise-id sets. Neither left work carried forward that
touches size. What they do leave is the cost of adding a governed skill here:

- `tests/test_evolution_contract.py` requires an `EVOLUTION.md` beside every
  governed `SKILL.md`, frontmatter matching the ledger version, a frontier digest
  over the exact `{status}|{revision}|{frontier}|{next job}` line, and a citation
  of the versioning contract.
- `tests/test_portable_skills.py` requires the skill name to match its directory,
  be unique across plugins, and be resolved by `plugins/hermes/AGENTS.md`, which
  currently states that Hermes is one Agent Skill and must become a selection
  table.
- `scripts/promise_machine.py check` requires declarations for the new skill and
  guards the expected id set; a promise at consequence 2 or higher also needs a
  runtime map in `tests/promise_machine_coverage.json`, whose `runtime` list holds
  29 ids and whose `rows` list holds 66.
- `tests/test_marketplace_prose.py` publishes one frontier per plugin across every
  file carrying a marketplace-context block. A second frontier inside the plugin
  therefore cannot be published in such a block, which is why item 1 of the
  assumptions ships Procrustes without one.
- `tests/test_shipped_prose_lints.py` requires every shipped document to score
  clean under Imprimatur, and `tests/test_boundary_currency.py` requires the
  committed Horos boundary to match a fresh scan of the new tree.

`audit/AUDIT.md` holds no Hermes round: the plugin's gates have never been through
this repository's audit loop, so no earlier round's accepted lead constrains this
design and none can be cited as having cleared one.

**Outside.** EIP-170 fixes the deployed-code limit at 24576 bytes. EIP-3860 caps
initcode at twice that, 49152 bytes, and charges 2 gas per initcode word, so a
constructor-heavy contract can pass one limit and fail the other; `forge build
--sizes` prints both columns, which is why the baseline records both. Solidity's
own size levers are the optimizer run count, `via_ir`, the metadata trailer under
`bytecode_hash` and `cbor_metadata`, custom errors in place of revert strings,
external libraries that are linked rather than inlined, and the diamond pattern of
EIP-2535. The last two are the ones that move code behind `delegatecall`.

## 3. Constraints and non-goals

- Starting ref `main` at `3c061c2e15df085cf300220250b421bbd03f664c`; run branch
  `fiat/procrustes-a-fail-closed-eip-170-code-size-optim`.
- Toolchain: Python 3.11 stdlib, `forge 1.7.1`, `git`. No new dependency.
- `hermes.py` is not edited in this run. Hermes holds its own frontier and its
  own held job, and a harness change here would be measured against a moved
  baseline there.
- No marketplace or manifest churn: the plugin set stays at fourteen and the
  plugin's published frontier stays Hermes's.
- Non-goals for the prototype: automatic selection of a size class, automatic
  facet or library extraction, source rewriting of any kind, a baseline
  promotion command, a published live Wildcat evidence bundle, and Hardhat
  targets.
- Deferred: binding an accepted Procrustes run to an Ariadne statement.

## 4. Design options

**A. Import Hermes's helpers, pin what is imported.** `scripts/procrustes.py`
inserts the sibling `hermes` script directory on `sys.path` and imports the
sealing and comparison helpers, adding only the size measurement, the size
comparison and the two new gates. A guard test asserts the imported names and
their signatures, so a later Hermes change breaks a test here rather than a run
in somebody's repository. Trade: Procrustes is coupled to Hermes's internals,
which is a real dependency and is why the guard test is part of the deliverable
rather than an extra.

**B. Extract a shared `foundry_evidence` module.** Both harnesses import it and
neither owns it. Cleanest boundary of the three, and it edits an audited script
whose own frontier job is an unpublished live evidence bundle. That job would then
be measured against a harness this run moved. Trade: correctness of the shared
abstraction bought with a change to Hermes nobody asked for.

**C. Copy what is needed.** Procrustes owns every line it runs and cannot be
broken by a Hermes edit. Trade: two copies of storage-layout canonicalisation,
which is exactly the code a past fix already had to normalise once, in
`7e68d9a`.

**Chosen: A.** It is the cheapest to comprehend, it leaves Hermes's audited
harness and its held job untouched, and its named trade has a mechanical guard.
B is the design to revisit if a third Foundry-evidence skill ever appears, and it
should be revisited then rather than now.

## 5. Risk register seed

The two gates that make this skill more than a byte counter are the check-deletion
gate and the delegatecall-surface gate. A size optimiser that only measures size
will accept a diff that deletes a bounds check, because deleting a bounds check
does make the contract smaller. Procrustes is named for the bed for that reason.

```risk-register
deleted-check | the candidate Solidity diff | a removed require, revert, assert, modifier use or custom-error throw is refused unless the declared class names it and a test proves the revert still occurs
delegatecall-surface | new library links and extracted facets | an added external library or delegatecall site is declared, and the evidence records which contract the bytes moved to
size-accounting | the parse of forge build --sizes | runtime and initcode sizes are read as separate columns and a claimed reduction is recomputed from both the baseline and the candidate artefacts
gas-regression | the gas snapshot taken beside the size measurement | a size win that costs gas records the number and is refused above the declared ceiling
metadata-only-win | foundry.toml bytecode_hash and cbor_metadata | a settings-only reduction is its own class and never shares attribution with a source change
layout-selector-drift | protected and frozen contracts | Hermes's storage-layout and method-identifier comparison runs unchanged and doubt counts as frozen
import-coupling | the helpers imported from hermes.py | a guard test pins the imported names and signatures and fails when either moves
subprocess-input | the argv passed to forge and git | arguments are pinned lists, no shell, and the target path is validated before use
partial-write | the evidence directory during a long build | a killed run leaves no half-written evidence that a later status read would treat as complete
```

## 6. Glossary seeds

- **Runtime code.** The bytes stored at the address after deployment; what EIP-170
  measures.
- **Initcode.** The deployment payload that returns the runtime code; what
  EIP-3860 measures.
- **Size class.** One declared kind of size change, the unit Procrustes measures,
  parallel to a Hermes gas class.
- **Protected contract.** A contract whose storage layout and selectors are frozen
  because a proxy, clone, factory or hook depends on them.
- **Facet.** A contract holding part of another contract's logic, reached by
  `delegatecall`.
- **Metadata trailer.** The CBOR block solc appends after the runtime code.
- **Declared ceiling.** The gas regression a run states it will tolerate before
  measuring.

## 7. Sources

- EIP-170, contract code size limit, 24576 bytes.
- EIP-3860, initcode limit 49152 bytes and per-word initcode gas.
- EIP-2535, the diamond pattern, for the facet route.
- Solidity documentation: optimizer runs, `via_ir`, metadata and `bytecode_hash`.
- Foundry documentation: `forge build --sizes`, `cbor_metadata`.
- `plugins/hermes/skills/hermes/SKILL.md` and `scripts/hermes.py`.
- `plugins/hermes/skills/hermes/references/optimisation-catalogue.md`.
- `plugins/hexaemeron/skills/VERSIONING.md`.
- `tests/` at the repository root, seven contract suites.
- Pull requests #287 and #291.

## 8. Signals, and the questions behind them

Procrustes is invoked from a terminal by somebody watching it, so most of the
on-call surface is absent, and saying so is the answer rather than inventing one.
Two questions survive because a run leaves evidence somebody reads later:

- Which gate refused this candidate, and what number did it measure? Answered by
  `result.json` carrying the gate index, the refusal reason and the per-contract
  byte deltas, written by the same step that exits non-zero.
- Where did the bytes go? Answered by the size comparison record naming every
  contract whose runtime or initcode size moved, including the ones that grew.

There is no alerting surface and no long-running process to page anyone about.
Ephoros owns what those two records must carry.

## 9. Boundaries, per capability

- **Subprocess.** The harness spawns `forge` and `git` in a directory the user
  named. Worth taking because the measurement has no other source. Closed by
  pinned argument lists, no shell, and a validated repository path.
- **Filesystem.** The harness writes an evidence directory and reads target
  sources. Closed by keeping evidence outside the target tree by default and
  refusing a path that escapes it, as Hermes's `is_within` already does.
- **Untrusted target repository.** A target's `foundry.toml` controls `ffi` and
  `fs_permissions`, so running its suite is arbitrary code execution as the
  caller. Procrustes records the resolved config it ran under, and the SKILL.md
  states plainly that an unvetted target belongs in a container. Naming the
  boundary is in scope; sandboxing the caller's machine is not, and pretending
  otherwise would be the more dangerous outcome.
- **No network, no credentials.** The harness fetches nothing and reads no
  secret. Phylax owns the control list for all of the above.

### Boundary tiers

**Always.** Both suites before a commit, meaning the root contract tests and the
new harness tests. The Imprimatur lint on every shipped document. The Horos scan
after files are added, because the committed boundary is guarded against drift.
The recorded size measurement on both sides of a candidate.

**Ask first.** Editing `hermes.py`. Adding a dependency. Changing a storage
layout, a selector or a public ABI in any target. Touching CI. Widening what the
harness is allowed to run in a target repository. Publishing a second frontier in
a marketplace-context block.

**Never.** Commit key material or an RPC credential. Edit a vendored directory.
Delete a failing test, or narrow a gate, to make a suite pass. Accept a candidate
whose reduction comes from a removed check. Claim a gate refused something when
it was never run.

## 10. The budget, or its absence

No performance budget. The wall clock is `forge build` and `forge test` in the
target, which Procrustes does not control and must not tune. The numbers this
skill does hold to are measurements rather than budgets: per-contract runtime and
initcode bytes from `forge build --sizes`, recomputed on both sides of the
candidate. Metron governs any later claim that the harness itself became faster.

## 11. The fail-closed posture

Non-zero exit at the first failed gate, with the failure recorded in the evidence
directory before the process ends, matching Hermes. Acceptance is one signal only:
`result.json` with status `accepted` and exit code 0. Every fix in the audit loop
lands with a guard test named for what it refuses, `test_<gate>_refuses_<case>`,
which fails without the fix. A gate that cannot be demonstrated to refuse its own
bad case is not a gate. Elenchus owns the triage order when a round finds one.

## 12. Decisions and their homes

- The import-rather-than-extract decision of item 4, with the trade named, lives
  in the committed study at `docs/procrustes/study.md`. The skill points at it
  and does not restate it.
- The two new gates and their refusal cases live in `SKILL.md`, because a caller
  needs them before a run rather than after.
- The size-class list lives in `references/size-catalogue.md`, beside Hermes's gas
  catalogue and separate from the gate rules, because the classes will grow and
  the gates should not.
- The frontier and every version step live in `EVOLUTION.md` under the versioning
  contract. Hypomnema owns which of these earns a record and which earns a
  pointer, never both.
