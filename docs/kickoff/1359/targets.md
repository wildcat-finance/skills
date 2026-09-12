# Kickoff target-input registry for issue 1359

Issue: https://github.com/wildcat-finance/skills/issues/1482 (prerequisite
child of https://github.com/wildcat-finance/skills/issues/1359).
Written 2026-09-12 by Shoggoth, acting as Surveyor under Protasis, in a
session run and published by Dave Coleman (kethcode, Wildcat Labs), who is
the committer and signer of the commit that carries it. The reviewer is
whoever reviews the pull request that lands it.

The four kickoff issues that depend on an unnamed venue are #1354, #1355,
#1359 and #1361; #1363 names the same registry as a prerequisite and is
carried too. Each of them now maps to at least one row of
[`targets.json`](targets.json), the machine-readable registry beside this
page. This page says what the rows hold, what still needs a human decision,
how the evidence was gathered and how to check it.

Two decisions are the target maintainer's and are recorded as `pending`.
Surveyor did not guess them, because the filing says a venue named by
protocol name is a guess. Every row is therefore `candidate` today; the
decisions section says how a row becomes `resolved`.

## Check it

```bash
python3 scripts/kickoff_targets.py check
python3 scripts/kickoff_targets.py specimen --specimen docs/kickoff/1359/specimens/wrong-generation.json
```

The first command reads the registry, recomputes the SHA-256 of every
evidence file it names, and cross-checks every contract's code hash against
the chain observation it cites. On 2026-09-12 it printed:

```text
kickoff-targets: clean; 5 consumers, 16 targets (0 resolved, 16 candidate, 0 blocked), 2 pending decision(s)
```

The second command rejects a specimen that claims the V2 market init code as
generation V1. The [specimen section](#specimens) lists all five.
`tests/test_kickoff_targets.py` holds both commands and breaks the registry
one field at a time to show the checker names each break.

## Consumers

| Issue | What it needs from the registry | Rows | Decision |
| --- | --- | --- | --- |
| [#1354](https://github.com/wildcat-finance/skills/issues/1354) fizz-4 | assembly-emitter repository, exact SHA, Foundry root, emitter and interface paths, compiler settings | `wildcat-v2-ethereum-mainnet`, `wildcat-v2-plasma-mainnet` | `kickoff-consumer-target` |
| [#1355](https://github.com/wildcat-finance/skills/issues/1355) hermes-5 | repository and commit, chain, reference block, factory, template and instance addresses, instance types mapped to source, hooks and role providers | same two rows | `kickoff-consumer-target` |
| [#1359](https://github.com/wildcat-finance/skills/issues/1359) lemma-9 | venue and generation inventory in order, source SHA per generation, chain and block scope, deployment evidence, pinned standard JSON and compiler identity | all 16 rows | `lemma-9-venue-order` |
| [#1361](https://github.com/wildcat-finance/skills/issues/1361) solidity-auditor-11 | the same inventory as #1354, deployed-source SHA per epoch | same two rows | `kickoff-consumer-target` |
| [#1363](https://github.com/wildcat-finance/skills/issues/1363) x-ray-13 | the deployed commit whose logs a capture decodes; the proposed commit belongs to #1485 | same two rows | `kickoff-consumer-target` |

## Decisions the target maintainer owes

### `kickoff-consumer-target`

Which deployed estate do #1354, #1355, #1361 and #1363 mean: the one whose
events are emitted through hand-written `log1`, `log2` and `log3`, and
whose markets a factory deploys with hooks and role providers?

What the evidence says. In the `wildcat-finance` organisation, exactly one
estate carries both features. `src/libraries/MarketEvents.sol` in
`v2-protocol` emits every market event through assembly, 22 sites at tag
v2.0.0 (9 `log1`, 9 `log2`, 4 `log3`), and `HooksFactory`
`0xdd7dd3b5076cf89440d05585ff56d246386207be` on Ethereum deploys markets
from stored init code under three hooks templates that consult role
providers. The Plasma estate is the same source line on chain 9745. V1 also
emits through assembly (21 sites at its head) but has no hooks factory and
is deprecated on the docs page.

Options: `ethereum-only` (`wildcat-v2-ethereum-mainnet`),
`ethereum-and-plasma` (both V2 rows), or `other` (the maintainer names an
estate this registry does not carry, which needs a new row).

Two sub-questions travel with it:

1. The factory lists a third hooks template,
   `0x731c775385d0efb2cac61074ba2d885d343a09cd`, named `FixedTermHooks`
   with 16 markets. It is in no deployment manifest, not on the docs page
   and not on Sourcify. This registry pins its source by reproduction (see
   the V2 row). Does it belong to the protected set for #1355?
2. `deployments/mainnet/deployments.json` names `MarketLens`
   `0xc672760757da93b5f3275dc97203d145806dae33`; the docs page names
   `0xfda5c5b96bb198d2fca1a01d759620b64ae5afe7`. Both are recorded. Which
   one is canonical?

### `lemma-9-venue-order`

Which venues and generations fill the five ordered slots #1359 inherited
from its filing: "the first venue's two generations, the second venue, the
venue with three generations, then the two remaining venues"?

The filing names no venue. The reuse issues #1139 to #1144 and #1148 name
seven. In this inventory two of them carry three generations and four carry
two, so the ordinal description does not settle on its own:

| Venue | Generations in this registry | Row ids |
| --- | --- | --- |
| Wildcat | V1, V2 (Ethereum and Plasma), V2.5 release line | `wildcat-v1-ethereum-mainnet`, `wildcat-v2-ethereum-mainnet`, `wildcat-v2-plasma-mainnet`, `wildcat-v2.5-release-line` |
| Aave | v3, v4 | `aave-v3`, `aave-v4` |
| Compound | v2, v3 | `compound-v2`, `compound-v3` |
| Euler | v1, v2 | `euler-v1`, `euler-v2` |
| Maple | v1, v2 | `maple-v1`, `maple-v2` |
| Centrifuge | Tinlake, v2 liquidity pools, v3 protocol | `centrifuge-tinlake`, `centrifuge-v2`, `centrifuge-v3` |
| Clearpool | permissionless pools | `clearpool-permissionless` |

Options: `wildcat-first` (an example shape, with Wildcat as the
three-generation venue), `maintainer-restates` (an explicit ordered list of
row ids replaces the ordinal description), or `defer` (#1359 stays blocked
on this and #1482 closes on the inventory alone).

### How a decision is recorded

Edit `targets.json`: set the decision's `status` to `recorded`, fill
`decision_maker` with `name`, `role`, `date` and an `https` `reference` (the
approving review on the pull request that carries the change, or an issue
comment), and set `selection`. Then set each selected row's `status` to
`resolved` with `decision` naming the decision id. A non-Wildcat row that a
selection names becomes `blocked` with `recovery` pointing at its
`owner_issue`, because its deployment is not pinned here. Run the check
command; it refuses a `resolved` row whose decision is still `pending` and a
`recorded` decision without a reference.

## Wildcat rows

Addresses and hashes are lowercase throughout so they match the JSON byte
for byte. Every code hash is `keccak256` of the runtime code returned by
`eth_getCode` at the observed block. A stored init code is a contract whose
code is one `0x00` byte followed by creation bytecode; for those rows the
table also gives the hash of the creation bytecode alone, which is what the
factory compares.

### `wildcat-v2-ethereum-mainnet`

Wildcat V2 HooksFactory estate on Ethereum mainnet (chain 1). Observed at
finalized block 25960042, hash
`0x3f817acb8a79c8158643f8ecdc0f1cd812ba00cf39078e76d816bf4cd7c198eb`,
2026-09-12T08:09:59Z, through `https://ethereum-rpc.publicnode.com`.

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

Deployed contracts at the observed block:

| Role | Contract | Address | Runtime code keccak256 | Source commit | How the match was made |
| --- | --- | --- | --- | --- | --- |
| registry | WildcatArchController | `0xfeb516d9d946dd487a9346f6fee11f40c6945ee4` | `0x3622afdfc583101952ff6e608d76f9c897d2767297315962d97f8b3a2cc2df56` | `da74452aa7d1a0f024d99efd22cc6d950a8116b7` (V1 repository) | Sourcify full match; blob equality with the V1 tree; solc 0.8.22 reproduces the runtime code exactly |
| sanctions sentinel | WildcatSanctionsSentinel | `0x437e0551892c2c9b06d3ffd248fe60572e08cd1a` | `0xdc8454a4d12757aaa87ab44b71a6292fc540001560d37cdfd6a3cce423b4e004` | `6164ddd4c75ef6da2181e5623b99795b9829e31c` (V1 repository) | Sourcify full match; blob equality; solc 0.8.22 reproduces the runtime code modulo immutables |
| factory | HooksFactory | `0xdd7dd3b5076cf89440d05585ff56d246386207be` | `0xf21fd79f56b27db5d249a3855eff8eff80d75a9f2177bc0018d0ba7cac39b5c0` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | verification input; Sourcify full match; solc 0.8.25 reproduction; runtime equals `deployedBytecode` modulo 22 immutable slots |
| market init code | WildcatMarket | `0xac3216fa28f81b8fae150fb5626ca79c7a570daf` | `0x3d18b90882fb6f7e36b6f942d263d42e75f3905e8cad842241031832e441e99c`; creation `0xc152ead6073d54f964e3c2fd317ec6c774e67465cf3e6fb9551badb88a09e43f` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | stored code is `0x00` plus the recorded creation bytecode; its hash equals `HooksFactory.marketInitCodeHash()` |
| hooks template 0 | OpenTermHooks | `0x4c62b4844c8371f321541e8d564a4b3896cecec7` | `0xc7d1fe188cc060abe3ca44abfffb422eb8d30ec4fbdf6d7313a6bbd1b01eb5cc`; creation `0x45a5a3cf0a4aeee877f71602848425bac849ee5bf59a2761014c7d6ee00be94f` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | stored code equals the recorded creation bytecode; 60 markets |
| hooks template 1 | FixedTermHooks, 365-day maximum term | `0x7e49caba6fb53cdc70cd98829731a2b8d76dfc36` | `0x90cbf3c32cbc9d1936ff2a3e41febe383e7385148c969e4f3ae7298f2f47c2f0`; creation `0xe283098ee6563da880b545b812e4eb94e24ee30498f2f109bbb6295c95dc3c4f` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | stored code equals the recorded creation bytecode; 4 markets |
| hooks template 2 | FixedTermHooks, 730-day maximum term | `0x731c775385d0efb2cac61074ba2d885d343a09cd` | `0xb4cbbd478498c7f02a78e33d79aff22fc024f48e77f8b6350568881588d55ab2`; creation `0x1e2fdf1700fe20e2e903b5c459c8b9db04798942ab7fe1ad49a88421dbd47a77` | `5838b2f3f5c0bb3489cd2ff16bb31ddd5194c7fa` | absent from every manifest; recompiling the FixedTermHooks input with that commit's `FixedTermHooks.sol` reproduces the stored code byte for byte; 16 markets |
| lens | MarketLens (deployments.json) | `0xc672760757da93b5f3275dc97203d145806dae33` | `0xc9364e3b8e67e771889f32df9d0589e2bbba7735e11e3b7bf8a7034635b99b8a` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | verification input; runtime equals `deployedBytecode` modulo 11 immutable slots; not on Sourcify |
| lens | MarketLens (docs page) | `0xfda5c5b96bb198d2fca1a01d759620b64ae5afe7` | `0x26ff0af4fbbbd64b3c66a82be70c034ebc7af07211a7a6c1616275c24e8944d5` | `e1f77540fef65736374de6c847743d8ca2233fb4` | Sourcify full match (runs 200); all 60 in-tree sources equal the `plasma` branch; deployed at block 23121577 |
| wrapper factory | Wildcat4626WrapperFactory | `0xea6de11f8f3f83c79bd9d8db5517fcfdf2bb148a` | `0x58bb549139a0aa9ddf20beba5645e9a940a1ca12a33f1ea0cefdb9f905386e3e` | `c7be4039f8f383a9dda4e45f63331c17d63f9ed9` (tag v2.1.0) | Sourcify full match (runs 200, `viaIR` off); all 9 in-tree sources equal the tag; deployed at block 24750455 |
| fee recipient | WildcatFeeRecipient | `0x35a5d1bd68f3139971027b92c1ee9384a0708554` | `0xb29ab171b6256affe18a6bb169cf2712d710dc8a33e4081e2ae9dbd850fe1cb9` | not located | Sourcify full match; `src/WildcatFeeRecipient.sol` is in no `v2-protocol` tree read; deployed at block 21854968 |
| collateral factory | CollateralFactory | `0xbdf64bd7ea91a534445d06736a0f0e2a33ffa47c` | `0x430982ffbd3051bd4068c561c04aed086569a4767b95cef0bece274a04260897` | not established | hash recorded only; the `collateral-contract` repository was not inspected |

The third template deserves a plain sentence. `getHooksTemplates()` on the
factory returns three addresses; the third answers
`getHooksTemplateDetails` with the name `FixedTermHooks`, index 2, enabled,
16 markets, and the same fee recipient as the other two. Its stored init
code has the same length as the 365-day template's and a different hash.
The only source difference between tag v2.0.0 and commit 5838b2f3 in
`src/access/FixedTermHooks.sol` is line 66, `MaximumLoanTerm = 365 days`
against `730 days`. Compiling the 365-day verification input with that one
file swapped in gives creation bytecode whose hash is
`0x1e2fdf1700fe20e2e903b5c459c8b9db04798942ab7fe1ad49a88421dbd47a77`,
exactly the stored code's. That commit sits on the `plasma` branch, not on
`main`.

Estate at the observed block: 3 hooks templates; 80 markets deployed under
them (60 OpenTermHooks, 4 FixedTermHooks 365-day, 16 FixedTermHooks
730-day), listed in `evidence/ethereum-mainnet.json` with SHA-256
`1b1c3684e01b3a99fe4f8ffb240639899b60ef5d7641105ef236cbf0ed73627a` over
the sorted list; 87 markets registered with the arch controller (the other
7 are V1), sorted-list SHA-256
`5a073d47686a971966098cf4d09189cc3048543ea6099751f52a70209cb171cc`; 54
registered borrowers; 2 registered controller factories (the V1
`WildcatMarketControllerFactory` and this `HooksFactory`); 4 registered
controllers (3 V1 controllers and the `HooksFactory`); arch controller owner
`0xc15be5214978d1fc509ecdd4f9d5bc067c94d9ae`.

Start block: 21788182, hash
`0xa8c8592292a62b31242bdc1e973a8092288c0f6fbf22ddb536f1aa6f4e35a4d5`, the
HooksFactory deployment in transaction
`0xe1c92956c9ec365859a40f6ef8bb1ad4b59b469dca64fcadfef1f9a935ee82df`. The
wrapper factory landed at block 24750455 (hash
`0xee783b648c000d7dc20db956b92cee90a1392f31ebb9c11de62a84fb99f11a72`,
transaction
`0x2dad1799cd230517ffb1c0e8709d8b92ca458209429b0211643570c446a41ba6`).

Documentation revisions: `wildcat-docs` commit
`636b1dcba90c816e699c0d876c22d39be2c58b06`, page
`technical-overview/contract-deployments.md`, blob
`8384e46a150d91327833559f46aabd5f1c426aed`, SHA-256
`fb46e0e41db8a226b3798c2ac8961342b24987364e11ea249cd10427043c9541`;
`subgraph` commit `63f399e6ceff76a85c14ed26017a792e15513efd`,
`networks.json` blob `bf864d9e2a02ac9b48cc013342a7519d1f59ba2a`;
`v2-protocol` `deployments/mainnet/factory-inventory.json` at tag v2.5.4,
SHA-256 `87d15ea62f69714cedd0b603aa2ff1d6f506b83c14477179b9aff82e01dbb312`.
Copies of all three sit under `evidence/upstream/`.

Excluded: Sepolia (11155111) deployments; the 80 markets' and the hooks
instances' own code hashes, each market being deployed from the recorded
init code with its own immutables; role-provider instances beyond the
templates; Etherscan, which was not queried; the templates' registration
blocks, because the log query did not answer.

Unresolved: the third template's place in the protected set; which
MarketLens is canonical; the fee recipient's and collateral factory's
source repositories.

### `wildcat-v2-plasma-mainnet`

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

## Candidate venues from the reuse issues

These rows record where each repository stood on 2026-09-12. They pin no
deployment and no build input; the owning framework issue carries that
work, and a selection under `lemma-9-venue-order` turns the row `blocked`
with `recovery` pointing there.

| Row | Repository | Default-branch head (date) | Latest tag | Owner issue | Records already in this repository |
| --- | --- | --- | --- | --- | --- |
| `aave-v3` | https://github.com/aave-dao/aave-v3-origin | `8305565ae342f1773c42cd2e4593f175fe5968a0` (2026-09-09) | v3.7.0 `cff15de6d1271b0c800fc001f4aea4c263e8a597` | #1139 | Probitas registry row `aave-v3`, unimplemented |
| `aave-v4` | https://github.com/aave/aave-v4 | `4d86c2d391b039bf2d3909fb2299b69998d0b720` (2026-08-28) | v0.5.11 `cdacec509e4f848bff1a5556f503afa83eee3b79` | #1139 | Alexandria `mappings/aave_v4.py`, Tabularium `adapters/aave_v4.py`, Lazarus `aave-v4-spoke-v1-release`, Berean `aave-v4-demo-v0` |
| `compound-v2` | https://github.com/compound-finance/compound-protocol | `a3214f67b73310d547e00fc578e8355911c9d376` (2022-06-07) | v2.31-rc1 `9ea64ddd166a78b264ba8006f688880085eeed13` | #1140 | none |
| `compound-v3` | https://github.com/compound-finance/comet | `f766f51583c23acc33b2a7824654ef2029a96804` (2026-06-23) | none | #1140 | Alexandria `compound_registry.py` pins this commit; Tabularium `compound_witness.py` names the USDC Comet proxy |
| `euler-v1` | https://github.com/euler-legacy-xyz/euler-contracts (archived) | `24da0f2de98d984b0007133b2c251e7fbbda4115` (2024-05-24) | solidified-audit `86f81180d4257376f4d4f66fbcbb7c9df64e18c2` | #1142 | Probitas `EULER_V1_PROXY`, Tabularium `adapters/euler_v1.py` |
| `euler-v2` | https://github.com/euler-xyz/euler-vault-kit, with https://github.com/euler-xyz/ethereum-vault-connector | `bfb325a6e6ca09613d940b46f72ccfe017353933` (2026-09-01); connector `838e5f72eaea25fab7d242760245244226096054` | yAudit-audit `7d2408dc1013b6f3149a5f08a69ded4dc99db7c8`; connector v1.0.1 `a7d3c29ef7e4964736e47675e0588630d6afbfd7` | #1142 | Tabularium `adapters/euler_v2.py`, Probitas `adapters/euler.py` |
| `maple-v1` | https://github.com/maple-labs/maple-core | `4577df4ac7e9ffd6a23fe6550c1d6ef98c5185ea` (2021-05-18) | v1.0.0 `d921a7c9c7bdb6b5d8794ae45ed7ac716a1a0d3c` | #1143 | none |
| `maple-v2` | https://github.com/maple-labs/maple-core-v2 | `f59f30c691fa0b831426d15832ee642f5ce38a42` (2025-11-27) | 2025-11, the head | #1143 | none |
| `centrifuge-tinlake` | https://github.com/centrifuge/tinlake | `4584b0d0cc6f4c8e7600a45f72ae8dc7d6c906c7` (2022-12-29) | v0.3.0 `fc1f8e275a9d05d877e64f46810c107cde0808ce` | #1148 | none |
| `centrifuge-v2` | https://github.com/centrifuge/liquidity-pools | `e556c1a7a0ec7f6d700b47841eb586f5f4801406` (2025-01-13) | release-v2.0 `109ba1560a0aa80e906e462147ac295d31e75b73` | #1148 | none |
| `centrifuge-v3` | https://github.com/centrifuge/protocol | `48f7dff6ec83b2f7c044d35139084fb501da5f9a` (2026-09-12) | v3.2.0 `87c358fa52bea91017fc3a848bc07db815eed91c` | #1148 | none |
| `clearpool-permissionless` | not located under `clearpool-finance`, which lists only `clearpool-payfi-vaults` | none | none | #1141 | Alexandria `mappings/clearpool.py` names the pool factory `0x969d7ddbe3b6f8b51e26d8473aaac1a9f4a6b47b` |

Aave v3 also has a second repository, https://github.com/aave/aave-v3-origin,
at `5c2eb37f39959dd491ba97fdc2af94bb4ee88f41` (2025-09-19); the row names
the `aave-dao` one and records the other.

## Method

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

Not done: Etherscan was not queried; the templates' registration blocks
were not recovered because the `HooksTemplateAdded` log query over the
factory did not return; no market or hooks instance was read individually;
the V1 market and controller init codes were not recompiled; the
`collateral-contract` and fee-recipient sources were not located.

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

## What this record establishes, and what it does not

It establishes that the named contracts held the recorded code at the
recorded blocks, that the recorded source commits compile to that code
under the recorded compilers, that the verification inputs live at the
recorded paths and digests, and that the registry agrees with its evidence
files under the checker. It establishes that every kickoff consumer maps to
a candidate row and that a wrong-generation, wrong-hash or wrong-chain
specimen is refused.

It does not establish which estate the kickoff filer meant, which venues
fill #1359's slots, that any contract is safe, that the chain still holds
the recorded code, that a source commit is the checkout a deployer used
rather than one of the equivalent commits, or anything about the
non-Wildcat venues beyond where their repositories stood on the day. A
maintainer's selection is recorded in `targets.json` when it happens, and
this page does not pretend to have it.

## Files

- [`targets.json`](targets.json): the registry the checker reads.
- [`evidence/ethereum-mainnet.json`](evidence/ethereum-mainnet.json) and
  [`evidence/plasma-mainnet.json`](evidence/plasma-mainnet.json): every
  code read, factory and arch-controller view, market list and block anchor.
- [`evidence/source-match.json`](evidence/source-match.json): blob equality
  per commit, reproduction results, the third-template experiment, the V1
  commit search, submodule pins and the upstream repository snapshot.
- [`evidence/sourcify-summary.json`](evidence/sourcify-summary.json):
  trimmed Sourcify records for every address queried.
- [`evidence/upstream/`](evidence/upstream/): byte copies of the docs
  deployment page, the subgraph manifest and the factory inventory.
- [`specimens/`](specimens/): the five specimens above.
- `scripts/kickoff_targets.py` and `tests/test_kickoff_targets.py`: the
  checker and its tests.
