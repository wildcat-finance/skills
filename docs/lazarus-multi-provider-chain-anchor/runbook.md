# Runbook: structured multi-provider chain anchors

This runbook derives from the receipted study at SHA-256
`f16d14e2182f872d95e56b4485218a264286a845f80b2857960dcd32c14442fd`.
Run every Python command in an environment populated from
`plugins/lazarus/requirements.lock`; the run-local CPython 3.12 baseline passed
all 364 existing Lazarus tests after that lock was installed. Each step keeps
plan-v1, manifest-v1, release-v1, the Goldfinch fixture bytes, the writer
`tool_version`, and the held `receipt-inclusion-proofs` frontier unchanged.

## Step 1: Define the anchor formats

**Goal.** Add the versioned plan and anchor-record contracts, their canonical helpers, the tracked specification copies, and the structured unittest runner required by later audit rounds.

**Entry.** Run branch `fiat/386-record-a-structured-multi-provider-chain-anc` at `0f835d5f5f7c95ad2716eb63bd9bdd8f68b0a841`, with the study receipt above and the 364-test locked-environment baseline green.

**Exit.** `plan-v2` copies the complete plan-v1 contract and requires one sorted, unique array of 1 to 32 objects containing only a `source_id` matching `^[a-z][a-z0-9_.-]{0,127}$`; plan-v1 still declares no anchors. `anchor-record-v1` admits only `schema_version`, `source_id`, `observed_at`, the exact `eth_getBlockByNumber` method and parameters, and the returned mainnet chain ID, block number, and block hash. The schema registry digest-pins both formats, semantic validation refuses non-UTC timestamps and plan ordering or uniqueness drift, canonical JSONL helpers sort and de-duplicate records by source ID, and `validate` accepts the new record kind. Exact study and runbook copies live under `docs/lazarus-multi-provider-chain-anchor/`. A repository-owned unittest runner emits one fresh `elenchus.unittest.v1` file without following links or accepting a path outside its worktree. Prove the exit with `python3 plugins/lazarus/scripts/lazarus.py validate schemas`, `python3 -m unittest plugins.lazarus.tests.test_schemas plugins.lazarus.tests.test_records plugins.lazarus.tests.test_scaffold plugins.lazarus.tests.test_runner -v`, `python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus -v`, `python3 -m unittest discover -s tests -v`, `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/lazarus-multi-provider-chain-anchor/study.md`, and `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/lazarus-multi-provider-chain-anchor/runbook.md`.

**Files.** Create `docs/lazarus-multi-provider-chain-anchor/{study.md,runbook.md}`, `plugins/lazarus/schemas/{plan-v2.json,anchor-record-v1.json}`, `plugins/lazarus/tests/{run_tests.py,test_runner.py}`; change `plugins/lazarus/scripts/lazarus.py`, `plugins/lazarus/scripts/lazarus_lib/{schemas.py,records.py}`, and `plugins/lazarus/tests/{support.py,test_schemas.py,test_records.py,test_scaffold.py}`.

**Tests.** Add positive, malformed, unknown-version, digest-substitution, source-ID grammar, 1/32/33-source, sorted/duplicate-plan, timestamp, method/parameter, returned-field, canonical-byte, sorted-record, duplicate-record, and runner path/report cases. The step audit runner contract is test command `python3 plugins/lazarus/tests/run_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `tmp/elenchus/lazarus-step-1.json`. Record the new full-suite count at implementation time; all 364 baseline cases must remain green.

**Disciplines.** phylax: schemas and the report path accept untrusted data, so closed fields, caps, no-follow traversal, fresh-file creation, and stable value-free refusals apply. ephoros: the runner's complete counters and stable schema/version errors answer whether a check actually ran; no metrics backend is added. metron: none, there is no performance claim. elenchus: the report emitter is the guard transport for every later fix, and its hostile path cases must fail before its safe case passes. hypomnema: the two public byte formats and runtime syntax are expensive to reverse; the committed study is their rationale and the schemas are their authority.

## Step 2: Verify anchor records offline

**Goal.** Extend manifest and whole-fixture verification so a declared anchor component is digest-bound, exactly covered, separately counted, and never promoted into a proof or canonical-chain claim.

**Entry.** The controller-receipted Step 1 commit with both new formats registered, canonical helpers green, and the full Lazarus and root Python suites passing.

**Exit.** Manifest-v1 accepts `anchors.jsonl` as a recognised optional component without changing its schema or three `evidence_counts`; plan-v2 requires that component and plan-v1 refuses it. Whole-fixture verification performs one digest-bound read, requires exact plan-to-record source coverage, rejects missing, extra, duplicate, malformed, wrong-chain, wrong-height, or header-disagreeing records, and returns `chain_anchors: {records: N, canonical_chain_claim: false, provider_independence_claim: false}`. CLI verification prints `chain-anchor-records: N`. Release-v1 and Ariadne-facing binding remain structurally unchanged while accepting the fixture digest and component inventory of an anchored fixture. Prove the exit with `python3 -m unittest plugins.lazarus.tests.test_manifest plugins.lazarus.tests.test_verifier plugins.lazarus.tests.test_binding plugins.lazarus.tests.test_release -v`, `python3 plugins/lazarus/scripts/lazarus.py verify plugins/lazarus/examples/goldfinch-v0`, `python3 plugins/lazarus/examples/preservation-release-demo.py`, `python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus -v`, and `python3 -m unittest discover -s tests -v`.

**Files.** Change `plugins/lazarus/scripts/lazarus.py`, `plugins/lazarus/scripts/lazarus_lib/{manifest.py,verifier.py}`, and `plugins/lazarus/tests/{support.py,test_manifest.py,test_verifier.py,test_binding.py,test_release.py,test_preservation_release.py}`.

**Tests.** Build plan-v1 and plan-v2 fixtures from local test material; cover zero and 1/32 records, component presence parity, exact source coverage, duplicate and reordered records, every returned identity disagreement, post-manifest mutation, recomputed count, both false claim booleans, unchanged evidence counts, CLI output, release round trip, and the unchanged Goldfinch digest. The step audit runner contract is test command `python3 plugins/lazarus/tests/run_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `tmp/elenchus/lazarus-step-2.json`. Record the new full-suite count; no test may depend on a live RPC.

**Disciplines.** phylax: manifest paths and provider-authored anchor bytes cross the filesystem and parser boundaries, so bounded no-follow reads, schema validation, digest binding, and one coherent report apply. ephoros: `chain-anchor-records`, the two false booleans, and source-specific stable refusals answer coverage and epistemic-boundary questions. metron: none, component limits are safety budgets and no speed claim is made. elenchus: every false claim, coverage drift, and one-read mutation begins as a failing test and closes only at the verifier cause. hypomnema: the separate count and refusal to alter release evidence classes implement the study's recorded decision; no second decision home is added.

## Step 3: Capture and demonstrate anchors

**Goal.** Wire declared runtime providers into atomic capture, document the operator contract, and ship a reproducible anchored-fixture demonstration under Lazarus generation `v1.2.0`.

**Entry.** The controller-receipted Step 2 commit whose offline verifier accepts only exact, digest-bound anchor coverage and whose legacy fixture and release demonstrations are green.

**Exit.** `capture` accepts repeated `--anchor-rpc-env SOURCE_ID=ENV_VAR`, requires its identifier set to equal the plan, reads only explicitly named non-empty environment variables, and never puts their values in argv, output, diagnostics, or fixture bytes. One client per source shares the existing request, response-byte, component-byte, total-byte, and elapsed-time limits; each calls `eth_chainId` and `eth_getBlockByNumber` for the fixed block. Capture writes source-sorted records with an injected UTC wall clock, scans the union of primary and anchor secrets, and leaves no output or stage on any mapping, transport, chain, height, hash, schema, limit, secret, or final verification failure. A checked-in synthetic fixture demonstrates two matching recorded observations while retaining both false claims; `python3 plugins/lazarus/scripts/lazarus.py verify plugins/lazarus/examples/multi-provider-anchor-v0` prints `chain-anchor-records: 2`. README, runtime contract, canonical skill, and chain-anchor guide state the mapping, evidence boundary, limits, refusals, and non-claims. The skill and ledger advance once to generation `lazarus-v1.2.0`, retaining the prior frontier revision, digest, status, current text, and held job byte for byte. Prove the exit with `python3 -m unittest plugins.lazarus.tests.test_capture plugins.lazarus.tests.test_limits plugins.lazarus.tests.test_scrub plugins.lazarus.tests.test_goldfinch plugins.lazarus.tests.test_scaffold -v`, `python3 plugins/lazarus/scripts/lazarus.py verify plugins/lazarus/examples/multi-provider-anchor-v0`, `python3 plugins/lazarus/scripts/lazarus.py verify plugins/lazarus/examples/goldfinch-v0`, `python3 plugins/lazarus/examples/preservation-release-demo.py`, `python3 -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus -v`, and `python3 -m unittest discover -s tests -v`.

**Files.** Create `plugins/lazarus/docs/chain-anchors.md` and `plugins/lazarus/examples/multi-provider-anchor-v0/`; change `plugins/lazarus/{AGENTS.md,README.md}`, `plugins/lazarus/scripts/lazarus.py`, `plugins/lazarus/scripts/lazarus_lib/{capture.py,scrub.py}`, `plugins/lazarus/tests/{fake_rpc.py,support.py,test_capture.py,test_limits.py,test_scrub.py,test_goldfinch.py,test_scaffold.py}`, and `plugins/lazarus/skills/lazarus/{SKILL.md,EVOLUTION.md}`.

**Tests.** Add CLI and direct-capture cases for exact/missing/extra/duplicate mappings, absent and empty environment variables, argument/output/error secrecy, deterministic source order under reversed CLI order, fixed injected timestamps, shared request/byte/time exhaustion, provider redirects and sanitised errors, wrong chain/height/hash, disagreement after partial success, final secret scan, interrupted finalisation, and no destination or stage after every refusal. The step audit runner contract is test command `python3 plugins/lazarus/tests/run_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `tmp/elenchus/lazarus-step-3.json`. Record the final full-suite count and exact anchored and Goldfinch fixture digests.

**Disciplines.** phylax: environment names, URL values, provider responses, errors, limits, staging, and finalisation are the live trust boundaries, with exact mapping, existing transport controls, union secret scanning, and atomic cleanup. ephoros: capture and verify expose declared/verified counts plus a non-secret source ID and bounded stage on refusal; the example preserves the two false claim booleans. metron: none, provider caps are safety bounds and no latency gain is claimed. elenchus: every new refusal is observed red against the unfixed parent before its cause-level guard is accepted, then the full suites and demonstrations rerun. hypomnema: `docs/chain-anchors.md`, the versioned schemas, the committed study, and one generation ledger row are the durable homes; release and Ariadne contracts stay untouched.

### Amendment -- 2026-08-25

**What changed.** Complete replacement Files: Create `docs/lazarus-multi-provider-chain-anchor/{study.md,runbook.md}`, `plugins/lazarus/schemas/{plan-v2.json,anchor-record-v1.json}`, `plugins/lazarus/tests/{run_tests.py,test_runner.py}`; change `plugins/lazarus/scripts/lazarus.py`, `plugins/lazarus/scripts/lazarus_lib/{schemas.py,records.py}`, `plugins/lazarus/tests/{support.py,test_schemas.py,test_records.py,test_scaffold.py}`, and `tests/promise_machine_coverage.json`.

**Why.** The exact root suite returned three PM071 failures because changing `plugins/lazarus/scripts/lazarus.py` changes the source digest recorded for Lazarus's three covered runtime promises. Root verification cannot be green until the coverage record names the implemented bytes.

**Steps touched.** Step 1's Files field.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-08-25

**What changed.** Complete replacement Files: Create `docs/lazarus-multi-provider-chain-anchor/{study.md,runbook.md}`, `plugins/lazarus/schemas/{plan-v2.json,anchor-record-v1.json}`, `plugins/lazarus/tests/{run_tests.py,test_runner.py}`; change `plugins/lazarus/scripts/lazarus.py`, `plugins/lazarus/scripts/lazarus_lib/{capture.py,schemas.py,records.py}`, `plugins/lazarus/tests/{support.py,test_capture.py,test_schemas.py,test_records.py,test_scaffold.py}`, and `tests/promise_machine_coverage.json`.

**Why.** Once plan-v2 is registered, the pre-anchor `capture_fixture()` path would otherwise accept its valid `anchor_sources` field and silently produce a fixture with no anchors. Step 1 must refuse that unsupported capture version until Step 3 replaces the refusal with complete anchor capture.

**Steps touched.** Step 1's Files field.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.
