# framework-74 Step 3 research report

## result

the development proxy frontier contains only `simple`, so `simple` is the
provisional nominee. this is not the final architecture decision. the sealed
behavioural comparison and native cache-lifecycle measurements still decide
behavioural eligibility and the per-runtime token frontier. raw/no-change and
simple are valid winners; the selection rule does not manufacture a complex
nominee merely because it is non-control.

| arm | assembled bytes | maximum complete prompt bytes | exact/native cases | development result |
| --- | ---: | ---: | ---: | --- |
| raw | 2,352,009 | 513,786 | 10/10 | eligible; dominated by simple on the available proxies |
| WAI1 | 2,331,228 | 510,360 | 7/0 | excluded from nomination: three cases lack exact-source recovery |
| Noema | 2,353,045 | 513,933 | 10/0 | eligible but fallback-only on all ten cases |
| simple | 2,070,767 | 485,735 | 10/10 | sole development proxy-frontier member and provisional nominee |
| section graph | 2,373,908 | 542,886 | 10/10 | eligible; dominated by simple on the available proxies |

all five arms refused all 12 hostile mutations without a crash and produced one
digest across two deterministic replays. no supported local tokenizer package
was installed: `tiktoken:cl100k_base` and `tiktoken:o200k_base` are explicitly
unavailable. the table therefore reports complete assembled bytes, not pooled
or guessed token counts. live p50/p95 timings, peak RSS and the resulting
selection record are observations; rebuild does not promise byte-identical
timing or RSS. the committed selection digest binds this observation.
each arm also runs 20 in-memory source-edit probes: one byte replacement and
one length-changing insertion for every development case. the record names the
five touched development artifacts, prompt-component fanout, rebind-attempt
p50/p95 and the exact stale-evidence refusal; it does not repair #1030.

## sealed behavioural comparison

the preregistration freezes 16 answer-producing case slots, two fixed repeat
and presentation-order conditions over the same case-model grid, five arms and
these seven exact model ids:

- `anthropic/claude-opus-5`, `google/gemini-3.7-flash`, and `qwen/qwen3.8-27b`
- `openai/gpt-5.6-sol` and `deepseek/deepseek-v4-pro-0813`
- `moonshotai/kimi-k3` and `z-ai/glm-5.3`

that is 1,120 logical calls before retries. the answer-free packet commits 224
contiguous five-arm pair blocks. one tuple is one atomic batch: both permitted
attempts are reserved before dispatch, success advances the immutable cursor,
and insufficient credit stops before dispatch so resume starts at the same
tuple. pair ids retain all five arms for each repeat condition, model and case.
a partial prefix cannot be reported as the complete matrix or reordered to
cherry-pick evidence.

the representation-blind scorer records a raw-only loss event when raw succeeds
and its paired candidate fails. the empirical gate requires zero such events
over the fixed 224-cell grid. only if execution establishes the frozen
independent stateless-dispatch predicate may zero events use the heterogeneous
Bernoulli AM-GM upper bound `1 - alpha^(1/n)`: 149 eligible cells suffice for
the 2% one-sided 95% gate and 224 are planned. any loss fails that inferential
gate; failed independence is inconclusive. this makes no task-population or net
paired-success generalization. critical-policy tolerance is zero and tuning
after opening is forbidden.

## native cache gate

cache-shaped raw Markdown and simple are mandatory baselines. any nominee and
statistically or operationally near-frontier arm admitted after the behavioural
holdout joins them. response reuse is disabled; the representation and
bootstrap are a stable prefix before five distinct changing task suffixes.
Claude Code `2.1.251` and Codex `0.151.0` are frozen across cold start,
continuous warm use, resume within TTL, resume after expiry and post-compaction.
before admission the schedule is ten runtime-arm chains and 50 observations,
with raw/simple first in each runtime.

the primary result is a two-axis vector kept separate by runtime, model and
tokenizer:

- Claude complete logical input is `input_tokens + cache_creation_input_tokens
  + cache_read_input_tokens`; fresh churn is `input_tokens +
  cache_creation_input_tokens`. after-expiry timing uses the first reported 5m
  or 1h creation class plus 60 seconds and still requires a later native miss.
- Codex complete logical input is `inputTokens`; cache read is
  `cachedInputTokens`; uncached suffix or miss is `inputTokens -
  cachedInputTokens - cacheWriteInputTokens`; fresh churn is cache write plus
  that remainder. when the optional write field is absent, its write/uncached
  split is unknown but total fresh churn remains exactly `inputTokens -
  cachedInputTokens`.

negative or overlapping categories refuse. cached tokens count in full for
logical context and separately as reads. invalidation counts only through later
fresh work. every provider-native usage event in a turn, including compaction,
contributes to the high-water maximum and churn sum; an unexpected answer call
makes the chain inconclusive. behaviour is an eligibility predicate; among
equal-behaviour arms, dominance requires no worse on both axes and strictly
better on one. disagreement retains a Pareto frontier, and the gate may select
none. billing and latency are secondary evidence, never a dollar weight on
tokens.

## deployment preflight

current eligible ZDR endpoint prices, the per-arm UTF-8-byte prompt caps, 768
output tokens, two attempts and the 5.5% fee give a conservative full-matrix
gross bound of `$4,435.75397516800`, below the `$4,500.00` authority ceiling.
the first frozen tuple is `qwen/qwen3.8-27b` and its two-attempt reservation is
`$0.38103308400`. the official credit endpoint proved 230 total
credits, 172.881550533 total usage and 57.118449467 available, enough for that
next atomic reservation. a null `/api/v1/key` limit is not treated as balance
proof. Step 4 must repeat the credit and price check before every tuple.

all three evaluator candidates passed spend, seven-model ZDR and isolated
native-auth preflights. these were bounded metadata GETs and no-session local
runtime probes only: zero paid or answer-producing calls. the reports store the
exact sanitized command; publish-once companion records retain facts and their
content digests. resolved native identities retain executable basename,
version and binary digest, never a host-absolute path or credential material.

Step 4 is not admitted by those files merely existing. The immutable Step 2
design record remains byte-identical. The tracked 3-candidate by 3-criterion
contract at `.fiat/conformance-overlay-contract.json` binds that base, the nine
current commands and all report/evidence paths. `build-conformance-overlay`
closes their hashes and pass facts into one publish-once ignored overlay;
Step 3's controller push receipts and replays it before opening Step 4. Every
holdout, provider and native-gate entrypoint then revalidates the receipt before
argument parsing or any credential, network or answer-session access.

## boundary and records

the holdout remains `opened: false`; Step 3 read no task, expected answer,
scorer key, model output or holdout source content. it made no production-path
change. the development evidence is committed by inventory SHA-256
`131cb09fd5af7b52a75bc4ee77a4025190b0f2bf928deaf62c73fd951d1630d8`;
the selection record's self-digest is
`a2ba7dc1cd2c4eb4c5c1fb2709053cc75a28d1976fa623660f8a0e07ea72cccd`.
the behavioural commitment-file SHA-256 is
`c27c8b2fb7adbd4acb59abe958154aa96b08be79417b67b3c63143632c645e74`;
the native commitment-file SHA-256 is
`e11a5cfe4917df785f0e558e35ca8da75c84c8a28786ddc1c9f970e2c308daa3`.

tracked fixtures own reproducible selection, preregistration, accounting,
runtime manifests and answer-free packet commitments. ignored
`.hexaemeron/model-evaluation-authority.json` and design reports own live credit,
price, authentication and executable observations so host/account facts do not
enter the portable research artifacts.
