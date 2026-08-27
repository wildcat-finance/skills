# Example attestations

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The grounded-agent predicate remains unimplemented; the state-fixture predicate now ships with its schema, gates, conformance fixtures and a capture path that reads a Lazarus fixture's evidence counts rather than recomputing them.
<!-- marketplace-context:end -->

Three statements produced by a capture and committed as they came out. Two are
Solidity releases over the fixture project in `../tests/fixtures/forge-project`; the
third is a state fixture over the Lazarus fixture in
`../../lazarus/examples/goldfinch-v0`.

The build records, digests and deltas in them came from the compiler. The test
and fuzz dispositions did not: capture takes those from whoever runs it, and
here they were supplied by hand to illustrate the two shapes. Nobody ran a fuzz
campaign against a nine-line escrow contract. A test asserts the examples still
describe the committed fixture, so a rebuild cannot leave them quoting bytecode
that no longer exists.

| File | What it shows |
| --- | --- |
| `escrow-v1.1.0.json` | A clean release: tests and fuzz passed, an audit covering the released commit, a deployment |
| `escrow-v1.1.0-with-gaps.json` | The same release with a fuzz campaign that timed out and an audit covering an earlier revision |
| `goldfinch-v0-fixture.json` | A Lazarus state fixture: the pinned block with its state root, eleven components, and the three evidence counts read from the manifest rather than recomputed |

The second one is why both are here. A format whose only examples are clean
releases teaches producers to make their releases look clean. Both verify, and
the second says out loud that a campaign ran out of budget with four properties
outstanding and that its audit covered a commit two behind the release.

```bash
python3 ../scripts/ariadne.py verify escrow-v1.1.0-with-gaps.json
```

Seven gate lines and three checks, exit 0, with the audit line reading `1
covering a revision other than the released commit`.

## The tampered copies

`tampered/` holds a copy of each with one thing changed, and the suite asserts
that `verify` exits 1 on each and names the gate.

| File | Change | Gate |
| --- | --- | --- |
| `escrow-v1.1.0-claim-repointed.json` | A claim points at bytes the statement does not cover | 1 |
| `escrow-v1.1.0-with-gaps-reason-removed.json` | The timed-out campaign keeps its disposition and loses its reason | 3 |
| `goldfinch-v0-fixture-state-root-removed.json` | The state root goes and the proof-backed count stays | the evidence check |

The third tamper is the rule the state-fixture predicate exists for. Two records are
counted as proved against a state root the statement no longer carries, so the count
describes work that could not have happened. Gate 2 still passes, which is the point:
the pin is intact and the claim about it is not.

```bash
python3 ../scripts/ariadne.py verify goldfinch-v0-fixture.json
```

Seven gate lines and three checks, exit 0, with the evidence line reading `2
proof_backed, 1 header_bound, 4 recorded_rpc` -- the counts Lazarus wrote.

## What tampering the gates do not catch

Worth knowing before anybody reads a clean run as more than it is.

A producer editing their own unsigned statement can delete a gap and record a
pass instead. Nothing in the gates can tell that apart from a run that really
passed, because both parse, both pass every gate, and neither contradicts
anything else in the document.

What catches it is an externally verified signature. A statement is signed
over its bytes, so an edit after signing fails verification, and an edit before
signing puts the producer's name on the claim. Gate 7 keeps that boundary
visible: Ariadne labels an unsigned statement unsigned and never supplies an
author from a signature it did not check.

The gates refuse the shapes that let a careless statement read as a careful
one. They do not, and cannot, refuse a producer willing to lie in a document
they signed.

The state fixture has its own version of this, worth naming because it is the thing
that predicate cares most about. A producer who moved four recorded responses into
the proof-backed column would verify clean: the counts come from the manifest, and
nothing here cross-checks a count against the components beside it. What refuses that
is the capture path, which reads the counts from what Lazarus wrote rather than taking
them from a caller, and a statement written by hand does not go through it.
