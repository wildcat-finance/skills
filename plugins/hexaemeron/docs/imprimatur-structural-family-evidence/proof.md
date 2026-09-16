# Imprimatur structural family evidence proof

This document preserves the step 4 evidence for the run described in
[study.md](study.md) and [runbook.md](runbook.md). The controller ledger under
`.hexaemeron/` stays authoritative for phase order and terminal state. The
fixture itself, its collection record and its digest tables live in
[the fixture README](../../skills/imprimatur/evals/structural-family-evidence-v1/README.md).

## Demo path

Run from the repository root on 2026-09-10:

```bash
python3 plugins/hexaemeron/skills/imprimatur/scripts/check_family_evidence.py \
  --fixture plugins/hexaemeron/skills/imprimatur/evals/structural-family-evidence-v1 \
  --allow-below-minimum --report /tmp/family-evidence.json
python3 -c "import json; r=json.load(open('/tmp/family-evidence.json')); print(r['families'], sorted(b['family_id'] for b in r['below_minimum']))"
```

Output:

```text
42 ['causal_fact_clause_wrapper', 'empty_expletive_case', 'existential_relative_shell', 'reason_is_because']
```

The same checker command without `--allow-below-minimum` exits 1 and prints
four `tier-minimum` findings, one per family above.

## Budget

`/usr/bin/time -p python3 plugins/hexaemeron/skills/imprimatur/scripts/check_family_evidence.py --fixture plugins/hexaemeron/skills/imprimatur/evals/structural-family-evidence-v1`
reported `real 0.13` on three consecutive runs on an Apple M5 Max (arm64,
Python 3.14.6), against the study's budget of 2.0 seconds on the full
42-family fixture and the design probe's 76 ms baseline for one family. The
same command reported `real 0.04` on this machine when the step was first
built earlier on 2026-09-10. The checker and fixture bytes are identical
between the two measurements, so the 90 ms difference is machine state and its
cause is not established; both readings sit two orders of magnitude inside the
budget.

## Per-family counts

| Family | Tier | Candidates | Judged | Independent positives | Negatives | Minimum met |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `causal_subject_has_no` | `high-value` | 17 | 9 | 2 | 2 | yes |
| `causal_negative_passive` | `signal` | 30 | 3 | 2 | 1 | yes |
| `reason_is_because` | `high-value` | 18 | 18 | 1 | 2 | no |
| `causal_fact_clause_wrapper` | `high-value` | 14 | 14 | 0 | 2 | no |
| `backward_demonstrative_cause` | `signal` | 16 | 3 | 2 | 1 | yes |
| `agentless_choice_passive` | `signal` | 93 | 3 | 2 | 1 | yes |
| `purpose_periphrasis` | `signal` | 35 | 3 | 2 | 1 | yes |
| `stacked_epistemic_modal` | `signal` | 20 | 8 | 2 | 1 | yes |
| `redundant_connective_pair` | `high-value` | 13 | 4 | 2 | 2 | yes |
| `litotic_double_negative` | `signal` | 25 | 9 | 2 | 1 | yes |
| `attention_adverb_opener` | `signal` | 33 | 3 | 2 | 1 | yes |
| `empty_expletive_case` | `high-value` | 15 | 15 | 0 | 2 | no |
| `existential_relative_shell` | `signal` | 23 | 23 | 1 | 1 | no |

38 specimens ship: 22 Markdown paragraphs, 8 commit messages, 5 issue bodies
and 3 pull request bodies. The four families below minimum were each searched
over the whole pinned universe with a bounded pattern for their own form:
`reason_is_because` has exactly one reason-noun-plus-`because` sentence in the
universe, `causal_fact_clause_wrapper` has no causal connector before any of
its 14 `the fact that` occurrences, `empty_expletive_case` has none of its 15
`the case that` occurrences in the `it is the case that` shell, and
`existential_relative_shell` has its form twice in one document. The README's
collection record carries each search.

## Source replay

`--verify-sources` with `--allow-below-minimum` exited 0 over all 38 rows at
2026-09-10T02:53:40Z in step 3 audit round 4, the run's last network read.
The 8 thread-kind rows replay a current body; the 30 others replay a file at a
pinned commit or a commit by its sha.

## Frozen digests

The five lint and lexicon files are byte-identical to the starting ref
`7d12d63e13fe193fcc1f8827b393f8aa51161731`; `git diff --stat` against it over
`evals/labelled-prose-v1`, `scripts/imprimatur.py`, `lexicon` and
`EVOLUTION.md` prints nothing. Paths are relative to
`plugins/hexaemeron/skills/imprimatur/`.

| Path | SHA-256 |
| --- | --- |
| `scripts/imprimatur.py` | `7522d57632d5ceee515f37355744718853ee82d26c5e549b68571a2dce9ad50a` |
| `lexicon/hard.json` | `a6ad7adbc6c8e06512032cf460c92749a49a6c139b4f2aee101de8bdc95df844` |
| `lexicon/gated.json` | `e554ab6f9661d88095f285c6651983c980bd672b854287f74daa288b1dabc34c` |
| `lexicon/structural.json` | `908e20c6319b587e95fa21de5949a10c0088ed698d546b0a1048686211826240` |
| `EVOLUTION.md` | `19d88c8bbf1548c99509a964fd0828cc047e6319c4682292ea79973c42a1a606` |
| `evals/structural-family-evidence-v1/families.jsonl` | `3e5585ba0ee86754d37085f181817471b5abfb34aa2b9bed05cffab215937a4c` |
| `evals/structural-family-evidence-v1/issue-1298.md` | `ccff01a9db78693b183a3193b5cd76edbd908f75f3d48b4e25c46fda907f1e46` |
| `evals/structural-family-evidence-v1/schemas/family.schema.json` | `46244a6a6a9386b903aa16731f4b4f30df07945b2e3221320544b243aafa8185` |
| `evals/structural-family-evidence-v1/schemas/specimen.schema.json` | `ed8de25920f263308ed22928b603dcbd351230595b521af471d1f144dd1700c9` |
| `evals/structural-family-evidence-v1/selection-rejections.jsonl` | `d23f94f7b927fef41a0980f9fa5b67ac5c75dff464b5909fde4cc539743ddb26` |
| `evals/structural-family-evidence-v1/specimens.jsonl` | `406ed81594b9691a20b0c7c5c25e6839d6ba873c4bb616d427ecd2e07d5dcc0a` |

## Package identities

The Hexaemeron package moves from `1.6.27` at the starting ref to `1.6.32`,
the smallest increment above the `1.6.31` on `origin/main` at
`592390722f10df53658906623b15428dbfb88d8f` when this step was built, in
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`, `tests/test_version_propagation.py` and
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`. That sixth site, the
`{"1.6.32"}` assertion at line 5679, is the one the runbook's Files field
first missed: it held `1.6.27` while the manifests read `1.6.32`, which failed
the Hexaemeron suite once in 2,519 tests and turned `scripts/run_checks.py`
red with failure class `test-failure`. `origin/main` keeps the same line at
`1.6.31` beside its manifests. No skill ledger row moves: the fixture is an
evaluation input, not a lint generation, and `EVOLUTION.md` is byte-identical
above.

## Design cell and the halt

The study's design record carries one conformance gate,
`two-independent-specimens`, a count of at least 2 that blocks `integration`,
resolved by
`python3 plugins/hexaemeron/skills/imprimatur/scripts/check_family_evidence.py --fixture plugins/hexaemeron/skills/imprimatur/evals/structural-family-evidence-v1 --min-independent-positive 2 --tier high-value --report .hexaemeron/reports/jsonl-fixture-two-independent-specimens.json`.
That command exits 1: `reason_is_because` holds 1 independent positive,
`causal_fact_clause_wrapper` and `empty_expletive_case` hold 0. Its result is
recorded as one `protasis-design-report/v1` object at that report path with
`value` 0, `unit` `count` and `exit` 1, and

```bash
python3 "$PLUGIN_ROOT/skills/protasis/scripts/design_evidence.py" .hexaemeron/design-evidence.json --transition integration
```

exits 1 with:

```text
.hexaemeron/design-evidence.json:1: D008 jsonl-fixture/two-independent-specimens report must record exit 0
```

The gate fails on the evidence, not on the design: the universe holds no
second example of three high-value forms. The record is digest-pinned for the
run, so no amendment reaches it. The operator decided on 2026-09-10 that the
run halts at integration on this gate rather than widen the universe or reset
the run, and that the step stack is landed by hand with the halt disclosed in
the run pull request. The `step:4` transition of the same checker exits 0.

## Gate results

Every command in the amended Step 4 Exit was run on this tree. The checker
with `--allow-below-minimum --report` exits 0 with `families` 42 and the four
`below_minimum` rows above; the strict checker exits 1 on those four.
`scripts/promise_machine.py check` reports `clean: 18 plugin(s), 18
copy/copies`. The root suite runs 1,623 tests, `OK`. The Hexaemeron suite runs
2,519 tests, `2519/2519 tests passed`, and its Elenchus report at
`.hexaemeron/elenchus/step-4.json` records 0 failures, 0 errors and 0 skipped.
The Imprimatur suite reports `112/112 passed`. The Phylax, Ephoros and
Hypomnema lints each print `clean` at exit 0. The Imprimatur lint over
`study.md`, `runbook.md`, `proof.md` and the fixture README scores 100.0 with 0
defects each at `--max-defects 0`. `cmp` between the committed runbook copy and
`.hexaemeron/runbook.md` prints nothing. `git diff --check` prints nothing.
`scripts/run_checks.py` plans from changed paths, so on the clean committed
tree it selects nothing and reports `outcome nothing-selected`; taken as
`python3 scripts/run_checks.py --base fiat/1298-imprimatur-structural-prose-family-evidence-step-3-collect-and-annotate-specimens-f`
against committed history it selects 11 checks, passes each one and reports
`outcome green`. `.githooks/greenlight` runs the same set on the staged tree at
exit 0 and records the tree in `LAST_GREEN`.

Two of those results were red before this step's last two changes, and both
causes are recorded rather than worked around. The stale sixth version pin is
above. `tests/test_demonstrations.py` then failed
`HorosCensusCurrencyTests.test_the_committed_census_matches_a_fresh_scan` at
committed `.md` bytes 19,625,589 against a fresh 19,627,401, because the
runbook amendment that added the sixth pin to the Files field added 1,812 bytes
to the committed runbook copy. The census is regenerated with
`horos.py scan . --write` and `horos.py scan . --census --write` after the last
document edit in this step, so the committed rows equal a fresh scan; the row
is not quoted here because this document is one of the files it counts. `dead_code.py suppressions --check` refuses any checkout
holding modified tracked files, so it is green only once this step's changes
are committed.
