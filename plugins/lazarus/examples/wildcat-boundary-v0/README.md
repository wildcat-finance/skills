# Wildcat boundary fixtures, v0

This example generates one Lazarus plan-v3 per Wildcat estate on Ethereum
mainnet at the block where that estate's sealed interval capture reports its
finalized boundary: V1 at block 22074622 (`0x150d4fe`) and V2 at block
26022093 (`0x18d10cd`). Each plan proves under EIP-1186 every storage word
behind every number the accepted value map says a consumer will print. It also
proves the code at every subject address, records the map's finite request
inventory byte for byte, and carries one scoped receipt witness. The plans are
regenerated, not committed. The fixtures captured from them, their releases and
their Alexandria admissions live in Miskatonic custody, as
`docs/decisions/drafts/keep-wildcat-boundary-fixtures-in-miskatonic-custody.md`
records. No fixture byte is in this repository. What is committed is each
capture's record and each estate's per-value relation report, described below.

The example reads the value map under `docs/kickoff/1384/` and needs a full
source checkout: the portable package omits everything here except this
README, and the generator refuses to run from anywhere but the repository root.

## Files

- `plan_v3.py`: the plan generator. This copy is the maintained one; the
  study-time copy accepted a probe from any path and defaulted both elapsed
  limits to 7,200 s.
- `wildcat_slots.py`: storage-slot derivation for the V1 and V2 market
  layouts, the balance layouts of the underlying tokens and the proxy pointer
  words.
- `probe.py`: the study-time probe that read every derived word from an
  archive node and compared it with the deployed getter. It reaches a network
  and is not rerun here.
- `probe-v1.json` and `probe-v2.json`: the probe's summaries at each boundary,
  with queue indices, token layouts, pointer words, per-market word counts,
  route outcomes and the receipt witness target.
- `plans.json`: each plan's SHA-256, byte count and counts of requests, proof
  targets and slots, as the generator printed them.
- `capture.py`: the capture driver. `capture` calls Lazarus's capture routine
  with the gateway bearer as a request header; `record` verifies a finished
  fixture offline and writes its capture record.
- `capture-v1.json` and `capture-v2.json`: each capture's record: the plan
  identity, the fixture manifest digest, each component's path, byte count and
  SHA-256, the verify report, and the terminal result with the measured
  elapsed seconds.
- `relations.py`: the relation report generator.
- `relations-v1.json` and `relations-v2.json`: each estate's report giving all
  61 value-map rows one evidence class and the entries that back it.

## Regenerate the plans

From the repository root, with no network:

```bash
python3 plugins/lazarus/examples/wildcat-boundary-v0/plan_v3.py --generation v1 \
  --probe plugins/lazarus/examples/wildcat-boundary-v0/probe-v1.json --out <fresh-v1-plan>
python3 plugins/lazarus/examples/wildcat-boundary-v0/plan_v3.py --generation v2 \
  --probe plugins/lazarus/examples/wildcat-boundary-v0/probe-v2.json --out <fresh-v2-plan>
python3 plugins/lazarus/scripts/lazarus.py validate plan <fresh-v1-plan>
python3 plugins/lazarus/scripts/lazarus.py validate plan <fresh-v2-plan>
```

`plans.json` records what those commands produce: V1
`13770a6987eed0c819809c6d68c8874a1fe243b148021a9cbee29511b736fa1c`, 196,264
bytes, 434 requests, 21 proof targets and 244 slots; V2
`0dcfbc330633ceb29e4c67819e33639681ef58e9ce4a0628bb7de316f20c285a`, 7,041,376
bytes, 14,561 requests, 151 proof targets and 9,080 slots. The elapsed limit
defaults to 3,600 s for V1 and 7,200 s for V2; another value changes the plan
bytes and the digest. `plugins/lazarus/tests/test_wildcat_boundary.py`
regenerates both plans and holds them to the record.

The generator reads only `docs/kickoff/1384/` and files inside its own
directory, and writes only to `--out`. It refuses when the request inventory
expanded from the value map differs in bytes or count from `request-spec.json`,
when a market's derived word count in any group differs from what the probe
read, when `--probe` is not a regular file inside this directory, when `--out`
exists or is a symlink, and when the current directory is not the repository
root.

## Capture the fixtures

Lazarus's `capture` command takes its RPC URL in argv and sends no request
header, while the gateway that served these boundaries authenticates with a
bearer header. `capture.py` reads the gateway URL from
`ALEXANDRIA_COMPOUND_RPC_URL` and the bearer from `ALEXANDRIA_RPC_BEARER`
inside the process, calls `lazarus_lib.capture.capture_fixture` with the URL
as its primary route and the bearer as an `authorization` header, and maps the
plan's two anchor sources to environment variable names: `local-archive` to
`RETH_RPC_URL` and `public-archive` to `PUBLIC_ARCHIVE_RPC_URL`. Neither value
enters argv, a file or the printed output. The output is Lazarus's own
terminal result, which Lazarus redacts against the union of provider secrets,
inside an envelope that adds the generation, the plan digest and the measured
elapsed seconds. The driver refuses when a named variable is unset, when the
plan is not the one `plans.json` records for the generation, and when `--out`
exists or is a symlink. A capture that fails at any stage leaves no fixture;
Lazarus's failure result names the stage and the counts it reached.

The fixtures land in private custody: a directory with mode 0700 outside every
checkout, whose path is not recorded here. From the repository root, with the
four variables exported in a subshell:

```bash
python3 plugins/lazarus/examples/wildcat-boundary-v0/capture.py capture --generation v1 \
  --plan <fresh-v1-plan> --out <custody>/v1-fixture > <custody>/v1-terminal.json
python3 plugins/lazarus/scripts/lazarus.py verify <custody>/v1-fixture
python3 plugins/lazarus/examples/wildcat-boundary-v0/capture.py record --generation v1 \
  --fixture <custody>/v1-fixture --terminal <custody>/v1-terminal.json \
  --out plugins/lazarus/examples/wildcat-boundary-v0/capture-v1.json
python3 plugins/lazarus/examples/wildcat-boundary-v0/relations.py --generation v1 \
  --plan <fresh-v1-plan> --out plugins/lazarus/examples/wildcat-boundary-v0/relations-v1.json
```

The same four commands with `v2` capture and record the second estate. `verify`
reaches no network, and `record` verifies the fixture a second time in process
before it writes anything. Both `record` and `relations.py` refuse an output
path that exists.

## What the captures recorded

Both captures ran on 2026-09-27 from plans regenerated to the digests above.
The numbers here are copied from the committed records.

| Record | V1 | V2 |
| --- | --- | --- |
| Fixture digest | `fac341a25dceb33b81a99600a6520e667a4413b8bb46e4b97e839ffb82739c2d` | `1f4a54d32c7359da494abbc06626148ad479fb3a22c61d59c4f225416726eac9` |
| Elapsed seconds | 26.322 | 787.337 |
| RPC requests sent, response bytes | 483, 2,431,517 | 14,870, 36,786,929 |
| Component bytes, with the manifest | 2,976,898 | 49,254,101 |
| Proof-backed, header-bound, recorded-RPC, receipt-trie-proved | 265, 1, 434, 2 | 9,231, 1, 14,561, 2 |
| Chain-anchor records | 2 | 2 |
| Recorded calls whose outcome is an error | 1 | 4 |

The study projected 25.9 s for V1 and 598 s for V2 at the probe's per-request
time; the observed V1 time is 26.322 s and the observed V2 time is
787.337 s, over its projection and under the plan's 7,200 s limit. The verify
counts equal the study's expectation for both
estates: proof targets plus slots, one header, the plan's requests, and the two
receipt relations. Each fixture holds six components and a manifest; the
records list every component's byte count and SHA-256. V1's one recorded error
is a `getAvailableWithdrawalAmount` call that reverts at the boundary; V2's four are `getAvailableWithdrawalAmount` calls that revert the same way.
Those calls stay recorded errors and their rows keep the class the proved
words give them.

## Which class a row gets

`relations.py` gives each of the 61 rows in `docs/kickoff/1384/values.json`
exactly one class, and each report states under `legend` what the classes
cover and that a recorded response is never proved. `proved` means every number behind the row is a storage
word or code the fixture proves under EIP-1186: the four state words for the
`state.*` rows and everything `currentState()` derives from them, the
underlying token's balance word for `credit.totalAssets`, the queue head and
data words for `native.unpaidExpiries`, the account, batch and status words for
the per-account and per-batch rows, and the market's runtime code for the
immutables behind `credit.asset`, the `config.*` rows and the four
`native.*` rate and duration rows. `header-bound` is `credit.observedAt`, the
header timestamp. `recorded` would mean only an exact recorded response backs
the row; no row needs it. `unsupported` is every row the map marks unsupported
and every row that is not in the estate, with the reason named. Per estate
that is 43 proved, 1 header-bound, 0 recorded and 17 unsupported: 14 rows the
map marks unsupported and 3 that belong to the other generation.

A proved row lists the word groups that back it. Each group carries its target
and slot counts, its first entry, and a SHA-256 over the whole group, sorted
`address:slot` lines with a trailing newline, so a reader can recompute it
from the regenerated plan without the report listing 9,080 V2 slots. A
`currentState()` derivation also names the header timestamp it accrues to and
the market code its rates come from, and a derivation that reads the market's
cash names the balance word too. The row's recorded views are listed the same
way, by request family, with the count of those calls whose recorded outcome
is an error. The three `native.batch.*` rows in V1 carry the differing
recorded view of market `0x605309f21c1864bb0522781a2f97b91fe3a48601` at
expiry 1742310239, with the stored and simulated value of each field; in V2
that list is empty. The `native.availableWithdrawal` row carries the same
pair, because `getAvailableWithdrawalAmount` runs the same state calculation
and takes the expired pending batch from it: the entry names the one account
holding a status at that expiry and the stored and simulated
`scaledTotalAmount` and `normalizedAmountPaid` the derivation reads, and the
row's proof entries name the state words, header timestamp, market code and
balance word that calculation reads beside the status and batch words. Each
report binds the plan digest and the SHA-256 and fixture digest of the
capture record it was built beside.

## How a word is named

The slot numbers in `wildcat_slots.py` come from `forge inspect
src/market/WildcatMarket.sol:WildcatMarket storageLayout`, run with Foundry
1.7.1 over the sources `docs/kickoff/1384/evidence/sources.json` pins. A
compiled layout describes source, not a deployed account, so the probe read
every derived word at the boundary and compared it with the deployed getter
before a plan used it: V1 91 state fields over 7 markets, 30 account words, 61
status words, 7 queues and 54 of 55 batch pairs agreed; V2 1,120 state fields
over 80 markets, 2,312 account words, 3,098 batch words, 3,175 status words and
80 queues agreed.

The one disagreement is the map's own warning that a view can simulate. Market
`0x605309f21c1864bb0522781a2f97b91fe3a48601`, expiry 1742310239, is that
market's `pendingWithdrawalExpiry` and had passed 1,032 s before the boundary:
`getWithdrawalBatch` simulates the expired pending batch as paid, while the
stored words hold the pre-payment amounts. The stored word is what gets proved
and the view is recorded beside it; the relation report marks that pair as a
proved word with a differing recorded view on the three batch rows and on
`native.availableWithdrawal`, whose getter reads the same simulated batch.

Each underlying token's balance word was recognised by equality with
`balanceOf` at the boundary under one of four layouts: a Solidity mapping, a
Vyper mapping, an ERC-7201 namespace or Solady. Where a proxy fronts a
token, the pointer word and the implementation's code are proof targets too,
so the layout a balance word is read under is itself pinned. A token whose
layout is not recognised refuses generation.

## Which receipt is the target

Each plan carries one scoped receipt witness. The target is the lowest-index
receipt in the boundary block carrying a log from one of that estate's markets;
when the block holds none, it is the lowest-index receipt carrying a log from
one of the estate's underlying assets. The filter is every market address at
the block hash. V1's target is receipt index 224 with 5 logs, and the filter
projects 3 logs. V2's block holds no market log, so the target is receipt index
0 with 7 logs, and the filter projects zero logs, which is the proved statement
that no market event sits in that block. Transaction hashes stay recorded, not
proved.

## Study-time evidence

`probe.py` and its two summaries are the record of how the plans' inputs were
measured on 2026-09-27. Nothing here reruns them, and no test reaches a
network. Provider URLs and bearer values were read from environment variables
and never written, by the probe and by the capture driver alike. The study-time copy wrote each refused route's provider
message truncated to 120 characters, and two route entries in each summary
held a refusal that quoted a URL; those two message strings are replaced in
the committed copies with a note that the raw message is withheld, and the
committed `probe.py` records a refusal as its integer code and the fixed
message `provider request failed`. No key the generator reads was touched,
which the unchanged plan digests show.

The study, runbook, design record and its reports are committed under
`docs/lazarus-wildcat-boundary-fixtures/`. The resolver there, `resolve.py`,
reads its probes and plan summaries from its own directory, so that copy is the
study-time record of how the reports were computed and is not rerun from there.

## What this does not establish

A regenerated plan proves nothing; Lazarus `capture` and `verify` do, and the
committed records report what they did without carrying the bytes. Nothing
here claims canonical-chain membership, provider independence, or a value the
map marks unsupported. A `proved` class says the words behind a number are
proved, not that a getter's simulated view equals them, which the one V1 batch
pair shows. The block numbers are the boundaries the captures reported,
carried as scope bounds and not re-derived.
