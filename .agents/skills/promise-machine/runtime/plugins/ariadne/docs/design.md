# Design

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The grounded-agent predicate now ships as the fifth registered Ariadne predicate, with a closed schema, gates 2 and 5, conformance fixtures and a bounded offline capture path that binds an existing `berean-release/v1` tree without importing or running Berean, executing an agent, regrading evaluations or reaching a network.
<!-- marketplace-context:end -->

Why ariadne is shaped the way it is, and what was considered and rejected on
the way.

## The problem

A release publishes a claim. The evidence behind it sits somewhere else, joined
by a URL and a promise: the compiler that produced the bytecode, the test run,
the fuzz campaign, the audit and its scope, the deployment.

The links do not establish that the audit covered the released commit, that the
build produced the deployed bytecode, or that the fuzz run used the settings the
report describes. The evidence exists. Its identity and provenance fall away
when the release is assembled, and what a recipient gets is a row of claims each
of them would have to reconstruct by hand. Most do not, and a green badge stands
in for the work rather than proving it happened.

Ariadne writes the join down as a statement whose subject is a digest, so a
reader can check the binding without trusting whoever assembled it.

## Prior art, and where this starts

The envelope and the statement are borrowed. Neither is forked.

- **in-toto Statement v1.** `_type` is the literal
  `https://in-toto.io/Statement/v1`, `subject` is an array of
  ResourceDescriptors each of which must carry `digest`, `predicateType` is a
  type URI, `predicate` is the object. Subjects match by digest alone; `name`
  only distinguishes entries.
- **in-toto ResourceDescriptor v1.** `name`, `uri`, `digest`, `content`,
  `downloadLocation`, `mediaType`, `annotations`, with at least one of `uri`,
  `digest` or `content` required.
- **DSSE v1.0.0.** Envelope fields `payload` (base64 of the serialised body),
  `payloadType`, and `signatures[].sig` with optional `keyid`. The signature
  covers `PAE(type, body) = "DSSEv1" SP LEN(type) SP type SP LEN(body) SP body`,
  where `LEN` is decimal ASCII with no leading zeros.
- **Sigstore.** `cosign attest` and `cosign verify-attestation` produce and
  check exactly this envelope. Signing is a solved problem and gets delegated.
- **SLSA provenance v1** covers how a build ran. It does not cover Solidity
  interfaces, storage layout, fuzz corpora, audit scope or deployment identity,
  which is where this work starts.
- **Sourcify and solc's CBOR metadata** bind deployed bytecode to source. That
  is a check ariadne records the result of, not one it reimplements.

The existing in-toto predicates nearest this problem are `test-result`,
`release` and `link`. None of them carries a bytecode digest or a
storage-layout delta.

## The shape

Two layers, and the split is the design.

**The core is artefact-neutral.** Its subject is a digest, of anything: a
compiled artefact, a content-addressed dataset, a fixture bundle, a corpus. What
it adds to a bare statement is the discipline a bare statement does not carry:
absence stays visible, a result is not upgraded into a conclusion, every claim
names the exact subject it covers, and replay separates what must match byte for
byte from what cannot.

**A predicate is the shape for one kind of artefact.** It declares which fields
a statement of that kind carries and how a verifier checks them. The core holds
predicates apart so a dataset statement and a contract statement share a
verifier and one envelope format without sharing a schema.

| Module | Layer | Holds |
| --- | --- | --- |
| `digests.py` | foundation | Digest sets, file and tree digests, and the rule for when two agree |
| `statement.py` | core | Statement v1 construction and parsing, subject handling |
| `envelope.py` | envelope | DSSE read and write, PAE, both base64 alphabets |
| `safejson.py` | boundary | Size, depth and duplicate-key bounds for documents from elsewhere |
| `core_predicate.py` | core | The `claims` and `commands` block every predicate carries |
| `gates.py` | verification | The five core gates, run for any predicate |
| `verify.py` | verification | The report: gates, signature state, and what went unchecked |
| `registry.py` | dispatch | Type URI to predicate module |
| `predicates/solidity_release.py` | predicate | The Solidity release predicate |
| `capture/foundry.py` | adapter | A Foundry build read into that predicate |
| `deltas.py` | comparison | ABI, method identifier and storage comparisons |
| `replay.py` | execution | Re-running the commands a statement marks deterministic |

## The gates

Five belong to the core and every predicate inherits them. Two are shape a
predicate fills in.

| Gate | Owner | What it holds |
| --- | --- | --- |
| 1 Every claim names its subject | core | A result tied to a repository or a branch is rejected; it names the digest it covers |
| 2 The environment is recoverable | predicate | A bare tool version is not a build description |
| 3 Absence stays visible | core | Skipped, failed, timed-out and redacted work stays in the statement |
| 4 Results are not upgraded into conclusions | core | A passing property records the property and the run, not that the artefact is safe |
| 5 Deltas name both sides | predicate | A comparison fails when either baseline cannot be identified exactly |
| 6 Replay distinguishes deterministic work | core | Bytecode can require an exact match; a fuzz campaign's coverage cannot |
| 7 Signature verification is external | core | An unsigned statement is labelled unsigned and no statement receives an implied author |

## Choices, and what they cost

**One Solidity release tool with the gates baked in** would be the shortest way
to a signed release statement. It was rejected because the specification's claim
is that one core serves four artefacts, and a tool built that way forks at the
second predicate.

**Predicates as JSON Schema documents, validated generically,** was rejected as
the enforcement path. The standard library has no JSON Schema validator, and the
gates are not expressible as schema anyway. Absence, delta baselines and
determinism classes are semantic checks. A schema that says `counterexamples` is
an array cannot say that an empty array beside an absent campaign record is a
lie.

What ships instead is a hand-written structural validator with the schema
published beside it as the interoperability artefact, and a test comparing the
schema's required-field lists and its revision pattern against the module's own
field tables, so the two cannot drift.

**Signing in process** was rejected twice over. It needs a dependency, and it
would put key custody inside a tool whose job is to be checkable by someone who
does not trust it. Gate 7 already makes the unsigned statement a supported state
rather than a degraded one.

## Constraints

The implementation uses only the standard library and the exact interpreter in
the suite [pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).
That rules out both a JSON Schema library and an in-process signing library,
and decides the two choices above. Tests touch no network and require no
`forge`: the Foundry output they read is committed.

## Where the risk is

What an audit should look hardest at, and what the log in
[`../audit/AUDIT.md`](../audit/AUDIT.md) works through.

1. **Canonicalisation.** DSSE signs bytes. A verifier that re-serialises the
   payload before checking it verifies something the signer never signed, or
   displays one thing and checks another.
2. **Base64 variance.** DSSE permits both alphabets. A lenient decoder paired
   with a strict re-encoder is a mismatch surface.
3. **Digest confusion.** Subjects match by digest alone. Mixed-case hex,
   truncated values, a weak algorithm accepted alongside a strong one, or an
   empty digest set are all ways to make a subject match something it should
   not.
4. **Gate bypass by omission.** Every absence gate breaks the same way, through
   a field left optional. A missing disposition must fail rather than default to
   passing.
5. **Replay as code execution.** A recorded command inside a statement is
   attacker-controlled data.
6. **Capture reading outside the project.** Paths, symlinks and traversal.
7. **Secrets in statements.** Build commands carry RPC URLs, API keys and
   tokens.
8. **Untrusted JSON.** Size, nesting depth, duplicate keys and integer size in a
   document handed to `verify` by a stranger.
9. **Missing-baseline degradation.** A delta whose baseline cannot be resolved
   must fail gate 5 rather than report no changes.
10. **Unsigned reported as verified.** Without `cosign`, the verifier reports
    structure and gates and says the signature was not checked. It must never
    print a word that reads as an authenticated author.

## Terms

- **Statement.** The in-toto v1 object: subject, predicate type, predicate.
- **Subject.** The digested artefact a statement is about. Matching is by
  digest.
- **Predicate.** The typed body of a statement, shaped for one kind of artefact.
- **Predicate type.** The versioned URI naming that shape, under
  `https://ariadne.wildcat.finance/`.
- **Envelope.** The DSSE wrapper carrying the payload and its signatures.
- **PAE.** Pre-authentication encoding, the byte string a DSSE signature
  actually covers.
- **Digest set.** Algorithm to hex value map, as in `{"sha256": "..."}`.
- **Gate.** A check the verifier runs over a statement; a breach fails the
  statement.
- **Disposition.** What happened to a declared check: passed, failed, skipped,
  timed out, redacted.
- **Determinism class.** Whether a recorded command's output must match byte for
  byte on replay, or cannot.
- **Delta baseline.** The named previous release a comparison is made against,
  identified by digest.
- **Release subject.** One compiled contract in a release, with its creation and
  runtime bytecode digests.
- **Conformance fixture.** A statement committed as a test case, valid or
  breaching a named gate, for other producers and verifiers to run against.
