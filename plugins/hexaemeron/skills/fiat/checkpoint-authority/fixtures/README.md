# Public record and signature specimens

## Inventory

[manifest.json](manifest.json) lists the complete released schema/fixture
inventory by SHA-256 and every `records-and-signatures` case. The golden
records cover all 19 types. Hostile vectors include malformed JSON and the
container-tag regression; the executable cases add field, reference, trust,
signature and resource-bound mutations.

## Keys and signatures

All enrolled identities and public keys are synthetic test material. Private
fixture keys are outside this package. Native SSH and OpenPGP proofs and
endorsements accompany the P-256 fixtures. The two valid randomized envelopes
share payload bytes; each double-hashed envelope has the exact matching valid
payload and an invalid signature over a second digest. Cosign's separate
specimen also matches the supplied semantic blob.

## Replay history

This directory also holds the Step 4 replay corpus. `replay-history.json` is
one complete signed history: five policy records, one root acceptance with its
parent link, endorsement, validation and copies, a finalization and a stream
permit, 39 envelopes in all, signed with ephemeral test keys that were never
retained, over synthetic native attestations that ran no native command.
`replay-hostile.json` records fourteen unsigned mutations of that history with
the code and stage each must refuse. `replay-budget.json` is the Metron
measurement of a 1,391-record workload against the study's budget, and
`replay-manifest.json` binds those files, Ariadne's schema copy and
conformance fixtures, and every `authority-replay` case id.
`python3 plugins/hexaemeron/tests/checkpoint_authority_replay_corpus.py --check`
inspects manifest drift; `--history` signs a fresh history and changes every
digest, so run it only when the fixture must change. The portable Promise
Machine runtime omits this directory and `../native-fixture/`; the reporters
that read them run from a full checkout, under
`adr/omit-checkpoint-authority-conformance-corpora-from-the-portable-runtime`.

## Deferred criteria

The historical empty corpus remains a refusal fixture in the scaffold tests.
Native admission and full authority replay have their own criteria and
reports; released interoperability retains a separate unresolved criterion. A
passing record, native or replay report proves no later transition and no
current production eligibility.
