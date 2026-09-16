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

## Deferred criteria

The historical empty corpus remains a refusal fixture in the scaffold tests.
Native admission, full authority replay and released interoperability retain
separate unresolved criteria. A passing record/signature report proves none
of those later transitions.
