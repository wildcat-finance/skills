# Imprimatur labelled-corpus calibration runbook

This run has one step. Corpus selection, blind labels, calibration, the sealed
holdout run and the frontier decision share one acceptance boundary so the
holdout cannot become a second tuning set.

## Step 1: Build and run the labelled prose evaluation

**Goal.** Measure Imprimatur by tier on a provenance-bound human and
model-assisted corpus, fix only calibration-proven errors, and record the
resulting frontier decision.

**Entry.** `main` at
`bcbaede047e746aec5573a31d70201275ee58533`, with Imprimatur
`imprimatur-v1.1.0`, its 55-test suite green, and no held-out evaluation.
Unrelated `.agents/skills/sapheneia/` and `plugins/sapheneia/` paths are
excluded from reads, writes, staging, tests and PR scope.

**Exit.** The repository contains a 64-paragraph immutable fixture with 32
human samples under the user's pre-1-August-2025 rule and 32 affirmatively
model-assisted samples; source-grouped 32/32 splits; two blind raw label sets;
adjudication; source, schema, balance, coverage and leakage checks; a
deterministic standard-library evaluator; baseline and final reports; and
prose-checked study and runbook copies. Calibration can change lint behavior
only for measured errors. The sealed holdout runs once after candidate hashes
are frozen. Imprimatur's version and ledger advance once, closing as mature
only if every study gate holds and otherwise retaining one exact evidenced
next job. The evaluator reproduces its checked-in report, the normal suite and
repository checks pass, and the controller reaches `done` after a merged PR.

**Files.** Create
`plugins/hexaemeron/skills/imprimatur/evals/labelled-prose-v1/` for the fixture,
annotations, reports, study and runbook. Add
`plugins/hexaemeron/skills/imprimatur/scripts/evaluate_labelled_corpus.py` and
focused tests. Change existing lint code or lexicons only when a calibration
error requires it. Update only Imprimatur's `EVOLUTION.md` and `SKILL.md`
version metadata for the governed frontier decision. Append this step's audit
record to `audit/AUDIT.md` without replacing earlier records.

**Tests.** Run the new evaluator offline with source verification and compare
its normalized output with `final.json`. Run
`python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py`,
`python3 plugins/hexaemeron/tests/run_tests.py`, and
`python3 -m unittest discover -s tests`. Validate every new JSON/JSONL row,
source hash, origin rule, split group, duplicate threshold, annotation offset,
agreement denominator, metric denominator, frontier digest and changed skill
frontmatter. Run Imprimatur over every shipped Markdown file and clear all
hard findings.

The implementation branch is `step-1-calibrate-imprimatur-corpus`, based on
`main`. The audit concentrates on provenance, label independence, offset
accuracy, source-group leakage, metric pairing, denominator handling, sealed
holdout discipline, evidence-backed lint changes and the maturity decision.
