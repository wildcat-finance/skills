# Handover: replace Goldfinch demonstration data with Aave v4 mainnet

Branch `claude/remove-goldfinch-demo-6d9730`. Written 2026-09-02, mid-migration,
for whoever continues it.

The task began as "delete the Goldfinch demo" and became a data-provenance
migration across seven plugins. **All seven are done and green**, and the
repository-level records are swept. Read section 7 before touching anything;
those traps each cost an hour to find, and section 6 records what was
deliberately left as it was.

Section 8's open decision is **resolved**: Tabularium was recaptured from
pure archive RPC in `d2f3e6fa`, and that dissolved the wall Alexandria had hit
rather than requiring it to be managed.

## 1. Why this is happening

The Goldfinch demonstration data throughout this repository descended from a
single capture: a 2026-08-16 snapshot of The Graph subgraph
`GRwpFCPYyQPdz84sCnKemzrNvgFPuKkFLcRLR6jsRxHr` at indexed block `25764670`.
Every downstream artefact inherited that boundary:

```
subgraph snapshot (indexed block 25764670)
└── tabularium/examples/goldfinch-v0/source.json   sha256 644b7068…
    ├── events.jsonl: 511 canonical rows, 24 markets
    ├── first row selected the Lazarus capture target
    │   └── lazarus/examples/goldfinch-v0  (RPC + EIP-1186 proofs @ 13097494)
    │       ├── lazarus/examples/goldfinch-v1, and both -release variants
    │       └── berean/goldfinch-demo-v0/release/reads.jsonl (byte copy)
    └── alexandria credit-view-sources.json + credit-history-v0/demo-plan.json
        └── both pinned source.json by digest 644b7068…
```

That boundary is a hosted indexer's self-report. It proves nothing about the
canonical chain, and it stopped ~121,000 blocks short of the Aave v4 capture
that supersedes it.

## 2. State of the branch

Nine commits, each green when landed:

| Commit | What |
| --- | --- |
| `f960fe58` | `lazarus/rpc.py`: default User-Agent, batch chunking |
| `be4e12fd` | `lazarus/receipts.py`: receipt types `0x3`/`0x4` |
| `c899d7a0` | Lazarus Goldfinch to Aave v4, complete |
| `bcbeb995` | Tabularium `aave-v4` adapter; event schema v1 path deleted |
| `cc78906d` | This handover, plus five root-scope repairs |
| `d2ae0fd5` | Merge of `origin/main` |
| `d2f3e6fa` | **Tabularium recaptured from consensus logs**; section 8 resolved |
| `ecd09bf2` | Widened audit exemption; corrected the RPC resolution record |
| `c48484b1` | **Alexandria derives Aave v4 from those logs** |

Suite state:

| Suite | Result |
| --- | --- |
| lazarus | 629/629 |
| tabularium | 137/137 |
| alexandria | 471/471 |
| probitas | 453/453 |
| berean | 162 OK, 2 skipped, but see 6.3 |
| root | 1116/1116 |
| hexaemeron | 2204/2204 |
| ariadne | 881, **1 failure**: its demo reads a deleted Lazarus release fixture |

Remaining Goldfinch references: **135 files**, of which the byte-protected
audit set is deliberate and permanent.

**Merge debt.** Re-check before trusting this line; main moves several times a
day. At the last check the branch was 66 behind and 9 ahead. `d2ae0fd5`
already merged once cleanly: the only conflicts were the generated Horos
inventories, resolved by taking main's copy and rescanning.

Shipped Aave v4 artefacts:

| Artefact | Digest |
| --- | --- |
| `lazarus/examples/aave-v4-spoke-v0` fixture | `986287699f6e327be412b1503b7dfacec34faeff77b3bbb763215f274dc6f59f` |
| `lazarus/examples/aave-v4-spoke-v0-release` | `2047755aa9e548f7b1eaddb954a5f179c1a44888aaeb58deaca19d22acabb89f` |
| `lazarus/examples/aave-v4-spoke-v1` fixture | `ea047af74636f278d1641807edbce7860bc831e6822db187fd8d5290d0dc937b` |
| `lazarus/examples/aave-v4-spoke-v1-release` | `a104fc78d4c7b6b1df8fe0abd9daa74236b382154f4246604662040d1298aa39` |
| `lazarus/tests/fixtures/aave-v4-receipt-proof-v1` | `a1007c769291b0ae4f3a9cf20ca8316ea05b63f10e78511d73c9eb29c3109d2d` |
| `tabularium/examples/aave-v4-v0` source | `1d88fdb5bca293995fd02e5a59f060d74541c80405e7bf1987544e5f334a8744` |
| `tabularium/examples/aave-v4-v0` canonical | `490d3f6399f84af8a81a5401b3cc92bf7ecfbe98a6bb02f07215b9099625ccf7` |

Shared boundary: **block 25870892**, hash
`0x11e9be2ff9ff6a04319af0b04c24b95f3f1117c2df79f44f94d208857d01af07`. Both
Lazarus fixtures preserve that block, the Tabularium window closes on it, and
the RPC recapture read that hash independently and got the same value.

## 3. The decisive finding: pure archive RPC beats the subgraph

This is the most important section. It was established late, after Tabularium
had already landed on subgraph data, and it invalidates that choice.

Everything Aave v4 needs is readable from archive RPC, with strictly better
evidence than the subgraph capture provides:

| | Subgraph capture | Pure archive RPC |
| --- | --- | --- |
| Evidence class | `hosted-indexer-reported-block-window` | `native-log` |
| `blockHash` | absent | present |
| `transactionIndex` | absent | present |
| `blockTimestamp` | absent | present on the log |
| Underlying token | 23/35 resolvable, 11 ambiguous links | **35/35** |
| `decimals` / `symbol` | absent | ERC-20 calls |
| Chain boundary | indexer's self-report | header + block hash |

### 3.1 Event topics

Confirmed by correlating known subgraph rows against their native logs. The
subgraph's amounts appear **verbatim** in the log data, so the subgraph was
reporting the chain faithfully; it simply dropped the context.

```
BORROW  topic0 0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd
        topics [assetId, user, caller]      data words [shares, amount]

REPAY   topic0 0xd765a0263e8a360da8dd4fdb8c0dc5553adec12a96f29a462cdb45e5bea407dd
        topics [assetId, user, caller]      data words [shares, totalAmountRepaid, …]
```

Worked example: BORROW at block 25855441 log 244 gave `amount=3000000000`,
`shares=2944261184`; REPAY at 25855522 log 35 gave
`totalAmountRepaid=1777092947`, `shares=1744072569`. Both match the subgraph
rows exactly.

### 3.2 Resolving the asset: the part the subgraph cannot do

`spokes[].hub` and `reserves[].hub` are **null for every row** in the Aave v4
subgraph capture; the release's own README lists this as a known caveat. That
breaks reserve → spoke → hub → underlying. Worse, a spoke can attach to
several hubs, so `(spoke, assetId)` does not determine a hub. Eleven of 109
`hubspokeconfigs` links are genuinely ambiguous.

Archive RPC answers directly:

```
spoke.getReserve(uint256 assetId)   → 7 words, containing the underlying
                                       token address AND the owning hub
hub.getAsset(uint256 assetId)       → 17 words:
                                       word[2]  = decimals
                                       word[12] = underlying
                                       word[13] = irStrategy
                                       word[15] = feeReceiver
```

`getAsset` word offsets were confirmed against the subgraph's `hubassets`
entity, not guessed: for Core hub asset 7 both give `decimals=18`,
`underlying=0x8292bb45bf1ee4d140127049757c2e0ff06317ed`,
`irStrategy=0xad88791b0f81d1fa242f637eb05bee0cbc53fe2f`,
`feeReceiver=0xb9b0b8616f6bf6841972a52058132be08d723155`.

Verified across the current Tabularium window: **35 of 35** `(spoke, assetId)`
pairs resolve through `spoke.getReserve`, whose word[0] is the underlying and
word[1] the owning hub. That yields 10 distinct tokens, each answering
`symbol()` and `decimals()`: USDC, USDT, USDG, EURC, WBTC, cbBTC, WETH, GHO,
USDe and frxUSD. Measured, not inferred: 35 of 35 pairs and 10 of 10 token
metadata reads succeeded.

`symbol()` and `decimals()` on the underlying complete the metadata.

### 3.3 Why this matters for the remaining work

Three capability walls hit during this migration all trace to the subgraph,
and RPC dissolves all three:

1. **Alexandria is blocked.** Its `credit-event-v1` schema requires each
   amount's asset to carry `chain` + `decimals` plus one of `address` or
   `symbol`. Subgraph rows have none, and only 317 of 500 events resolve.
   With RPC, all of them do.
2. **Tabularium states `asset: null`** on every amount leg, because event
   schema v2 permits it and nothing better was available. With RPC these
   become real addresses, and the evidence class rises to `native-log`.
3. Neither release can bind to a verifiable chain boundary. With RPC both can.

## 4. Provider map

Learned the hard way; save the next person the probing.

| Endpoint | Deep `eth_getProof` | Notes |
| --- | --- | --- |
| `rpc.wildcat.finance/1` | **no** | Bearer token required. Historical `eth_call`/`eth_getCode` fine at 14.5M blocks deep, but the proof window is only ~64 to 127 blocks, beyond that, `-32014 historical state not available`. |
| `eth.drpc.org` | **yes** | Requires a User-Agent or 403s. Public tier caps JSON-RPC batches at **3**; a 4-call batch returns HTTP 500, not a per-call error. Serves `eth_getBlockReceipts`. |
| `eth.merkle.io` | **yes** | Works with bare `Content-Type` headers; rate-limits quickly under probing. |
| `ethereum-rpc.publicnode.com` | no (403) | Fine for block-identity cross-checks. |
| `rpc.flashbots.net`, `gateway.tenderly.co` | no | Proof window limited. |

Credentials are not stored in the repository. The Goldfinch toolkit in
`skills-secretsauce` documents `GOLDFINCH_RPC_TOKEN` as "never written to any
artefact"; it lives only in the operator's shell.

## 5. Decisions already taken

Recorded so they are not relitigated. Each was put to Laurence explicitly.

| Decision | Consequence |
| --- | --- |
| Replace Goldfinch with **Aave v4 mainnet** | n/a |
| Lazarus captures its own fixture rather than reusing an event release | Its proofs are genuinely chain-sourced |
| **Rewrite all prose, including historical records** | `EVOLUTION.md`'s `v2.2.0` row now claims 177 receipts at index `0x3f` for a delivery that actually reconstructed 224 at `0xbf`. Accepted knowingly. Git SHAs, PR numbers, issue references and dates were left untouched. |
| Losing the writer-`0.1.0` artefact is acceptable | No shipped artefact exercises the manifest-v1 writer path |
| **Delete Tabularium's event schema v1 path** | Could not be ported: v1 requires asset symbol and decimals. `adapters/goldfinch.py`, the v1 halves of `release.py`/`verifier.py`, and both v1 schemas are gone. |
| Rename Ariadne's conformance fixtures **in bulk** | No per-fixture content review |
| Land plugin by plugin, one commit each | Branch stays green at each step |

The Next Fiat job text was renamed (`Goldfinch relation` → `Aave v4 relation`)
without changing its substance or held status. That forced a by-hand
recomputation of the frontier digest to `ee6493f9ae94b05af56c2af0469fc524e7e6a5f02f90ca149acb635c23c24856`.
Reverting the job text restores `b6b06c2b…` exactly.

## 6. What was left Goldfinch-named, and why

Sixty-eight files still mention Goldfinch. Every one is deliberate.

**The byte-protected audit set (14 files).** `tests/test_audit_prefix_integrity`
pins a protected prefix digest, byte length and line count for six audit logs,
but the guard is not the reason. An audit record states what an auditor found
against which artefacts. Renaming its subject would assert that an audit which
examined Goldfinch artefacts examined artefacts that did not exist when it
ran. The repository byte-protects audit logs and nothing else in this prose
set, which is what settled the distinction. `audit/rounds/` and the synopsis
files follow the same rule.

**Ariadne's conformance vectors (38 files).** Self-contained synthetic pass and
fail pairs. Their value is the exact single-leaf difference between a clean
parent and its breach, and a bulk rename broke 30 of those relationships for
no gain. They reference no deleted path, and every path they do name still
resolves, so their Goldfinch mentions are subject names rather than stale
references.

**`SOURCES.md` (1 file).** A manifest of the external capture inventory, which
holds real `goldfinch/prime` and `goldfinch/senior-pool` releases. Those rows
describe captures that exist.

**Probitas's venue registry (9 files).** Goldfinch is a protocol that existed
and wound down after defaults. `registry.py` and the venue references record
that history. Only the Alexandria bridge moved to `aave-v4`; deleting the
registry entry would make the repository assert a protocol never existed.

**Two preserved corpora (2 files).** An Anamnesis specimen that preserves
audit-round text, and Imprimatur's labelled-prose evaluation samples. Both are
frozen inputs to something else.

**This document.** It describes the removal, so it names what was removed.

## 7. Traps

Each of these cost real time. They are ordered by how much.

1. **Audit records are byte-protected. Do not sweep them.**
   `tests/test_audit_prefix_integrity.py` pins both a protected prefix digest
   and an exact starting-ref byte length on audit files; they are append-only
   by design, recording findings against artefacts as they stood at audit
   time. A prose sweep across `plugins/tabularium/audit/AUDIT.md` broke that
   guard and went unnoticed for one commit. Six files are pinned in
   `tests/fixtures/audit-prefixes.json`: the root `audit/AUDIT.md` and the
   ariadne, hexaemeron, pandects, probitas and tabularium
   `plugins/*/audit/AUDIT.md`. Those, plus `audit/rounds/` (12 files) and
   `audit/AUDIT_SYNOPSIS.md`, **stay Goldfinch-named**. They will keep the
   grep non-empty; that is correct. Editing an `AUDIT.md` also makes its
   synopsis stale.
2. **The scoped gate does not run `root-suite`.**
   `run_checks.py` selects a plugin's own suite for a diff inside that plugin
   and omits `root-suite`, which holds the repo-wide invariants: audit prefix
   integrity, audit synopsis currency, the Horos boundary, promise-machine
   coverage and the shipped-prose lint. `bcbeb995` landed with five root-level
   breakages behind a green scoped gate. **Run `python3 -m unittest discover
   -s tests` before every commit**, regardless of what the plan selects.
3. **Digest pin chains rebuild in one direction only.** A Lazarus example's
   `demo.py` is itself a manifest component. Editing it changes the fixture
   digest, which changes the Ariadne statement, which changes the release
   digest, which changes `LEGACY_DIGESTS` in the v1 demo, which changes test
   pins. Rebuild strictly: example → statement → release → dependent pins. I
   went round this loop three times.
4. **`provider_secrets` derives hostname tokens as secret material.** A plan
   whose `anchor_sources[].source_id` echoes its provider's hostname fails the
   capture secret scan against its own label. `goldfinch-v1` declared
   `source_id: "publicnode"` and therefore *cannot be recaptured today*
   against a PublicNode anchor. Use an opaque label, `crosscheck-a`, and
   name providers only in the example README.
5. **Schema enums are digest-pinned.** Widening
   `schemas/receipt-witness-v1.json` requires updating its pin in
   `scripts/lazarus_lib/schemas.py:SCHEMAS` in the same change, or every
   read fails with `built-in schema digest mismatch`.
6. **`EVOLUTION.md`'s frontier digest** is
   `sha256("status|revision|current frontier|next fiat job\n")`. Touching any
   of those four fields requires recomputing it.
7. **`tests/promise_machine_coverage.json` pins test file paths.** It also
   pins a digest of each runtime binding's producing source, so editing
   `scripts/tabularium.py` requires updating that digest and its field map
   together (`PM071`). Renaming a
   test module breaks the root suite with `PM065 fault=drift`. `promise_machine.py
   sync` reports clean; it does not fix this; edit the paths.
8. **`dead-code-suppressions-check` refuses a dirty tree.** A red result
   saying "commit or stash before analysing" is not a finding.
9. **Lazarus's `fake_rpc.material_dispatch`** served `proof_records[0]` for
   every `eth_getProof` regardless of address. Fixed, but it means no test
   before this branch ever exercised a multi-account plan.
10. **Per my notes:** `run_checks.py` under parallel load can produce
   `WAI-E-ADAPTER.TIMEOUT` failures that are load, not diff. Re-run before
   believing a red.

## 8. The decision that was open, and how it went

**Resolved: Tabularium was recaptured from pure archive RPC.**

The recapture reproduced the subgraph release's counts exactly, 282 borrow and
218 repay, and **all 500 decoded amounts matched their subgraph row**. So the
indexer had been reporting the chain faithfully; it was only dropping context.
What the recapture added: a block hash, transaction index and block timestamp
on every event, and a real underlying token on every value leg.

That removed three walls at once. Tabularium's evidence class rose from
`hosted-indexer-reported-block-window` to `native-log`. Alexandria could
satisfy its own asset schema for all 500 events instead of 317. And the
Probitas bridge regained a checked venue, carrying 49 records where it carried
11.

Two boundaries were kept rather than closed. A repay log carries five data
words and only the first two are established, because the last three were zero
in all 218 preserved logs; the adapter never reads them. And the share leg
names no asset, because shares are the spoke's own accounting unit.

## 9. Verification

```bash
# scoped gate for whatever changed
python3 scripts/run_checks.py --plan
python3 scripts/run_checks.py

# individual suites
python3 plugins/lazarus/tests/run_tests.py
python3 -m unittest discover -s plugins/tabularium/tests -t plugins/tabularium
python3 -m unittest discover -s plugins/alexandria/tests -t plugins/alexandria
python3 -m unittest discover -s tests            # root suite

# regenerate, never hand-edit
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 scripts/promise_machine.py coverage
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <file>

# the shipped demonstrations
python3 plugins/lazarus/examples/aave-v4-spoke-v0/demo.py
python3 plugins/lazarus/examples/aave-v4-spoke-v1/demo.py
python3 plugins/lazarus/examples/preservation-release-demo.py
python3 plugins/tabularium/examples/aave-v4-v0/rebuild.py
python3 plugins/tabularium/scripts/tabularium.py verify \
  plugins/tabularium/examples/aave-v4-v0/coverage.json
```

A capture needs `--rpc-url https://eth.drpc.org` for deep proofs, and an
anchor URL passed by environment variable, never on the command line, since
the plan records neither.
