# Brevitas evaluation interface

The evaluation surface runs offline from
`plugins/brevitas/skills/brevitas/`. It does not call a model or infer a model
identity from prose, filenames or Git metadata.

## Legacy cases

Each legacy case directory directly under `evals/cases/` contains `case.json`,
`original.md` and `target.md`. Run all current unit and evaluation cases with:

```bash
mise exec python@3.13.15 -- make -C plugins/brevitas/skills/brevitas test
```

The three legacy cases predate the held cross-model corpus. They remain
regression fixtures but do not count as cross-model coverage.

## Held corpus

The held-corpus manifest is `evals/corpus.json`; qualifying fixtures live below
`evals/cases/fixtures/`, grouped in `held-FAMILY/` directories. The manifest is
a closed, versioned interface. Each case must name one of `x-ray`,
`solidity-auditor`, `gas`, `invariant` or
`diff-review`, its provider and requested model identifier, explicit null
provider-returned backend identifier, capture client version and identity
evidence, source, prompt, request and output digests, pre-lint classification,
expected result and exact protected evidence spans.

All manifest paths are relative to the corpus root. The offline runner rejects
unknown or duplicate fields, escaped, linked, non-regular or oversized files,
invalid UTF-8, digest drift, incomplete family/requested-model coverage,
unclassified cases, forbidden capture metadata and protected spans that are
missing, duplicated or reordered. It also rejects a zero source commit, an
unbound source derivation, a non-null backend identifier, mismatched client
identity evidence and false human-review provenance. It validates held bytes
before invoking Brevitas and never uses a model output as authority.

The v2 corpus holds one reviewed output for each requested capture-client
selection, `openai/gpt-5.6-sol` and `openai/gpt-5.6-terra`, in every family.
`provider_returned_backend_id` is null in every case: the selected model and
matching `codex-cli` banner do not establish provider backend routing. Each
case records its public Apache-2.0 source provenance, redistribution and
sensitivity decision, output-only `codex-cli 0.150.1` capture, named Mason
agent classification before the first current-linter comparison, rule-cited
basis and ordered span inventory. Raw client logs, session metadata,
credentials and hidden reasoning are not corpus fields.

`codex-cli-request-banner-v1` records the exact requested model argument and
matching client banner. Its binding is SHA-256 over newline-terminated compact
JSON with sorted keys: the evidence schema, case id, family, provider,
requested model, null backend id, client, version, mode, requested argument,
acknowledged banner and the actual prompt, source, request and output digests.
The binding detects manifest drift; it does not turn a client banner into a
provider response receipt.

Every source has a closed derivation object. Exact line-range excerpts bind
identical input and output digests. The diff-review fixture instead binds the
3,139-byte `git show --format= --unified=3` result at commit
`2afa9438e7b7c2d61c627c1d4b0cb515fb8a8461`, SHA-256
`65fc5f4b8f73cc296864338b4c4974157585bb90d4da555b344b504d5c3ee1fc`,
to the captured 2,680-byte curated excerpt, SHA-256
`4c4cb2d17c7cc841091a18eff6fb34f2adbec37d79508732265abe98b8dce7af`.
Its ordered steps record the removed context and explanatory comments and the
rewritten excerpt hunk ranges; the capture request and output bytes stay
unchanged.

Validate only the held interface with:

```bash
mise exec python@3.13.15 -- python3 \
  plugins/brevitas/skills/brevitas/scripts/run_evals.py \
  --validate-corpus-only
```

`prompt-source-v1` reconstructs the captured request as the exact `prompt.md`
bytes, one newline and `--- BEGIN SOURCE EXCERPT ---`, the exact `source.md`
bytes, then `--- END SOURCE EXCERPT ---` with its newline. The manifest pins
that request and all three component files by SHA-256. Validation prints only
case ids, families, providers, requested client model identities, the
unestablished backend state, classifications, short prompt, source, request and
output digests, coverage counts and bounded `HC` failure codes; it never prints
prompt or output bytes.

Protected-span kinds are `file-reference`, `numeric-claim`,
`causal-mechanism`, `counterexample-step`, `reproduction-step`, `invariant`
and `establishment-limit`. Their one-based order is part of the contract; each
exact span must occur once in the output and match its own SHA-256 digest.

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
