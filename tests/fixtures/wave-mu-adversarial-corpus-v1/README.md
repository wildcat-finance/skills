# Wave μ exact-byte fixture-contract corpus v1

**Status:** Local design candidate; 60 exact-byte transport-neutral fixture contracts; not adapted, executed, independently reviewed, shared, or accepted by Wildcat.  
**Built:** 2026-08-28T02:07:08Z  
**Corpus root:** `b6563135ebc5a7a874c22818b48a7414268ae9b62a0b7389238d72b95a7758be`

## What this is

This directory turns the earlier 60-row Wave μ hostile-case catalogue into 60 immutable fixture-contract files. Each fixture binds:

- canonical synthetic stimulus bytes, byte count, and SHA-256;
- the issue and programme gate it covers;
- the trusted component that must enforce the result;
- an explicit expected decision and failure effect;
- required trusted evidence classes;
- zero-side-effect invariants for credentials, private data, normal-machine visibility, undeclared egress, controller mutation, and remote writes; and
- an explicit `not_run` observation placeholder.

The fixture bytes are data, not executable commands. They authorize no run or external action.

## Files

- `JS-01.json` through `PB-06.json`: 60 canonical fixture contracts.
- `fixture-contract.schema.json`: the v1 structural schema.
- `corpus-manifest.json`: file digests, corpus-root rule, #706 acceptance mapping, dependency policy, role separation, and non-claims.
- `validation.json`: deterministic local validation result.

Artifact SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `corpus-manifest.json` | `748406dd05c00a0acb1f019cb2665670b842cac5a00bb4ff17c354fc796b1e16` |
| `fixture-contract.schema.json` | `1af15c0039194e43f47211cea6984da0aa077177d7d83521148d79530cf1c422` |
| `validation.json` | `02e40bf0f59f41a0050702e3977ae93c6b48dd9a2875ae20b2195cc49ebb50f7` |

The corpus root is SHA-256 over the sorted concatenation of `fixture_id`, a NUL byte, the fixture-file SHA-256, and a line feed. It covers the 60 fixture files; the schema, manifest, validation, and this README are separately addressed.

## Safety choices

- All canaries are inert sentinel strings, never live credentials.
- The P0 dependency mode is JobSpec-bound, digest-pinned inputs only. Runtime dependency fetch and package-manager network access are absent.
- Publisher isolation uses permission/installation introspection and an expressly owned negative-control repository. It prohibits live probing of upstream or unrelated repositories.
- A remote mismatch stops and revokes. Closing, deleting, rewriting, or repairing a remote object requires new exact human approval.
- Fixture author, independent security reviewer, human publication approver, and publisher are distinct roles.

## What remains

These are exact-byte **contract fixtures**, not implementation-specific wire packets. Wildcat still needs to name the owner and repository, select the actual JobSpec/VM/proxy/gate/verifier/supervisor interfaces, and create a versioned adapter that translates each exact stimulus without weakening its oracle. The adapter bytes and digest must become additional bound inputs.

Only then can a credential-free synthetic run populate separate observation and trusted-receipt objects. A fresh independent reviewer must inspect the frozen implementation, adapter, fixtures, observations, and evidence before any patch-only pilot or publisher test.

No result here means Fiat is safe, Wave μ is production-ready, or a contribution is authorized for publication.
