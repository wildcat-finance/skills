# Issue 1355: Wildcat V2 protected inventory

This directory holds the protected-contract inventory for the Wildcat V2
Ethereum estate and the evidence behind it. Step 1 of the delivery adds the
inventory, the checker and the profile-invariance evidence. No Hermes Gate 1
is sealed yet; later steps add the fixture, the baselines and the Gate 5
rejections.

## Check it

```sh
python3 scripts/kickoff_hermes_1355.py check
```

The command reads committed files only and starts no subprocess. It exits 0
when all of the following hold:

1. `inventory.json` maps each of the 137 contracts in registry row
   `wildcat-v2-ethereum-mainnet` of `docs/kickoff/1359/targets.json`
   (SHA-256 `417f727d018ecbfa86efb23ea8c9cdfc53d429cf3f4a6285543ae24e89fc40ea`)
   to one of 17 protected types. Each type's registry role, template or lens
   source must match.
2. Each type names its deployed state, anchor, coverage mode and deployed
   compiler profile. The profile must agree with every Sourcify or registry
   record of those settings.
3. The eight registry exclusions are kept unchanged, each with owner and
   reason.
4. `study.md`, `runbook.md` and `design-evidence.json` are byte-identical to
   the receipted run files, and every selection report under `design-reports/`
   matches the digest the design record names.
5. `evidence/profile-invariance.json` records every type's canonical storage
   layout and method map under both profiles, and the two are byte-equal.
6. Nothing under this directory is a symlink, a Solidity source, a Hermes
   `baseline-sources` copy or a private-repository build input.

Each refusal prints the record, the field and the digest that failed.

## Profile invariance

Hermes Gate 1 runs each anchor under its default Foundry profile with the
study's compiler pins. The deployed contracts were built with other optimiser
and via-IR settings. The `profile-invariance` criterion checks that those
settings do not move a storage layout or method map.

For every type, the evidence inspects the contract at its deployed state and,
where different, at its anchor: 28 comparisons over 22 builds in 10 trees.
Each comparison runs `forge inspect <identifier> storageLayout --json` and
`forge inspect <identifier> methodIdentifiers --json` twice. The first run
uses the tree's Gate 1 pins; the second adds `FOUNDRY_SOLC`,
`FOUNDRY_EVM_VERSION`, `FOUNDRY_OPTIMIZER=true`, `FOUNDRY_OPTIMIZER_RUNS` and
`FOUNDRY_VIA_IR` for the deployed profile. Layouts pass through Hermes's
`canonical_storage_layout`. The record keeps the canonical maps themselves,
the `forge config --json` settings each build resolved and the compiler
settings each artefact reports. The checker recomputes every map digest from
the recorded content rather than trusting the stated digest.

The design report is written by:

```sh
python3 scripts/kickoff_hermes_1355.py conformance --criterion profile-invariance \
  --candidate anchor-and-inspect \
  --report .hexaemeron/design-reports/anchor-and-inspect-profile-invariance.json
```

It writes one `protasis-design-report/v1` with value `true` only when every
comparison is byte-equal, refuses an existing report path, and writes nothing
otherwise. The other five conformance criteria refuse by name until the step
that owns their evidence lands.

To reproduce a comparison, check out the tree at its recorded commit with
submodules, then run the two `forge inspect` commands with each build's
recorded `environment` and a separate `FOUNDRY_OUT` and `FOUNDRY_CACHE_PATH`.
The captures used Forge 1.7.1, commit
`4072e48705af9d93e3c0f6e29e93b5e9a40caed8`. The capture script is kept with
the run's files; its SHA-256 is in the record.

## Evidence classes and custody

The registry values are recorded observations, not proofs; Step 2 binds the
code hashes to a verified fixture. Maps for the fee recipient and role
provider come from private repositories. The public tree carries their
layouts, method maps and digests only. Private source, test source and
complete private Hermes directories stay outside Git.

The role provider's registry source commit names the private blob. This
inventory records the public v2-protocol copy at `e1f77540` as its deployed
state, per study section 2. The registry itself is unchanged; that correction
belongs to its owner.
