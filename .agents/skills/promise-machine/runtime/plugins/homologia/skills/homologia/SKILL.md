---
name: homologia
description: >
  Inspect or build the scaffold for comparing one pinned on-chain computation
  with one pinned off-chain mirror, integer for integer, over declared vectors.
  The substantive comparison operations have not shipped: the current command
  is help-only and every verb refuses, so never report agreement or divergence.
  The planned boundary covers SDK or analytics calculations involving rounding,
  fixed-point scales, or token decimals. Fizz owns vector generation and
  single-implementation fuzzing; Pandects owns economic laws.
metadata:
  version: "0.1.0"
---

# Homologia

## Frontier

Homologia owns the cross-implementation agreement frontier, not Hexaemeron's
delivery or Solidity frontier. Its version, held target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run another
frontier pass after that ledger becomes mature.

<!-- marketplace-context:start -->
## Where this sits

Homologia defines the boundary for a future comparison between one pinned on-chain computation and one pinned off-chain mirror. Its current scaffold performs no comparison.

**Current frontier.** Homologia ships its contracts, packaging and a help-only command. No manifest is checked, no mirror is executed and no verdict is produced, so nothing yet establishes that a pair agrees.
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

## Promises, and why the three domain ones are not here

This scaffold declares one promise, about its own packaging, and none about
numeric agreement.

A promise says what a successful operation establishes and names the evidence
behind it. Nothing here compares anything: every verb refuses with exit 3.
Declaring the three promises the study designs would put three claims in the
contract with no case that could support them, and the root law's first sentence
refuses exactly that. What this version can show is that it is installed under
one identity and that it refuses, so that is what it claims.

Each of the three lands in the step that builds its behaviour, together with its
coverage row and its own positive, missing, overclaim and recovery cases:

| Promise | Arrives with |
| --- | --- |
| `homologia-expected-answer-provenance` | Manifest, vector and provenance checking |
| `homologia-mirror-execution` | The pinned subprocess adapter protocol |
| `homologia-parity-verdict` | Comparison, rendering and verification |

The full text of all three is in
[the study](../../docs/homologia-study.md), under design options, where it is a
plan rather than a claim.

## Promise Machine contract

### homologia-scaffold-identity

- Promise: This plugin's declared identity is one value across both host manifests and the suite marketplace, its canonical contract points at its ledger, its installed root-law copy is byte-identical to the suite law, and every command verb refuses instead of answering.
- Evidence: The two host manifests, the marketplace entry, the canonical contract and ledger bytes, a byte comparison against the suite's `PROMISE_MACHINE.md`, and the exit status and streams of each verb.
- Evidence classes: checked
- Boundary: This establishes packaging and refusal consistency. It establishes nothing about a manifest, a vector, a mirror or agreement between implementations, because nothing here compares anything.
- Authorises: Installing and selecting the skill, and building the checking behaviour of the next step on top of it.
- Consequence: 0
- Refuses: A version that differs between the manifests and the marketplace, a contract with no ledger link, a drifted installed root-law copy, and a verb that exits zero as though it had compared something.
- Recovery: Repair the named file and rerun the plugin suite.
- Exceptions: none
