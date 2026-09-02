---
name: homologia
description: >
  Validate one closed Homologia manifest and its declared JSONL vector sets
  into deterministic, cap-bounded checked inputs. Expected integers retain a
  proved, recorded or asserted provenance form; a proved form requires a
  repository-relative Lazarus artefact reference. Mirror execution, comparison
  and verdicts have not shipped, so never report agreement or divergence. Fizz
  owns vector generation and Pandects owns economic laws.
metadata:
  version: "1.1.0"
---

# Homologia

## Frontier

Homologia owns the cross-implementation agreement frontier, not Hexaemeron's
delivery or Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run another
frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Homologia defines the boundary for comparing one pinned on-chain computation and one pinned off-chain mirror. It now checks the pair declaration and evidence-classed expected answers, but performs no comparison.

**Current frontier.** `check` admits one closed, cap-bounded manifest and its declared vectors into a deterministic checked-inputs record. It executes no mirror and produces no verdict, so nothing yet establishes that a pair agrees.
<!-- marketplace-context:end -->

Never report agreement as correctness.

The name comes from *homologia*, agreement. Agreement between two
implementations is the whole subject, and it is a narrower claim than either
being right.

A protocol's arithmetic gets written twice. Once in Solidity, where it runs in
unsigned 256-bit integers with an explicit rounding direction and a ray or wad
scale. Again off-chain, in an SDK that renders a balance or fills a signing
prompt, or in an analytics job that produces a report a desk acts on, where it
runs in IEEE-754 doubles, JavaScript `BigInt`, Python `int` or
`decimal.Decimal`, with the token decimals and the day-count applied by hand.

Nothing in an ordinary suite compares the two. A fuzzing campaign asks whether
the contract agrees with itself. A prose lint asks whether a signing prompt is
readable, not whether its number is right. So a mirror that is wrong by one
rounding direction, or by six orders of decimal magnitude, passes everything and
shows a person the wrong figure.

## What a verdict says, and what it never says

A verdict states that a named pair agreed, or diverged, over the vectors it was
given, at the revisions it names. It never states that either implementation is
correct. Two implementations of the same misunderstanding agree perfectly, and
the verdict carries that as its nearest overclaim so a reader cannot mistake one
for the other.

It also never claims coverage it was not given. Agreement over a vector set says
nothing about the vectors nobody supplied, so a verdict reports the set it read
rather than implying a class of inputs.

## The pieces

- **A pair.** One pinned on-chain computation, named by chain, contract and
  function identity, and one pinned mirror.
- **A mirror.** An off-chain reimplementation, executed as a pinned subprocess
  through the adapter protocol: vectors in as JSONL on stdin, one decimal
  integer per vector on stdout.
- **An expected answer.** The chain side's integer for one vector, carrying a
  provenance class of `proved`, `recorded` or `asserted`. A verdict inherits the
  weakest class used anywhere in it.
- **A divergence specimen.** The preserved vector, both answers and their
  signed difference, for one disagreement.

## Boundaries

Homologia consumes vector files; it never generates, mutates or minimises them,
which stays with fizz and Foundry. It executes no EVM: the chain side arrives as
evidence, and producing that evidence stays with lazarus. It judges no economic
law, which is pandects, and makes no performance claim, which is metron. It
compares two implementations at one pinned revision each, never two runs over
time, which is synkrisis.

## Promises at this frontier

This generation declares its packaging promise and the checked expected-answer
provenance promise. It declares nothing about mirror execution or numeric
agreement.

A promise says what a successful operation establishes and names the evidence
behind it. `check` can establish that declared bytes passed the closed shape,
path, cap, scale, tolerance and provenance rules and were bound into one
canonical record. It cannot establish that a referenced artefact proves the
answer, that a mirror ran or that two implementations agree.

The remaining two promises land with the step that builds their behaviour,
together with their own coverage rows and cases:

| Promise | Arrives with |
| --- | --- |
| `homologia-mirror-execution` | The pinned subprocess adapter protocol |
| `homologia-parity-verdict` | Comparison, rendering and verification |

The planned text is in
[the study](../../docs/homologia-study.md), under design options, where it is a
plan rather than a current claim.

## Promise Machine contract

### homologia-scaffold-identity

- Promise: This plugin's declared identity is one value across both host manifests and the suite marketplace, its canonical contract points at its ledger, its installed root-law copy is byte-identical to the suite law, and every operation that has not shipped refuses instead of answering.
- Evidence: The two host manifests, the marketplace entry, the canonical contract and ledger bytes, a byte comparison against the suite's `PROMISE_MACHINE.md`, and the exit status and streams of each unavailable verb.
- Evidence classes: checked
- Boundary: This establishes packaging and unavailable-operation refusal consistency. It establishes nothing about a mirror answer or agreement between implementations.
- Authorises: Installing and selecting the skill, then invoking only the operations whose own promises have shipped.
- Consequence: 0
- Refuses: A version that differs between the manifests and the marketplace, a contract with no ledger link, a drifted installed root-law copy, or an unavailable verb that exits zero as though it had produced an answer.
- Recovery: Repair the named file and rerun the plugin suite.
- Exceptions: none

### homologia-expected-answer-provenance

- Promise: A successful `check` establishes that one version-1 manifest and every declared vector set passed the closed pair, scale, path, cap, tolerance and expected-answer provenance rules and were bound by source digest into one canonical checked-inputs record.
- Evidence: The manifest and vector source bytes and SHA-256 digests, the canonical checked record, stable success summary, published version-1 schemas, focused positive and hostile-input cases, and byte equality from checking the committed example twice.
- Evidence classes: checked, recorded
- Boundary: Admission preserves the supplied `proved`, `recorded` or `asserted` form. Homologia checks that a proved form names a safe Lazarus artefact reference but does not open or verify it, execute an EVM or mirror, establish that an expected integer is correct, or produce an agreement verdict.
- Authorises: Using the checked record as the declared chain-side input to the later mirror-execution step for exactly the pair, vector sets and source digests it names.
- Consequence: 1
- Refuses: An unknown or incomplete provenance form, bare `proved`, missing recorded chain or block identity, missing asserted author, unsafe or repeated path, duplicate id or key, malformed JSON, non-canonical integer, missing or unequal scale, undeclared tolerance, any fixed cap breach, changed input identity, or partial output on failure.
- Recovery: Repair the named manifest field or vector, keep every path inside its declared directory, reduce the input below the named cap, remove the stale destination only if desired, and rerun `check`; do not strengthen the evidence class during recovery.
- Exceptions: none
