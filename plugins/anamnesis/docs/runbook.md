# Anamnesis prototype runbook

**Target:** `wildcat-finance/skills`
**Entry base:** `1c1137898bce9086c34310bd29b5cf8a889f800c`
**Selected construction:** `anamnesis-member`

This is a proposed Fiat runbook, not an active controller state. Before a run
receipts it, copy [study.md](study.md), this file, and the exact
design-evidence record at `.hexaemeron/design-evidence.json` into the run's
`.hexaemeron/` paths. If the implementation base has changed, return to
Protasis rather than silently carrying this review forward.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 7c16ec848d490bc5d39bf137b50d25795da5e4538ed2864bd8bbaf8876cd2394
candidate | anamnesis-member
```

Three later claims remain deliberately unproved. Step 1 must produce the seed
rights-admission report before Step 2 opens. Step 2 must produce the release
byte report before Step 3 opens. Step 3 must produce the deterministic rebuild
report before integration.

## Step 1: Scaffold Anamnesis and admit the pilot inputs

**Goal.** Add the dependency-closed Anamnesis plugin skeleton, its three promise boundaries, and a checked rights inventory for the pilot sources.

**Entry.** Start from exact commit `1c1137898bce9086c34310bd29b5cf8a889f800c` with the study, runbook, design record, and resolved reports copied byte-for-byte into `.hexaemeron/`; `python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:1` exits zero and consumes `pilot-input-policy-defined`.

**Exit.** The plugin has `AGENTS.md`, `PROMISE_MACHINE.md`, README, licence, host manifests, one canonical `SKILL.md`, Python `3.14.6` entrypoint, check-map ownership, portable runtime copy, four ADRs, committed study and runbook copies, closed source and rights schemas, a 25–50-record pilot manifest, and no product implementation beyond source admission. The exact pending resolver writes `.hexaemeron/reports/anamnesis-member-seed-source-rights-admitted.json`; `python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:2` exits zero before the pull request is ready.

**Files.** Create `plugins/anamnesis/` with `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `AGENTS.md`, `LICENSE`, `PROMISE_MACHINE.md`, `README.md`, `docs/decisions/ADR-001-member-boundary.md` through `ADR-004-consumer-projections.md`, `docs/study.md`, `docs/runbook.md`, `skills/anamnesis/SKILL.md`, `skills/anamnesis/schemas/source-v1.json`, `skills/anamnesis/schemas/rights-v1.json`, `skills/anamnesis/scripts/anamnesis.py`, `specimens/pilot/policy.json`, and `tests/elenchus.py`; update root routing, marketplace manifests, `tests/check-map-v1.json`, Promise Machine coverage, version tests, and generated portable runtime files.

**Tests.** Add `plugins/anamnesis/tests/` cases for closed schemas, unknown keys, duplicate ids, missing rights basis, forbidden disclosure transitions, digest mismatch, symlink and size refusal, no-network default, bounded error output, and the exact rights report object. The audit runner contract is `python3 plugins/anamnesis/tests/elenchus.py --step 1 {report}`, its format is `elenchus-report/v1`, and Warden writes `.hexaemeron/elenchus/anamnesis-step-1.json`. Run the plugin tests, `python3 scripts/portable_promise_machine.py check`, `python3 scripts/run_checks.py --plan`, the Step 2 evidence check, and `git diff --check`; the exact focused test count is set in the step pull request after the scaffold is enumerated.

**Disciplines.** phylax: this step opens local source, rights, filesystem, and future locator boundaries. ephoros: source refusals need durable rule, record, policy, and correlation ids. metron: no runtime budget applies yet, but source and report byte caps are enforced. elenchus: malformed and unauthorised specimens must reproduce a refusal before their guards pass. hypomnema: member ownership, graph, rights, and projection decisions are expensive to reverse and land as ADR-001 through ADR-004.

## Step 2: Build the corpus graph and deterministic seed release

**Goal.** Ingest the admitted pilot sources, curate the lossless finding-to-remedy graph, and emit one checked release below the declared byte cap.

**Entry.** Step 1's pull request is merged into the run branch; its plugin checks and whole selected check plan are green; `.hexaemeron/reports/anamnesis-member-seed-source-rights-admitted.json` exists; and the design checker at `step:2` exits zero.

**Exit.** `anamnesis ingest`, `curate`, `release`, and `verify` produce closed source, engagement, assertion, relation, policy, quarantine, and release manifests from the pilot. The release retains every native id and source digest, keeps unknown distinct from none, preserves duplicate and many-to-many edges, and never lets proposed, applied, released, deployed, reverted, or verified imply another state. The exact resolver measures the release and writes `.hexaemeron/reports/anamnesis-member-seed-release-byte-cap.json`; `python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:3` exits zero.

**Files.** Extend `plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py`; add `schemas/engagement-v1.json`, `schemas/assertion-v1.json`, `schemas/relation-v1.json`, `schemas/policy-v1.json`, `schemas/release-v1.json`, mapper catalogues and versioned policies; add admitted source fixtures, expected entities, relations, evidence, rights, quarantine, policy, and release manifests under `plugins/anamnesis/specimens/pilot/`; extend plugin tests and check-map ownership.

**Tests.** Cover native-source preservation, deterministic ids, duplicate clusters, one-fix-to-many-findings and many-fixes-to-one-finding, rejected and accepted-risk findings, zero-finding rounds, missing legacy fields, unguarded and inconclusive verification, taxonomy drift, source tampering, restricted-output egress, partial-write cleanup, output collision, manifest tampering, and the 50,000,000-byte report. The audit runner contract is `python3 plugins/anamnesis/tests/elenchus.py --step 2 {report}`, its format is `elenchus-report/v1`, and Warden writes `.hexaemeron/elenchus/anamnesis-step-2.json`. Run plugin tests, the full selected root checks, `python3 scripts/portable_promise_machine.py check`, the Step 3 evidence check, and `git diff --check`.

**Disciplines.** phylax: this step parses untrusted heterogeneous records and writes a release, so path, parser, subprocess, egress, and atomic-write controls apply. ephoros: ingestion, quarantine, curation, and release events answer why a record or build refused. metron: measure the exact release bytes with the design-record command and record runtime only as a baseline. elenchus: each parser or release-boundary fix needs its exact bad specimen and old-fails/new-passes guard. hypomnema: schema and policy changes amend the owning ADR or add a versioned decision rather than silently changing released semantics.

## Step 3: Wire the read-only consumers and demonstrate the whole path

**Goal.** Prove the bounded pilot end to end with an Elenchus analogue view, a Synkrisis cohort projection, and a byte-identical rebuild.

**Entry.** Step 2's pull request is merged into the run branch; the seed release and byte report exist; plugin and selected root checks are green; and the design checker at `step:3` exits zero.

**Exit.** The Elenchus adapter returns source-linked analogues without a causal or guarded verdict; the Synkrisis adapter emits only the explicitly admitted audit-corpus observation schema with cohort, denominator, policy, and unknowns intact. The problem-statement demo command builds twice in fresh temporary directories, verifies equal release digests, runs both consumers, records duration and peak resident memory as non-gating baselines, and writes `.hexaemeron/reports/anamnesis-member-deterministic-rebuild.json`. The design checker at `integration`, `python3 scripts/run_checks.py`, `python3 scripts/portable_promise_machine.py check`, all plugin tests, and `git diff --check` exit zero.

**Files.** Add versioned Elenchus and Synkrisis projection schemas and adapters under `plugins/anamnesis/skills/anamnesis/`; add consumer fixtures, expected projections, rebuild and tamper specimens, operator event examples, and demo documentation; update only the consumer contracts and tests required to admit the new producer; regenerate portable runtime and marketplace metadata from canonical sources.

**Tests.** Prove analogue retrieval cannot promote similarity to cause, a guarded result requires the exact Elenchus evidence binding, the Synkrisis projection rejects an undeclared producer or missing cohort field, restricted data cannot cross either adapter, fresh rebuilds are byte-identical, a one-byte input or policy change alters the bound digest, a partial build never verifies, and every risk-register id is covered or explicitly not applicable. The audit runner contract is `python3 plugins/anamnesis/tests/elenchus.py --step 3 {report}`, its format is `elenchus-report/v1`, and Warden writes `.hexaemeron/elenchus/anamnesis-step-3.json`. Run the problem-statement demo from a clean snapshot plus the integration evidence check and the complete selected repository checks.

**Disciplines.** phylax: both adapters and fresh-build subprocesses are new egress and execution boundaries. ephoros: the demonstration must leave closed events that locate refusal, divergence, and adapter identity. metron: record repeatable duration and peak-memory baselines without inventing a threshold. elenchus: deterministic rebuild and adapter-overreach failures need fixed specimens and regression guards. hypomnema: any consumer-contract broadening or schema migration is recorded before the final integration pull request.
