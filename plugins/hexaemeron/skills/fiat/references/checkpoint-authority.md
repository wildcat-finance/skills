# Checkpoint authority records, signatures, native verification and replay

## Scope

Step 2 implements `records-and-signatures`, Step 3 `native-boundary-coverage`
and Step 4 `authority-replay` for `ordered-replay`, under
`adr/verify-checkpoint-authority-by-ordered-replay`. Native checkpoint v1 is
unchanged. Released interoperability remains unresolved at its later
criterion, and no local result establishes current production eligibility.

## Records and bytes

The [schema source](../scripts/checkpoint_authority/schema.py) defines all 19
closed record types. Its [published schemas](../checkpoint-authority/schemas/)
use JSON Schema 2020-12. All declared fields are required; optional values have
an explicit null branch. Unknown fields and unsupported tags refuse.
`parse_record` also checks calendar dates, scope, predecessor shape, validity
intervals, digest roles and record-local joins. A validation record's claimed
commit list is structurally checked; the Step 3 adapter independently derives
the complete local governed set before reporting coverage.

Canonical JSON is UTF-8 with sorted keys, ASCII escapes, compact separators
and no trailing newline. Duplicate keys, floats, nonfinite values, surrogates
and integers outside signed 64-bit range refuse. Records are capped at 65,536
bytes and depth 32; envelopes at 131,072 bytes. Supplied reference inventories
are bounded to 65,536 entries and 268,435,456 record bytes. Arrays have the
smaller bounds declared by their schema. `check_reference_order` rejects
self, cyclic, duplicate and forward references using a typed digest index;
it does not authenticate that index.

The three native identities retain distinct names: `snapshot_id`,
`controller_manifest_sha256` and `outer_sha256`. Acceptance identity hashes
`wildcat/checkpoint-authority/acceptance/v1` followed by a zero byte and the
canonical unsigned acceptance record. It is external to that record.
Exact envelope SHA-256 hashes include the randomized signature; two valid
signatures over one payload therefore retain different envelope identities.

## Signatures and trust

The authority profile is `dsse-p256-sha256-der/v1`: P-256 ECDSA, SHA-256 applied
once to the DSSE PAE bytes, and strict ASN.1 DER scalar encoding. The payload
is the exact canonical in-toto v1 statement. `payloadType` is
`application/vnd.in-toto+json`; emitted and admitted `keyid` is empty. Exactly
one signature is admitted. Standard or URL-safe base64, with correct optional
padding, is accepted for envelope fields; mixed alphabets and nonzero pad
bits refuse. Public keys use canonical padded standard base64.

Authority keys use P-256 SPKI DER and its SHA-256 fingerprint. Contributor
proofs and endorsements also support SSH Ed25519, SSH P-256 and OpenPGP v4.
SSH fingerprints hash the native public blob; OpenPGP fingerprints come from
the pinned native verifier and the exact public export. Enrollment proofs
bind `wildcat/checkpoint-authority/enrollment-proof/v1`, a zero byte, and the
canonical challenge. SSH uses namespace `wildcat-checkpoint-authority-v1`.
GnuPG reads a fixed public keyring in private scratch; verification neither
imports a key nor starts an agent.

`verify_envelope` retains an immutable exact payload, record bytes and envelope
digest. A returned parsed record is a fresh copy. `TrustPrefix` accepts explicit
external bootstrap roots and separates test and production roots. It checks
ordered policy predecessors, authorized roles, key validity, scoped one-use
challenges, proof of possession, rotations, revocations and upload grants.
Carried keys never bootstrap trust. This authenticates only the supplied
prefix; completeness and fresh authority heads belong to Step 4.
Consumed challenges and superseded policy bodies are discarded. Retained
projections contain only the typed identities and state later entries need.

Callers supply `ToolPin` values with absolute executable paths and SHA-256
pins. Fixed public-key verification commands use private scratch, bounded
streams and deadlines, with executable identity checked before and after.
Records cannot choose tools, paths or commands. The caller owns the local
tool installation; executable hashing does not attest its dynamic libraries.

## Reproduce conformance

Use the repository Python pin. The product parser uses the standard library;
mandatory test dependencies are separate:

```bash
python3 -m pip install --requirement plugins/hexaemeron/tests/requirements.lock
python3 plugins/hexaemeron/tests/checkpoint_authority_corpus.py --check
python3 plugins/hexaemeron/tests/checkpoint_authority_conformance.py --candidate ordered-replay --criterion records-and-signatures --report .hexaemeron/reports/ordered-replay-records-and-signatures.json
```

Provide OpenSSL, `ssh-keygen`, GnuPG and cosign. Test overrides are
`CHECKPOINT_OPENSSL`, `CHECKPOINT_SSH_KEYGEN`, `CHECKPOINT_GPG` and
`CHECKPOINT_COSIGN`. The [tool profile](../checkpoint-authority/tool-profile.json)
pins cosign 3.1.3 assets and every schema-oracle package; CI installs these
explicitly. Cosign verifies caller-supplied public keys offline. Transparency
log checking is disabled; the results supply no keyless identity or
transparency claim.

A pass requires every manifest case to start and finish, with zero failures,
errors, skips or expected failures. Evidence binds actual source, fixture,
tool, runtime, counter and output identities. Empty historical corpora and the
released-interoperability criterion still return 3. Malformed or unsafe invocations return 2;
completed failing cases return 1. Outputs contain fixed codes, test identities
and hashes; raw failure messages stay inside the test runner.

Reports use the exact `.hexaemeron/reports/ordered-replay-<criterion>.json`
path and a sibling `.evidence.json`, each capped at 16 KiB, exclusive mode 600.
Source reads have a 64 KiB cap and reject symlinks, hard links, special files
and observed drift.
The evidence file is written first. Preserve partial or earlier pairs before
retrying; the command never overwrites them. The caller owns the report
directory and excludes competing writers; namespace checks do not make
concurrent directory renames atomic.

## Native verification

[`verify_native`](../scripts/checkpoint_authority/native.py) accepts a local
archive, a private job root, caller-owned executable and source pins, one
`NativeInput`, and an `ApprovedRun`. The caller authenticates the run anchor,
initial base, first governed range base, and historical enrollment/key
intervals before calling it. These are independent trusted inputs. Carried
keys and uploader identity cannot supply historical approval. Full authority
replay remains a Step 4 requirement.

The [source profile](../checkpoint-authority/native-profile.json) binds the
runtime to commit `1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74`, including adjacent
Python, JSON, Markdown and version dependencies. `NativePin` separately pins
Python, Git, GnuPG and gpgconf executables. It rechecks those bytes throughout
the attempt. Dynamic libraries and the host image remain caller-owned trust.
This profile supports OpenPGP v4 and SHA-1 Git objects. SSH native admission,
other producer versions and unsupported history classes refuse by name.

The adapter creates an exclusive attempt directory, captures the input once,
then runs `checkpoint inspect`, fresh `checkpoint restore`, `verify
--observations`, and `checkpoint identity`. Every command must exit zero.
The bounded stdout and private stderr hashes retain the attempt id and input
digest. The returned record grants no service acceptance or current
eligibility. An existing success file cannot replace execution; a failed
restore cannot be repaired by a later verify. Retry with a new attempt id and
preserve the old attempt's refusal and logs.

The closed native parsers retain the nested restore object and both literal
`verify: "ok"` fields. Observation verification emits plain text. The adapter
requires its positive binding count, checks the returned worktree against the
fresh destination, and joins snapshot, status, next directive and manifest
digests. The controller manifest digest includes its original canonical JSON
and one LF. Identity reconstruction preserves the immediate restore tail and
proves the original producer prefix. Nested older restore history refuses.

[`coverage.py`](../scripts/checkpoint_authority/coverage.py) derives each
implementation, audit-fix and push range from the verified producer ledger,
receipt boundaries and real Git ancestry. Embedded `verified_commits` arrays
must agree with that independently enumerated range. The native proof must
equal the expected current-boundary subset. Every required local commit,
including earlier steps, then receives an independent cryptographic check
against the approved historical public keys. No author or trailer filter
removes a required commit. The uploader can differ from its historical
signers. Initial/base endpoints have a separate evidence class, with no local
governed signature claim. Platform-only integration merges remain an
unsupported evidence class and refuse admission.

## Native limits and reproduction

The [capability map](../checkpoint-authority/native-capabilities.json) lists all
35 original hostile fixtures and 24 native refusal names, with source
functions and producer, inspect or restore stages. The 35 cases assert 17
distinct inspection refusals. They do not demonstrate every native refusal
at inspection. The manifest retains the native raw-member secret scan's
limits, unsupported custody classes and the three open native obligations:
#1647 private key diagnostics, #1648 destination-parent ownership and #1649
exclusive scratch for concurrent attempts.

The caller provides an isolated environment, owns the destination parent and
excludes competing writers. Descriptor checks detect observed pathname
changes; they do not make pathname execution or renames atomic. The adapter
does not enforce aggregate descendant CPU, memory, process or filesystem
budgets. It limits the carrier to 1 GiB, each command to 120 seconds, the
attempt to 900 seconds, stdout to 64 KiB and private stderr to 16 KiB. Native
archive limits remain in force. The adapter also caps governed commits at
4096, producer ledger entries at 100,000 and parsed JSON depth at 32. It
refuses missing private custody before native commands and never fetches a
carried locator or executes a historical worker, guard, replacement or next
directive to repair admission.

Set `CHECKPOINT_AUTHORITY_NATIVE_SOURCE` to the trusted checkout matching the
source profile. The native criterion requires real Git and GnuPG; absence or
a skipped case cannot pass. It executes the original 35 hostile cases, the
adapter and conformance unit cases, a real four-command positive sequence,
and a historical-key refusal after all four native commands succeed:

```bash
python3 plugins/hexaemeron/tests/checkpoint_authority_native_corpus.py --check
python3 plugins/hexaemeron/tests/checkpoint_authority_conformance.py --candidate ordered-replay --criterion native-boundary-coverage --report .hexaemeron/reports/ordered-replay-native-boundary-coverage.json
```

The whole conformance check has the repository's 1,800-second check budget;
each native attempt retains its own 900-second limit. Optional caller-owned
`CHECKPOINT_AUTHORITY_NATIVE_EVIDENCE` retains a bounded private test log and
the positive attempt's raw evidence. Use a fresh private directory each time.

The [public two-step fixture](../checkpoint-authority/native-fixture/fixture.json)
contains four real signed governed commits. The native proof covers the
latest two; the adapter independently verifies the earlier two. Its public
key was exported independently before admission and the producer private
keyring was removed. Upstream fake GitHub/ref tooling and synthetic
observation prefixes belong to fixture generation. They establish neither
production trust nor actual run telemetry. The fixture's source/setup
history is outside the two governed ranges.

## Ordered replay

[`replay.py`](../scripts/checkpoint_authority/replay.py) consumes one signed
envelope at a time from an explicit `Bootstrap` and returns a complete-head
verdict only when the last record is an `authority-head` whose
`policy_history` and `decisions` counts and tails equal the replayed prefix.
Trust records extend the policy prefix through `TrustPrefix`; each decision
event must be followed by exactly one `journal-entry` committing its exact
signed payload and predecessor commitment; evidence records carry sequence 1
with no predecessor; every typed reference must already be present with the
declared type, and no record may reference itself or a later record. Records
outside the bootstrap scope, unknown types, unjournaled events, duplicate
envelopes, gaps, reordering and forked predecessors refuse by code. Each
envelope's carrier and signed body are decoded once; after the join only the
typed projection in `RETAIN` survives, and a journaled event body is replaced
by its type and digest. The decision index and the replay carry the aggregate
65,536-entry and 268,435,456-byte limits; a refusal leaves the reader unusable
until a new replay is constructed.

Authorization and cancellation are exclusive per snapshot and per candidate,
in either order. Authorization is durable across lease, endorsement and grant
expiry. Publication is finite: both exact archive copies at acceptance, both
receipt copies and both finalization copies, each at the policy's primary and
recovery locations, make a publication `complete`; anything less stays
`incomplete`. A caller-supplied presence map turns missing objects into
`unexplained-absence`, or `authorized-absence` when a signed
`authorized-removal` following a denial names every missing digest; neither
restores eligibility. `retry` recognises an exact or randomized re-signature
of the first accepted envelope as the same decision through the replayed
policy, never through a caller key; `equivalent` returns the canonical
archive and receipt digests for an alternate carrier whose native identity
matches and accepts nothing new.

[`parents.py`](../scripts/checkpoint_authority/parents.py) joins a
`parent-link` to caller-owned native evidence: the exact `NativeResult`
payload the validation names and the producer ledger whose length, tail and
digest the reconstructed identity binds. Only prefix digests survive. An
acceptance is a registered root when the registration permits it and no
accepted prefix of the same registration exists; otherwise its parent is the
unique longest complete accepted producer prefix, every prior receipt is
carried in order and bounded at 64, the transition names that parent link and
prefix, and a poisoned parent refuses a child. A producer anchor naming
another run, another base or another native pin is a base/run mismatch.

Denials take effect against the current head and mark every matching
authorized acceptance; `descendants: poison` closes the accepted children in
one ordered pass. Stream permits are verified in journal order against the
head they name: complete publication, matching archive and receipt digests, a
download grant, an unexpired head, and one use per actor, session and nonce.
A permit ordered before a denial remains a historical admission; one after it
refuses. [`eligibility.py`](../scripts/checkpoint_authority/eligibility.py)
holds the caller-supplied `Freshness`: the challenge the head must echo,
trusted time inside the head's validity and the policy's `max_head_age_seconds`,
and the remembered policy and decision floors the replay must pass through
with matching tails. Without it, `current_eligibility` is `unknown`; with it,
`denied`, `unavailable` or `eligible`. `GATEWAY_CONTRACT` states the consuming
gateway's cancellation push, two-second and 8 MiB head checks and five-second
channel-freshness cancellation; the replay does not execute a gateway, prove
an unused nonce offline or recall delivered bytes.

[`wire.py`](../scripts/checkpoint_authority/wire.py) closes the private
lookup, inventory, status and download-grant shapes: canonical JSON, at most
100 items and 262,144 bytes for an inventory page and 65,536 bytes for any
other control response, sorted unique acceptance identities, a status state
bound to its code, a grant expiring within 60 seconds, one fixed absence
response for unknown and unauthorized resources, `private, no-store`
octet-stream headers with a digest-derived filename and no provider location,
and `capability_not_enabled` for frontier, resolution and public discovery.

## Ariadne evidence boundary

Ariadne registers `https://wildcat.finance/attestations/checkpoint-authority/v1`
over a release copy of `schema.family_document()`. Its predicate checks one
record's closed shape, digest roles, typed evidence references, timestamp
recoverability, predecessor and parent relations and copy or coverage
inventories, and reports signature authentication, native execution, storage
observations, complete replay and current eligibility as unchecked. Its copy of
the schema and result vocabulary is held to this owner by a checkout parity
test; no runtime import crosses the plugins. An Ariadne pass never replaces a
replay verdict. [The Ariadne guide](../../../../ariadne/docs/checkpoint-authority.md)
publishes the field and gate contract.

## Reproduce the replay criterion

```bash
python3 plugins/hexaemeron/tests/checkpoint_authority_replay_corpus.py --check
python3 plugins/hexaemeron/tests/checkpoint_authority_conformance.py --candidate ordered-replay --criterion authority-replay --report .hexaemeron/reports/ordered-replay-authority-replay.json
```

The [replay manifest](../checkpoint-authority/fixtures/replay-manifest.json) binds the
committed positive history, its recorded hostile mutations, the Metron budget
record, Ariadne's schema copy and conformance fixtures, and every replay,
conformance and Ariadne case id. The
[positive history](../checkpoint-authority/fixtures/replay-history.json) is one signed
root acceptance, finalization and permit with ephemeral test keys and
synthetic native attestations; no native command ran and no private key is
retained. [Its hostile file](../checkpoint-authority/fixtures/replay-hostile.json)
records fourteen unsigned mutations with the code and stage each must refuse.
Regenerate the history only with `--history`, then `--write`; every
regeneration produces new signatures. The `fixtures/` and `native-fixture/`
corpora are read only by these reporters from a full checkout; the portable
Promise Machine runtime omits them and records the two omission patterns and
their reasons in its manifest, under
`adr/omit-checkpoint-authority-conformance-corpora-from-the-portable-runtime`.
The schemas, `native-profile.json`, `native-capabilities.json` and the
READMEs stay in the runtime.

The [budget record](../checkpoint-authority/fixtures/replay-budget.json) is the Metron
measurement for this step: 1,391 signed records replayed one body at a time
with 1,391 signed-body and 1,391 carrier decodes, no retained body nodes and a
62,013,440-byte peak child RSS against the study's 512 MiB ceiling, at a
10,588.742 ms median over three fresh processes including real public-key
subprocesses. The study's 1,280-decode and 266,697-byte model comparison
reports are preserved unchanged; this record measures the protocol, not the
model, and establishes no production latency or throughput.

## Native fixture limits

Small fixture success does not resolve the full-layout Step 1 native inspect
Git-fetch timeout or establish the adopted service benchmark. The historical
111,860,548-byte CP-3 reference has absent observation bindings and its
observation precondition returns `FOB001`; no current four-command success or
service admission follows from its old transport result. The fixture Linux
environment permits executable temporary files for upstream producer tools;
that is test support, not an adopted production isolation profile.
