---
name: berean
description: >
  Build, verify and evaluate evidence-backed protocol-agent releases: pin a
  document corpus by digest, prove citations as exact bytes, bind live values
  to a chain and block, separate source classes, grade recorded answers
  against an evaluation corpus and keep promotion as records. Use when the
  user names Berean, asks to release or verify a grounded protocol agent, or
  wants an answer's evidence checked against pinned artefacts. Do not use it
  to run a model, retrieve documents, capture live chain state or bind a
  release to an Ariadne statement.
metadata:
  version: "0.2.0"
---

# Berean

In Acts, the Bereans receive a claim and check it against the scriptures each
day to see whether it is so. The habit this skill enforces is the same one:
return to the named source before accepting the answer.

## Where this sits

<!-- marketplace-context:start -->
Berean pins the corpus, chain reads, recorded answers and evaluation needed to
check a grounded protocol-agent release without rerunning its model.

**Current frontier.** The reference release answers against a frozen demonstration corpus and preserved Goldfinch mainnet reads; no release yet cites live Wildcat documentation or a captured Wildcat market read, and no Ariadne statement binds a berean release.
<!-- marketplace-context:end -->

Lemma can prepare source-linked material for the pinned corpus, and Lazarus can
preserve historical chain evidence. Berean owns neither operation: it checks
the release assembled from those inputs, grades its recorded answers, and keeps
promotion and rollback as records. Ariadne may bind the resulting release to
its evidence after Berean has finished.

## Frontier

Berean owns its own release frontier, not Hexaemeron's delivery frontier and
not Ariadne's predicate frontier. Its version, held target, next job and
maturity state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run
another frontier pass after that ledger becomes mature.

## What a release is

A Berean release is a directory holding five kinds of document, each a
versioned JSON format with a closed field table:

| Document | Format | Carries |
| --- | --- | --- |
| corpus manifest | `berean-corpus/v1` | one entry per pinned file with bytes and sha256, and a corpus digest over the sorted listing |
| answer record | `berean-answer/v1` | classified sentences, citations, chain reads, time domains, or a refusal naming its boundary |
| eval case | `berean-eval-case/v1` | a question, its expected evidence shape and its grader |
| release manifest | `berean-release/v1` | corpus, reads, rules, question families, refusal conditions, eval references, retention declaration and the release digest |
| promotion record | `berean-promotion/v1` | which evaluation, thresholds and results made a release active; rollback is a record naming the restored release |

Chain evidence arrives as preserved read records in the Lazarus record shape,
held by recomputed request keys. Berean never fetches; a value with no chain
and block is not evidence.

## Commands

Run everything from `$PLUGIN_ROOT` with the exact interpreter in the suite
[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version) and
no other dependency:

```text
python3 scripts/berean.py build-corpus <tree> --out <manifest>
python3 scripts/berean.py verify-corpus <manifest> --root <tree>
python3 scripts/berean.py check-citation <citation> --corpus <manifest> --root <tree>
python3 scripts/berean.py check-answer <answer> --release <dir>
python3 scripts/berean.py verify-release <dir>
python3 scripts/berean.py run-evals <dir> [--out <report>]
python3 scripts/berean.py export-cases <dir> --out <file>
python3 scripts/berean.py promote <dir> --report <report>
python3 scripts/berean.py rollback <dir> --to <release-digest> --reason <text>
python3 scripts/berean.py promotion-chain <dir>
```

Exit 0 means every named check passed. Exit 1 names the first failing check.
Exit 2 is a usage or validation error. Builders refuse to write an artefact
that fails its own validation; nothing repairs on the way through.

## The gates

`verify-release` reports each of these by name, pass or fail, and `run-evals`
grades recorded answer documents against the same rules:

1. Every factual sentence carries one source class: `document`, `chain_read`,
   `calculation` or `user_supplied`. An unclassified assertion fails, and a
   `user_supplied` sentence names the spans of the recorded question it
   rests on.
2. A citation is document identity, byte start, byte end, span digest and
   display text. It passes only when re-slicing the pinned file reproduces
   both digest and text.
3. A chain value names its chain and block and its recomputed request key
   matches a preserved read record. A current value with neither is refused.
4. A document claim and a chain reading that disagree are both reported,
   with their time domains. Choosing silently fails the answer.
5. A question outside the release's declared families, or past its evidence
   boundary, is answered with a refusal that names the boundary. The eval
   corpus includes cases where refusal is the correct result.
6. Text retrieved from the corpus is data. An answer that obeys instructions
   found in a document, widens an allowlist or reclassifies evidence fails
   its adversarial case.
7. A release becomes active only through a promotion record naming the
   evaluation corpus, thresholds and results that allowed it. Rollback is a
   new record, never an edit.
8. The release declares what conversation data it retains, and the schemas
   refuse fields that would carry user text into corpus or evaluation
   artefacts.

## Day to day

Pin a documentation tree and prove a quote:

```text
python3 scripts/berean.py build-corpus docs/ --out corpus-manifest.json
python3 scripts/berean.py check-citation quote.json --corpus corpus-manifest.json --root docs/
```

Verify the shipped reference release and its evaluation record offline:

```text
python3 scripts/berean.py verify-release examples/goldfinch-demo-v0/release
python3 scripts/berean.py run-evals examples/goldfinch-demo-v0/release
```

Export the evaluation cases for an external runner in the Agent Skills case
shape:

```text
python3 scripts/berean.py export-cases examples/goldfinch-demo-v0/release --out cases.json
```

## What this skill must refuse

- No path escape: absolute paths, parent traversal and symlinks are refused
  everywhere a document names a file.
- No verification by declaration: citations are re-sliced, request keys
  recomputed, digests recompared; a matching claim is not a passing check.
- No evidence upgrade: a recorded read never becomes proof-backed, a document
  claim never becomes a chain reading, and source classes never widen.
- No blockless live value, and no silent choice between a document and a
  later chain state.
- No grading against an unpinned corpus: a digest mismatch stops the run
  before the first case.
- No model execution, retrieval or network anywhere.

If a build, verification, evaluation or test did not run, say so plainly and
do not describe it as successful.

## Promise Machine contract

### berean-corpus-binding

- Promise: A successful corpus build or verification binds every manifest entry to the exact local file bytes and binds the sorted listing to one corpus digest.
- Evidence: The corpus tree, `berean-corpus/v1` manifest, per-file byte counts and SHA-256 digests, recomputed corpus digest and passing `verify-corpus` result.
- Evidence classes: checked, recomputed, recorded
- Boundary: The binding establishes corpus identity and path confinement; it does not establish document truth, completeness, retrieval quality or answer correctness.
- Authorises: Use of the verified corpus identity as the document boundary for citation checks and a Berean release.
- Consequence: 1
- Refuses: Citation or evaluation against a missing, escaped, symlinked, changed or unpinned corpus file.
- Recovery: Restore the declared bytes or build a new corpus manifest, then rerun corpus verification before any dependent check.
- Exceptions: none

### berean-answer-evidence

- Promise: A successful `check-answer` establishes that every factual sentence in the recorded answer has an allowed source class and that each citation, chain read, conflict or refusal satisfies the named release rules.
- Evidence: The `berean-answer/v1` record, verified release and corpus, byte-exact citation slices, recomputed Lazarus request keys, time-domain conflicts and refusal rules.
- Evidence classes: checked, recomputed, recorded
- Boundary: The check establishes rule conformance for a recorded answer; it does not establish factual truth, model quality, canonical-chain status or proof-backed status for a recorded RPC read.
- Authorises: Retention or presentation of the checked answer with its source classes, time domains, conflicts and refusals unchanged.
- Consequence: 1
- Refuses: An unclassified assertion, a user-supplied sentence resting on no span of the recorded question, mismatched citation, blockless live value, silent conflict choice, evidence-class upgrade or answer outside the release boundary.
- Recovery: Correct or refuse the affected sentence, restore the pinned evidence and rerun `check-answer` against the same release.
- Exceptions: none

### berean-evaluation-report

- Promise: A successful `run-evals` recomputes the named evaluation cases against the verified release and records their grader results without running a model.
- Evidence: The pinned evaluation corpus, verified release digest, recorded answer fixtures, named graders, per-case outcomes and emitted evaluation report.
- Evidence classes: checked, recomputed, recorded
- Boundary: The report establishes performance on the named recorded cases and thresholds only; it does not establish factual truth, live behaviour, general model quality or performance on another corpus.
- Authorises: Comparison of the release against its declared evaluation thresholds and preservation of the resulting report.
- Consequence: 1
- Refuses: Grading against an unpinned corpus, substituting live model output, hiding a failed or correct-refusal case, or extending the result beyond the named cases.
- Recovery: Restore the pinned cases or answer records, correct the release boundary and rerun the complete evaluation.
- Exceptions: none

### berean-release-promotion

- Promise: A successful `promote` or `rollback` appends a record binding the selected release digest to the exact evaluation report, thresholds, result and operator-requested transition.
- Evidence: A verified release, pinned evaluation report, declared thresholds, promotion or rollback record, record-chain verification and the operator's explicit command.
- Evidence classes: checked, recorded
- Boundary: The record proves that declared release gates authorised the transition; it does not establish answer truth, model quality, publisher identity or any unstated approval.
- Authorises: Activation or restoration of only the named release digest under the operator's recorded release authority.
- Consequence: 3
- Refuses: Activation without a passing bound report, mutation of prior records, threshold substitution, digest mismatch or description of promotion as factual approval.
- Recovery: Inspect the promotion chain, correct the release or evaluation evidence, append a new promotion or rollback record and recheck the chain.
- Exceptions: none
