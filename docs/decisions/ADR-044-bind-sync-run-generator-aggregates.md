# ADR-044: Bind sync-run generator aggregates to static authority and exact final trees

## Status

Accepted, 2026-08-28. This decision was first recorded as ADR-042, then
renumbered after pull request
[#718](https://github.com/wildcat-finance/skills/pull/718) assigned that number
to the interpreter-advance decision on `origin/main`. Only the identity
changed; the accepted generator-aggregate design remains unchanged.

This record fixes the design selected for issue
[#710](https://github.com/wildcat-finance/skills/issues/710). The controller
implementation belongs to Fiat Step 2; this record alone does not establish
that implementation.

## Context

Fiat's version-1 integration revalidation represents every affected path
individually and refuses a path list over 500 entries. The product-first sync
reconstructed from issue #622 has 1,095 required paths. Of those, 887 form the
portable Promise Machine runtime generated under
`.agents/skills/promise-machine/runtime/`; the remaining 208 still fit the
individual bound.

A higher general cap would admit the incident but would not establish who owns
the large surface or which command validates it. The portable runtime already
has a generated `MANIFEST.json` with sorted per-file byte counts and SHA-256
digests. That manifest names 886 payload files but cannot contain a digest of
itself, so revalidation must bind the manifest as an additional file.

## Decision

Introduce `fiat-integration-revalidation/v2` while retaining the version-1
parser and its 500-path refusal unchanged. Version 2 separates individually
listed paths from generator aggregates. An aggregate is authorised only by a
controller-source registry entry; an artefact cannot declare, widen, or
override its owner.

The initial registry contains one id,
`promise-machine-portable-runtime-v1`. It fixes the prefix
`.agents/skills/promise-machine/runtime/`, generator
`scripts/portable_promise_machine.py`, manifest `MANIFEST.json`, manifest
schema `promise-machine-portable-runtime/v1`, and verification command
`python3 scripts/portable_promise_machine.py check`. Its reviewed envelope is
at most 1,024 final files and 32 MiB of final file bytes. Existing Git command
limits remain 30 seconds and 2 MiB of metadata output.

Each aggregate binds the entire final prefix tree in the exact sync commit,
not merely the members changed by the sync. The controller reads Git objects,
never mutable worktree bytes. It validates manifest paths, modes, byte counts,
and blob SHA-256 values, then adds the manifest itself as one row. It computes
each file digest as
`SHA256("fiat-generator-file/v1\0" || path_utf8 || NUL || mode_ascii || NUL || decimal_byte_count || NUL || file_sha256_hex)`.
It sorts those digests by full repository-relative path and computes the tree
digest as
`SHA256("fiat-generator-tree/v1\0" || concatenated_raw_file_digests)`.

Every required path outside a selected registered prefix remains an exact
individual entry under the 500-path limit. A successful check must cover each
individual path and name each aggregate id with the registry's exact command.
All schema, path, Git-object, manifest, resource, digest, and coverage checks
finish before the controller changes state or appends a ledger entry.

## Alternatives

Raise the integration cap to 4,096. This would be a smaller code change, but it
would treat any large diff as acceptable without generator authority or
whole-tree evidence. Rejected.

Split the base advance into several syncs or shard the revalidation artefact.
The 887-path runtime addition is atomic in the upstream delta, so each hop
still encounters the same surface. Sharding would also weaken exact coverage.
Rejected.

Let each version-2 artefact supply its own prefix and generator command. This
would avoid a controller release for a new generator, but untrusted evidence
would choose both the authority boundary and the command said to validate it.
Rejected.

## Consequences

Once implemented and guarded, issue #710's reconstructed topology can use one
checked 887-file aggregate plus 208 individual paths without weakening the
ordinary 500-path rule. Version-1 receipts and small fixtures remain on their
existing route.

The whole final tree supplies evidence for additions, changes, and deletions,
but it costs one bounded Git-object read and hashes files that did not change.
The manifest self row is evidence supplied by the revalidation artefact rather
than by the self-referential manifest.

A new generator, prefix, or larger resource envelope requires a reviewed
controller-source change. A failed check refuses before receipt mutation. This
decision does not mutate or recover the halted #622 run, and this ADR alone
does not establish that the version-2 controller has been implemented.
