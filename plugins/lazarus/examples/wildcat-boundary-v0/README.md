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
capture's record, each estate's per-value relation report, statement, release
document and Alexandria plan, the archive inventory, and the demonstration,
described below.

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
- `statement-v1.json` and `statement-v2.json`: each estate's unsigned Ariadne
  `state-fixture/v2` statement, byte for byte as the release digests it.
- `release-v1.json` and `release-v2.json`: each Lazarus release document, with
  the fixture digest, the statement digest and the eight binding checks.
- `alexandria-plan-v1.json` and `alexandria-plan-v2.json`: the Alexandria
  capture plans that admit each fixture as a `proof-backed-state` capture.
- `archive.py`: the deterministic archive builder.
- `archives.json`: the digest inventory of the four handoff archives, member by
  member.
- `handoff.json`: the custody handoff record: the Miskatonic pull request that
  proposes the four archives, the handoff id, one proposed source id per
  archive, each archive's byte count and SHA-256 as `archives.json` records
  them, and a null replication receipt with the reason.
- `demo.py`: the demonstration. `mutations` refuses altered bytes,
  `verify-releases` verifies both release trees and `verify-preserved` checks
  the committed records offline.

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
inside the process. It calls `lazarus_lib.capture.capture_fixture` with the URL
as its primary route and the bearer as an `authorization` header. It maps the
plan's two anchor sources to environment variable names: `local-archive` to
`RETH_RPC_URL` and `public-archive` to `PUBLIC_ARCHIVE_RPC_URL`. Neither value
enters argv, a file or the printed output.

The output is Lazarus's own terminal result, which Lazarus redacts against the
union of provider secrets. An envelope around it adds the generation, the plan
digest and the measured elapsed seconds. The driver refuses when a named
variable is unset, when the plan is not the one `plans.json` records for the
generation, and when `--out` exists or is a symlink. A capture that fails at
any stage leaves no fixture, and Lazarus's failure result names the stage and
the counts it reached.

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
time. The observed V1 time is 26.322 s. The observed V2 time is 787.337 s,
over its projection and under the plan's 7,200 s limit.

The verify counts equal the study's expectation for both estates: proof
targets plus slots, one header, the plan's requests, and the two receipt
relations. Each fixture holds six components and a manifest, and the records
list every component's byte count and SHA-256. V1's one recorded error is a
`getAvailableWithdrawalAmount` call that reverts at the boundary. V2's four are
`getAvailableWithdrawalAmount` calls that revert the same way. Those calls stay
recorded errors, and their rows keep the class the proved words give them.

## Which class a row gets

`relations.py` gives each of the 61 rows in `docs/kickoff/1384/values.json`
exactly one class. Each report states under `legend` what the classes cover
and that a recorded response is never proved.

`proved` means every number behind the row is a storage word or code the
fixture proves under EIP-1186. Those are:

- the four state words, for the `state.*` rows and everything `currentState()`
  derives from them;
- the underlying token's balance word, for `credit.totalAssets`;
- the queue head and data words, for `native.unpaidExpiries`;
- the account, batch and status words, for the per-account and per-batch rows;
- the market's runtime code, for the immutables behind `credit.asset`, the
  `config.*` rows and the four `native.*` rate and duration rows.

`header-bound` is `credit.observedAt`, the
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
that list is empty.

The `native.availableWithdrawal` row carries the same pair, because
`getAvailableWithdrawalAmount` runs the same state calculation and takes the
expired pending batch from it. Its entry names the one account holding a
status at that expiry, with the stored and simulated `scaledTotalAmount` and
`normalizedAmountPaid` the derivation reads. The row's proof entries name the
state words, header timestamp, market code and balance word that calculation
reads, beside the status and batch words. Each report binds the plan digest and the SHA-256 and fixture digest of the
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

## Write the statements and releases

Each fixture gets an unsigned Ariadne `state-fixture/v2` statement and a
Lazarus release-v2 binding. From the repository root, with no network, for
each generation:

```bash
python3 plugins/ariadne/scripts/ariadne.py capture-state-fixture \
  --fixture <custody>/v1-fixture --name wildcat-boundary-v1 --capture-tool lazarus \
  --capture-command python3 \
  --capture-command plugins/lazarus/examples/wildcat-boundary-v0/capture.py \
  --capture-command capture --capture-command=--generation --capture-command v1 \
  --capture-command=--plan '--capture-command=<fresh-v1-plan>' \
  --capture-command=--out '--capture-command=<custody>/v1-fixture' \
  --parameter generation=v1 --parameter plan_sha256=<v1 plan digest from plans.json> \
  --first-capture-reason 'first preservation release of the Wildcat V1 boundary fixture at its sealed interval end' \
  --out <custody>/v1-statement.json
python3 plugins/lazarus/scripts/lazarus.py release <custody>/v1-fixture \
  --statement <custody>/v1-statement.json --out "$WILDCAT_BOUNDARY_V1_RELEASE"
python3 plugins/lazarus/scripts/lazarus.py verify-release "$WILDCAT_BOUNDARY_V1_RELEASE"
python3 plugins/ariadne/scripts/ariadne.py verify "$WILDCAT_BOUNDARY_V1_RELEASE/statement.json"
```

Ariadne reads the manifest beside the fixture and copies its four evidence
counts; it counts nothing itself. The command words it records are the capture
driver's, with the plan and output operands written as role names rather than
paths, so no statement carries a local path. `release` verifies the fixture,
holds the statement's counts to what that verification recomputed, and writes
the tree whole or not at all: `fixture/`, `statement.json` and `release.json`.
`--out` must not exist yet. `statement-v1.json` and `release-v1.json` here are
those two files byte for byte, and `verify-releases` below refuses a tree whose
copies differ from them. The same commands with `v2` write the second estate.

## Admit each fixture into Alexandria

`alexandria-plan-v1.json` and `alexandria-plan-v2.json` are the capture plans.
Each declares one `proof-backed-state` capture. Its source reference is the
fixture digest, and its subjects are every proof target in the plan. Its
snapshot is the boundary block's number and hash, with `observed_at` set to the
header timestamp `header.json` carries. The components are the manifest, under
the `lazarus-manifest` role, and the six fixture files, all marked restricted
because the bytes stay in custody. Every component path is relative to the
plan's own directory, so admission runs from a staging directory holding a copy
of the plan and a copy of the fixture:

```bash
mkdir <custody>/v1-alexandria-input
cp plugins/lazarus/examples/wildcat-boundary-v0/alexandria-plan-v1.json <custody>/v1-alexandria-input/capture-plan.json
cp -R "$WILDCAT_BOUNDARY_V1_RELEASE/fixture" <custody>/v1-alexandria-input/fixture
python3 plugins/alexandria/scripts/alexandria.py ingest \
  --plan <custody>/v1-alexandria-input/capture-plan.json --output <custody>/v1-alexandria-release
python3 plugins/alexandria/scripts/alexandria.py verify <custody>/v1-alexandria-release
```

`verify` prints the release id. It rebuilds the fixture from the release's
objects in a temporary directory and reruns Lazarus's offline verifier over it.
It refuses a subject outside the proof targets, a block other than the proved
one, or any finality other than `unknown`, because Lazarus proves block binding
and reports no finality class. It does not make the release public, name a
provider, or say anything about a block's place in the chain.

## Build the handoff archives

`archive.py` writes four archives, one per estate for the Lazarus release tree
and one per estate for the Alexandria release, and records every member in
`archives.json`:

```bash
python3 plugins/lazarus/examples/wildcat-boundary-v0/archive.py \
  --v1-lazarus-release "$WILDCAT_BOUNDARY_V1_RELEASE" --v1-alexandria-release <custody>/v1-alexandria-release \
  --v2-lazarus-release "$WILDCAT_BOUNDARY_V2_RELEASE" --v2-alexandria-release <custody>/v2-alexandria-release \
  --out-dir <custody>/archives --record plugins/lazarus/examples/wildcat-boundary-v0/archives.json
```

The format is an uncompressed ustar tar: regular files only, sorted by the
UTF-8 bytes of their archive path under a top-level directory named after the
archive, with mtime 0, uid and gid 0, empty owner names and mode 0644. It was
chosen because it is the plainest form whose bytes are a function of the
members alone. A gzip or zip stream carries a timestamp and depends on the
compressor's version, so two honest rebuilds could differ by digest. Plain tar
with fixed headers does not, and the members are JSON that object storage can
compress at rest. Rebuilding into a fresh directory with `--expect
plugins/lazarus/examples/wildcat-boundary-v0/archives.json` exits 0 only when
the rebuilt inventory equals the committed one; both `--out-dir` and `--record`
must not exist yet. Each archive's entry records its byte count and SHA-256,
its member count, every member's path, byte count and SHA-256, the fixture
digest, and the release digest or Alexandria release id. The Lazarus archives
hold nine members each and the Alexandria archives eight. The inventory does
not establish that any copy exists outside the machine that built it; the
handoff pull request and the operator's acceptance do that.

## What the releases recorded

The figures are copied from the committed documents and `archives.json`.

| Record | V1 | V2 |
| --- | --- | --- |
| Release digest | `b1b404b875cdc121e140bfa47e2406ddd6fc8142b5266dec3fb42ff6c26d1294` | `94813eb2c7041f211870d49f6fbfc82b493bd69707648e5def571afad0b2e614` |
| Statement SHA-256 | `38c569267eac79cb1da01e004323b0f02acac64f033ab47746658ef5dd27189e` | `b1c9241957ec8a3ecb685edac4feb6b3b5ecedcd23a0cd6fe849040cc261662e` |
| Statement evidence counts | 265, 1, 434, 2 | 9,231, 1, 14,561, 2 |
| Alexandria release id | `sha256:ffb8aff7cbcfa2891aee0fcb4afd3b98c13556327dfda7c11d54cb6cfcc3159d` | `sha256:33570d48cca74126b35b8fb8211c31b7be7079fc7b49131497109a47993bcd31` |
| Lazarus release archive, bytes and SHA-256 | 3,000,320, `5fe72b7c33c3f748341582dbd5dfb78ce619263c6af84b6fb78fb066108cf809` | 49,274,880, `aa10493ee13163d446d97ca553074ef29604c80f110b8d7d5a3f72ec2a4670dd` |
| Alexandria release archive, bytes and SHA-256 | 2,990,080, `c4a1b0707e523af53aac3615df78c0133f843d1f924414e2c81fbc9700fbfac9` | 49,274,880, `995770e58f86b2f7a82744ec9326f4063c8fbee7b3026db63bd559185b47b7d7` |

## Run the demonstration

`demo.py` has three subcommands and reads the release trees only through
`WILDCAT_BOUNDARY_V1_RELEASE` and `WILDCAT_BOUNDARY_V2_RELEASE`. From the
repository root:

```bash
python3 plugins/lazarus/examples/wildcat-boundary-v0/demo.py mutations
python3 plugins/lazarus/examples/wildcat-boundary-v0/demo.py verify-releases
python3 plugins/lazarus/examples/wildcat-boundary-v0/demo.py verify-preserved
```

`mutations` copies each estate's fixture into a fresh temporary directory,
first unchanged, and requires Lazarus `verify` to exit 0 on the copy and the
copy's manifest digest to equal the committed capture record's. Then, in
separate fresh copies, it changes the first storage value in `proofs.jsonl`,
the last byte of the first captured code, and the target receipt's cumulative
gas in `receipt-witness.json`, and verifies each copy twice. With the manifest
untouched, Lazarus refuses at its component digest check. With the manifest
re-sealed to the altered bytes, so that no digest disagrees, Lazarus refuses at
the storage proof, the code hash and the reconstructed receipts root
respectively. The subcommand prints one line per copy, naming the estate, the
change, the manifest state and the check that refused. It exits 0 only when all
six changes are refused in both forms, which is twelve refusals, and both
unchanged copies verified. The copies are removed as they are used. It writes
nothing inside a release tree and proves nothing about a change it did not
make.

`verify-releases` requires each tree's `release.json` and `statement.json` to
be byte-identical to the committed copies, runs `lazarus.py verify-release` on
the tree and `ariadne.py verify` on its statement, and requires the printed
release and fixture digests to be the committed document's. Exit 0 says both
trees verify as the committed records describe them.

`verify-preserved` needs no release tree and no variable. It reads the
committed capture records, statements, release documents, Alexandria plans and
`archives.json` and holds them to one another: each capture record's manifest
recomputes to its fixture digest, each statement's SHA-256 is the one its
release document names and its counts, block, roots and component digests are
the capture record's, each release document's `release_digest` recomputes from
its fields, each plan names the recorded fixture and block, every archive
member's digest is one of the committed ones, and `handoff.json` repeats each
archive's name, byte count, SHA-256 and member count and the digest of
`archives.json` itself, so an edited whole-archive digest in either record is
refused although no tar is read. It refuses an edited digest,
count or root, a boolean or non-finite number, and a symlinked example
directory. It reads no fixture byte and reruns no proof check, so exit 0 says
the committed records agree, not that an external archive still holds them.

Each subcommand takes `--report <path>` to write its observations as JSON to a
path that must not exist, and refuses a report path inside a release tree.
`verify-preserved` still needs neither variable; it reads one that is set only
to refuse a report path inside the tree it names. Exit 2 is a refusal before
any check ran: a missing or empty variable, an existing or symlinked report
path, a symlinked tree, entry or example directory. Exit 1 is a check that ran
and failed, and the report then says so. Every subprocess is a pinned argument
list with no shell. The two `design-evidence.json` conformance cells run
`mutations` and `verify-releases` with no other arguments;
`plugins/lazarus/tests/test_wildcat_boundary.py` runs `verify-preserved` and
the mutation routine against the committed Aave v4 release fixture in the
suite. The two tree-bound subcommands are not unit tests, because the hosted
Darwin job refuses a skipped Lazarus test and never holds the trees. Their
record is `docs/lazarus-wildcat-boundary-fixtures/proof.md`, which lists
`demo.py mutations` and `demo.py verify-preserved` with their exit codes and
output digests. The two conformance cells above run `mutations` and
`verify-releases` at integration.

## Hand off custody and record the generation

The archives reach Miskatonic R2 through a handoff pull request, not through
this repository. The pull request that `handoff.json` names adds
`storage/r2/handoffs/wildcat-boundary-fixtures-20260928/` to
wildcat-finance/miskatonic. It holds a README, the four archive digests, a byte
copy of `archives.json` and four proposed source-register rows. There is one
row per archive, because a register row binds one archive digest and
Miskatonic's custody tooling admits one archive per job. It records no
acceptance or upload and stays open for the operator, who accepts each row by
digest and uploads through Miskatonic's own tooling. `handoff.json` repeats the
handoff id, the four proposed source ids and each archive's byte count and
SHA-256 from `archives.json`. Its `replication_receipt_sha256` is null, with
the reason stated in the record, because no upload had happened when it was
written. If the rows are not accepted by integration, R2 admission is carried
forward by name.

The Lazarus ledger at `plugins/lazarus/skills/lazarus/EVOLUTION.md` gains one
generation row for this delivery. Its frontier revision and digest are the
row's before it, byte for byte, and the skill's metadata version moves with
it. The delivery proof at `docs/lazarus-wildcat-boundary-fixtures/proof.md`
records each demo-path command from the study with its exit code and output
digest, the twelve mutation refusals and the edited-digest refusal.
`plugins/lazarus/tests/test_wildcat_boundary.py` holds `handoff.json` to
`archives.json`, the proof to the study's command list, and the ledger to
exactly one added row with the frontier fields unchanged.

## What this does not establish

A regenerated plan proves nothing; Lazarus `capture` and `verify` do, and the
committed records report what they did without carrying the bytes. Nothing
here claims canonical-chain membership, provider independence, or a value the
map marks unsupported. A `proved` class says the words behind a number are
proved, not that a getter's simulated view equals them, which the one V1 batch
pair shows. The block numbers are the boundaries the captures reported,
carried as scope bounds and not re-derived.

A release binds a statement to what one verification recomputed and says
nothing about a signature; neither tool holds a key. An Alexandria admission
says the fixture rebuilt from the release's objects verified under Lazarus at
admission time, not that the release is public or that anyone else holds it.
The archive inventory says what bytes were built here, not where they are now.
The mutation refusals cover three changes per estate and no other, and
`verify-preserved` compares committed records with one another and reads no
fixture byte.
