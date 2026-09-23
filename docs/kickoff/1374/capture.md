# Kickoff reference capture: selection, specification and blocker

Issue: https://github.com/wildcat-finance/skills/issues/1490, a prerequisite
child of https://github.com/wildcat-finance/skills/issues/1374.

**The reference capture target is the Wildcat V1 and V2 Ethereum mainnet
estate. No capture of it exists, and the interval collector cannot produce one.
This record selects the target, specifies what its capture must contain, and
hands the missing capability to
[#1731](https://github.com/wildcat-finance/skills/issues/1731).** Nothing here
is sealed, because there are no bytes to seal.

Dr Laurence E. Day, capture maintainer, decided this on 2026-09-18 by answering
six structured questions in the delivery session across two rounds. The
[decision comment](https://github.com/wildcat-finance/skills/issues/1490#issuecomment-5737251991)
reproduces each question, every option offered and the option selected,
including the two round-one answers that round two superseded. The delivery
session posted it from his account; it is not a separate GitHub review.
[`evidence/decision.json`](evidence/decision.json) preserves the same answers
and binds that comment's 7,207 bytes by SHA-256.

Shoggoth prepared the evidence as Surveyor under Protasis. The reviewer is the
independent agent the decision-maker chose; its report names the digests it
checked and sits in [`evidence/review.json`](evidence/review.json) and the body
of the pull request that adds this record. It ran twice and raised five
findings, three of them against claims this record made: an overstated Sourcify
count, two paraphrased gap reasons presented as quotations, and a wrong
description of which registry entry a specimen mutates. Each was corrected here.
Two of the five were answered after the reviewer's last round, so the bytes now
on disk are not reviewed in full, and `not_established_by_this_review` in that
file says so.
[`capture.json`](capture.json) carries the selection, the specification and the
inventory in a form #1374 can read.
[`evidence/sources.json`](evidence/sources.json) holds every file read with its
digest, and [`evidence/commands.json`](evidence/commands.json) holds the six
commands and their results. Every path and line below is at
`f0fa0c6632bd5fbef7f35e731646c32741ef282a`.

## Decisions

| Question | Selected | Recommended when asked |
| --- | --- | --- |
| What does this record select as the reference capture? | asked for an explanation; named Wildcat V1/V2 as the target | Compound v3 under a narrow scope |
| How is the tail between the interval end and the finality boundary treated? | Scope bound, not a gap | Scope bound, not a gap |
| Where does the adapter blocker go? | New narrow issue | New narrow issue |
| Who does the record name as reviewer? | Independent agent | Independent agent |
| What does this PR deliver? | Select Wildcat, specify, blocker | Select Wildcat, specify, blocker |

Round one offered three ways to seal the existing Compound v3 release. He took
none of them, asked what a reference capture is, and said Wildcat V1/V2 should
be it. Round two replaced the selection question and the blocker question with
that premise in place. Both superseded answers are in the decision comment; the
record does not quietly drop them.

## The registry as it stands

[`../1359/targets.json`](../1359/targets.json) admits nine targets. All nine
are `blocked`. Seven carry no deployment at all.

| Target | Status | Deployment recorded |
| --- | --- | --- |
| `wildcat-v1-ethereum-mainnet` | blocked | yes |
| `wildcat-v2-ethereum-mainnet` | blocked | yes |
| `aave-v3` | blocked | no |
| `maple-v1` | blocked | no |
| `maple-v2-fixed-term` | blocked | no |
| `maple-v2-open-term` | blocked | no |
| `euler-v1` | blocked | no |
| `euler-v2` | blocked | no |
| `centrifuge-v3` | blocked | no |

The two Wildcat rows are the only admitted targets whose deployment identity is
recorded well enough to specify a capture against. That is why the selection
lands there rather than being a preference.

Alexandria holds one sealed interval release, over the Compound v3 USDC Comet.
Its registry row `compound-v3` is `excluded`: "Outside the operator-approved
five-venue order and Ethereum Wildcat estate; retained as a dated inventory
observation, not an admitted target." It is not the reference capture, and it
is not an interim one.

## What the Wildcat capture must contain

Both rows share `eip155:1`, the WildcatArchController at
`0xfeb516d9d946dd487a9346f6fee11f40c6945ee4` and the WildcatSanctionsSentinel
at `0x437e0551892c2c9b06d3ffd248fe60572e08cd1a`. The observed head both are
recorded against is block 25,960,042, hash
`0x3f817acb8a79c8158643f8ecdc0f1cd812ba00cf39078e76d816bf4cd7c198eb`,
2026-09-12.

| | V1 | V2 |
| --- | --- | --- |
| Start block | 18,686,645 (2023-11-30) | 21,788,182 (2025-02-06) |
| What starts it | WildcatArchController deployment | HooksFactory deployment |
| Start block hash | `0xf875ac25e366bd6e03a94bd552c5a7be9469062e1ca9af4ca46bf4eda97f151a` | `0xa8c8592292a62b31242bdc1e973a8092288c0f6fbf22ddb536f1aa6f4e35a4d5` |
| Contracts with a recorded code hash | 6 | 12 |
| Of those, a Sourcify match | 4 | 6 |
| Blocks to the observed head | 7,273,397 | 4,171,860 |
| Factory | WildcatMarketControllerFactory `0xfd31007613c9f671df6a8d4234901324986bfd13` | HooksFactory `0xdd7dd3b5076cf89440d05585ff56d246386207be` |

Every contract address, code keccak and code length is in
[`capture.json`](capture.json) under `required_capture`, copied from the
registry rather than retyped.

The eight contracts without a Sourcify match are matched by other means, and
`matched_by_other_means` in [`capture.json`](capture.json) carries each one's
method verbatim. They are not equally strong, and a capture should not treat
them as one class:

- V1's two init-code storage rows are the weakest in either estate after
  CollateralFactory. Each is a keccak comparison against the figure the
  controller factory reports at the observed block, and each says in as many
  words "not reproduced from source in this pass".
- V2's market init-code row, its OpenTermHooks and 365-day FixedTermHooks
  templates, and its MarketLens at `0xc672760757da93b5f3275dc97203d145806dae33`
  are reproduced byte for byte by solc 0.8.25 from a verification input in the
  v2-protocol tree; the three init-code rows additionally match a stored
  init-code keccak.
- V2's 730-day FixedTermHooks template is in no deployment manifest, docs page
  or Sourcify. It is reproduced by recompiling the FixedTermHooks input with
  `src/access/FixedTermHooks.sol` taken from commit `5838b2f3`, which is a
  different commit from the other templates'.
- V2's CollateralFactory is the weakest row in either estate: "code hash
  recorded only; not on Sourcify; the collateral-contract repository was not
  inspected".

Three properties the capture must carry, each taken from the pattern release
below rather than invented here: an interval bounded by its opening and closing
block hashes with a declared finality policy; per-component coverage with a
`gaps` list where every gap states a reason; and a second transport reconciled
against the first, with the comparison count and the disputed set both recorded.

The registry's own unresolved items stay unresolved and are not this record's
to close. For V2 they are the third FixedTermHooks template's registration
epoch, the two MarketLens deployments, and the WildcatFeeRecipient and
CollateralFactory sources. For V1 they are the market and controller init-code
hashes, the MarketLens source commit, and the deployer's exact checkout among
five equivalent commits.

## The worked pattern

The Compound v3 USDC Comet release is the shape a Wildcat capture must reach.
It is inventoried here for that reason and no other.

Release `sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32`,
format `alexandria-release/v1`, 9 components, 429,114 bytes. Ethereum mainnet
blocks 25,903,935 to 25,905,934 over the proxy
`0xc3d688b66703497daa19211eedff47f25384cdc3`, in four shards of 500 blocks
carrying 47, 25, 6 and 15 logs, 93 in all. The interval opens at
`0xa4e35dad60b77815249c12cf22ad83056f2ad041ef9b6340dee03e83502d70f0` and closes
at `0xc0ac604f5eaf0b78ee147ed3cec4f5c5ab1f7d66d1607266cbf343d7bdc959bd`. The
second transport compared 106 items, matched 106 and disputed none.

| Component | Role | Bytes | Coverage status |
| --- | --- | --- | --- |
| `boundary-blocks` | json-rpc-response | 89,359 | partial |
| `epoch-evidence` | json-rpc-response | 168,231 | partial |
| `epoch-table` | interval-receipt | 2,241 | complete |
| `error-receipts` | error-receipt | 56 | complete |
| `implementation-code` | implementation-code | 74,602 | complete |
| `interval-plan` | capture-contract | 722 | complete |
| `logs` | json-rpc-response | 64,597 | partial |
| `reconciliation` | provider-reconciliation | 1,073 | complete |
| `registry` | deployment-registry | 28,233 | partial |

Every SHA-256 is in [`capture.json`](capture.json). The four `partial` rows each
carry their reason, in these words:

- "the traces evidence class was not declared by the plan, so it was never requested or preserved; no internal call to the proxy was preserved"
- "no credit event, position observation or repayment conclusion is derived here"
- "27 of the 28 registry entries at the pin were not collected; this release covers the Ethereum USDC Comet only"

The first two are carried by `boundary-blocks`, `epoch-evidence` and `logs`; the
third by `registry`. `boundary-blocks` and `logs` also name
`credit-event-mapping` as an unsupported collection.

Four commands reproduce all of it offline, with no network. Each exits 0 and the
release identifier is identical across all four:

```bash
python3 plugins/alexandria/examples/usdc-interval-live-v0/demo.py build --output <out>
python3 plugins/alexandria/examples/usdc-interval-live-v0/demo.py verify <out>
python3 plugins/alexandria/scripts/alexandria.py verify <out>/release
python3 plugins/alexandria/scripts/usdc_interval.py check <out>/release
```

## Why the collector cannot produce the Wildcat capture

Two independent causes.

**The registry byte-pin.**
`plugins/alexandria/scripts/alexandria_lib/compound_registry.py:216` hashes the
whole registry and compares it to a single constant. Above it, `validate_registry`
pins the format string, the Comet repository URL, the commit, both tree
identities, a count of exactly 28 entries and a market allowlist.
`plugins/alexandria/scripts/usdc_interval.py:1184` calls it on every build. Two
specimens, each exiting 1:

| Specimen | Refusal | Refused at |
| --- | --- | --- |
| [`specimens/wildcat-v2-registry.json`](specimens/wildcat-v2-registry.json), declaring the V2 HooksFactory | `usdc-interval: Compound registry format is unknown` | `compound_registry.py:165` |
| the shipped registry with `entries[0].proxy` set to the HooksFactory | `usdc-interval: Compound registry bytes do not match the pinned registry` | `compound_registry.py:216` |

The second reaches the byte-pin rather than the format check, so the pin
refuses on its own. Its exact mutation recipe is in
[`evidence/commands.json`](evidence/commands.json).

**The epoch model.**
`plugins/alexandria/scripts/alexandria_lib/interval.py:77-78` hard-wires the
EIP-1967 implementation slot and the `Upgraded(address)` topic, and epochs are
derived only from those at `:1188` and `:1243`. No contract in either Wildcat
row is an upgradeable proxy: the estate is direct deployments, stored init code
and create2 clones. There is no upgrade log to read and no implementation slot
to sample, and the axis that does vary, the set of market instances the factory
emits, has nowhere to go in this model.

This cause is read from source, not executed. Because the estate has no
upgradeable proxy, there is no input that would reach a refusal here, so no
specimen is offered for it.

[#1731](https://github.com/wildcat-finance/skills/issues/1731) owns both.
[#1379](https://github.com/wildcat-finance/skills/issues/1379) is related and is
not a prerequisite: it generalises subject filtering across a 200-subject,
six-venue, five-chain campaign and names neither cause. #1490 forbids depending
on it.

## The tail

The Compound release's declared interval is fully swept.
`staging/checkpoint.json` records `next_shard` 4 and a last accepted block of
25,905,934, which is the declared end. Zero blocks inside the declared interval
are unswept.

The plan's finality boundary is block 25,919,986, which leaves 14,052 blocks
between the interval end and that boundary. The record treats those as a scope
bound rather than a gap, on the maintainer's decision: the plan never declared
them, and naming them a gap would record a hole the interval never claimed to
fill.

#1374's premise that a tail of the declared interval was left unswept does not
hold for this release. When the Wildcat capture is collected, its own tail is a
fact about that run and is not settled here.

## Consumers

| Consumer | What it takes from here | Still blocked on |
| --- | --- | --- |
| [#1374](https://github.com/wildcat-finance/skills/issues/1374) | the selected target, the specification its `dataset/v1` statement must cover, and the pattern release's coverage and gap shape | the capture itself, via [#1731](https://github.com/wildcat-finance/skills/issues/1731) |
| [#1493](https://github.com/wildcat-finance/skills/issues/1493) | the same selected target, for its consumer value map | the same |

#1374 cannot bind a Wildcat `dataset/v1` statement until a Wildcat capture
exists. This record supplies everything about that capture except its bytes.

## What this does not establish

No Wildcat capture exists; this selects and specifies one. The Compound v3
release covers no admitted target, and inventorying it here does not admit it.
Nothing here establishes provider completeness, publisher identity, consensus
finality or canonical-chain membership, and it derives no credit event,
position or repayment conclusion. It authorises no live capture, no endpoint and
no provider spending; selecting the interval and authorising a run remain the
capture maintainer's decisions.

## Refresh of 2026-09-20

Everything above this heading is the observation of 2026-09-18, at
`f0fa0c6632bd5fbef7f35e731646c32741ef282a`. It is left as written, with one
exception: a metaphor in the byte-pin section became the plain verb "refuses"
so that the prose lint passes. That edit changed no claim. This note
records what [`capture.json`](capture.json) reads now and which of its fields
moved. Step 5 of the delivery run for
[#1731](https://github.com/wildcat-finance/skills/issues/1731) made the change.

`source_revision` moved from `f0fa0c6632bd5fbef7f35e731646c32741ef282a` to
`97773e760171a55995bbebad8f7dfa69d5f64be7`. That commit refreshed the registry
under [`../1359`](../1359) from `origin/main` at
`aededf66434ed4b4e3994bbaab5f1005fe10b453`. A file cannot name the commit that
contains it, so the record names the commit directly before its own. At that
commit both kickoff rows of `inputs` reproduce the byte count and SHA-256 of the
file they name.

| Target | Status on 2026-09-18 | Status now |
| --- | --- | --- |
| `wildcat-v1-ethereum-mainnet` | blocked | resolved |
| `wildcat-v2-ethereum-mainnet` | blocked | resolved |

The registry closed both rows after 2026-09-18.
[#1590](https://github.com/wildcat-finance/skills/issues/1590) read the V2
instances, hooks and role providers, and recovered the fee recipient,
collateral and role-provider sources the V2 row lacked.
[#1748](https://github.com/wildcat-finance/skills/issues/1748) recovered the
init-code and MarketLens source matches the V1 row lacked.
[#1589](https://github.com/wildcat-finance/skills/issues/1589) read every V1
controller and market instance.
[Pull request 1736](https://github.com/wildcat-finance/skills/pull/1736) rewrote
`../1359/evidence/source-match-1590.json` to carry the fee recipient's
recompilation record. The refreshed `targets.json` binds that file by digest. It
is not an `inputs` row here.

Two `inputs` rows moved, `inputs[0]` and `inputs[1]`, and no others:

| Row | Bytes before | Bytes now | SHA-256 before | SHA-256 now |
| --- | --- | --- | --- | --- |
| `docs/kickoff/1359/targets.json` | 164,821 | 340,997 | `9e0d3c88c76ec727ea8aabe67fb8ac0648b039ef1fa9836a6a7f2f2ae4d4ca98` | `417f727d018ecbfa86efb23ea8c9cdfc53d429cf3f4a6285543ae24e89fc40ea` |
| `docs/kickoff/1359/targets.md` | 53,142 | 74,040 | `4bd599b1967819ac65db95cecce3b05d0c6ef60f4b145eb051a60668d22dc443` | `f3d310e11f2adbefb341a2831092875f753df383c0b71970c290f2c004ba3baf` |

Seven fields moved in each `required_capture` row. Each is derived from the
matching registry row and none is typed:

| Field | V1 before | V1 now | V2 before | V2 now |
| --- | --- | --- | --- | --- |
| `registry_status` | blocked | resolved | blocked | resolved |
| `registry_blocker` | one sentence pair | null | one sentence pair | null |
| `contracts` | 6 entries | 16 entries | 12 entries | 137 entries |
| `contract_count` | 6 | 16 | 12 | 137 |
| `code_hash_recorded_count` | 6 | 16 | 12 | 137 |
| `sourcify_match_count` | 4 | 4 | 6 | 7 |
| `unresolved` | 3 items | null | 3 items | null |

The V1 `sourcify_match_count` is the one cell whose value did not change. It is
still derived. `selection.reference_target` did not move, because it already
named both estates.

Fields this refresh did not move, which a reader should not take as current:

- `inputs[2]` to `inputs[8]`, the collector-source rows, stay as observed on
  2026-09-18. At `97773e760171a55995bbebad8f7dfa69d5f64be7` five of them still
  reproduce. `plugins/alexandria/scripts/usdc_interval.py` is 111,898 bytes
  there against the 103,886 recorded, and
  `plugins/alexandria/scripts/alexandria_lib/interval.py` is 87,399 against
  69,955, because the #1731 delivery changed both. The `blockers` line
  references were read against the recorded bytes.
- `matched_by_other_means` still lists the 2 V1 and 6 V2 entries of 2026-09-18.
  The refreshed `contracts` arrays carry 12 V1 and 130 V2 entries without a
  Sourcify match, each with its method.
- The V2 `observed_block` and `blocks_to_observed_head` still name block
  25,960,042. The registry's V2 row now observes block 26,006,289 and keeps
  25,960,042 as `prior_observed_block`.
- `selection.admitted_targets_blocked` still lists both Wildcat rows.

[`tests/test_kickoff_capture_record.py`](../../../tests/test_kickoff_capture_record.py)
now recomputes both kickoff `inputs` rows and the seven fields on both rows,
and checks this note's revision and status table against the JSON. The registry
can no longer move without this record failing a test.

## Refresh of 2026-09-23

[#1591](https://github.com/wildcat-finance/skills/issues/1591) resolved the
`aave-v3` row, which rewrote `../1359/targets.json` and `../1359/targets.md`.
Two `inputs` rows moved, `inputs[0]` and `inputs[1]`, and no others:

| Row | Bytes before | Bytes now | SHA-256 before | SHA-256 now |
| --- | --- | --- | --- | --- |
| `docs/kickoff/1359/targets.json` | 340,997 | 400,627 | `417f727d018ecbfa86efb23ea8c9cdfc53d429cf3f4a6285543ae24e89fc40ea` | `ccc5e89816258f537af532bf7ea5c34fd48fa05282dacc1e20341859a7c0b319` |
| `docs/kickoff/1359/targets.md` | 74,040 | 82,600 | `f3d310e11f2adbefb341a2831092875f753df383c0b71970c290f2c004ba3baf` | `78be25361dc7f876b67e264aaec4316cfe36a7e11606eef0dcd521fa60a0a9ae` |

Neither Wildcat row changed, so both `required_capture` rows and
`source_revision` stay as the 2026-09-20 refresh left them.

## Aave row refresh of 2026-09-23

Step 5 of the [#1872](https://github.com/wildcat-finance/skills/issues/1872)
delivery made this change, after
[#1591](https://github.com/wildcat-finance/skills/issues/1591) resolved the
`aave-v3` row. The record still listed that row as blocked and without a
deployment, and carried no `required_capture` row for it.

`source_revision` moved from `97773e760171a55995bbebad8f7dfa69d5f64be7` to
`b479c21b72d58edcf1a2e8f1ca9910fc37ab5a6d`, the commit directly before the one
carrying this note. No `inputs` row moved: #1591 had already moved `inputs[0]`
and `inputs[1]`, and at `b479c21b72d58edcf1a2e8f1ca9910fc37ab5a6d` both still
reproduce the byte count and SHA-256 of the file they name.

| Target | Status on 2026-09-18 | Status now |
| --- | --- | --- |
| `aave-v3` | blocked | resolved |

`required_capture` gains a third row, for `aave-v3`. It carries `target` and
seven fields, each derived from the registry row and none typed:

| Field | Value |
| --- | --- |
| `registry_status` | resolved |
| `registry_blocker` | null |
| `contracts` | 22 entries |
| `contract_count` | 22 |
| `code_hash_recorded_count` | 22 |
| `sourcify_match_count` | 21 |
| `unresolved` | null |

The `aave-v3` row records each contract's Sourcify outcome in
`code_match.verification` rather than in the `code_match.sourcify` field the
Wildcat rows use. Of its 22 contracts, 10 read `sourcify:exact_match`, 11 read
`sourcify:match` and 1 reads `blockscout eth-bytecode-db:partial`. The count
takes both Sourcify outcomes and leaves the Blockscout contract out. The row
does not copy the chain, block, `matched_by_other_means` or proxy fields the
Wildcat rows carry; the registry row holds them.

Two `selection` lists moved. Both are now derived from the registry's admitted
slots rather than typed:

| Field | Before | Now |
| --- | --- | --- |
| `admitted_targets_blocked` | 9 targets | 6 targets |
| `admitted_targets_without_deployment` | 7 targets | 6 targets |

`wildcat-v1-ethereum-mainnet`, `wildcat-v2-ethereum-mainnet`, `aave-v3` left
the blocked list because their registry rows are resolved. `aave-v3` left the
list without a deployment because its row now records one. Both lists now name
`maple-v1`, `maple-v2-fixed-term`, `maple-v2-open-term`, `euler-v1`,
`euler-v2`, `centrifuge-v3`. The two Wildcat entries are the ones the
2026-09-20 note listed as not current. `admitted_targets` and
`admitted_target_count` were re-derived and did not move.

The two Wildcat `required_capture` rows did not move. Fields this refresh did
not move, which a reader should not take as current:

- `inputs[2]` to `inputs[8]`, the collector-source rows, stay as observed on
  2026-09-18. At `b479c21b72d58edcf1a2e8f1ca9910fc37ab5a6d` 5 of them still
  reproduce. `plugins/alexandria/scripts/usdc_interval.py` is 175,756 bytes
  there against the 103,886 recorded.
  `plugins/alexandria/scripts/alexandria_lib/interval.py` is 96,697 bytes there
  against the 69,955 recorded.
- The V2 `observed_block` and `blocks_to_observed_head` still name block
  25,960,042. The registry's V2 row observes block 26,006,289.
- `matched_by_other_means` still lists the entries of 2026-09-18.

[`tests/test_kickoff_capture_record.py`](../../../tests/test_kickoff_capture_record.py)
now covers the `aave-v3` row and the two `selection` lists, reads a Sourcify
outcome from either field, and refuses by name a contract that records both.
