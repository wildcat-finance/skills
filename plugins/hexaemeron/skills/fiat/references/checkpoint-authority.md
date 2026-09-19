# Checkpoint authority records and signatures

## Scope

Step 2 implements `records-and-signatures` for `ordered-replay`, under
`adr/verify-checkpoint-authority-by-ordered-replay`. Native checkpoint v1 is
unchanged. Native admission, complete journal replay, current eligibility and
released interoperability remain unresolved at their later criteria.

## Records and bytes

The [schema source](../scripts/checkpoint_authority/schema.py) defines all 19
closed record types. Its [published schemas](../checkpoint-authority/schemas/)
use JSON Schema 2020-12. All declared fields are required; optional values have
an explicit null branch. Unknown fields and unsupported tags refuse.
`parse_record` also checks calendar dates, scope, predecessor shape, validity
intervals, digest roles and record-local joins. A validation record's claimed
commit list is structurally checked; Step 3 must independently derive it.

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
three later criteria still return 3. Malformed or unsafe invocations return 2;
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
