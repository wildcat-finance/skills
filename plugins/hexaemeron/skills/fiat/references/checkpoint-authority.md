# Checkpoint authority records, signatures and native verification

## Scope

Step 2 implements `records-and-signatures`; Step 3 implements
`native-boundary-coverage` for `ordered-replay`, under
`adr/verify-checkpoint-authority-by-ordered-replay`. Native checkpoint v1 is
unchanged. Complete journal replay, current eligibility and released
interoperability remain unresolved at their later criteria.

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
two later criteria still return 3. Malformed or unsafe invocations return 2;
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

Small fixture success does not resolve the full-layout Step 1 native inspect
Git-fetch timeout or establish the adopted service benchmark. The historical
111,860,548-byte CP-3 reference has absent observation bindings and its
observation precondition returns `FOB001`; no current four-command success or
service admission follows from its old transport result. The fixture Linux
environment permits executable temporary files for upstream producer tools;
that is test support, not an adopted production isolation profile.
