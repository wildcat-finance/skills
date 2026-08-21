---
name: procrustes
description: Cut a Solidity contract to fit EIP-170's deployed-code limit with an executable, fail-closed Foundry loop that measures runtime and initcode bytes, keeps behaviour tests green, holds storage layouts and method identifiers still, and refuses a reduction bought by deleting a check or by moving code behind delegatecall unannounced. Use for contract-size work, EIP-170 or EIP-3860 limit failures, `forge build --sizes` reductions, library or facet extraction for size, and any proposed change whose purpose is smaller deployed bytecode.
metadata:
  version: "0.1.0"
---

# procrustes code-size optimiser

## Frontier

Procrustes owns its own code-size evidence frontier, not Hermes's gas frontier
and not Hexaemeron's delivery frontier. Its version, held target, next job and
maturity state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run
another frontier pass after that ledger becomes mature.

The bed is 24576 bytes. The point of the gates is that the contract fits without
being maimed to get there.

## Where this sits

Procrustes measures deployed bytecode. Hermes measures gas, and rejects any
candidate whose declared target shows no gas saving, so it refuses most size
reductions by construction rather than by judgement. That refusal is correct for
Hermes and useless when the deployment is the thing that fails.

Use Hermes when the number that matters is gas. Use Procrustes when the number
that matters is bytes, and expect the two to disagree: a size win usually costs
gas, which is why a Procrustes run declares the gas regression it will tolerate
before it measures anything.

Pick a candidate class from [references/size-catalogue.md](references/size-catalogue.md).

## What the limits are

EIP-170 caps deployed runtime code at 24576 bytes. EIP-3860 caps the initcode
that returns it at 49152 bytes, and charges gas per initcode word, so a
constructor-heavy contract can sit inside one limit and outside the other.
`forge build --sizes --json` reports both, and Procrustes records both. A run
that quotes one number and calls it "the size" is the first mistake this harness
exists to prevent.

## Before touching source

1. Work from the Foundry root. If the repository keeps `foundry.toml` under
   `build/`, pass `build/` as `--repo`.
2. Start from a clean Git tree with a green suite. Finish unrelated work first.
3. Re-derive the layout set. Search for proxies, `delegatecall`, clones,
   factories, hooks, role providers, and contracts called by them. Treat doubt
   as frozen layout.
4. Name the contracts whose size must fall, before editing. Each
   `--size-target` is a regular expression over compiled contract names and must
   carry a measured reduction.
5. Read the target's `foundry.toml` before running anything. A target controls
   its own `ffi` and `fs_permissions`, so running its suite executes its code as
   you. An unvetted target belongs in a container, and this harness does not put
   it in one.

Set `PROCRUSTES_PY` to this skill's `scripts/procrustes.py` path.

## Gate 1: seal a green baseline

```bash
python3 "$PROCRUSTES_PY" baseline \
  --repo "<foundry-root>" \
  --size-target "^Market$" \
  --fuzz-seed 0x5EED \
  --no-match-path "test/Fork.t.sol" \
  --protected-contract "Market=src/Market.sol:Market"
```

Repeat `--size-target`, `--protected-contract` and `--no-match-path` as needed.
Where no layout is frozen, say so explicitly with
`--assert-no-protected-contracts`; the harness refuses a silent empty set.
`--fuzz-seed` is required: a green suite recorded under a seed nobody pinned is
not comparable to the candidate suite that follows it.

Gate 1 records the per-contract runtime and initcode sizes with both margins,
the declared targets and the contracts each one matched, the resolved Foundry
configuration, the Forge version, the Git revision, every Solidity source, and
the protected storage layouts and method identifiers. Then it runs the suite and
requires it green.

A contract already over a limit is recorded rather than refused. Being over the
limit is why somebody runs this.

Gate 1 refuses a dirty tree, a red suite, a failed or unparsable size report, a
`--size-target` matching no compiled contract, an evidence directory inside the
target or holding somebody else's run, and a missing `foundry.toml`.

Keep the printed run directory. Every later command uses it.

## The imported surface

Procrustes takes its sealing, layout and selector machinery from Hermes rather
than copying it, and `PINNED_HERMES_SURFACE` in `scripts/procrustes.py` names
every helper it takes with the signature it was written against. When a Hermes
change moves one of those, the harness exits 70 and says which name moved,
before it touches a repository. `test_procrustes.py` fails at the same point.

That coupling is deliberate and it is the skill's main structural risk. Do not
work around a drift refusal by loosening the pin: fix the call, or record why
the new signature is compatible and pin the new one.

## Refusals that are not about size

Two refusals exist because a harness that only measures bytes will happily
accept a smaller, weaker contract.

**A deleted check.** Removing a `require`, `revert`, `assert`, modifier
application or custom-error throw does make a contract smaller. The candidate
gates refuse a diff that removes one unless the declared class names it and a
test proves the revert still happens.

**A moved delegatecall surface.** Extracting an external library or splitting
into facets does not delete code; it moves it somewhere the size report no longer
counts. A run must declare the new library link or `delegatecall` site, and the
evidence records which contract the bytes went to.

Both gates ship in the candidate loop, which this version of the skill does not
have yet. The ledger holds that as the next job; do not report a candidate as
accepted until the gates exist.

## Promise Machine contract

### procrustes-sealed-baseline

- Promise: A successful `baseline` seals a green, clean Foundry baseline carrying the per-contract runtime and initcode sizes, the declared size targets and the contracts they matched, the resolved configuration, the source revision, and the protected storage layouts and method identifiers.
- Evidence: The run directory, `sizes.json` with both limits and both margins, the full test log, the Forge version, the canonical Foundry configuration, the Git revision and source manifest, the sealed layouts and method maps, and the pinned Hermes surface the run loaded under.
- Evidence classes: checked, measured, recorded
- Boundary: The baseline describes one repository state and one toolchain. It does not establish that a later candidate preserves behaviour, reduces deployed code, brings any contract inside either limit, or leaves the delegatecall surface where it was.
- Authorises: Comparison of one declared size class against this sealed baseline and its fixed target set.
- Consequence: 1
- Refuses: Sealing from a dirty tree, a red suite, a failed or unparsable size report, a target expression matching no compiled contract, an unresolved protected set, an evidence directory inside the target, or a moved Hermes helper signature.
- Recovery: Restore a clean green repository, re-derive the protected and target sets, and take a fresh baseline into an empty evidence directory.
- Exceptions: none
