# Decision: Verify checkpoint authority by ordered replay

## Status

Proposed, 2026-09-16, for P-862 in issue #1676. This draft awaits the governed
implementation and integration. It authorizes no production signer or store.

## Context

Native CP-3 inspection verifies the archive's claimed boundary signature
list and internal evidence. It does not prove contributor enrollment,
complete historical commit coverage, current denial state or replicated
publication. The adopted #862 specification needs those meanings released
in Skills before the service consumes them.

Ariadne checks evidence bindings and predicate gates. Giving a predicate a
signature-authentication promise would change its existing boundary and
leave native reconstruction, key history and freshness without a clear owner.

## Decision

Ship a separate, versioned authority protocol and offline verifier under
Fiat. Use closed canonical records, exact-byte DSSE PAE, SHA-256/P-256 DER
signatures, explicit trust roots and empty emitted DSSE key hints. Derive
the complete required commit set from the verified native boundary and
check exact signature coverage and authorized history. Keep native anchor
and identity v1 unchanged.

Replay one bounded journal record at a time through a signed complete head,
retaining the decision index. Keep authorization/cancellation exclusive,
make publication evidence finite, and order one-use stream permits with
denials. Separate historical verification from live eligibility: offline
evidence cannot prove that a newer denial does not exist.

Register an Ariadne checkpoint predicate for explicit digest roles and
evidence gates. External verification authenticates signatures; Ariadne
does not. Minimal parent continuation belongs in this release, while full
frontier and resolution operations remain #865.

## Alternatives

An eager replay model retained every parsed journal body before replaying
the same records. On the executed 1,280-record, 512-decision corpus both
models decoded 1,280 records and passed the same hostile cases. Peak traced
Python allocation was 5,578,310 bytes for eager indexing and 266,697 bytes
for ordered replay. The selected model is the unique frontier on equal
decode work and lower measured memory. The measurement does not prove
production latency, total RSS, cryptographic authority or native coverage.

Using only the native signature list would leave the required-set denominator
unproved. Treating an Ariadne pass as signature authenticity would exceed its
contract. Choosing a newest database row would leave journal omission and
rollback unproved. Those shortcuts do not satisfy the adopted specification.

## Consequences

The verifier needs an explicit complete history and trusted freshness input
for current eligibility. It may verify historical evidence while refusing
the current authority claim. Missing private native dependencies remain
unavailable; the adapter never runs archived commands to repair them.

Schemas, verifier, fixture corpus, native capability limits and exact tool
profiles become release components with immutable pins. New conformance
evidence must establish production-format signatures, complete coverage,
replay and independent interoperability before integration.

R2 governing amendments use content-addressed keys, full read-back and
indefinite bucket locks in separate EU accounts. The common provider stays
a documented risk. Service code, live key custody and deployment remain
their separately governed packets. Native issues #1647, #1648 and #1649
remain open containment obligations.
