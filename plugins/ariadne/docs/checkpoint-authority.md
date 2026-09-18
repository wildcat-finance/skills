# The checkpoint authority predicate

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The grounded-agent predicate now ships as the fifth registered Ariadne predicate, with a closed schema, gates 2 and 5, conformance fixtures and a bounded offline capture path that binds an existing `berean-release/v1` tree without importing or running Berean, executing an agent, regrading evaluations or reaching a network.
<!-- marketplace-context:end -->

Type URI: `https://wildcat.finance/attestations/checkpoint-authority/v1`.

This predicate binds one closed checkpoint authority record: the signed body
the Hexaemeron checkpoint authority protocol carries inside a DSSE envelope.
Ariadne checks the record's own bytes and the statement around it. It does not
authenticate the signature, run a native checkpoint command, contact a store,
replay the policy or decision journal, or decide whether a snapshot is
eligible now. Each of those is reported as unchecked on every run.

## The body

The predicate is one of nineteen closed record types, selected by `type`. The
published schema, `schemas/checkpoint-authority-v1.json`, is a release copy of
the owner's schema source, `plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/schema.py`,
projected as one `oneOf`. A checkout parity test compares the parsed copy with
the owner's projection and the `authority-replay` manifest binds the copy's
bytes by digest; an isolated installation reads only the copy and imports no
sibling plugin. Every object is closed: an unknown key, a missing key, a value
of the wrong exact type, a boolean where an integer belongs, or a body above
65,536 canonical bytes fails `predicate-fields`.

Every record carries `protocol`, `environment`, `service`, `scope`, `type`,
`sequence`, `previous`, `issued_at` and `issuer`. All but the first
`authority-policy` also carry `policy`, the typed reference to the policy they
were issued under. The remaining fields belong to one record type each:

| Record type | Fields |
| --- | --- |
| `authority-policy` | `authorities`, `allowed_protocols`, `signature_profile`, `native`, `release`, `storage_policy_sha256`, `locations`, `max_head_age_seconds` |
| `enrollment-challenge` | `actor_id`, `key`, `nonce`, `expires_at` |
| `key-enrollment` | `actor_id`, `key`, `proof`, `not_before`, `not_after` |
| `key-rotation` | `actor_id`, `key`, `proof`, `replaces`, `not_before`, `not_after` |
| `key-revocation` | `actor_id`, `enrollment`, `effective_at`, `reason` |
| `run-grant` | `actor_id`, `enrollment`, `permissions`, `not_before`, `not_after` |
| `run-registration` | `native_anchor_sha256`, `initial_base`, `source`, `owner_id`, `permitted_protocols`, `initial_parent`, `root_authorized` |
| `upload-endorsement` | `actor_id`, `enrollment`, `grant`, `candidate_id`, `nonce`, `expires_at`, `identities`, `carrier_length`, `parent` |
| `validation` | `candidate_id`, `attempt_id`, `lease_id`, `identities`, `carrier_length`, `native`, `release`, `input_sha256`, `output_sha256`, `started_at`, `ended_at`, `native_results`, `coverage`, `authorization`, `parent`, `resources` |
| `storage-copy` | `role`, `location_id`, `object`, `object_key`, `operation`, `get_sha256`, `get_length`, `configuration_policy_sha256`, `verified_at` |
| `parent-link` | `registration`, `initial_base`, `parents`, `prior_receipts`, `producer_prefix_sha256`, `native` |
| `acceptance` | `repository_slug`, `issue`, `initial_base`, `identities`, `carrier_length`, `accepted_representation`, `semantic_subject`, `native`, `release`, `actor_id`, `endorsement`, `contributor_key`, `enrollment`, `signing_history`, `grant`, `validation`, `parent_acceptance_ids`, `transition`, `copies`, `signer_policy_identity` |
| `cancellation` | `decision_id`, `candidate_id`, `reason` |
| `publication-finalization` | `acceptance_id`, `acceptance`, `authorization_head`, `archives`, `receipts` |
| `denial` | `target`, `reason`, `descendants`, `effective_at`, `policy_head` |
| `authorized-removal` | `denial`, `removed`, `incident_sha256`, `operator_approvals`, `outcome` |
| `journal-entry` | `stream`, `event`, `decision_id`, `payload_sha256`, `previous_commitment` |
| `authority-head` | `policy_history`, `decisions`, `challenge`, `expires_at` |
| `stream-permit` | `actor_id`, `session_id`, `nonce`, `expires_at`, `outer_sha256`, `receipt_sha256`, `acceptance_id`, `finalization`, `head`, `grant` |

A typed evidence reference is an object with exactly `type` and `sha256`. The
digest is the SHA-256 of the exact signed envelope it names, never of a bare
body, and the `type` says which record kind the reader should find there.

## Subjects and digest roles

A record carrying `identities` gives the statement three subjects, named for
their roles: `snapshot_id` is the semantic state, `controller_manifest_sha256`
the native controller evidence, and `outer_sha256` the exact carrier bytes. A
record without `identities` has one subject named `record`, whose digest is the
SHA-256 of the record's canonical bytes. `subject-roles` fails when the subject
names, order or digests differ from what the record's own fields say.
`evidence-references` fails when any typed reference names one of the three
identity digests or the record's own digest, which is the role substitution
the owner protocol refuses.

## The gates

Gate 2, `environment`: every timestamp names a real UTC instant, and each
declared interval holds. `not_before` is at or before `issued_at`, which is
before `not_after`; `expires_at` follows `issued_at` by at most 300 seconds, or
60 for a `stream-permit`; a `storage-copy` was `verified_at` no later than it
was issued; a `validation` `started_at`, `ended_at` and `issued_at` are
ordered; a `denial` or `key-revocation` takes effect no later than it is
issued; and each policy authority's interval is non-empty. The published
pattern accepts `2026-02-30T00:00:00Z`; this gate does not.

Gate 5, `comparison`: relations name both sides. `sequence` is 1 exactly when
`previous` is null; a `journal-entry`'s `previous_commitment` follows the same
rule; an `authority-head`'s `policy_history` and `decisions` have a null tail
exactly when their count is zero; a `parent-link`'s immediate parent appears
among its `prior_receipts`; a `run-registration` is `root_authorized` exactly
when it has no `initial_parent`; and an `acceptance` `transition` is
`registered-root` exactly when `parent_acceptance_ids` is empty, with a
continuation's `initial_base` equal to the record's.

`required-coverage`: an `acceptance` binds `accepted_representation` to
`outer_sha256` and `carrier_length`, and carries one `primary` and one
`recovery` copy at distinct locations, each over that exact object under
`sha256/<digest>`. A `validation` lists a non-empty sorted `required` commit
set, verifies exactly that set in order, runs the four native stages in order
and binds `input_sha256` and `input_bytes` to the carrier. A
`publication-finalization` carries both archive and receipt copies, the
receipts over the acceptance envelope. A `storage-copy` reads back the exact
object it names. An `authority-policy` names two locations at distinct
location and account identities and unique P-256 authority fingerprints.

## What Ariadne does not establish

A clean report says the record is well formed and internally bound. It does
not say the record was signed by an enrolled or authorised key, that the
native commands ran, that the copies exist in any store now, that the record
sits in a complete policy or decision history, or that the snapshot is
eligible for release. Those are the authority verifier's results, in the
owner's closed vocabulary: `historical` is `valid`; `publication` is one of
`complete`, `incomplete`, `authorized-absence` or `unexplained-absence`;
`current_eligibility` is one of `eligible`, `denied`, `unavailable` or
`unknown`. Ariadne copies that vocabulary for its parity test and never
produces a value from it.

There is no capture path for this predicate. The checkpoint authority service
produces and signs the records; Ariadne reads what it is handed.

## Fixtures

`tests/fixtures/conformance/pass-checkpoint-authority-acceptance.json` and
`tests/fixtures/conformance/pass-checkpoint-authority-head.json` verify clean.
The breaching fixtures each change one leaf of the acceptance:
`fail-gate2-checkpoint-authority-calendar-instant.json`,
`fail-gate5-checkpoint-authority-orphan-predecessor.json`,
`fail-check-subject-roles-checkpoint-authority-swapped-roles.json`,
`fail-check-evidence-references-checkpoint-authority-identity-as-evidence.json`
and `fail-check-required-coverage-checkpoint-authority-copy-length.json` fail
the one result their name claims;
`fail-check-predicate-fields-checkpoint-authority-unknown-field.json` fails
every result, because a record outside the closed shape establishes nothing.
