# Wildcat dataset statements

Step 1 preserves the accepted specification and input metadata for issue 1374.
The binding implementation is due in Step 2. No dataset statement or verifier
result is shipped by this scaffold.

The accepted scope contains both Ethereum mainnet Wildcat estates. The
[study](https://github.com/wildcat-finance/skills/blob/main/plugins/ariadne/examples/wildcat-datasets-v0/spec/study.md), [runbook](https://github.com/wildcat-finance/skills/blob/main/plugins/ariadne/examples/wildcat-datasets-v0/spec/runbook.md) and
[design evidence](https://github.com/wildcat-finance/skills/blob/main/plugins/ariadne/examples/wildcat-datasets-v0/spec/design-evidence.json) are exact copies of the accepted
Fiat records. The design selects every release file as a subject, with one
unsigned statement per estate. Ariadne's existing `dataset/v1` interface owns
the statement and verification rules.

- V1 covers inclusive blocks 18743513 to 22074622 and binds 110 files.
  Release ID: `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`.
- V2 covers inclusive blocks 21866550 to 26022093 and binds 128 files.
  Release ID: `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`.

## Input contract

[inputs.json](https://github.com/wildcat-finance/skills/blob/main/plugins/ariadne/examples/wildcat-datasets-v0/inputs.json) records exact file sizes and SHA-256 digests. Its
`subjects` counts file subjects; it excludes the bundle subject that Step 2
adds to each outer in-toto subject array. The `files` inventory covers the
preserved specification, design observations,
source metadata and observed input checks. Each estate names its original
manifest, plan, registry, staging manifest, archive digest and capture history.
The release manifests retain all source scopes, access labels, evidence classes,
unsupported collections and gap strings unchanged. Only metadata is committed;
the full release trees and staging archives remain external.

The fourteen estate JSON documents use deterministic gzip with `mtime=0`.
Their references pin encoded and decoded sizes and SHA-256 digests separately.
A reader checks the encoded bytes before decoding, reads at most the declared
decoded size plus one byte, and checks the decoded size and digest. Both sizes
must be within the 1,048,576-byte metadata limit. Decoding recovers the exact
original JSON bytes; it does not reserialise them. The source checkout retains these exact records.

`observed_rebuild` records the command, observed interpreter version `3.14.6`, source revision,
staging location and report from this Fiat run. `producer_sources` pins the
Alexandria entrypoints and library files at that revision. Original collection
runtime and source ambiguity remain in their own copied records. Historical
commands are provenance data and must not be executed from these records.
The V2 history does not establish its original collection argv.

Each estate's `release_location` records the host location used for the accepted
rebuild. The planned Step 2 caller takes `ARIADNE_WILDCAT_V1_RELEASE` and
`ARIADNE_WILDCAT_V2_RELEASE` for those directories. The archive locations are
access requirements, with no promise of public availability. V2's old mutable
staging omitted `reconciliation/errors.jsonl`; the observed rebuild used a
fresh copy of the verified archive. Both refusals and the recovery record remain
under `inputs/observations/`.

## Full source checkout required

The portable package retains only this README from the example. Its metadata,
specification, reports and demonstration belong to the full source checkout.
Use that checkout for both metadata verification and the Step 2 demonstration.
Core Ariadne capture, verifier and schema runtime files remain installed.

## Check the preserved metadata

From the repository root, using its pinned Python:

```bash
python3 plugins/ariadne/tests/run_tests.py
```

The example's tests check the exact inventory, input identities, specification
copies and ten selection-report digests. They perform no external archive
read, new collection, release rebuild or signature verification. The preserved
reports record earlier executed checks; reading a report does not rerun it.
The local selection probe measured listing time and bytes only. It supplies no
peak-memory or general performance claim.

## Coverage and next step

All 667 V1 and 3,463 V2 interval shards completed in the accepted handoff.
The planned statements retain semantic limits through a reasoned whole-interval
gap and the exact source inventory. That gap represents evidence omissions;
it does not say every block was unread. Partition notes remain partition notes.
Targeted traces omit transactions without matching subject logs. V1 has twelve
unknown deployment blocks and five equivalent source checkouts; V2 retains its
private source references. The capture does not establish complete positional
agreement, provider completeness, canonical finality or publisher identity.

Step 2 implements the offline adapter, preserves both unsigned statements and
complete verifier reports, and exercises the three required coverage refusals.
The [Ariadne ledger](../../skills/ariadne/EVOLUTION.md) holds the full-release
choice and its rejected alternative. This example reuses the repository's
licence, Python pin and CI; it adds no dependency or service.
