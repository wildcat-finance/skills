# Preserved Wildcat V1 mainnet interval, v0

This example rebuilds Ethereum mainnet blocks 18,743,513 to 22,074,622 for all
16 subjects of `wildcat-v1-archcontroller`. The capture contains 667 shards of at most 5,000 blocks.
Its two transports agreed on 4,325 comparisons, with 4,325 matches and no disputes.

The 107 staging files total 18,665,266 bytes and are preserved outside this repository.
`staging-manifest.json` binds each file and the 4,323,015-byte archive by SHA-256:
`25322e603679a24a4d9410f24aca07696cdf83ed0349b9f86b900d246b76a687`.

## Rebuild

```bash
export ALEXANDRIA_WILDCAT_V1_STAGING=/path/to/unpacked/staging
python3 plugins/alexandria/examples/wildcat-v1-interval-v0/demo.py build --output <directory>
python3 plugins/alexandria/examples/wildcat-v1-interval-v0/demo.py verify <directory>
python3 plugins/alexandria/examples/wildcat-v1-interval-v0/demo.py verify-preserved
```

`build` checks every staged file before rebuilding. A changed, extra or missing
file refuses before the builder runs. An unset staging variable refuses by
name. `verify` recomputes the built release and checks all expected values.
`verify-preserved` checks the committed manifest, rebuild record and expected
values without reading the archive or rebuilding it. Tests that require an
unavailable staging tree report the rebuild as not run.

## Capture record

The capture maintainer selected the first V1 market deployment as the start on
19 September 2026 at 17:28:48.599 UTC. At 17:29:33.485 UTC he selected the
last Wintermute market termination as the end and delegated shard width.
The recorded market-closure lookup resolved the end to block 22,074,622;
market names were provider observations and do not prove actor identity.
`capture-evidence.json` preserves the authorization messages, boundary
observations, exact production runtime, all five collection attempts and the
successful reconciliation. Its six pre-plan probes are preserved under
`pre-plan-probes/` with their response digests. Both providers returned code
for the first market at block 18,743,513 before either capture plan was fixed.

Two 25,000-block attempts hit request deadlines. A new plan used 5,000-block
shards and fresh staging. Of its three collection attempts, the first was
interrupted to increase shard concurrency, the second met a transport failure,
and the final attempt resumed to completion in 849.428 seconds. Reconciliation
took 85.966 seconds. These are separate attempt durations, not a serial-versus-
parallel benchmark. The completed runs used eight shards and eight targeted
trace workers under a shared limit of eight RPC requests.

## Evidence and limits

The release is
`sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`,
with 16 epochs. Every subject retains its own established source commit.
Fourteen share one recorded commit among five byte-identical candidates;
the four alternatives and the unresolved checkout caveat remain in the registry.
Four deployment blocks are known and 12 remain declared gaps. Epoch code
hashes come from this capture's opening reads, including the observed first
code blocks of subjects whose deployment block is unknown.

The shared ArchController has 54 V1 and 215 V2 logs, with 15 identical logs
in the overlapping interval. The shared SanctionsSentinel has zero in both.
`shared-subject-comparison.json` records these raw observations; separate tests
check release attribution and exercise positive attribution for both shared
subjects using constructed capture releases.

Traces cover only transactions selected by matching subject logs. A logless
transaction was not traced; an empty shard does not establish no activity.
Provider agreement establishes neither completeness, canonical-chain membership,
consensus finality nor publisher identity. This example derives no credit events.
The primary was a local archive node and the secondary a hosted archive and
trace provider. Their endpoints and bearer are absent from the committed
example and preserved staging. The offline build and verification open no socket.
