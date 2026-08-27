# Brevitas evaluation interface

The evaluation surface runs offline from
`plugins/brevitas/skills/brevitas/`. It does not call a model or infer a model
identity from prose, filenames or Git metadata.

## Legacy cases

Each directory under `evals/cases/` contains `case.json`, `original.md` and
`target.md`. Run all current unit and evaluation cases with:

```bash
mise exec python@3.13.15 -- make -C plugins/brevitas/skills/brevitas test
```

The three legacy cases predate the held cross-model corpus. They remain
regression fixtures but do not count as cross-model coverage.

## Held corpus

The held-corpus manifest is `evals/corpus.json`; qualifying fixtures live in
`evals/cases/<case-id>/`. The manifest is a closed, versioned interface. Each
case must name one of `x-ray`, `solidity-auditor`, `gas`, `invariant` or
`diff-review`, its provider and full returned model identifier, capture client
version, source, prompt and output digests, pre-lint classification, expected
result and exact protected evidence spans.

All manifest paths are relative to the corpus root. The offline runner rejects
unknown or duplicate fields, escaped, linked, non-regular or oversized files,
digest drift, incomplete family/model coverage, unclassified cases and
protected spans that are missing, duplicated or reordered. It validates held
bytes before invoking Brevitas and never uses a model output as authority.

This scaffold contains no qualifying held cases yet and establishes no
cross-model coverage. The manifest and its validator arrive with the captured
corpus.

## Elenchus report

The source-owned unit runner accepts one fresh report path below the worktree:

```bash
mise exec python@3.13.15 -- python3 plugins/brevitas/tests/run_tests.py \
  .elenchus/brevitas-unittest.json
```

It writes one bounded mode-`0600` `elenchus.unittest.v1` JSON object through a
private temporary file and atomic replacement. It refuses an existing target,
an absolute path outside the worktree, a parent escape, a linked path or a
non-directory parent. A failed or interrupted write leaves no report.

The equivalent Make target is:

```bash
mise exec python@3.13.15 -- make -C plugins/brevitas/skills/brevitas report \
  REPORT=.elenchus/brevitas-unittest.json
```
