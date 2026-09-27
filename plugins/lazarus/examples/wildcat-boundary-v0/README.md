# Wildcat boundary fixtures, v0

This example generates one Lazarus plan-v3 per Wildcat estate on Ethereum
mainnet at the block where that estate's sealed interval capture reports its
finalized boundary: V1 at block 22074622 (`0x150d4fe`) and V2 at block
26022093 (`0x18d10cd`). Each plan proves under EIP-1186 every storage word
behind every number the accepted value map says a consumer will print, proves
the code at every subject address, records the map's finite request inventory
byte for byte and carries one scoped receipt witness. The plans are
regenerated, not committed. The fixtures captured from them, their releases and
their Alexandria admissions live in Miskatonic custody, as
`docs/decisions/drafts/keep-wildcat-boundary-fixtures-in-miskatonic-custody.md`
records, and no fixture byte is in this repository.

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
proved word with a differing recorded view.

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
and never written. The study-time copy wrote each refused route's provider
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

A regenerated plan proves nothing; Lazarus `capture` and `verify` do. Nothing
here claims canonical-chain membership, provider independence, or a value the
map marks unsupported. The block numbers are the boundaries the captures
reported, carried as scope bounds and not re-derived.
