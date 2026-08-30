# Wave mu adversarial corpus v1

## Status and scope

This is a data-only contribution candidate for issue #878. It carries 60
frozen hostile-case contracts and no adapter, provider call, Fiat run, runtime
fetch, deployment, publication action, credential, or remote mutation.

The files are custody material, not a completed implementation. They are
unadapted and unexecuted. A local advisory review of this contribution candidate
occurred during preparation; it is not an accepted independent implementation or Fiat security review
required by #878, and it is not maintainer acceptance. The corpus is not
independent Fiat safety evidence.

## Contents and custody

The corpus lives at
`tests/fixtures/wave-mu-adversarial-corpus-v1/`. Its 60 JSON fixtures, README,
schema, manifest, and validation receipt are frozen exact-byte inputs. The
schema also has a byte-identical mirror at
`schemas/wave-mu-fixture-contract-v1.schema.json`.

The fixture root is
`b6563135ebc5a7a874c22818b48a7414268ae9b62a0b7389238d72b95a7758be`.
The support-file SHA-256 values are:

| File | SHA-256 |
| --- | --- |
| `README.md` | `f35617a9e5912f8b54b323f3b6056999be9ed34cb8ca53fb1cd4f9be7245e369` |
| `fixture-contract.schema.json` | `1af15c0039194e43f47211cea6984da0aa077177d7d83521148d79530cf1c422` |
| `corpus-manifest.json` | `748406dd05c00a0acb1f019cb2665670b842cac5a00bb4ff17c354fc796b1e16` |
| `validation.json` | `02e40bf0f59f41a0050702e3977ae93c6b48dd9a2875ae20b2195cc49ebb50f7` |
| `source-catalog.json` | `3f26d7741d3204ae39d670f31ebb1b790c2154eb7347edf27ddd288e8032935c` |

No licence header was added to a frozen corpus file. The validator is an
offline, read-only, Python-standard-library checker. It allowlists every
member, caps file sizes, rejects symlinks and nonregular members, checks
support and fixture digests, the fixture root, canonical JSON and base64
stimuli, the schema mirror, and the declared non-execution boundaries. It does
not evaluate the supplied JSON Schema with a JSON Schema implementation.

`source-catalog.json` is byte-addressed historical/source support outside the
60-member corpus-root calculation. The validator bounds and digests it, checks
its JSON registry `EV-01` through `EV-17`, and resolves every fixture's
required-evidence identifier. It is not executed evidence.

The frozen README retains two Markdown hard-break byte sequences from its
source. `.gitattributes` disables whitespace checking only for that exact
README path; it does not waive whitespace checks for any other corpus member
or repository path.

The frozen README and `validation.json` Status and Built fields are 2026-08-28
freeze-time custody metadata. A later draft pull request is a separate sharing event;
preserving that wording keeps the recorded hashes and custody intact. The frozen corpus
grants no publication authority. Ashir's separate authorization to prepare or submit
this draft is external and exact-action-specific.

## Contract boundaries

Each fixture keeps `execution_status` and its observation at `not_run`, with
null decision and side-effect fields. Every adapter remains unresolved. The
stimuli are synthetic and inert. The manifest disallows live credentials,
private repositories, personal data, authority to mutate a remote target,
runtime dependency fetch, and package-manager network access.

The fixture author, independent security reviewer, human publication approver,
and publisher are separate roles. A future implementation must name its owner,
interfaces, adapter bytes and digest, receipt consumer, isolated environment,
and approval boundary before it can use this data. A successful future adapter
test would still establish only the named fixture, adapter, implementation,
configuration, and recorded evidence.

## Provenance and inbound terms

This contribution is original local custody material. Its stimuli are
synthetic and inert; it contains no live credentials, private data, or private
repository content. It is proposed as an Apache-2.0 inbound contribution,
subject to any maintainer CLA, DCO, AI-disclosure, authorship, signing, and
review terms that apply at submission time. This document grants no authority
to submit, publish, or accept the contribution.
