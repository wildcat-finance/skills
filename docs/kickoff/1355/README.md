# Issue 1355: Wildcat V2 protected inventory

This directory holds the protected-contract inventory for the Wildcat V2
Ethereum estate and the evidence behind it. Step 1 of the delivery adds the
inventory, the checker and the profile-invariance evidence. Step 2 adds the
fixed-block fixture, the preserved release and the owner-handoff table. No
Hermes Gate 1 is sealed yet; later steps add the baselines and the Gate 5
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
6. Nothing under this directory is a symlink, a Solidity source (including
   one carried inside a JSON string or pasted into Markdown as escaped JSON),
   a Hermes `baseline-sources` copy or a private-repository build input.
7. `evidence/fixture.json` names chain 1, block 26006289 and its hash, the
   four capture limits, a passing Lazarus verify and replay, and one row per
   inventory address whose proved code hash equals the inventory's.
8. `evidence/release.json` names a passing Alexandria verify and preserves
   the registry, source-match and chain-observation files and the fixture by
   digest. The checker hashes each named file itself.
9. `evidence/owner-handoffs.json` has one complete row for each of scope,
   registry, source matching, chain observations, fixture, release and
   inventory. Each row names its producer, reviewer and artefact, and the
   artefact's SHA-256 matches its bytes.

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

## Chain evidence

The Lazarus fixture holds, at block 26006289, an EIP-1186 account proof and
the runtime code for each of the 137 inventory addresses, plus one recorded
`eth_getCode` per address so that replay can serve it. The plan declared its
limits before capture: 600 requests, 33,554,432 bytes per component,
67,108,864 bytes in total and 1,800 seconds. The capture used 414 requests,
12,106,815 response bytes and 51.4 seconds. It called `capture_fixture`,
the function behind `lazarus.py capture`, from a script that reads the RPC
URL and bearer from environment variables, because the command-line form
puts the URL in argv. `lazarus.py verify` reports 137 proof-backed accounts,
one header-bound header and 137 recorded responses. Offline replay served all
137 code reads byte-equal to the proof records and answered a request for
another block with miss `-32070`.

The two open `fiat-383` findings, `S1-R1-01` and `S2-R1-03`, concern
receipts. This fixture carries no receipt witness and no receipt request, so
neither applies.

The Alexandria release preserves the registry, source-match and
chain-observation files and the five fixture files by digest. Its
`proof-backed-state` capture earns that class only because `alexandria.py
verify` reruns Lazarus over the fixture.

Neither payload fits the committed tree: custody allows only `.md` and
`.json` here. Both stay in the run worktree's ignored `.hexaemeron/restricted/`
directory. The committed records name them by digest.

The `owner-handoffs` design report is written by:

```sh
python3 scripts/kickoff_hermes_1355.py conformance --criterion owner-handoffs \
  --candidate anchor-and-inspect \
  --report .hexaemeron/design-reports/anchor-and-inspect-owner-handoffs.json
```

It runs `check`, then re-verifies both retained payloads in-process with
Lazarus's and Alexandria's own verifiers. From those bytes it recomputes every
fixture row, component digest, plan limit and replayable response. It writes
value `true` only when all of them match the committed records.

## Evidence classes and custody

Two classes stay apart. A recorded value is what someone wrote down: the
registry's `code_keccak256` and the chain observations' code hash and length
come from provider responses and prove nothing. A proved value comes from the fixture's
proof records, where Lazarus checked the account against the header's state
root and hashed the captured code against the proved `codeHash`. Each
`fixture.json` row keeps both recorded values and the proved value in
separately labelled fields, and the checker refuses a recorded value labelled
`proof-backed` or a proved value from any other source. Replayed `eth_getCode`
responses are recorded evidence. The owner-handoffs check compares their bytes
with the proved code. The header is self-consistent and matches the
registry's recorded hash, which does not establish that it belongs to the
canonical chain.

Maps for the fee recipient and role provider come from private repositories.
The public tree carries their layouts, method maps and digests only. Private
source, test source and complete private Hermes directories stay outside Git.

The role provider's registry source commit names the private blob. This
inventory records the public v2-protocol copy at `e1f77540` as its deployed
state, per study section 2. The override names the Sourcify source SHA-256,
and the checker requires it to equal the digest that
`docs/kickoff/1359/evidence/source-match-1590.json` records for the role
provider's address, with that file matching the registry's evidence digest.
The registry itself is unchanged; that correction belongs to its owner.
