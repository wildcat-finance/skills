# ADR-071: Hold checkpoint authority in locked storage behind replaceable compute

## Status

Accepted, 2026-09-02. This record is the standing successor to
[ADR-030](ADR-030-use-s3-object-lock-behind-replaceable-digitalocean-compute.md),
which [ADR-028](ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md)
retired on 2026-08-27 and which keeps its Retired status and its body.
[ADR-069](ADR-069-reinstate-the-distributed-checkpoint-layer-above-the-local-store.md)
reopened the distributed layer and asked for one successor per retired record;
this is the second of four. It carries ADR-030's decision forward, rebased on
what `fiat-v5.49.1` already ships.

## Context

ADR-030 chose a first deployment: a DigitalOcean Droplet in `LON1` for the API
and worker, DigitalOcean Managed PostgreSQL as the derived index, and two AWS
accounts holding quarantine and locked authority buckets with a KMS signer.
Reading it now, the substrate choices and the durability rules sit in one
record, and only the durability rules still decide anything.

Nothing is deployed. ADR-028's mandatory local hand-off amendment makes
`<origin>/.hexaemeron/checkpoints/<run-worktree-name>/` the only current
transport, and no checkpoint operation uploads, posts, commits or pushes.
`hexctl checkpoint export` writes the controller capsule that a step checkpoint
carries; the outer archive around it, its Git bundle, its signature proof and
its sidecars remain a manual procedure ADR-028 leaves in place. A step
checkpoint on this machine is about 94 MB, and a service would be accepting
objects of that order.

What has also changed is how many identities such an object has. The capsule
manifest digest names exact controller bytes. `hexctl checkpoint identity` on
the default branch names the checkpoint's meaning, derived from the verified run
anchor and the accepted boundary, and survives repacking. The outer archive
digest names the packed bytes a service would receive. ADR-030 was written when
`archive_sha256` was the only identity in sight, and its acceptance statement
reflects that.

## What this carries from ADR-030

**Carried verbatim.** Authority rests with the object store, which enforces
retention at the version rather than the key and sits in an account separate
from the compute that writes to it. An unlocked quarantine bucket takes short-lived,
checksum-bounded and size-bounded candidate uploads and expires rejected or
abandoned bytes. A primary bucket with versioning and object lock in governance
mode holds accepted archives, acceptance statements, revocations, resolutions,
key transitions and run-anchor records for at least 365 days, that value being a
minimum first profile: extending it is allowed, and shortening it or adding
lifecycle deletion needs a new decision with migration and recovery proof. A
destination bucket in a separate account and region receives locked replicas
with retention no shorter than primary. The service does not return `accepted`
until it has read back and verified the primary archive version, the locked
replica version, the signed acceptance statement and that statement's replica.
The signing key is asymmetric, its private half never leaves the key service,
the protocol pins the public verifier and key identity, and rotation happens
through a typed signed transition so old statements stay verifiable. Compute
obtains short-lived credentials through a federated identity path with separate
profiles for validator, publisher, replica verifier and statement signer; no
long-lived access key sits on the host. Runtime roles receive no object or
version delete, no governance bypass, no retention shortening, and no bucket,
policy, lock, replication or key administration. Bypass is break glass: multi-
factor authentication, two named approvers, one exact object version, a bounded
session, a stated reason and a durable after-action record. Ordinary poison
handling writes a signed revocation and retains the bytes. The derived index is
a query store rebuilt from immutable object records; a database restore may
speed recovery but cannot decide which checkpoint was accepted.

**Rebased on `fiat-v5.49.1`.** Three changes. First, the acceptance statement
binds three identities rather than one: the outer archive digest for the bytes
received, the `fiat-controller-checkpoint/v1` manifest digest for the controller
capsule inside them, and the semantic checkpoint identity for what the
checkpoint means. A service that repacks a carrier changes the first without
changing the third, and a client resolving acceptance needs to know which one it
is holding. Second, the validator runs against a real artifact shape: a step
checkpoint is a Git bundle, an exported capsule, a manifest, a public key, a
proof transcript and their sidecars, with sizes near 100 MB, so quarantine
quotas, scratch sizing and expansion limits are measured against that rather
than estimated. Third, the current transport is the local filesystem, so this
record governs a deployment that does not exist and is not authorised; every
clause reads as a requirement on a future service, not a description of one.

**Dropped.** The provider commitments. DigitalOcean compute in `LON1`,
DigitalOcean Managed PostgreSQL, AWS S3 Object Lock and AWS KMS were chosen for
a first deployment that never happened, and naming them here would state a
decision nobody has taken with current prices, current accounts and a current
threat model. They stay in ADR-030 as the worked example of a substrate that
satisfies the rules above, and the deployment record that authorises a service
picks the substrate and records why. Also dropped: the claim that one host may
run API and worker together under separate service identities, which is a
sizing decision for whoever deploys.

## Decision

Checkpoint authority is the locked object store and the signed statement, never
the compute or the index in front of them. Any deployment of the checkpoint
service satisfies the carried rules above and names its substrate in its own
record.

The acceptance statement binds the outer archive digest, the controller capsule
manifest digest and the semantic checkpoint identity, and names which of the
three a client may treat as the checkpoint's meaning.

This record authorises no account, no provider, no spend and no deployment.

## Alternatives

- **Name the substrate again, updated.** Concrete and immediately actionable.
  Rejected because a provider decision taken today would be stale before anyone
  is authorised to deploy, and it would arrive in a record whose subject is
  durability rules rather than procurement.
- **Compute or attached volume as authority.** Cheapest to operate. Rejected for
  ADR-030's reason, unchanged: host or project compromise then alters both the
  decision and its only evidence.
- **One account and one region.** Less policy and replication work. Rejected
  because losing that account removes the independent recovery copy along with
  the primary.
- **Keep the local checkpoint store as the permanent answer.** It ships and it
  works. Rejected as a general answer, because a local archive cannot be
  accepted by anyone but the machine holding it, which is the gap the reopened
  layer exists to close. It remains the current transport until a service is
  authorised.
- **Bind acceptance to the outer archive digest alone.** Simplest statement.
  Rejected because repacking a carrier would then read as a different
  checkpoint, and the identity that survives repacking already ships.

## Consequences

A future service has a rulebook without a shopping list. Whoever deploys picks
the substrate and defends it in a record of their own, and this one tells them
which properties they may not trade away.

Binding three identities makes the acceptance statement larger and the client
rules more explicit. A client that wants one number to compare has to say which
number, and that is the honest cost of a capsule, a carrier and a meaning being
three different things.

Nothing executable changes. The local checkpoint store remains the only
transport, and this record adds a file.
