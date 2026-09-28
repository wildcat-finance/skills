# Wildcat boundary fixtures delivery proof

## Result

Fiat issue 1384, Step 4, ran the study's demo path from the repository root
on 2026-09-28 with `WILDCAT_BOUNDARY_V1_RELEASE` and `WILDCAT_BOUNDARY_V2_RELEASE`
naming the two release trees in private custody. All ten commands exited 0
with nothing on stderr. Both regenerated plans hashed to the digests
`plans.json` records: V1 `13770a6987eed0c819809c6d68c8874a1fe243b148021a9cbee29511b736fa1c`,
196,264 bytes; V2 `0dcfbc330633ceb29e4c67819e33639681ef58e9ce4a0628bb7de316f20c285a`,
7,041,376 bytes. The six mutation changes were refused
twice each, twelve refusals, and an edited committed digest was refused
offline, once as a member digest and once as a whole-archive digest. The
Lazarus skill moves one generation, from `lazarus-v3.2.0` to
`lazarus-v3.3.0`, with its frontier fields byte-identical; the installable
plugin moves from 1.1.9 to 1.1.10.

## Demo path

Each command is the study's, with the custody trees named by their variables
and the fresh plan paths by role. The output is the command's stdout; its
SHA-256 and byte count are recorded as observed. No output named a custody
path, so a rerun over the same bytes reproduces each digest. Every command was
run as a pinned argument list with no shell, from the repository root.

| # | Command | Exit | Output SHA-256 | Output bytes |
| --- | --- | --- | --- | --- |
| 1 | `python3 plugins/lazarus/examples/wildcat-boundary-v0/plan_v3.py --generation v1 --probe plugins/lazarus/examples/wildcat-boundary-v0/probe-v1.json --out <fresh-v1-plan>` | 0 | `86f25d0c012fc946b243adfe1757b63b1db3d00e774cd9a26dccf066160686ca` | 379 |
| 2 | `python3 plugins/lazarus/examples/wildcat-boundary-v0/plan_v3.py --generation v2 --probe plugins/lazarus/examples/wildcat-boundary-v0/probe-v2.json --out <fresh-v2-plan>` | 0 | `ea919658f4ddf532c56c5c94affa21015d0228b9274ef8ff8392439c181723ce` | 395 |
| 3 | `python3 plugins/lazarus/scripts/lazarus.py verify "$WILDCAT_BOUNDARY_V1_RELEASE/fixture"` | 0 | `0ee0e298d32e2aad5ec56d687f0433689ff50c836b022dc280f970f4b70d9ec8` | 430 |
| 4 | `python3 plugins/lazarus/scripts/lazarus.py verify "$WILDCAT_BOUNDARY_V2_RELEASE/fixture"` | 0 | `161c9f2d92f051217f2b96eeab56052a5c75bc679d1ddcba06c5b46a20f4067f` | 432 |
| 5 | `python3 plugins/lazarus/scripts/lazarus.py verify-release "$WILDCAT_BOUNDARY_V1_RELEASE"` | 0 | `74407d7624fb65629e2d5fab2c18b929e040def6df16df99b0033ccc8b310936` | 491 |
| 6 | `python3 plugins/lazarus/scripts/lazarus.py verify-release "$WILDCAT_BOUNDARY_V2_RELEASE"` | 0 | `e8734bcb2f602794f4bae59fc19238a0e79cab35380d54ea01e7a7f37101ff3a` | 494 |
| 7 | `python3 plugins/ariadne/scripts/ariadne.py verify "$WILDCAT_BOUNDARY_V1_RELEASE/statement.json"` | 0 | `69ce3ca82f5677073c9cc39e093ed21c5e3c5b242a9b2cc6ef4f45a94464505f` | 865 |
| 8 | `python3 plugins/ariadne/scripts/ariadne.py verify "$WILDCAT_BOUNDARY_V2_RELEASE/statement.json"` | 0 | `69ce3ca82f5677073c9cc39e093ed21c5e3c5b242a9b2cc6ef4f45a94464505f` | 865 |
| 9 | `python3 plugins/lazarus/examples/wildcat-boundary-v0/demo.py mutations` | 0 | `a260449135d77b6c021a614c78346cc9df97330488d341c1d75859b65969e9d3` | 1,615 |
| 10 | `python3 plugins/lazarus/examples/wildcat-boundary-v0/demo.py verify-preserved` | 0 | `efef4b8802ec45b6ec5e88780d6169acced5555f5de80e283b24f1fb07a74de1` | 2,220 |

Commands 1 and 2 print the plan's digest, byte count and word counts; the
plan files themselves are the digests above. Commands 3 and 4 report V1
proof-backed 265, header-bound 1, recorded-RPC 434, receipt-trie-proved 2 over
226 receipts with target index `0xe0` and 3 filtered logs, and V2 9,231, 1,
14,561, 2 over 216 receipts with target index `0x0` and 0 filtered logs, each
with 2 chain-anchor records. Commands 5 and 6 report release digests
`b1b404b875cdc121e140bfa47e2406ddd6fc8142b5266dec3fb42ff6c26d1294` and
`94813eb2c7041f211870d49f6fbfc82b493bd69707648e5def571afad0b2e614` with all
eight binding checks. Commands 7 and 8 pass all seven Ariadne gates and the
state-fixture/v2 checks on unsigned statements; their outputs are
byte-identical because the verifier prints gate results and no digest. The
elapsed wall-clock times were 7.946 s for
command 4 and 27.858 s for
command 9; nothing budgets them. The captures Step 2 measured took 26.322 s
for V1 and 787.337 s for V2, as `capture-v1.json` and `capture-v2.json`
record.

## Mutation refusals

Command 9 copied each estate's fixture into a fresh temporary directory,
verified the unchanged copy to the committed fixture digest, then changed one
storage value, one code byte and one receipt byte in separate copies and
verified each twice: with the manifest untouched and with it re-sealed to the
altered bytes. Lazarus refused every copy at the check named.

| Estate | Change | Manifest | Exit | Check |
| --- | --- | --- | --- | --- |
| v1 | storage-value | untouched | 1 | `component-digest-mismatch` |
| v1 | storage-value | resealed | 1 | `storage-value-mismatch` |
| v1 | code-byte | untouched | 1 | `component-digest-mismatch` |
| v1 | code-byte | resealed | 1 | `code-hash-mismatch` |
| v1 | receipt-byte | untouched | 1 | `component-digest-mismatch` |
| v1 | receipt-byte | resealed | 1 | `receipts-root-mismatch` |
| v2 | storage-value | untouched | 1 | `component-digest-mismatch` |
| v2 | storage-value | resealed | 1 | `storage-value-mismatch` |
| v2 | code-byte | untouched | 1 | `component-digest-mismatch` |
| v2 | code-byte | resealed | 1 | `code-hash-mismatch` |
| v2 | receipt-byte | untouched | 1 | `component-digest-mismatch` |
| v2 | receipt-byte | resealed | 1 | `receipts-root-mismatch` |

The V1 changes were the balance word of `0x2260fac5e5542a773aa44fbcfedf7c193bc2c599`
at slot `0x0b2128e5…203cfb0` from `0x484` to `0x480`, byte 4581 of that
contract's 4,582 code bytes from `29` to `28`, and the target receipt's
`cumulative_gas_used` at transaction index 224 from `0xd04a27` to `0xd04a26`.
The V2 changes were slot 0 of `0x02e0415e828a5f97309f93f001885b5db8a87d71`
from `0x48c2739500000` to `0x48c2739500001`, byte 19750 of the 19,751 code
bytes of `0x0004da6611b3c4f557ba88105ebd85e5bd214dcd` from `0a` to `0b`, and
the target receipt's `cumulative_gas_used` at index 0 from `0x2c23c` to
`0x2c23d`. The unchanged V1 and V2 copies verified to
`fac341a25dceb33b81a99600a6520e667a4413b8bb46e4b97e839ffb82739c2d` and
`1f4a54d32c7359da494abbc06626148ad479fb3a22c61d59c4f225416726eac9`. The
observations were also written with `--report` to a scratch path outside
every tree; that run's stdout digest equalled command 9's.

## Edited-digest refusal

With neither variable set, `python3 plugins/lazarus/examples/wildcat-boundary-v0/demo.py
verify-preserved --example <copy>` ran over a copy of the example directory in
which `archives.json` had one member digest edited: the first member of
`wildcat-boundary-v1-lazarus-release.tar`, `fixture/anchors.jsonl`,
from `e080f66797db73734405b8c08d2f25845976ce9589a2420cbc1b04e765f01ad2` to
`0080f66797db73734405b8c08d2f25845976ce9589a2420cbc1b04e765f01ad2`. It exited 1 with no
stdout and one stderr line, `demo: archives.json: wildcat-boundary-v1-lazarus-release.tar members differ from the committed digests`,
stderr SHA-256 `9ac8935354e30f8617712c888b79f2a6b6420b61d0ea2f75e00348d8d5bd4398`, 103 bytes.
A second copy with the whole-archive `sha256` of the same entry edited, from
`5fe72b7c33c3f748341582dbd5dfb78ce619263c6af84b6fb78fb066108cf809` to
`0fe72b7c33c3f748341582dbd5dfb78ce619263c6af84b6fb78fb066108cf809`, exited 1
with no stdout and one stderr line, `demo: handoff.json: wildcat-boundary-v1-lazarus-release.tar sha256 differs from archives.json`,
stderr SHA-256 `eae6e11e1fff99de24fed6de758387efaaa55cce10ba8e1df74bc98c5311d522`, 94 bytes.
`verify-preserved` reads no tar, so it holds each whole-archive digest and
byte count between `archives.json` and the copy `handoff.json` repeats; the
bytes themselves are held by the handoff directory's `archive-SHA256SUMS` and
by the custody tooling on admission.

## Governed state

The ledger row `lazarus-v3.3.0` is a generation entry: its frontier revision
`empty-block-receipt-witnesses` and digest
`28eda7875d079d615279db2f8f39d72b78aa5746ba9d92b3da6bb3a3f65a4df6` are the
`lazarus-v3.2.0` row's, the status stays `mature` and the next job stays
`None -- mature`. Removing that row and reverting the version line
reproduces the ledger the run started from, SHA-256
`6c3b54566007139a9fe909af7ed558ac5696f15e0d13224de6668771de99c669`.
`plugins/lazarus/tests/test_wildcat_boundary.py` holds the handoff record to
`archives.json`, this proof to the study's command list, and the ledger to
that one added row. The Miskatonic handoff pull request that `handoff.json`
names was open and unaccepted when this proof was written; no archive had
been uploaded.

## What the demonstration does not establish

Canonical-chain membership of either boundary block; the fixtures prove
binding to the verified header and nothing about the header's place in the
chain. Provider independence; each fixture carries two chain-anchor records
and claims neither. Any value the map marks unsupported, which is 14 rows per
estate plus the 3 rows that belong to the other generation. Anything about
the R2 upload: no row has been accepted and no replication receipt exists,
so `handoff.json` carries a null receipt digest with its reason. The mutation
refusals cover three changes per estate and no other, and `verify-preserved`
compares committed records with one another and reads no fixture byte.
