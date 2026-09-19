# Kickoff target-input registry for issue 1359

Issue: https://github.com/wildcat-finance/skills/issues/1482, a prerequisite
child of https://github.com/wildcat-finance/skills/issues/1359.

Dave Coleman approved the scope on 2026-09-13 in the delivery session and
authorised the PR update. The [approval record](https://github.com/wildcat-finance/skills/pull/1583#issuecomment-5655443034) preserves the
selected order, estate, exclusions and operator statement; it was posted by
the publisher and is not a separate GitHub review. The same record is bound
by SHA-256 in [`evidence/scope-approval.json`](evidence/scope-approval.json).

This revision was prepared by Dave Coleman with Shoggoth as Surveyor under
Protasis. The original chain observations and source experiments were
recorded by Shoggoth on 2026-09-12 and are preserved unchanged. Dave owns the
scope decision; the reviewer of PR #1583 owns implementation review. The
exact source commits, input digests and source links live in
[`targets.json`](targets.json) and the evidence files it names.

The 2026-09-18 revision, recorded under `revisions` in `targets.json`,
completes [#1590](https://github.com/wildcat-finance/skills/issues/1590):
the Wildcat V2 Ethereum row moves from `blocked` to `resolved` on the
evidence in [`evidence/ethereum-mainnet-1590.json`](evidence/ethereum-mainnet-1590.json)
and [`evidence/source-match-1590.json`](evidence/source-match-1590.json).
Shoggoth as Surveyor under Protasis produced it; the reviewer of the pull
request carrying it checks the source/deployment mapping. The 2026-09-12 and
2026-09-13 evidence files are unchanged.

## Approved decisions

`lemma-9-venue-order` is recorded with the following five ordered slots:

| Slot | Venue | Ordered target rows |
| --- | --- | --- |
| 1 | Wildcat | `wildcat-v1-ethereum-mainnet`, `wildcat-v2-ethereum-mainnet` |
| 2 | Aave V3 | `aave-v3` |
| 3 | Maple | `maple-v1`, `maple-v2-fixed-term`, `maple-v2-open-term` |
| 4 | Euler | `euler-v1`, `euler-v2` |
| 5 | Centrifuge V3 | `centrifuge-v3`, covering the hub and corresponding ERC-7540 spokes |

The Maple slot means three contract families: legacy V1, V2 fixed-term and
V2 open-term. Both term families are V2; relevant Syrup pools and routers
belong alongside V2. This interpretation was proposed and approved, rather
than recovered as an explicit historical generation list. Source pins for
the separate loan modules are recorded in `source.components` and
[`evidence/source-refs.json`](evidence/source-refs.json).

`kickoff-consumer-target` is recorded as `ethereum-only`: Wildcat V2 on
Ethereum mainnet for #1354, #1355 and #1361, including the factory,
registered templates, instances, hooks and role providers. #1363 consumes
the same deployed comparison base. The third FixedTermHooks template is
included by that scope. Hermes still derives its protected set from the
deployment map. Both MarketLens observations remain available; #1590 maps
their epochs and consumer use.

The emitter source record from [PR #1460](https://github.com/wildcat-finance/skills/pull/1460)
pins `wildcat-finance/v2-protocol` at
`f5a26146987926f4811b72a795d662813dedfe85`. It records 27 emitters in
`src/libraries/MarketEvents.sol` and `src/spherex/SphereXProtectedEvents.sol`,
with declarations in `src/interfaces/IMarketEventsAndErrors.sol` and
`src/spherex/SphereXConfig.sol`. The registry records that study's digest.
Its source equivalence to `v2.1.0` does not establish every deployed epoch;
the remaining epoch mapping belongs to #1590.

Alternatives were an unresolved choice among all seven reuse epics, Wildcat
or Centrifuge in the three-generation slot, and closure on an unselected
inventory. The approval replaces the first; #1395's explicit Maple scope
rules out the second; #1482's acceptance rules out the third. Euler leads
the later pair because its existing adapters supply reusable work; the
Centrifuge hub/spoke mapping follows. Plasma, unreleased Wildcat code,
Aave V4, Compound, Clearpool, Tinlake and Centrifuge V2 are excluded from
this initial registry scope. Their dated rows remain marked `excluded`.

## Admission and recovery

Scope is settled. Deployment identity remains a separate field. Eight of
the nine selected rows carry a specific `blocker` and source-recovery child;
`wildcat-v2-ethereum-mainnet` is `resolved` since 2026-09-18 on the evidence
its child #1590 supplied. None is promoted from a source-only record to
deployed identity. The eight excluded rows have no consumers. Each admitted row names its
intended corpus directory, source inputs, observed deployment evidence where
available and the exact missing-input owner.

| Recovery | Rows | Missing evidence |
| --- | --- | --- |
| [#1589](https://github.com/wildcat-finance/skills/issues/1589) | Wildcat V1 | Init-code reproduction, lens source and historical instance epochs |
| [#1590](https://github.com/wildcat-finance/skills/issues/1590) | Wildcat V2 Ethereum | Completed 2026-09-18: instance/hook/role-provider map, fee-recipient, collateral and role-provider sources, lens epochs and emitter-pin binding |
| [#1591](https://github.com/wildcat-finance/skills/issues/1591) | Aave V3 | Deployment/source table, compiler inputs and documentation revisions |
| [#1592](https://github.com/wildcat-finance/skills/issues/1592) | Three Maple families | Separate source/deployment and build bundles, shared V2/Syrup coverage |
| [#1593](https://github.com/wildcat-finance/skills/issues/1593) | Euler V1 and V2 | Proxy/module and vault/EVC deployment bindings, build and documentation inputs |
| [#1594](https://github.com/wildcat-finance/skills/issues/1594) | Centrifuge V3 | Joined hub/spoke epochs, source, compiler and documentation inputs |

These are children of #1482 and were compared with the existing open queue
before filing. Their exact bodies, target coverage and parent are preserved
in [`evidence/recovery-issues.json`](evidence/recovery-issues.json). A child
changes a row to `resolved` only after supplying the missing evidence;
approval alone cannot clear an evidence gap. #1482 permits this blocked-row
handoff. It does not require downstream corpora, adapters, audits or campaigns
to land before the registry can be accepted.

## Consumers

[`evidence/consumer-inputs.json`](evidence/consumer-inputs.json) preserves the
59 kickoff bodies and nine prerequisite bodies inspected on 2026-09-13.
The registry classifies all 68: 58 have target mappings and ten have stated
reasons for being outside this registry. All 17 GitHub dependency edges out
of #1482 are mapped; #1376 also names the registry in its body. The checker
requires the preserved denominator, dispositions and reverse row references
to agree. A consumer mapping supplies only the approved identity for that
consumer's target-specific work; the full boundary is in its JSON row.

| Consumer | Target rows | Boundary |
| --- | --- | --- |
| [#1354](https://github.com/wildcat-finance/skills/issues/1354) | Wildcat V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1355](https://github.com/wildcat-finance/skills/issues/1355) | Wildcat V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1358](https://github.com/wildcat-finance/skills/issues/1358) | Wildcat V2 Ethereum | This supplies the deployed comparison subject only. The existing Janus model remains modeled until #1376 binds it; its V2.5 label is not deployment evidence. |
| [#1359](https://github.com/wildcat-finance/skills/issues/1359) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1361](https://github.com/wildcat-finance/skills/issues/1361) | Wildcat V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1363](https://github.com/wildcat-finance/skills/issues/1363) | Wildcat V2 Ethereum | Deployed comparison base only; #1485 owns the separately approved proposed indexed-actor source. |
| [#1365](https://github.com/wildcat-finance/skills/issues/1365) | All nine selected rows | Historical V1 documents remain included for the V1 corpus. Deprecation excludes a path only from the incompatible generation, never from its own historical row. |
| [#1366](https://github.com/wildcat-finance/skills/issues/1366) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1367](https://github.com/wildcat-finance/skills/issues/1367) | All nine selected rows | #1486 still owns the finite two-chain pilot; the registry supplies eligible target identities only. |
| [#1368](https://github.com/wildcat-finance/skills/issues/1368) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1369](https://github.com/wildcat-finance/skills/issues/1369) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1370](https://github.com/wildcat-finance/skills/issues/1370) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1371](https://github.com/wildcat-finance/skills/issues/1371) | Wildcat V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1372](https://github.com/wildcat-finance/skills/issues/1372) | Wildcat V2 Ethereum | The approved registry supplies the deployed comparison base only; it does not select or approve unreleased code. |
| [#1373](https://github.com/wildcat-finance/skills/issues/1373) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1374](https://github.com/wildcat-finance/skills/issues/1374) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1375](https://github.com/wildcat-finance/skills/issues/1375) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1376](https://github.com/wildcat-finance/skills/issues/1376) | Wildcat V2 Ethereum | The existing V2.5 model cannot be relabelled as deployed V2. Match or correct the model through this consumer before a deployed claim. |
| [#1377](https://github.com/wildcat-finance/skills/issues/1377) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1378](https://github.com/wildcat-finance/skills/issues/1378) | Wildcat V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1379](https://github.com/wildcat-finance/skills/issues/1379) | All nine selected rows | The five-venue registry is the initial admitted scope. The original 200-subject, six-venue, five-chain campaign remains unfulfilled; this approval neither supplies the sixth venue nor authorises endpoints or spending. |
| [#1381](https://github.com/wildcat-finance/skills/issues/1381) | Wildcat V2 Ethereum | Deployed comparison base only; the added-topic candidate remains with #1485. |
| [#1382](https://github.com/wildcat-finance/skills/issues/1382) | Wildcat V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1383](https://github.com/wildcat-finance/skills/issues/1383) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1384](https://github.com/wildcat-finance/skills/issues/1384) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1385](https://github.com/wildcat-finance/skills/issues/1385) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1386](https://github.com/wildcat-finance/skills/issues/1386) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1387](https://github.com/wildcat-finance/skills/issues/1387) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1388](https://github.com/wildcat-finance/skills/issues/1388) | `aave-v3` | Aave V3 is the first further adapter in #1395 under the approved venue order; the source map and effort evidence still precede implementation. |
| [#1389](https://github.com/wildcat-finance/skills/issues/1389) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1390](https://github.com/wildcat-finance/skills/issues/1390) | Wildcat V1 and V2 Ethereum | Wildcat is the grounded-release subject; the existing Aave V4 demonstration remains separate. |
| [#1391](https://github.com/wildcat-finance/skills/issues/1391) | Wildcat V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1392](https://github.com/wildcat-finance/skills/issues/1392) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1393](https://github.com/wildcat-finance/skills/issues/1393) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1394](https://github.com/wildcat-finance/skills/issues/1394) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1395](https://github.com/wildcat-finance/skills/issues/1395) | Aave V3, three Maple families, Centrifuge V3 | Three Maple contract families mean legacy V1, V2 fixed-term and V2 open-term; shared V2 and Syrup sources do not create an invented protocol generation. |
| [#1396](https://github.com/wildcat-finance/skills/issues/1396) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1397](https://github.com/wildcat-finance/skills/issues/1397) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1398](https://github.com/wildcat-finance/skills/issues/1398) | Wildcat V1 and V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1399](https://github.com/wildcat-finance/skills/issues/1399) | Wildcat V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1400](https://github.com/wildcat-finance/skills/issues/1400) | Wildcat V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1401](https://github.com/wildcat-finance/skills/issues/1401) | Wildcat V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1402](https://github.com/wildcat-finance/skills/issues/1402) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1403](https://github.com/wildcat-finance/skills/issues/1403) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1404](https://github.com/wildcat-finance/skills/issues/1404) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1405](https://github.com/wildcat-finance/skills/issues/1405) | Wildcat V1 and V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1406](https://github.com/wildcat-finance/skills/issues/1406) | Wildcat V2 Ethereum | Only the deployed comparison mode receives the approved V2 identity; #1485/#1372 still own the proposed mode. |
| [#1407](https://github.com/wildcat-finance/skills/issues/1407) | Wildcat V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1408](https://github.com/wildcat-finance/skills/issues/1408) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1485](https://github.com/wildcat-finance/skills/issues/1485) | Wildcat V2 Ethereum | The registry supplies only the deployed comparison base. Unreleased source selection is outside this approved scope. |
| [#1486](https://github.com/wildcat-finance/skills/issues/1486) | All nine selected rows | Target identities only. Two-chain selection, block windows and finite proof bounds still belong to this child. |
| [#1488](https://github.com/wildcat-finance/skills/issues/1488) | All nine selected rows | Target identities only. Fleet membership, endpoint entitlement, concurrency and budgets still need this child’s own decision. |
| [#1490](https://github.com/wildcat-finance/skills/issues/1490) | All nine selected rows | Target identities only. No reference capture or historical interval is selected by scope approval. |
| [#1492](https://github.com/wildcat-finance/skills/issues/1492) | Wildcat V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1493](https://github.com/wildcat-finance/skills/issues/1493) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1494](https://github.com/wildcat-finance/skills/issues/1494) | All nine selected rows | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1497](https://github.com/wildcat-finance/skills/issues/1497) | Wildcat V2 Ethereum | Registry identity only; this consumer still checks its source/capture match and supplies its own required artefacts, policy and execution evidence. |
| [#1498](https://github.com/wildcat-finance/skills/issues/1498) | `aave-v3` | Aave V3 is the first further adapter; the contribution rule and prior source map remain this child’s deliverable. |

The excluded census entries are #1350, #1351, #1352, #1356, #1357, #1360,
#1362, #1364, #1380 and #1409. Their exact reasons remain in
`consumer_census`; a closed reference delivery or a schema/application task
does not acquire a new venue scope from this registry.

The original six-venue, five-chain, 200-subject requirement in #1379 remains
unchanged. This five-venue approval does not supply the sixth venue, a
capture interval, endpoint entitlement or a budget. The finite two-chain
pilot and the proposed indexed-actor branch also retain their own owners.
Historical V1 documentation belongs in the V1 corpus even when deprecated;
#1365 must apply exclusions per generation, not remove historical evidence
from every corpus.

## Check it

```bash
python3 scripts/kickoff_targets.py check
python3 scripts/kickoff_targets.py specimen --specimen docs/kickoff/1359/specimens/accepted-v2-market-init-code.json
python3 scripts/kickoff_targets.py specimen --specimen docs/kickoff/1359/specimens/wrong-generation.json
python3 -m unittest discover -s tests -p test_kickoff_targets.py
```

Use the exact interpreter recorded in `.python-version`. The 2026-09-13
validation used its `3.14.6` pin. The checker verifies the approved order,
attribution, consumer denominator, recovery links, file digests and recorded
code-hash comparisons offline. A specimen command first validates
the registry. Identity acceptance means the specimen matches that recorded
row; it does not admit a blocked row for deployed-code use. Wrong generation,
hash, chain or excluded scope refuses.

The source-reference fetch on 2026-09-13 confirmed that the named immutable
Git commits resolve. It did not repeat historical RPC reads or compiler
reproduction. The source and observation details below retain their dated
producer and limits; repository and specimen checks are separate evidence.

## Wildcat rows

Addresses and hashes are lowercase throughout so they match the JSON byte
for byte. Every code hash is `keccak256` of the runtime code returned by
`eth_getCode` at the observed block. A stored init code is a contract whose
code is one `0x00` byte followed by creation bytecode; for those rows the
table also gives the hash of the creation bytecode alone, which is what the
factory compares.

### `wildcat-v2-ethereum-mainnet`

Status `resolved` since 2026-09-18. The 2026-09-12 observation and source
record below is preserved; the estate map, epochs and located sources that
completed #1590 follow it under **Estate map, 2026-09-18**.

Wildcat V2 HooksFactory estate on Ethereum mainnet (chain 1). First observed
at finalized block 25960042, hash
`0x3f817acb8a79c8158643f8ecdc0f1cd812ba00cf39078e76d816bf4cd7c198eb`,
2026-09-12T08:09:59Z, through `https://ethereum-rpc.publicnode.com`; the
complete estate was observed at finalized block 26006289, hash
`0x3d069f254a10d98ad19eff0f397cf28db3613fd98bff1df48c798920552f4ec5`, 1789757399 (2026-09-18T18:49:59Z). Every contract
recorded at the first block has the same runtime code at the second.

Source pin: https://github.com/wildcat-finance/v2-protocol at tag v2.0.0,
commit `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657`. Every in-tree source of
the five verification inputs below has the same blob at
`8dc8e449a0029927c70ad39efcf196315071f324` (2025-02-06, the deployment-era
commit), `d1691193dc09d4186b4cc47a131280c62e5c5b76`, tag v2.1.0
`c7be4039f8f383a9dda4e45f63331c17d63f9ed9`, the `mainnet` branch head
`2624204522e5e13817ecad3655411bb9fc35ab11` and the `main` head
`f5a26146987926f4811b72a795d662813dedfe85`. Other files differ between
those commits, so a consumer that wants one tree should take the tag. None
of those sources has the same blob at tag v2.5.4, which is why the V2.5
line is a separate row.

Compiler: solc `0.8.25+commit.b61c2a91`, EVM `cancun`, optimizer on with
50000 runs, `viaIR` on, `bytecodeHash` `none`, CBOR appended. Foundry root
is the repository root; `foundry.toml` pins solc 0.8.25 and `cancun`, and
its `ir` profile carries the 50000-run `viaIR` setting the deployment used.

Build inputs, all under `deployments/mainnet/` at tag v2.0.0:

| Input | Git blob | SHA-256 | Bytes |
| --- | --- | --- | --- |
| `HooksFactory-0xdd7dd3b5076cf89440d05585ff56d246386207be/standard-input.json` | `34d238ea60b2f3205195f9d8cf942f3a46c08272` | `63dabbfdd5b7c140c314a0892baa639e217b0a15b20a51e604ecd2bd10ad4309` | 161751 |
| `WildcatMarket-0xac3216fa28f81b8fae150fb5626ca79c7a570daf/standard-input.json` | `0f86f94ad1165975a2812b3acfd0a333c5d0724f` | `f9a92fe4072d8f44406448377730c4b38b908571fa3db6b8ff3a81719e801346` | 224443 |
| `FixedTermHooks-0x7e49caba6fb53cdc70cd98829731a2b8d76dfc36/standard-input.json` | `813f522c2c4c8f311775b21abeda69f7fb8da7cd` | `a099de64cf9612dc116ce2d1a2df403fbd3feef5b991c54e00c032a7be1a5f33` | 141522 |
| `OpenTermHooks-0x4c62b4844c8371f321541e8d564a4b3896cecec7/standard-input.json` | `7ec48fb58293cb9cbb47767b0a0c06a90e3537ca` | `b5ea57d8c54b1f1e4640384426c1f0dbfddd2fae1c32e81f4ff393c2b6d31e80` | 138286 |
| `MarketLens-0xc672760757da93b5f3275dc97203d145806dae33/standard-input.json` | `9e77f86ba4860e6d0d370daa31126088d767f383` | `82f2b4bfd732136094d7f60a9d6d7f1240d324e44251e60065dfc907d50986c3` | 434585 |

Compiling each input with `solc-linux-amd64-v0.8.25+commit.b61c2a91`
(SHA-256 `c42aada7a52057ddbed93ec011235e256c564c440b68dbaac5ae482babbb3d6d`)
reproduced the creation and deployed bytecode in the neighbouring
`output.json` byte for byte, all five of them. The `lib/` sources those
inputs carry come from the submodules pinned at the tag: `lib/solady`
`2ba1cc1eaa3bffd5c093d94f76ef1b87b167ff3c`, `lib/openzeppelin-contracts`
`fd81a96f01cc42ef1c9a5399364968d0e07e9e90`, `lib/forge-std`
`b6a506db2262cad5ff982a87789ee6d1558ec861`, `lib/solmate`
`1b3adf677e7e383cc684b5d5bd441da86bf4bf1c`, `lib/sol-utils`
`ffc4766f208e71901205a20cbb38a37d0c1619d5`, `lib/ds-test`
`e282159d5170298eb2455a6c05280ab5a73a4ef0`, `lib/vulcan`
`95d6be4c447a23400d876caff078abcf6a881a12`, `lib/ethereum-access-token`
`937b1daa32d0343f538ac217b31e8eb1c6e1e6be`.

Emitter and interface paths at the tag, for #1354 and #1361:

| Path | Blob | Holds |
| --- | --- | --- |
| `src/libraries/MarketEvents.sol` | `80d93961d74cfa36feee0fe34a423c989d9ca034` | 22 assembly log sites: 9 `log1`, 9 `log2`, 4 `log3`; consumed by the five `src/market/*.sol` files |
| `src/spherex/SphereXProtectedEvents.sol` | `d5415f1c37cc0df2fea1febe6ab1a861b49d02a4` | 5 `log1` sites |
| `src/interfaces/IMarketEventsAndErrors.sol` | `dd6d3838b2990610b7914bc3f49103c082fd2784` | 23 event declarations |
| `src/interfaces/IERC20.sol` | `9ee5c3aecc25e36414b022353b3126524d3049bc` | 2 event declarations |
| `src/interfaces/ISphereXProtectedRegisteredBase.sol` | `8e9078e846875d8de0df1979f726a6a9af9c1b64` | 2 event declarations |
| `src/IHooksFactory.sol` | `6e883a21b21a39b6989d9f0331bd7e91c12b04e7` | 5 event declarations, emitted with `emit` |
| `src/interfaces/IWildcatArchController.sol` | `2ee945fb20874de2da96c79b0dc5fe0056132268` | 15 event declarations |
| `src/access/IHooks.sol` | `14e80db27ffcd53597d1aefef4e9d3082c253659` | hook interface |
| `src/access/IRoleProvider.sol` | `904b886f6d22798451b9f83ee347eeafd5422866` | role-provider interface |

The counts are text matches over the tag's `src/` tree, not a semantic
census; the hooks and arch-controller contracts emit through `emit`, and
`src/market/` carries three `emit` statements beside the assembly library.

Deployed contracts, protocol level (the 42 hooks instances and 80 markets are
listed in `targets.json` and the estate evidence, not here):

| Role | Contract | Address | Runtime code keccak256 | Source commit | How the match was made |
| --- | --- | --- | --- | --- | --- |
| registry | WildcatArchController | `0xfeb516d9d946dd487a9346f6fee11f40c6945ee4` | `0x3622afdfc583101952ff6e608d76f9c897d2767297315962d97f8b3a2cc2df56` | `da74452aa7d1a0f024d99efd22cc6d950a8116b7` (V1 repository) | Sourcify full match; blob equality with the V1 tree; solc 0.8.22 reproduces the runtime code exactly |
| sanctions sentinel | WildcatSanctionsSentinel | `0x437e0551892c2c9b06d3ffd248fe60572e08cd1a` | `0xdc8454a4d12757aaa87ab44b71a6292fc540001560d37cdfd6a3cce423b4e004` | `6164ddd4c75ef6da2181e5623b99795b9829e31c` (V1 repository) | Sourcify full match; blob equality; solc 0.8.22 reproduces the runtime code modulo immutables |
| factory | HooksFactory | `0xdd7dd3b5076cf89440d05585ff56d246386207be` | `0xf21fd79f56b27db5d249a3855eff8eff80d75a9f2177bc0018d0ba7cac39b5c0` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | verification input; Sourcify full match; solc 0.8.25 reproduction; runtime equals `deployedBytecode` modulo 22 immutable slots |
| market init code | WildcatMarket | `0xac3216fa28f81b8fae150fb5626ca79c7a570daf` | `0x3d18b90882fb6f7e36b6f942d263d42e75f3905e8cad842241031832e441e99c`; creation `0xc152ead6073d54f964e3c2fd317ec6c774e67465cf3e6fb9551badb88a09e43f` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | stored code is `0x00` plus the recorded creation bytecode; its hash equals `HooksFactory.marketInitCodeHash()` |
| hooks template 0 | OpenTermHooks | `0x4c62b4844c8371f321541e8d564a4b3896cecec7` | `0xc7d1fe188cc060abe3ca44abfffb422eb8d30ec4fbdf6d7313a6bbd1b01eb5cc`; creation `0x45a5a3cf0a4aeee877f71602848425bac849ee5bf59a2761014c7d6ee00be94f` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | stored code equals the recorded creation bytecode; 28 instances, 60 markets |
| hooks template 1 | FixedTermHooks, 365-day maximum term | `0x7e49caba6fb53cdc70cd98829731a2b8d76dfc36` | `0x90cbf3c32cbc9d1936ff2a3e41febe383e7385148c969e4f3ae7298f2f47c2f0`; creation `0xe283098ee6563da880b545b812e4eb94e24ee30498f2f109bbb6295c95dc3c4f` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | stored code equals the recorded creation bytecode; 3 instances, 4 markets |
| hooks template 2 | FixedTermHooks, 730-day maximum term | `0x731c775385d0efb2cac61074ba2d885d343a09cd` | `0xb4cbbd478498c7f02a78e33d79aff22fc024f48e77f8b6350568881588d55ab2`; creation `0x1e2fdf1700fe20e2e903b5c459c8b9db04798942ab7fe1ad49a88421dbd47a77` | `5838b2f3f5c0bb3489cd2ff16bb31ddd5194c7fa` | absent from every manifest; recompiling the FixedTermHooks input with that commit's `FixedTermHooks.sol` reproduces the stored code byte for byte; registered at block 22094295 by the arch controller owner; 11 instances, 16 markets |
| lens | MarketLens (deployments.json) | `0xc672760757da93b5f3275dc97203d145806dae33` | `0xc9364e3b8e67e771889f32df9d0589e2bbba7735e11e3b7bf8a7034635b99b8a` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | verification input; runtime equals `deployedBytecode` modulo 11 immutable slots; not on Sourcify; deployed at block 21788205 in the core set |
| lens | MarketLens (docs page; `MarketLensV2` in the SDK) | `0xfda5c5b96bb198d2fca1a01d759620b64ae5afe7` | `0x26ff0af4fbbbd64b3c66a82be70c034ebc7af07211a7a6c1616275c24e8944d5` | `e1f77540fef65736374de6c847743d8ca2233fb4` | Sourcify full match (runs 200); all 60 in-tree sources equal the `plasma` branch; deployed at block 23121577 |
| wrapper factory | Wildcat4626WrapperFactory | `0xea6de11f8f3f83c79bd9d8db5517fcfdf2bb148a` | `0x58bb549139a0aa9ddf20beba5645e9a940a1ca12a33f1ea0cefdb9f905386e3e` | `c7be4039f8f383a9dda4e45f63331c17d63f9ed9` (tag v2.1.0) | Sourcify full match (runs 200, `viaIR` off); all 9 in-tree sources equal the tag; deployed at block 24750455 |
| fee recipient | WildcatFeeRecipient | `0x35a5d1bd68f3139971027b92c1ee9384a0708554` | `0xb29ab171b6256affe18a6bb169cf2712d710dc8a33e4081e2ae9dbd850fe1cb9` | `ac73bda3642c9a7c8de64e39856b31af53f06068` (`fee-recipient-contract`, private) | the repository's recorded `output.json` `deployedBytecode` equals the runtime byte for byte, 1649 bytes, no immutables; its `standard-input.json` sources equal the Sourcify full-match sources byte for byte; deployed at block 21854968 |
| role provider | OpenAccessRoleProvider | `0x5620553d8881335f74ad19259daacd1d9b373101` | `0x35325d49e13e90e3064edf7e4c7b7fff9b7840b6ce21caf765930240d3b17ff1` | `5d7f8c889a8d29935838a3906172feb8d9861807` (`chainalysis-ofac-role-provider`, private) | Sourcify full match (0.8.25, runs 200, `viaIR`); the repository blob compiled alone reproduces the runtime modulo the 2 oracle immutable slots; deployed at block 21825574; pull provider on 37 instances |
| collateral factory | WildcatMarketCollateralFactory (`WildcatCollateralFactoryV1`) | `0xbdf64bd7ea91a534445d06736a0f0e2a33ffa47c` | `0x430982ffbd3051bd4068c561c04aed086569a4767b95cef0bece274a04260897` | `46dba596fa111f868200358f551796e8f73b5fd7` (`collateral-contract`, branch `multi-exchange`) | `forge build` under the repository's `ir` profile (solc 0.8.28, `viaIR`, 50000 runs, `cancun`, `bytecodeHash` none) reproduces the 7615-byte runtime modulo 4 immutable slots; not on Sourcify; deployed at block 23167812 |
| collateral init code | SimpleMarketCollateralMultiParty | `0xbbb998043a20a26828617769f37dc3980be25ebc` | `0xd56243fb840e67c08b12dc97460327e9cf399aeeb1c481d8a5d52d1c5dadfe78`; creation `0x382141330847ee36f45e2750567618f6b5179749e3cc55a5b929845fd43cbc52` | `46dba596fa111f868200358f551796e8f73b5fd7` | stored code is `0x00` plus the creation bytecode built from the same branch; its hash equals `collateralInitCodeHash()` |
| collateral lens | CollateralLens | `0x422489ba6bddd5954c379c41b6c97ab0e4494f90` | `0xd2fd4aee3c10526d8737dfee0b10ef71cc2892a9d58ae6b680ac22b1602f35d8` | `46dba596fa111f868200358f551796e8f73b5fd7` | the same build reproduces the 8287-byte runtime modulo 1 immutable slot, the factory address; deployed at block 23168260 |

#### Estate map, 2026-09-18

Read at block 26006289 through `eth_call` and `eth_getCode` pinned to
that number. Factory views: `getHooksTemplates`, `getMarketsForHooksTemplate`,
`getHooksInstancesForBorrower` over every registered borrower,
`getHooksTemplateForInstance`, `isHooksInstance`,
`getMarketsForHooksInstance`. Arch controller views: `getRegisteredBorrowers`
(54), `getRegisteredMarkets` (87). Each market: `hooks()`, `borrower()`,
`name()`, `version()`. Each hooks instance: `borrower()`, `name()`,
`version()`, `getPullProviders()`, `getPushProviders()`. The factory's
complete event history, blocks 21788182 to 26006347, was
read with `eth_getLogs` in 10,000-block chunks: 129 logs, of which
80 `MarketDeployed`, 42 `HooksInstanceDeployed`, 3 `HooksTemplateAdded`, 2
`HooksTemplateFeesUpdated` and the two SphereX configuration events of the
creation transaction. The same 129 logs were listed by an indexer and each
one was matched against its `eth_getTransactionReceipt`.

Templates:

| Template | Address | Created | Registered | Registration transaction | Instances | Markets |
| --- | --- | --- | --- | --- | --- | --- |
| OpenTermHooks | `0x4c62b4844c8371f321541e8d564a4b3896cecec7` | 21788183 | 21788203 | `0x64a832f9a335993f6bfb3c4698989bf336aa74570d39988892f3841686c9d75d` | 28 | 60 |
| FixedTermHooks, 365-day | `0x7e49caba6fb53cdc70cd98829731a2b8d76dfc36` | 21788194 | 21788204 | `0xd82bd8a66de64acb8117ce6158767c6b53fa354356cb552c86b1cd2e4b85ece6` | 3 | 4 |
| FixedTermHooks, 730-day | `0x731c775385d0efb2cac61074ba2d885d343a09cd` | 22081282 | 22094295 | `0x1d9aee83f68194a287314d553f72f96e742a6b917a30ae1799199504117d7175` | 11 | 16 |

The two v2.0.0 templates were registered by the deployer
`0x240334405021f4242d57a3785df39edc23e1b607` with itself as fee recipient at
1000 bips; the fee update at block 21873682 (transaction
`0x30f21de191969bc6d13a8faccbde686ef988df57fd454022580389eefc10e1a0`) moved
both to the WildcatFeeRecipient at 500 bips through the arch controller owner
Safe `0xc15be5214978d1fc509ecdd4f9d5bc067c94d9ae`. The third template was
created by the operations account `0xb4b9f935bf0189c2ff46165f04b0d517e9553fbc`
(nonce 43) at block 22081282 and registered through the same Safe at block
22094295 with the fee recipient at 500 bips. It is enabled at the observed
block; its 11 instances and 16 markets are part of the deployed estate, and
the protected set Hermes derives from this map includes them.

Hooks instances: 42, sorted-list SHA-256
`e5827c094ab8594a7951ba3b8a0bc5e2ce1bb3600f615fc3976660ddca57e469`; 28 OpenTermHooks,
3 FixedTermHooks 365-day, 11 FixedTermHooks 730-day. All 42 have runtime
code equal to their template's compiled `deployedBytecode` modulo its
immutable slots (14 for OpenTermHooks, 15 for FixedTermHooks), all 42 answer
`isHooksInstance` true, all 42 have a `HooksInstanceDeployed` event naming the
same template, and every market each instance lists names it back through
`hooks()`. 5 instances belong to borrowers no longer registered at the
observed block and were reached through their markets' `hooks()` immutable
rather than `getHooksInstancesForBorrower`. First instance at block 21866550,
last at block 25895380.

Markets: 80, sorted-list SHA-256
`fd7174beb547e841a6f1b9716b4d13e5d861279f38b3d355d761dd6755a96ec0` (the same 80 addresses as the
2026-09-12 list, hashed over a different serialisation); 60 OpenTermHooks, 4
FixedTermHooks 365-day, 16 FixedTermHooks 730-day. All 80 have runtime code
equal to the v2.0.0 WildcatMarket `deployedBytecode` modulo its 63 immutable
slots, all 80 answer `version()` `2`, and all 80 have a `MarketDeployed`
event whose hooks address, template, name and symbol agree with the views.
The 87 registered markets minus these 80 are the 7 V1 markets.

Role providers: 32 distinct addresses. 31 are each instance's own
borrower, installed as its push provider at initialisation with an unbounded
time to live: 20 have no code at the observed block and 11 are contracts,
7 of them Safe proxies by their Sourcify or indexer label. The one shared
pull provider is the OpenAccessRoleProvider above, on 37 instances with a
7,776,000-second (90-day) credential; it answers `isPullProvider` true and
holds the Chainalysis `SanctionsList` `0x40c57923924b5c5c5455c48d93317139addac8fb`
as its immutable oracle. 5 instances carry no pull provider.

Deployment epochs, all from creation receipts and factory events:

| Epoch | Blocks | What |
| --- | --- | --- |
| core set | 21788178 to 21788205 (2025-02-06) | deployer `0x240334405021f4242d57a3785df39edc23e1b607`, nonces 1 to 9: market init code, HooksFactory, OpenTermHooks and FixedTermHooks templates, MarketLens `0xc672760757da93b5f3275dc97203d145806dae33`; both templates registered |
| fee recipient | 21825574, 21854968, 21873682 | OpenAccessRoleProvider (nonce 31), WildcatFeeRecipient (nonce 32), then the fee update through the Safe |
| first market | 21866550 (2025-02-17) | first `HooksInstanceDeployed` and `MarketDeployed` |
| third template | 22081282, 22094295 (2025-03-19, 2025-03-21) | 730-day FixedTermHooks init code (nonce 43), then its registration through the Safe |
| lens and collateral | 23121577, 23167812, 23168260 (2025-08-11, 2025-08-18) | MarketLens `0xfda5c5b96bb198d2fca1a01d759620b64ae5afe7` (nonce 47), collateral factory (nonce 51), CollateralLens (nonce 52) |
| wrapper factory | 24750455 (2026-03-27) | Wildcat4626WrapperFactory |
| last market | 25895380 (2026-09-03) | last `MarketDeployed` before the observed block |

The five operations-account creations agree with `cast compute-address
--nonce N` over that account, so the receipts and the nonce arithmetic date
the same contracts.

MarketLens epochs and consumers: `0xc672760757da93b5f3275dc97203d145806dae33`
is the core-set lens (block 21788205, source tag v2.0.0) and is named only by
`v2-protocol` `deployments/mainnet/deployments.json` and, as a stale in-repo
book, by `project-aleph` `manifest.yaml`. `0xfda5c5b96bb198d2fca1a01d759620b64ae5afe7`
(block 23121577, source `e1f77540`) is the lens every application-facing
consumer reads: `wildcat.ts` `src/constants.ts` as `MarketLensV2`, the
`wildcat-app-v2` lender and borrower hooks through that SDK, the docs
deployment page, `wildcat-juris` `wildcat-claims/src/wildcat/config.ts` and
`project-aleph` as `MarketLensV2`. Both stay in the row because both are
deployed, source-matched code; the SDK's `MarketLens` key is the deprecated
V1 lens `0xf1d516954f96c1363f8b0ae48d79c8dde6237847`, outside this row.

Emitter pin: `wildcat-finance/v2-protocol@f5a26146987926f4811b72a795d662813dedfe85`
from PR #1460. Every emitter, interface and hooks-base path
(`src/libraries/MarketEvents.sol`, `src/spherex/SphereXProtectedEvents.sol`,
`src/interfaces/IMarketEventsAndErrors.sol`, `src/spherex/SphereXConfig.sol`,
`src/IHooksFactory.sol`, `src/interfaces/IWildcatArchController.sol`,
`src/access/IHooks.sol`, `src/access/IRoleProvider.sol`,
`src/access/BaseAccessControls.sol`, `src/access/OpenTermHooks.sol`,
`src/lens/MarketLens.sol`, `src/interfaces/IERC20.sol`,
`src/interfaces/ISphereXProtectedRegisteredBase.sol`) has the same blob at
the pin, at v2.0.0, at the deploy-era commit `8dc8e449`, at v2.1.0 and at both
plasma-line commits `5838b2f3` and `e1f77540`; only
`src/access/FixedTermHooks.sol` differs, on the plasma line, by the 730-day
constant. The pin therefore binds to every deployed epoch of this estate: the
market init code from block 21788178, the two v2.0.0 templates from blocks
21788183 and 21788194, the 730-day template from block 22081282, and both
lenses.

Located sources. The fee recipient lives in the private
`wildcat-finance/fee-recipient-contract` at `ac73bda3642c9a7c8de64e39856b31af53f06068`
(`src/WildcatFeeRecipient.sol` blob `baf1d44ff3b4c5db74570e157886a940350eb4b6`,
`src/libraries/LibERC20.sol` blob `b31a43cda80b78c09e3b0c521875b5f4feeef865`,
verification input blob `3c6c62e5b5f755b953b49930cc290338682c14aa`, SHA-256
`6357b167846ba49110ede1a76ad7fa5fc85beec5f8ba5f0e4be8da6fc319d35d`); its constructor arguments
name the arch controller owner Safe twice. The collateral factory, its stored
child init code and the CollateralLens live in the public
`wildcat-finance/collateral-contract` on branch `multi-exchange` at
`46dba596fa111f868200358f551796e8f73b5fd7` (factory blob
`94c5228482e0eaa804a47e63f7fc0367b37eef30`, child blob
`c745896b8a9e44a4e423eda8d81306826adb42bc`, lens blob
`707ff2b8a547dc30249b74eb87113c4643ec3c76`), built under the repository's
`ir` profile with solc 0.8.28. Those sources were committed on 2025-11-24,
three months after the 2025-08-18 deployment; the `audit_2026_feb` and
`kethic/underflow-fix` branches share the factory and lens blobs but carry a
child whose creation code does not hash to the stored init code, and the
default branch carries none of the three. The open-access role provider lives
in the private `wildcat-finance/chainalysis-ofac-role-provider` at
`5d7f8c889a8d29935838a3906172feb8d9861807` (blob `5d2597a098d871857898389af97ef31831c3aa01`), which
differs from the Sourcify source only in indentation, the SPDX line and a
`view`-versus-`pure` keyword and compiles to the same runtime.

Excluded: Sepolia (11155111) deployments; Etherscan, which was not queried;
the collateral instances the collateral factory deployed; the V1 controller
factory, controllers and 7 V1 markets, which belong to the V1 row.

Protected-set exclusions, each with its owner and reason, are listed under
`protected_set_exclusions` in `targets.json`: the 31 borrower push providers
(each borrower; not protocol code, identity by code hash only), the arch
controller owner Safe (Wildcat Labs operations; a Safe proxy, Sourcify
`exact_match`), the Chainalysis `SanctionsList` and the SphereX engine
`0x4f90c0a26cc2ad22ee98398dcc02bbe314a1766a` (third parties; code hash and
Sourcify status recorded), the Bebop settlement
`0xbbbbbbb520d69a9775e85b458c58c648259fad5f` (address only), the
`protocol-ownership` delegator (no mainnet deployment located), the V1 lens,
and the collateral instances (no kickoff consumer).

### `wildcat-v2-plasma-mainnet`

Excluded by the 2026-09-13 scope approval; the dated observations below are retained.

The same estate shape on Plasma mainnet, chain 9745 (`eth_chainId`
`0x2611` from `https://rpc.plasma.to`). Observed at finalized block
32261184, hash
`0xb983d701256d863e14c8f634ea0848456788d398910ebf39046dee684af4add4`,
2026-09-12T08:29:14Z.

Source pin: `v2-protocol` commit `e1f77540fef65736374de6c847743d8ca2233fb4`
("add plasma-mainnet deployments", 2025-12-01) on the unmerged `plasma`
branch, whose head `1bc514b1b0b903b1e94ca8046741fa8c9d367294` has the same
blobs for every in-tree source of the twelve `deployments/plasma-mainnet/`
verification inputs. Against tag v2.0.0 this line differs in
`src/access/FixedTermHooks.sol` (730 days), `src/lens/MarketData.sol`,
`src/lens/HooksConfigData.sol`, and adds `src/OpenAccessRoleProvider.sol`
and `src/WildcatCopyOfChainalysisList.sol`. The emitter library and the
market interface have the same blobs as at v2.0.0. Compiler: solc
`0.8.25+commit.b61c2a91`, `cancun`, optimizer 200 runs, `viaIR` on. The
twelve inputs are listed with blob and SHA-256 in `targets.json`; the
HooksFactory, WildcatMarket, WildcatArchController and
OpenAccessRoleProvider inputs were recompiled and matched their
`output.json` byte for byte.

| Role | Contract | Address | Runtime code keccak256 | Match |
| --- | --- | --- | --- | --- |
| registry | WildcatArchController | `0xdb2e0de97d6d96aa56754635704a4273e0f348ae` | `0x06947561474996c8be6474a214c0857be0fa5b0e4eb5aab624bb7c1ed88c19c4` | recompiled; runtime identical, no immutables |
| sanctions sentinel | WildcatSanctionsSentinel | `0x37064895ba2c1e269eaf7ff32564818d08903f5b` | `0xf26374e1752f30d49309c1c709f827e6ebe548fc8d5ebf020ceccf3c787839ab` | verification input recorded; not recompiled |
| factory | HooksFactory | `0xb46bae25ac6d23148531ed1853a8881fd842e517` | `0xf655292fe7ef1f2c76eac7dfa4d2513f665942b45596f217059de486be6f94c0` | recompiled; runtime equals `deployedBytecode` modulo 22 immutable slots |
| market init code | WildcatMarket | `0x74b253041be30b7698b5f69239c271ea8db57261` | `0xe583179fb2bb61ffd06d1e8949d657ee6157894812a370d08a1fa472bf4df2a8`; creation `0xbaa6a8ea7519c36d1d1a9417fc6b59ef0d565b223b173c4691d76b5b4b8dbd0c` | recompiled; stored code is `0x00` plus the creation bytecode; hash equals `marketInitCodeHash()` |
| hooks template 0 | OpenTermHooks | `0x40217f6e5891c8f1524744c0747e07d316a0c798` | `0xb98eda9d084e6962017cedc87db6c596107d0fed39599727f17ee89eb66125a2`; creation `0x464519dae5573af83bacec80d7072c01285161bb495d8437c66d348007ab68ee` | stored code equals the recorded creation bytecode; 4 markets |
| hooks template 1 | FixedTermHooks, 730-day maximum term | `0x59010b706959c15977304c2553f3f4c697a73018` | `0x4f57d03b05ebf51479b193f2a6eda33e7202e6d70a88ce92f9b7b73087fab227`; creation `0xbbf77dc0804fe3f2b75bbdf2779642c5c8fa0f56b2fa52e6edd1af8b73798695` | stored code equals the recorded creation bytecode; 0 markets |
| lens | MarketLens | `0x7e5d6d9f9a2091dd781118514f5397a8107c81c5` | `0xa9e619f7afdc5b23cb73a6739adea5dde81fdcc3f55506ac1e9183c8722a0a6f` | verification input recorded; not recompiled |
| role provider | OpenAccessRoleProvider | `0x792f1368f8b8f450c14875eb6ff0028dfc2629b4` | `0x4008623e2fce20f82fcb0f8bdf0201f134d289f673e554533f85db478439e0f3` | recompiled; runtime equals `deployedBytecode` modulo 2 immutable slots |
| SphereX engine | SphereXEngine | `0x931fe4a88e1c1f1a7402df6a40988f38503f1061` | `0xfa19d6740e1281178fb69200cd5dd9438c7cccedc87a19069e2a091f4fa3e340` | verification input recorded; not recompiled |
| sanctions proxy | ChainalysisProxy | `0x38056f7fe6396417b191bf7dc6a3aa04235f3f46` | `0x0bea4108a880a6b0e882f26f74933c28aa205a7ec9eb18769464e5d83fa7d791` | verification input recorded; not recompiled |
| sanctions list copy | WildcatCopyOfChainalysisList | `0xfeb516d9d946dd487a9346f6fee11f40c6945ee4` | `0x472b55e3bde3f78282cfd318f6de3638479fca77ba461e31e20c01ea297676cf` | verification input at the branch head recorded; not recompiled |
| fee recipient | WildcatFeeRecipient | `0x437e0551892c2c9b06d3ffd248fe60572e08cd1a` | `0xb29ab171b6256affe18a6bb169cf2712d710dc8a33e4081e2ae9dbd850fe1cb9` | runtime hash equals the Ethereum fee recipient's; source not located |

Two addresses are reused across chains with different contracts behind
them: `0xfeb516d9d946dd487a9346f6fee11f40c6945ee4` is the arch controller
on Ethereum and a sanctions-list copy on Plasma;
`0x437e0551892c2c9b06d3ffd248fe60572e08cd1a` is the sentinel on Ethereum
and the fee recipient on Plasma. The `wrong-chain.json` specimen exists
because of this.

Estate: 2 templates, 4 markets (all OpenTermHooks), 4 borrowers, 1
controller factory. Start blocks from the subgraph manifest: arch
controller 1989721 (hash
`0x4ba78b31be560d14ada419eb40f22419898a7fe361b94b26d1ab591185f561f1`),
sentinel 1989725, HooksFactory 1989742 (hash
`0x6f58b983f039d5594ccaaf7204855fc7671b63b1700527b32a4ee0d0d3bbf7d3`).
Nothing on Plasma is verified on Sourcify; the repository's verification
inputs are the only published source binding. Excluded: Plasma testnet
(9746), the four markets' own code hashes, eight uncompiled inputs.

### `wildcat-v1-ethereum-mainnet`

Wildcat V1 controller-factory estate on Ethereum mainnet, deprecated on the
docs page. Core contracts were read at the estate block above; the factory's
views and init-code storages at finalized block 25960074, hash
`0xe60835a79184f61e49da1109be50056619701e39945f8f75c9af72400b4bf7a2`,
2026-09-12T08:16:23Z.

Source pin: https://github.com/wildcat-finance/wildcat-protocol commit
`da74452aa7d1a0f024d99efd22cc6d950a8116b7` (2023-11-30, "Add blacklisting
changes from #68"). The controller factory's 37 and the arch controller's 8
in-tree Sourcify sources have identical blobs at that commit and at
`ebb6cecc4e72ea90187bc10006f8aa35d7ae2da9`,
`e9552f0e8a093e214dd69947dc689023df09ff20`,
`e962bf37866483a3573016a3087331c5de9f0929` and
`016d0658d6d442b8f42e3bb68f01fae43c150307`. The next commit,
`6164ddd4c75ef6da2181e5623b99795b9829e31c`, rewrote every licence header,
and the sentinel's Sourcify sources match from there to the head
`488b30d08c73a93be3e4bf99128c774997411d3a`; bytecode is unaffected because
`bytecodeHash` is `none`. Compiler: solc `0.8.22+commit.4fc1097e`,
`shanghai`, optimizer 200 runs, `viaIR` on. V1 keeps no standard JSON in
its repository; the inputs are Sourcify's `stdJsonInput` documents, pinned
in `targets.json` by SHA-256 of their canonical JSON form. Recompiling
those three with `solc-linux-amd64-v0.8.22+commit.4fc1097e` (SHA-256
`8be0aeb74fc1b8213292a09a84cb524a403602526df87ecad5f5cd2a7ea7d089`)
reproduced the runtime code exactly for the arch controller and modulo
immutables for the factory and sentinel.

| Role | Contract | Address | Runtime code keccak256 | Source commit | Match |
| --- | --- | --- | --- | --- | --- |
| registry | WildcatArchController | `0xfeb516d9d946dd487a9346f6fee11f40c6945ee4` | `0x3622afdfc583101952ff6e608d76f9c897d2767297315962d97f8b3a2cc2df56` | `da74452aa7d1a0f024d99efd22cc6d950a8116b7` | as above; deployed at block 18686645 |
| sanctions sentinel | WildcatSanctionsSentinel | `0x437e0551892c2c9b06d3ffd248fe60572e08cd1a` | `0xdc8454a4d12757aaa87ab44b71a6292fc540001560d37cdfd6a3cce423b4e004` | `6164ddd4c75ef6da2181e5623b99795b9829e31c` | as above; deployed at block 18686645 |
| factory | WildcatMarketControllerFactory | `0xfd31007613c9f671df6a8d4234901324986bfd13` | `0x820f5453768df9f33465663ad5ade3416a82b821d3f39383ec2d358fd13ad945` | `da74452aa7d1a0f024d99efd22cc6d950a8116b7` | Sourcify full match; blob equality; reproduction modulo immutables; deployed at block 18687391 |
| market init code | WildcatMarket (V1) | `0xd0c690707b5642475f68a0487cea08e30a5719bd` | `0x79fa042e1a64cf7f2b02b7074c16f324ee3ac1fab1da99be6066aee6bf0138b6`; creation `0x8b23c52817c2111fa0b1b7ccbcfa266a27aa8dedcbcaad31c6799a6b1c780e93` | not reproduced | creation hash equals the factory's `marketInitCodeHash()` |
| controller init code | WildcatMarketController (V1) | `0x93caaddc316f699f9249e93a689566cefc446c3c` | `0x8e1eb2f3e38e1effddfd26b92802c0cb9aba828051fc0996696017a3cc414066`; creation `0xb9f6037204680e0dabbff502e6180d92712ea1515682089ce758f15e727f2371` | not reproduced | creation hash equals the factory's `controllerInitCodeHash()` |
| lens | MarketLens (V1) | `0xf1d516954f96c1363f8b0ae48d79c8dde6237847` | `0x60a6478c59b7c6b95d7549d05b5801203ba70e79aa63e0e5fe1a91eccd4a431f` | not pinned | Sourcify full match; 40 of 46 in-tree sources equal the head and six library files differ |

Estate: 3 controllers (`0xd22cc5d80529401cd3eedea4a6e8958c6da49cb8`,
`0xc2321ed31a274595e087b5010d200b748eb600e4`,
`0x34e7aa31d0151b60490619a8f560ce5ee8196cc6`) and 7 markets, derived as
the registered markets that no V2 template lists, sorted-list SHA-256
`b96da6374d45b26ac157a81b6811dc48931714d8baac80adb027f89fa8027c42`. Start
block 18686645, hash
`0xf875ac25e366bd6e03a94bd552c5a7be9469062e1ca9af4ca46bf4eda97f151a`, the
arch controller deployment in transaction
`0x185630a823edeb2261ae6fa92b62c1b3200facf2a54ad9356cccbf4630a75d2d`.

Unresolved: the market and controller init codes are hashed but not
recompiled from the pinned source; the V1 lens has no pinned commit; the
five equivalent commits are one source state, not one checkout.

### `wildcat-v2.5-release-line`

Excluded from deployed scope; #1485 owns any proposed-source comparison.

Proposed source, not a deployment. `v2-protocol` tag v2.5.4, commit
`bea503c2736d47de7fd34130c64f10783dc35b39`, also the `release/v2.5` head
(2026-09-05). Its `foundry.toml` sets solc 0.8.25, `cancun`, `viaIR` and
44 optimizer runs. None of the 153 in-tree sources of the five mainnet
verification inputs has the same blob at this commit, so it is a different
source state from the deployed V2 estate. `deployments/mainnet/` at this
tag holds only the V2 legacy inputs and `factory-inventory.json`, which
says revolving factories are to be added as separate entries when deployed;
`deployments/sepolia/` holds v2.5.3 Sepolia deployments (`HooksFactory`
`0x89797b782ca5b4bbfc975146b98ba3941fe26c56`, `HooksFactoryRevolving`
`0xb3fbd4fbeb1ee4bee7afdbc4a75c7c4e97cf105c`), excluded here as testnet.
The v2.5.4 release notes list pull requests 159 to 166. Whether a mainnet
deployment of this line exists outside the repository records is
unresolved. The Janus manifest `wildcat-open-term.json` names host
`wildcat-v2.5` with no commit binding.

## Repository observations from the reuse issues

The original observations below date from 2026-09-12. Selected rows are now
blocked on the specific recovery children above; the rest are excluded.
The broad framework epics remain reuse sources, not substitutes for those
recovery children. Maple V2 is now split into two approved family rows.

| Row | Repository | Default-branch head (date) | Latest tag | Owner issue | Records already in this repository |
| --- | --- | --- | --- | --- | --- |
| `aave-v3` | https://github.com/aave-dao/aave-v3-origin | `8305565ae342f1773c42cd2e4593f175fe5968a0` (2026-09-09) | v3.7.0 `cff15de6d1271b0c800fc001f4aea4c263e8a597` | #1139 | Probitas registry row `aave-v3`, unimplemented |
| `aave-v4` | https://github.com/aave/aave-v4 | `4d86c2d391b039bf2d3909fb2299b69998d0b720` (2026-08-28) | v0.5.11 `cdacec509e4f848bff1a5556f503afa83eee3b79` | #1139 | Alexandria `mappings/aave_v4.py`, Tabularium `adapters/aave_v4.py`, Lazarus `aave-v4-spoke-v1-release`, Berean `aave-v4-demo-v0` |
| `compound-v2` | https://github.com/compound-finance/compound-protocol | `a3214f67b73310d547e00fc578e8355911c9d376` (2022-06-07) | v2.31-rc1 `9ea64ddd166a78b264ba8006f688880085eeed13` | #1140 | none |
| `compound-v3` | https://github.com/compound-finance/comet | `f766f51583c23acc33b2a7824654ef2029a96804` (2026-06-23) | none | #1140 | Alexandria `compound_registry.py` pins this commit; Tabularium `compound_witness.py` names the USDC Comet proxy |
| `euler-v1` | https://github.com/euler-legacy-xyz/euler-contracts (archived) | `24da0f2de98d984b0007133b2c251e7fbbda4115` (2024-05-24) | solidified-audit `86f81180d4257376f4d4f66fbcbb7c9df64e18c2` | #1142 | Probitas `EULER_V1_PROXY`, Tabularium `adapters/euler_v1.py` |
| `euler-v2` | https://github.com/euler-xyz/euler-vault-kit, with https://github.com/euler-xyz/ethereum-vault-connector | `bfb325a6e6ca09613d940b46f72ccfe017353933` (2026-09-01); connector `838e5f72eaea25fab7d242760245244226096054` | yAudit-audit `7d2408dc1013b6f3149a5f08a69ded4dc99db7c8`; connector v1.0.1 `a7d3c29ef7e4964736e47675e0588630d6afbfd7` | #1142 | Tabularium `adapters/euler_v2.py`, Probitas `adapters/euler.py` |
| `maple-v1` | https://github.com/maple-labs/maple-core | `4577df4ac7e9ffd6a23fe6550c1d6ef98c5185ea` (2021-05-18) | v1.0.0 `d921a7c9c7bdb6b5d8794ae45ed7ac716a1a0d3c` | #1143 | none |
| `maple-v2-fixed-term` | https://github.com/maple-labs/maple-core-v2 | `f59f30c691fa0b831426d15832ee642f5ce38a42` (2025-11-27) | 2025-11, the head | #1592 | fixed-term loan source recorded separately |
| `maple-v2-open-term` | https://github.com/maple-labs/maple-core-v2 | `f59f30c691fa0b831426d15832ee642f5ce38a42` (2025-11-27) | 2025-11, the head | #1592 | open-term loan source recorded separately |
| `centrifuge-tinlake` | https://github.com/centrifuge/tinlake | `4584b0d0cc6f4c8e7600a45f72ae8dc7d6c906c7` (2022-12-29) | v0.3.0 `fc1f8e275a9d05d877e64f46810c107cde0808ce` | #1148 | none |
| `centrifuge-v2` | https://github.com/centrifuge/liquidity-pools | `e556c1a7a0ec7f6d700b47841eb586f5f4801406` (2025-01-13) | release-v2.0 `109ba1560a0aa80e906e462147ac295d31e75b73` | #1148 | none |
| `centrifuge-v3` | https://github.com/centrifuge/protocol | `48f7dff6ec83b2f7c044d35139084fb501da5f9a` (2026-09-12) | v3.2.0 `87c358fa52bea91017fc3a848bc07db815eed91c` | #1148 | none |
| `clearpool-permissionless` | not located under `clearpool-finance`, which lists only `clearpool-payfi-vaults` | none | none | #1141 | Alexandria `mappings/clearpool.py` names the pool factory `0x969d7ddbe3b6f8b51e26d8473aaac1a9f4a6b47b` |

Aave v3 also has a second repository, https://github.com/aave/aave-v3-origin,
at `5c2eb37f39959dd491ba97fdc2af94bb4ee88f41` (2025-09-19); the row names
the `aave-dao` one and records the other.

## Method

This is the original producer’s 2026-09-12 method and result record. The
2026-09-13 revision preserves its bytes and reports separately which checks
were rerun.

Chain reads used `cast` 1.7.1 (`4072e48705af9d93e3c0f6e29e93b5e9a40caed8`)
against `https://ethereum-rpc.publicnode.com` and `https://rpc.plasma.to`:
`cast block finalized`, then `cast code --block N` and `cast call --block N`
at that number, and `cast keccak` over the returned code. Each observation
block is recorded with its hash and timestamp in the evidence files. Block
hashes for start blocks and deployment transactions came from `cast block`
and `cast receipt`.

Source identity used three checks. Blob equality: the Git blob SHA-1 of
each source inside a verification input, compared with the blob the GitHub
trees API reports for the same path at each candidate commit; `lib/` paths
are compared through the submodule pins instead. Reproduction: `solc
--standard-json` over the recorded input with `outputSelection` widened,
compared byte for byte with the recorded `output.json`, and for a stored
init code compared with the on-chain bytes after the leading `0x00`.
Runtime modulo immutables: every byte where the on-chain runtime differs
from the recorded `deployedBytecode` must lie inside an
`immutableReferences` range. Sourcify's v2 API supplied verification status,
compiler settings, sources and deployment blocks; its records are copied,
trimmed, into `evidence/sourcify-summary.json`.

Not done on 2026-09-12: Etherscan was not queried; the templates'
registration blocks were not recovered because the `HooksTemplateAdded` log
query over the factory did not return; no market or hooks instance was read
individually; the V1 market and controller init codes were not recompiled;
the `collateral-contract` and fee-recipient sources were not located.

The 2026-09-18 pass for #1590 closed every Wildcat V2 item on that list
except Etherscan. Chain reads were JSON-RPC `eth_call` and `eth_getCode`
pinned to one finalized block, batched over three public endpoints, with
`keccak256` over the returned code; the factory's log history was read in
10,000-block `eth_getLogs` chunks and every log was re-read from its
receipt; creation blocks came from creation receipts, with the operations
account's `cast compute-address --nonce` arithmetic as a second witness.
Source identity used the same three checks as before, plus a fourth for
Foundry projects without a recorded verification input: `forge build` under
the repository's own profile with the compiler pinned, then runtime modulo
immutables, with the immutable values read off the chain and named. Two
private repositories were read through the GitHub API; their blob SHA-1s and
SHA-256s are recorded so a copy can be checked without access.

## Specimens

Each file under `specimens/` is one claim of the form "this address on this
chain is generation G of target T with code hash H". Results on
2026-09-12:

| Specimen | Claim | Result |
| --- | --- | --- |
| `accepted-v2-market-init-code.json` | the recorded V2 market init-code storage | accepted, exit 0 |
| `wrong-generation.json` | the same address and hash claimed as generation V1 | rejected: generation 'V1' is not the row's 'V2' |
| `wrong-code-hash.json` | the V2 market init-code address carrying the V1 market init code hash | rejected on code hash |
| `wrong-template-source.json` | the 730-day template carrying the 365-day template's hash | rejected on code hash |
| `wrong-chain.json` | the Plasma sanctions-list copy at `0xfeb516d9d946dd487a9346f6fee11f40c6945ee4` claimed on chain 1 | rejected: chain 1 is not the row's 9745 |

Added on 2026-09-18, once the row listed every hooks instance and market:

| Specimen | Claim | Result |
| --- | --- | --- |
| `accepted-v2-hooks-instance.json` | the 730-day FixedTermHooks instance `0x0004da6611b3c4f557ba88105ebd85e5bd214dcd` with its recorded runtime hash | accepted, exit 0 |
| `wrong-instance-template-hash.json` | the same instance carrying its template's stored-init-code hash | rejected on code hash |

## Evidence boundary

The approval establishes the selected venue order and Wildcat Ethereum estate.
The offline checker establishes agreement between the registry, its preserved
approval and consumer records, recovery coverage, digests and recorded code
hashes. The source-reference record establishes retrievability of the named
Git commits at the recorded time.

The evidence files record chain observations, blob comparisons and
compiler-reproduction results with their stated limits. A hash-only entry,
an unresolved source match or a located repository head does not establish
deployed identity. One selected row, `wildcat-v2-ethereum-mainnet`, claims
complete deployment coverage of the HooksFactory estate at block 26006289:
every contract it lists reproduces from a named commit byte for byte or
modulo immutables, and its excluded and third-party members are named with
an owner and a reason. That claim is about the observed block; contracts
deployed later are not in it. No result here establishes contract safety,
current chain state, an exact deployer checkout among equivalent source
trees (the collateral sources were committed after their deployment), or
completion of a consumer’s own capture, corpus, policy, proof, audit or
campaign.

## Files

- [`targets.json`](targets.json): the registry the checker reads.
- [`evidence/scope-approval.json`](evidence/scope-approval.json): operator approval, exact recorded comment and selected slots.
- [`evidence/consumer-inputs.json`](evidence/consumer-inputs.json): preserved input issues and dependency denominator.
- [`evidence/recovery-issues.json`](evidence/recovery-issues.json): source-recovery children and row coverage.
- [`evidence/source-refs.json`](evidence/source-refs.json): successful immutable source-reference reads.
- [`evidence/ethereum-mainnet.json`](evidence/ethereum-mainnet.json) and
  [`evidence/plasma-mainnet.json`](evidence/plasma-mainnet.json): every
  code read, factory and arch-controller view, market list and block anchor.
- [`evidence/source-match.json`](evidence/source-match.json): blob equality
  per commit, reproduction results, the third-template experiment, the V1
  commit search, submodule pins and the upstream repository snapshot.
- [`evidence/sourcify-summary.json`](evidence/sourcify-summary.json):
  trimmed Sourcify records for every address queried on 2026-09-12.
- [`evidence/ethereum-mainnet-1590.json`](evidence/ethereum-mainnet-1590.json):
  the 2026-09-18 estate observation: every code read at block 26006289, the
  three templates with their markets and instances, the 42 hooks instances
  with providers and epochs, the 80 markets, the 32 role providers, every
  creation receipt and the factory's 129 events.
- [`evidence/source-match-1590.json`](evidence/source-match-1590.json):
  the located fee-recipient, collateral and role-provider sources with their
  reproductions, the third-template registration, the instance and market
  bytecode comparisons, the MarketLens epoch and consumer map and the
  emitter-pin blob table.
- [`evidence/upstream/`](evidence/upstream/): byte copies of the docs
  deployment page, the subgraph manifest and the factory inventory.
- [`specimens/`](specimens/): the seven specimens above.
- `scripts/kickoff_targets.py` and `tests/test_kickoff_targets.py`: the
  checker and its tests.
