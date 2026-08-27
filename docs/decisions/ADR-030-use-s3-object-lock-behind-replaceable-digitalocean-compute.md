# ADR-030: Use S3 Object Lock behind replaceable DigitalOcean compute

## Status

Retired, 2026-08-27. The proposal below was never accepted and no longer
governs. [ADR-028](ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md)
replaces it with checkpoint continuation that works without S3 Object Lock or
DigitalOcean compute. The remaining body is preserved as historical rationale.

PR #569 published this record as ADR-025. It moved to ADR-030 so the five
Wave Delta records stay contiguous and in reading order once the collisions on
ADR-023 and ADR-024 were resolved. The decision is unchanged.

## Context

The checkpoint service needs public API/worker compute, scratch space, a query
index, immutable accepted bytes, a separate recovery copy, and a signer whose
private key is not on the worker. A DigitalOcean Droplet with a large disk can
host the API cheaply, but the same project credentials or host compromise could
then affect the decision and its only stored evidence.

S3 Object Lock protects object versions rather than key names. Governance mode
prevents ordinary deletion, overwrite of an existing version, or retention
change while still permitting an explicitly authorised bypass. A new write at
the same key can create a new version, so discovery must bind exact versions
rather than assume a content-addressed key has only one object. S3 replication
can copy locked objects and retention metadata to another locked bucket, but it
is asynchronous.

DigitalOcean supports compute and Managed PostgreSQL in London. Its database
backup/restore path is useful for index recovery, but destroying a cluster also
destroys its retained backups. Database rows cannot be the only accepted
record.

## Decision

The first deployment uses replaceable DigitalOcean compute in `LON1` for the
API and worker. One host may run both initially under separate service
identities; a measured security, availability, or performance need can split
them later without changing protocol. Encrypted scratch is sized from measured
archive expansion and concurrency, has hard quotas and short expiry, and never
holds the only accepted copy.

DigitalOcean Managed PostgreSQL is a derived query/index store with encrypted
connections, separate migration/application roles, automated backup/restore,
and a tested rebuild from immutable object records. A database restore may
accelerate recovery but cannot decide which checkpoint was accepted.

AWS carries authority in two separately controlled accounts and regions:

1. An unlocked quarantine bucket accepts short-lived, checksum/size-bounded
   candidate uploads and expires rejected or abandoned bytes.
2. A primary bucket created with versioning and S3 Object Lock stores accepted
   archives, acceptance statements, revocations, resolutions, key transitions,
   and run-anchor/base records in governance mode for at least 365 days.
3. A destination bucket in a separate account and region has Object Lock
   enabled and receives locked replicas with retention no shorter than primary.

The service does not return `accepted` until it has read back and verified the
exact primary archive version, the corresponding locked replica version, the
KMS-signed acceptance statement, and that statement's locked replica. The
statement names both bucket/key/version identities, checksums, retention,
protocol/policy/validator versions, `snapshot_id`, and `archive_sha256`.

An asymmetric KMS `ECC_NIST_P256` signing key using `ECDSA_SHA_256` signs the
typed acceptance/revocation/resolution service statements. Its private key does
not leave KMS. The Skills protocol pins the public verifier and key identity;
key rotation uses a typed signed transition so old statements remain
verifiable.

The DigitalOcean workload obtains short-lived AWS credentials through IAM
Roles Anywhere and separate profiles/session policies for validator, publisher,
replica verifier, and statement signer. No long-lived AWS access key is stored
on the host.

Runtime roles do not receive object/object-version delete, governance bypass,
retention shortening, bucket/policy/Object-Lock/replication administration, or
KMS administration/deletion. Governance bypass is break glass: MFA, two named
approvers, one exact object version, bounded session, stated reason, and a
durable after-action record. Ordinary poison handling creates a signed
revocation and retains the bytes.

## Alternatives

- **Droplet or attached volume as authority.** Cheapest and easiest to operate.
  Rejected because host/project compromise or disk loss can change both the
  service decision and its only evidence.
- **DigitalOcean Spaces as the only object store.** Keeps one provider and
  removes cross-cloud identity. Rejected because this design needs version-
  specific retention enforcement, a separate authority account, and a signer
  outside the Droplet's custody.
- **Ordinary versioned S3 without Object Lock.** Easier lifecycle and deletion.
  Rejected because a runtime or administrator credential can erase accepted
  versions without leaving the evidence the protocol expects.
- **S3 Object Lock compliance mode.** Stronger deletion resistance, including
  against account root. Not chosen for the first deployment because the
  governance-mode exact-version break-glass boundary was explicitly retained.
  Runtime roles still receive no bypass, and a later move to compliance mode is
  a new recorded decision rather than a flag change.
- **One AWS account/region.** Less policy and replication work. Rejected because
  account/region loss or compromise would remove the independent recovery copy.

## Consequences

The deployment spans two providers and two AWS accounts. Roles Anywhere,
replication, KMS, certificate rotation, permission tests, and recovery drills
add operational work. Acceptance can wait on asynchronous replication rather
than returning immediately after primary upload.

In return, losing or compromising the DigitalOcean host or mutable database
does not erase accepted object versions or supply the receipt private key. A
checkpoint described as accepted already has two locked copies and a statement
that binds their exact versions.

Governance mode is not absolute immutability. A specially authorised bypass
can act, which is why the permission is absent from runtime and held behind a
recorded human boundary. Object Lock also permits later versions at one key,
which is why no client may resolve acceptance from a key name alone.

The 365-day value is a minimum first profile. Extending retention is allowed;
shortening it or adding lifecycle deletion for accepted state needs a new
decision and migration/recovery proof.
