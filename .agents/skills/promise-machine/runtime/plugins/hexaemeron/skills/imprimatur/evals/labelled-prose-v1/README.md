# Labelled prose evaluation v1

This fixture measures Imprimatur's three prose tiers on 64 public Wildcat
paragraphs. It is an enriched evaluation set, not an estimate of how often a
pattern appears in Wildcat prose and not an authorship detector.

## Selection and provenance

The fixture has 16 source groups with four paragraphs each. Eight groups are
human under the maintainer-supplied rule: the source commit is reachable from
a pinned public default-branch head and its committed timestamp precedes
`2025-08-01T00:00:00Z`. Eight groups have affirmative model-assistance
evidence in a commit trailer. Unmarked prose at or after the cutoff is
unknown and is not scored.

Each origin contributes 32 samples. Each origin has three technical
documentation groups, three delivery or incident report groups, and two
GitHub change-description groups. Candidate paragraphs within a group are
ordered by:

```text
sha256("imprimatur-labelled-prose-v1" || source_url || text)
```

The first four eligible rows survive. Paragraphs contain 18 to 180 words and
exclude code, tables, generated data, quotations of other work, vendored
material, current Imprimatur prose, and copied skill mirrors.

Duplicate checks apply NFKC, lowercase the text, remove Markdown markers, and
collapse whitespace. Exact normalized matches are rejected. A candidate is
also rejected when its word five-gram Jaccard similarity is at least 0.80
against a selected sample, the current Imprimatur tests and prose, or the
pinned slopkit specimens at
`b33718bb9283c11b09567dc714f92d90ffb7bd16`. The selection produced no
rejected candidates; `selection-rejections.jsonl` is therefore empty.

`samples.jsonl` records the immutable source, pinned collection head, source
timestamp, content hashes, source group, genre, origin class, affirmative
origin evidence, selection rank, and nearest duplicate comparison for each
paragraph.

## Split

`split.json` assigns whole source groups. Each half has eight groups and 32
samples, split 16 human and 16 model-assisted. Each origin in each half
contains all three genres. No source group crosses calibration and holdout.

The calibration split was the only labelled prose available while lint code
or lexicons could change. Holdout labels stayed sealed until the candidate
code and lexicon hashes were frozen. The holdout then ran once. A later change
creates a new fixture version rather than rewriting this result.

## Blind annotation

Annotators receive a separate JSONL packet containing only `sample_id`,
`text`, and `rules`. Its identifiers are opaque `B-001` through `B-064`; an
identifier must not encode origin, genre, source, or split. The hidden mapping
is kept outside the tracked fixture until two independent annotations and
blind adjudication are complete.

`annotation-seal.json` binds the packet, hidden mapping, samples, split, and
pre-annotation schemas to SHA-256 digests. It discloses the mapping digest,
not the mapping. The packet schema and both annotation schemas reject the
internal `H-` and `M-` sample identifiers. After annotation and blind
adjudication ended, `blind-id-map.json` made that mapping reproducible in the
published fixture.

Each annotator returns one row per blind sample. A row may have no annotations.
Every annotation supplies tier, family, UTF-8 byte offsets, decision, severity,
and a reason. A licensed gated term also names the local evidence range.
Adjudication uses the blind identifiers and records a reason for each sample.
The mapping back to internal sample identifiers occurs only after adjudication.

## Metrics

Predicted and adjudicated spans match one to one within a sample and tier.
They need the same family and either exact offsets or token-span intersection
over union of at least 0.50. The pairing with the greatest overlap wins.

The evaluator reports TP, FP, FN, TN, precision, recall, F1, specificity and
gold prevalence by tier, origin, and represented family. Undefined ratios are
`null`. Advisory signals have a separate alert-yield measure. Agreement is
binary sample-by-tier Cohen's kappa plus one-to-one raw span F1 between the
two independent files.

The fixture is deliberately enriched. Before the sealed run, each holdout
tier was required to have at least eight actionable gold spans and eight
negative samples. Those counts support measurement; they do not describe
production frequency.

## Recorded outcome

Both raw annotations and the adjudication cover all 64 samples. Annotator A
supplied 99 spans and annotator B supplied 90. They matched on 46 spans. The
overall raw span F1 is 0.486772. Binary sample-by-tier Cohen's kappa is
0.644820 over 192 decisions. Both are below the pre-registered 0.80 minimum,
so the adjudication is insufficient evidence for lint tuning.

Holdout coverage also failed before evaluation. It has 12 hard and 25 gated
actionable spans, but only two structural actionable spans. All tiers have at
least eight negative samples. The corpus was preserved without refill or
reannotation so the failure remains inspectable.

The candidate is the untouched `imprimatur-v1.1.0` implementation. Its lint
and three lexicon digests are in `candidate-freeze.json`. No lint behavior or
lexicon changed. The calibration and holdout counts are provisional because
the agreement and coverage requirements failed:

| Split | Tier | TP | FP | FN | TN | Precision | Recall | F1 | Specificity |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| calibration | hard | 0 | 0 | 5 | 27 | null | 0.0 | null | 1.0 |
| calibration | gated | 0 | 0 | 12 | 24 | null | 0.0 | null | 1.0 |
| calibration | structural | 0 | 0 | 2 | 30 | null | 0.0 | null | 1.0 |
| holdout | hard | 0 | 0 | 12 | 21 | null | 0.0 | null | 1.0 |
| holdout | gated | 0 | 0 | 25 | 15 | null | 0.0 | null | 1.0 |
| holdout | structural | 0 | 0 | 2 | 30 | null | 0.0 | null | 1.0 |

The holdout is spent. Its results may be replayed to check the published
artefact, but they must not guide a v1 change. Any replacement corpus or lint
tuning belongs to `labelled-prose-v2` and must not tune against the v1
holdout.

The source and evidence checks run without invoking the lint:

```bash
python3 ../../scripts/evaluate_labelled_corpus.py \
  --fixture . --validate-only --verify-sources
```

The published calibration report can be reproduced without reading the
holdout:

```bash
python3 ../../scripts/evaluate_labelled_corpus.py \
  --fixture . --split calibration --expect baseline.json
```

## Files

- `samples.jsonl`: immutable source and provenance rows.
- `split.json`: source-group calibration and holdout assignment.
- `selection-rejections.jsonl`: deterministic selection rejections, empty for
  this fixture.
- `schemas/`: sample, split, blind packet, raw-label and adjudication schemas.
- `annotation-seal.json`: pre-annotation digests.
- `raw-label-a.jsonl` and `raw-label-b.jsonl`: independent blind labels.
- `adjudication.jsonl`: adjudication completed with opaque ids.
- `blind-id-map.json`: opaque-to-internal mapping published after blind work.
- `labels.jsonl`: adjudicated labels mapped to internal sample ids.
- `candidate-freeze.json`: lint, lexicon, fixture and holdout-label digests at
  the sealed boundary.
- `baseline.json`: untouched calibration result.
- `final.json`: frozen calibration result and the single holdout result.
- `source-validation.json`: offline checks plus the authenticated immutable
  source replay summary.
- `study.md` and `runbook.md`: the amended specification and delivery step.

Source verification uses immutable GitHub objects and the pinned collection
heads. Normal metric replay is offline.
