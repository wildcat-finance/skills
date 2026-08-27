---
name: hermes
description: Optimise Solidity gas usage with an executable, fail-closed Foundry loop that measures savings, re-runs behaviour tests, checks storage layouts and method identifiers, and demands targeted differential or property evidence for state-sensitive unchecked arithmetic. Every candidate names a rule from a pinned corpus of 120 gas rules and 28 rejected ones, and the harness refuses a rule outside the target's compiler, fork or pipeline scope. Use for Solidity gas work, Forge snapshot reductions, gas-report reviews, storage packing, unchecked arithmetic, or any proposed EVM gas-saving change.
metadata:
  version: "0.1.1"
---

# hermes gas optimiser

## Frontier

Hermes owns its own gas-optimisation evidence frontier, not Hexaemeron's delivery or
Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run
another frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Hermes measures one named Solidity gas optimisation class at a time and rejects the candidate unless every Foundry, behaviour, layout, selector, and arithmetic gate clears.

**Current frontier.** Hermes's twelve optimisation classes name 62 of the corpus's 120 rules, so 58 documented rules cannot be selected as candidates.
<!-- marketplace-context:end -->

Hermes alone owns Solidity gas optimisation. Metron handles measured
performance in every other unit. Pandects can supply economic laws a candidate
must preserve, Janus can constrain hook effects, and the Pashov suite can audit
the resulting contracts. None of them can replace Hermes's sealed baseline or
accept a gas candidate on its behalf.

The ideas are cheap. The evidence is the job.

Use `scripts/hermes.py` for every run. It owns the order, seals the baseline, writes the evidence, and exits non-zero at the first bad gate. Every candidate names a rule from [references/gas-rule-corpus.json](references/gas-rule-corpus.json), the pinned corpus of 120 rules, 28 rejected universal rules and 40 citations transcribed from one source document. Use [references/optimisation-catalogue.md](references/optimisation-catalogue.md) to read the twelve classes those rules map onto.

Check the corpus before a run and read what it holds:

```bash
python3 "$HERMES_PY" corpus --validate
python3 "$HERMES_PY" corpus --validate --json
```

62 of the 120 rules name a class and can be selected. The other 58 constrain how a run is conducted, or they are architecture; the harness refuses them as candidates and says so rather than measuring something they do not describe.

## Day to day

**Developers.** A gas change shaves a few hundred units off a hot path and nobody can say whether behaviour moved with it. Run Hermes on that one optimisation class and the review arrives with the snapshot diff, both fuzz passes, the storage layout comparison and a `result.json`, rather than a number and an assurance.

**Security and audit.** A gas change arrives from outside the team. Instead of reading it for intent, put it through Gate 5 to see whether any protected contract's storage layout or method identifiers moved, and Gate 6 for unchecked arithmetic that reaches persistent state.

## Before touching source

1. Work from the Foundry root. If the repository keeps `foundry.toml` under `build/`, pass `build/` as `--repo`.
2. Read the repository instructions and satisfy its issue or branch rules before writing.
3. Start from a clean Git tree. Finish unrelated work first.
4. Pin one fuzz seed for the run. Keep any fork-test exclusions identical through Gates 1 to 4.
5. Re-derive the layout set. Search for proxies, `delegatecall`, clones, factories, hooks, role providers, and contracts called by them. Treat doubt as frozen layout.
6. Name the intended gas measurements before editing. Each `--gas-target` is a regular expression and must contain a measured saving.

Set `HERMES_PY` to this skill's `scripts/hermes.py` path. Keep the run directory printed by Gate 1; every later command uses it.

## Gate 1: seal a green baseline

List every hook, role provider, proxied implementation, facet, factory-sensitive contract, and other frozen layout with `--protected-contract`. Use a qualified `path:Contract` identifier when names collide.

```bash
python3 "$HERMES_PY" baseline \
  --repo "<foundry-root>" \
  --fuzz-seed 0x5EED \
  --no-match-path "test/Fork.t.sol" \
  --protected-contract "Market=src/Market.sol:Market" \
  --protected-contract "Hooks=src/Hooks.sol:Hooks"
```

Repeat `--no-match-path` and `--protected-contract` as needed. Omit exclusions that the repository does not need.

If no frozen contract is in scope, say so explicitly:

```bash
python3 "$HERMES_PY" baseline \
  --repo "<foundry-root>" \
  --fuzz-seed 0x5EED \
  --assert-no-protected-contracts
```

Add `--layout-contract "Label=path:Contract"` for a non-frozen contract whose layout still needs recording. This is useful for a deliberate packing change.

Gate 1 runs `forge snapshot` and then `forge test`, in that order. It records the snapshot, green test result, Forge version, canonical Foundry config, Git revision, Solidity sources, storage layouts, method identifiers, and the rule corpus with its digest. A corpus that fails its own schema ends the run here, so a candidate is never judged under advice nobody checked. A dirty tree, red suite, missing snapshot, failed inspect, or invalid JSON ends the run.

## Gate 2: name a rule and make one class of change

Every `verify` names one corpus rule with `--rule`. The rule decides the class, so a declared
`--optimisation-class` that disagrees with it is refused. Gate 2 refuses before Gate 3
spends a Forge run, and `result.json` carries a `refusal` field naming which condition failed:

- `corpus/unknown-rule`: no rule of that id
- `corpus/myth-selected`: a rejected universal rule named as a candidate, answered with its correction
- `corpus/myth-cited`: a rationale or obligation answer citing a rejected rule as its justification
- `corpus/rule-names-no-class`: a rule that constrains the run or is architecture, so no candidate implements it
- `corpus/class-disagreement`: the declared class is not the rule's class
- `corpus/out-of-scope`: the target's compiler, fork or pipeline is outside the rule's declared scope
- `corpus/scope-unresolved`: the target pins no readable `solc`, or names a fork the corpus does not order
- `corpus/obligation-unanswered`: an obligation the rule's own statement makes has no substantive answer
- `corpus/obligation-malformed`: an `--obligation` argument is not `<n>=<answer>`, or names an index the rule lacks
- `corpus/digest-moved`: the corpus changed after the baseline sealed it
- `corpus/invalid`: the corpus does not pass its own schema

Answer each of the rule's obligations with `--obligation "<n>=<answer>"`, one per obligation, indexed
from one. Those answers are recorded judgement rather than measurement, and `result.json` marks them
as such. The six gates below do not move because of them.

Then choose that rule's class and make only that kind of source change. Do not mix cleanup, compiler settings, test edits, or a second gas idea into the candidate.

Review `candidate.solidity.diff` before attesting. The harness rejects Solidity file additions or removals, test-source edits, an empty candidate, added `unchecked` outside `unchecked-arithmetic`, and added assembly outside `assembly`. The attestation remains a judgement: read the diff and confirm that every hunk belongs to the declared class.

If the required property test is absent, add it in a preparatory change, get green, and take a fresh baseline. The optimisation candidate uses the existing fuzz suite rather than changing its own oracle.

## Gates 3 to 6: verify the candidate

For an ordinary candidate:

```bash
python3 "$HERMES_PY" verify \
  --run-dir "<run-dir>" \
  --rule STO-09 \
  --obligation "1=The cache is loaded after the last write and every use sits inside one call frame." \
  --optimisation-class storage-load-caching \
  --attest-single-class \
  --gas-target 'LedgerTest:test_update' \
  --gas-target 'LedgerTest:test_batch' \
  --no-sensitive-unchecked
```

For unchecked arithmetic outside state-sensitive code, add a real explanation:

```bash
  --no-sensitive-unchecked \
  --non-sensitive-rationale "The loop counter is bounded by the in-memory array length and cannot affect persistent state, asset balances, external call parameters, or rounding."
```

For unchecked arithmetic that can affect persistent state, asset accounting, external calls, permissions, or rounding, run the existing targeted differential or property test:

```bash
python3 "$HERMES_PY" verify \
  --run-dir "<run-dir>" \
  --rule CTL-05 \
  --obligation "1=Every intermediate is bounded by the array length checked at the loop head." \
  --obligation "2=The unchecked region is three lines and the bound is stated beside it." \
  --optimisation-class unchecked-arithmetic \
  --attest-single-class \
  --gas-target 'LedgerTest:test_update' \
  --sensitive-unchecked \
  --targeted-match-path 'test/StateDifferential.t.sol' \
  --targeted-match-test 'testFuzz_diff_stateTransition' \
  --property-proof "Compare the checked reference and candidate across the complete reachable input domain; assert equal state transitions and equal overflow reverts at the arithmetic boundaries."
```

### Gate 3: quantify the gas change

Run `forge snapshot --diff <baseline>` and capture a candidate snapshot. Reject a positive deterministic delta anywhere, a changed measurement set, a target with no match, or a target with no saving. Then run `forge test --gas-report`.

Historical Foundry snapshots also contain fuzz statistics whose sampled inputs can change when the compiled bytecode changes. Hermes records their baseline and candidate means and medians, but does not call those aggregates a gas regression or saving. It still rejects a changed fuzz-test set or run count. Foundry `invariant_callSummary()` rows are stricter: their test set, run count, call count, and revert count must stay identical.

### Gate 4: prove behaviour is unchanged

Run the full `forge test` suite with the pinned seed, followed by a full unpinned run. Any failure rejects the candidate.

### Gate 5: preserve layouts and selectors

Re-run `forge inspect <C> storageLayout --json --force` and `methodIdentifiers` for every recorded contract. The layout comparison canonicalises solc's compilation-local AST IDs, while retaining raw inspector output in evidence; it hard-aborts on any structural protected-layout difference or method-selector difference. A declared layout change is allowed only for an unprotected contract under the rules below.

### Gate 6: prove state-sensitive unchecked arithmetic

When `--sensitive-unchecked` applies, run the named targeted differential or property test and record its oracle. Otherwise, record why the candidate does not introduce or rely on state-sensitive unchecked arithmetic.

## Deliberate layout change outside the frozen set

Only `storage-packing` and `constants-immutables` may declare one. The contract must have been listed with `--layout-contract`, never `--protected-contract`.

```bash
  --allow-unprotected-layout-change \
  --layout-change-rationale "No proxy, hook, role provider, delegate call, deployed factory instance, storage-reading test, or indexer consumes this layout."
```

Hermes records the diff. It rejects an undeclared difference, a declared difference that never occurred, or any difference on the frozen set.

## State-sensitive arithmetic property standard

Before accepting the Gate 6 result, inspect the named test and confirm all of the following:

- Exercise the changed unchecked operation rather than a neighbouring helper.
- Compare against the original checked implementation or enforce an equivalent property oracle.
- Preserve checked overflow and underflow behaviour; a wrapped result cannot stand in for a reference revert.
- Cover applicable `0`, `1`, maxima, time deltas, input bounds, balance bounds, rounding boundaries, plus the exact safe and unsafe arithmetic edges.
- Avoid a `bound()` or assumption that removes the dangerous region.
- Keep the existing fuzz or invariant configuration from the named test path, such as `test/Fuzz.t.sol`, with the baseline seed recorded in the command.

A comment explaining why arithmetic looks safe is useful review context. It is not Gate 6 evidence.

## Accept, reject, repeat

Exit `0` plus `result.json` status `accepted` is the acceptance signal. Exit codes identify the rejected gate: `10`, `20`, `30`, `40`, `50`, or `60`. `result.json`, the command logs, gas comparison, source diff, layouts, and method maps stay together in the run directory.

Stop after any rejection. Do not tweak tolerances, alter the target set after seeing the result, weaken a test, or add another optimisation to cover the loss. Remove only the candidate changes, return to the last green state, and begin again at Gate 1.

After acceptance, promote the candidate snapshot deliberately:

```bash
python3 "$HERMES_PY" promote --run-dir "<run-dir>"
```

That accepted state becomes the baseline for the next class. Never run two classes through one Hermes record.

## Refuse shortcuts

- If `forge` is unavailable, report that no gas result can be measured.
- If the baseline is red or dirty, fix that in separate work.
- If someone asks to skip the layout diff, keep the gate.
- If someone asks to bundle changes, run them in sequence.
- If the gas saving cannot be quantified, reject it.
- If a state-sensitive unchecked change lacks the targeted proof, reject it whatever the gas number says.
- If the candidate implements no corpus rule, add the rule to the corpus in separate work first. There is no flag that skips the requirement.

## Promise Machine contract

### hermes-sealed-baseline

- Promise: A successful `baseline` seals a green, clean Foundry baseline with the named gas measurements, configuration, seed, source revision, protected layouts, method identifiers and the validated rule corpus with its digest.
- Evidence: The run directory, baseline snapshot, full test log, Foundry version, canonical configuration, Git and source records, storage layouts and method maps.
- Evidence classes: checked, measured, recorded
- Boundary: The baseline describes one repository state and environment; it does not establish that a later candidate preserves behaviour or improves gas.
- Authorises: Evaluation of one declared optimisation class against the sealed baseline and fixed measurement set.
- Consequence: 1
- Refuses: Beginning a candidate comparison from a dirty tree, red suite, missing snapshot, unresolved protected set, changed exclusions or a corpus that fails its own schema.
- Recovery: Restore a clean green repository, re-derive the protected and measured sets and take a fresh baseline.
- Exceptions: none

### hermes-corpus-selection

- Promise: A successful Gate 2 corpus selection establishes that the named rule exists in the corpus the baseline sealed, that it names the declared optimisation class, that the target's pinned compiler, fork and pipeline fall inside the rule's declared scope, and that every obligation the rule's own statement makes carries a recorded answer.
- Evidence: The sealed corpus digest, the corpus schema result, the selected rule with its grade and automation level, the resolved compiler, fork and pipeline read from the sealed Foundry configuration, the paired obligation answers and the `refusal` field on any rejection.
- Evidence classes: checked, recorded
- Boundary: Selection establishes that the candidate is in scope for reviewed advice and that its obligations were answered; it does not establish that the answers are correct, that the optimisation saves gas, or that behaviour is preserved. Obligation answers are recorded judgement rather than measurement and the six gates do not move because of them.
- Authorises: Measurement of that one candidate against the sealed baseline under the named rule, with the rule id and corpus digest carried into the accepted record.
- Consequence: 1
- Refuses: An unknown rule, a rejected universal rule named as a candidate or cited as a justification, a rule that names no class, a declared class the rule does not name, a compiler, fork or pipeline outside the declared scope, a scope that cannot be resolved from the sealed configuration, an unanswered or malformed obligation, a corpus that moved after the baseline, and a corpus that fails its own schema.
- Recovery: Select the rule the candidate actually implements, answer each of its obligations, pin the target's `solc_version` and `evm_version` where the scope cannot be resolved, or add the missing rule to the corpus in separate work before starting a new run.
- Exceptions: none

### hermes-candidate-acceptance

- Promise: A successful `verify` with `result.json` status `accepted` establishes measured savings for every named target, no deterministic regression, passing pinned and unpinned behaviour suites, preserved protected layouts and selectors, and the required unchecked-arithmetic evidence for one declared class, under one named corpus rule whose scope the target satisfies.
- Evidence: The sealed baseline, candidate Solidity diff, gas snapshot comparison, gas report, both full test runs, layout and selector comparisons, targeted property result when required, the corpus digest with the selected rule and its answered obligations, and accepted `result.json`.
- Evidence classes: checked, measured, recomputed, recorded
- Boundary: Acceptance covers one candidate, repository state, toolchain, measurement set and optimisation class; it is not a general security proof or permission to combine another change.
- Authorises: Retaining and reviewing that exact gas candidate as a repository mutation with its complete evidence directory.
- Consequence: 2
- Refuses: Acceptance after any gate fails, a target lacks a saving, the measurement set moves, a protected interface changes, sensitive unchecked arithmetic lacks its named property evidence, or the candidate names no corpus rule.
- Recovery: Remove only the rejected candidate, return to the sealed green state, correct prerequisite tests separately and start a new Hermes run.
- Exceptions: none

### hermes-baseline-promotion

- Promise: A successful `promote` advances the Hermes baseline only to the exact candidate already accepted by the same run record.
- Evidence: The accepted `result.json`, matching run directory, candidate snapshot and promotion command result.
- Evidence classes: checked, recorded
- Boundary: Promotion changes the local measurement baseline; it does not publish code, accept another optimisation class or validate unrecorded edits.
- Authorises: Using the promoted accepted snapshot as the baseline for the next separately declared optimisation class.
- Consequence: 2
- Refuses: Promotion of a rejected, changed, missing or differently scoped candidate record.
- Recovery: Restore the accepted run directory or take a fresh baseline from the intended repository state.
- Exceptions: none
