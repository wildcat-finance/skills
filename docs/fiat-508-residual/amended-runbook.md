# Issue 508 residual runbook

Assuming the receipted study remains authoritative, use Python 3.14.6 and the selected native macOS executable prototype. Preserve the retired run and existing programme ownership. Each step is one independently audited pull request; its green exit is required before the next entry.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 4a493318b2e68811b9ae9c18b293530b943f31e5795f5319671b23e787d4ce93
candidate | whole-worker-sandbox
```

```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
protasis | plugins/hexaemeron/skills/protasis/EVOLUTION.md | next-generation-after-integration-base
```

Every changed path must have an owner in tests/check-map-v1.json. Regenerate applicable portable copies and Horos artefacts before the checked runner and staged-tree greenlight. Existing licence, toolchain and CI satisfy scaffold needs. Version relations preserve held frontiers and settle against the integration base.

Each resolver is the exact command recorded in .hexaemeron/design-evidence.json for whole-worker-sandbox and the named criterion. Its implementation must execute every specimen before writing a passing report. A missing implementation or report refuses. Frozen reports remain under .hexaemeron/reports/ and are consumed at the stated transition.

## Step 1: Contracts and fixtures

**Goal.** Commit the study, runbook, design record and probe evidence, and define inert fixtures for all three modules.

**Entry.** The receipted study and starting commit 45f2a7e3e14395af218c9373eeecaf263bf766da; no product changes.

**Exit.** Preserved study and design bytes, checked fixture schemas and a resolver that refuses every unimplemented criterion. Keep the existing Python pin, licence and CI. Validate using `python3 scripts/run_checks.py --scope hexaemeron --scope docs`.

**Files.** docs/fiat-508-residual/; plugins/hexaemeron/tests/prove_issue_508.py; plugins/hexaemeron/tests/fixtures/issue508/; tests/check-map-v1.json. Also update declared check ownership and generated copies when their sources change.

**Tests.** Schema fixtures cover malformed requests, carryover manifests and command declarations. No positive report may stand in for an absent executor. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `elenchus.unittest.v1`; report file: `.hexaemeron/reports/step-1-elenchus.json`. Counts are observed when run.

**Disciplines.** phylax: inert inputs remain data. ephoros: each unavailable criterion names its refusal. metron: none, no speed claim. elenchus: preserve the four-draft parser failure as a specimen. hypomnema: record the selected contracts in docs/fiat-508-residual/.

## Step 2: Native supervisor policy lifetime and caps

**Goal.** Implement the macOS worker supervisor and bounded private output capture.

**Entry.** Step 1 exits green with frozen contracts and refusal-only future resolvers.

**Exit.** Native workers have a two-second deadline specimen that refuses within ten seconds and a 1 MiB stream/artifact limit. Timeout and uncertain cleanup admit no mutable output. Run the worker-deadline and worker-output-cap resolvers before step 3, then `python3 scripts/run_checks.py --scope hexaemeron`.

**Files.** plugins/hexaemeron/skills/fiat/scripts/worker_exec.py; plugins/hexaemeron/tests/test_worker_exec.py; plugins/hexaemeron/tests/prove_issue_508.py. Also update declared check ownership and generated copies when their sources change.

**Tests.** Test supported-host preflight, clean environment, closed inherited descriptors, default-deny filesystem/network/IPC policy, descendant lifetime, bounded streams and descriptor-bound no-follow regular-file snapshots. Exercise deadline and output-cap boundaries with real processes. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `elenchus.unittest.v1`; report file: `.hexaemeron/reports/step-2-elenchus.json`. Counts are observed when run.

**Disciplines.** phylax: the OS policy governs every executor descendant and refuses unsupported hosts. ephoros: report policy identity, termination and uncertain cleanup. metron: measure the declared deadline and output cap. elenchus: real denied-write and timeout guards. hypomnema: document controller-owned snapshots and scratch retirement.

## Step 3: Controller launch binding and origin recovery

**Goal.** Bind worker execution to controller evidence while preserving independent origin changes.

**Entry.** Step 2 is green and both step:3 conformance reports pass.

**Exit.** worker-exec binds canonical root, argv, executable identities, policy digest, complete tool inventory, deadline and cap. All enabled shell/Python/patch writes remain confined; external deputies and live metadata are unavailable. Run whole-launch-dispatch and origin-drift-recovery before step 4, then `python3 scripts/run_checks.py --scope hexaemeron`.

**Files.** plugins/hexaemeron/skills/fiat/scripts/hexctl.py; plugins/hexaemeron/skills/fiat/scripts/worker_exec.py; plugins/hexaemeron/tests/test_worker_exec.py; plugins/hexaemeron/tests/prove_issue_508.py; plugins/hexaemeron/agents/mason.md. Also update declared check ownership and generated copies when their sources change.

**Tests.** Exercise shell, Python, patch, symlink, origin writes, live .hexaemeron and shared Git metadata, inherited descriptors, network/IPC deputies, nested policy loosening and setsid descendants. Resolve report destinations absolutely; preserve source declarations. Verify private snapshot stability, refusal on receipt mismatch and preservation/resnapshot of unattributed user drift. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `elenchus.unittest.v1`; report file: `.hexaemeron/reports/step-3-elenchus.json`. Counts are observed when run.

**Disciplines.** phylax: controller signing, metadata and publication stay outside workers. ephoros: retain denied targets and attributed versus independent drift. metron: record launch/copy observations without a speed claim. elenchus: exercise the complete dispatcher. hypomnema: document enabled tools and unsupported deputies.

## Step 4: Cumulative packet binding

**Goal.** Export one complete inert cumulative packet at exhausted audit boundaries.

**Entry.** Step 3 is green and both step:4 conformance reports pass.

**Exit.** A closed bounded manifest includes all passes, finding occurrences, producer evidence and changed-file bytes, deletions and modes. Validate packet specimens using `python3 scripts/run_checks.py --scope hexaemeron`; replacement admission stays unavailable until step 5.

**Files.** plugins/hexaemeron/skills/fiat/scripts/carryover.py; plugins/hexaemeron/skills/fiat/scripts/hexctl.py; plugins/hexaemeron/tests/test_carryover.py; plugins/hexaemeron/tests/fixtures/issue508/. Also update declared check ownership and generated copies when their sources change.

**Tests.** Test the 64 MiB cap, metadata/path/symlink/special-file refusals, complete cumulative payload, raw repeated findings with normalised identities, unknown legacy fields, monotonic issue-CARRYOVER[-N].md numbering, packet digest, attachment URL/identity, archived controller evidence and locally verified signed fixed-tree ref. Never auto-close PRs, delete remote branches or merge. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `elenchus.unittest.v1`; report file: `.hexaemeron/reports/step-4-elenchus.json`. Counts are observed when run.

**Disciplines.** phylax: untrusted payload stays inert before validation. ephoros: name missing lineage and producer evidence. metron: cap packet bytes at 64 MiB. elenchus: omission and duplicate sequence guards. hypomnema: document packet format and custody.

## Step 5: Replacement reconstruction and inoculation

**Goal.** Admit a complete current-base replacement and execute every required inherited guard before fresh audit.

**Entry.** Step 4 exits green with complete export and no premature replacement admission.

**Exit.** Privately reconstruct two exhausted passes from one packet, then require actual non-skipped guard passes and family coverage. Run single-cumulative-reconstruction, executed-inoculation-guards and carryover-lineage-recovery before step 6, then `python3 scripts/run_checks.py --scope hexaemeron`.

**Files.** plugins/hexaemeron/skills/fiat/scripts/carryover.py; plugins/hexaemeron/skills/fiat/scripts/hexctl.py; plugins/hexaemeron/tests/test_carryover.py; plugins/hexaemeron/tests/prove_issue_508.py. Also update declared check ownership and generated copies when their sources change.

**Tests.** Test full reconstruction before any test/lint/acceptance, transformed/conflicted path mappings, missing prior occurrence, stale source and duplicate identity, interrupted admission and retained originals. Discovery-only, skipped, replaced and lifecycle-suppressed guards refuse. Distinguish replacement from checkpoint restore and require a new independent audit after inoculation. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `elenchus.unittest.v1`; report file: `.hexaemeron/reports/step-5-elenchus.json`. Counts are observed when run.

**Disciplines.** phylax: bounded inert validation precedes complete private reconstruction. ephoros: retain recovery phase and missing guard/family identities. metron: enforce the packet/copy caps. elenchus: execute all mapped guards and detect suppressed execution. hypomnema: document recovery without rewriting historical evidence.

## Step 6: Command validation and receipt replay

**Goal.** Validate executable runbook interfaces without executing runbook commands and bind their sources to receipts.

**Entry.** Step 5 is green and all three step:6 conformance reports pass.

**Exit.** Literal argv and finite per-file loops validate through registered checked-in adapters; unsupported evaluation refuses. Run source-owned-report-compatibility, gate-parser-no-execution and gate-receipt-replay before step 7, then `python3 scripts/run_checks.py --scope hexaemeron`.

**Files.** plugins/hexaemeron/skills/protasis/scripts/gate_commands.py; plugins/hexaemeron/skills/protasis/scripts/protasis.py; plugins/hexaemeron/skills/fiat/scripts/hexctl.py; plugins/hexaemeron/tests/test_gate_commands.py; plugins/hexaemeron/tests/prove_issue_508.py. Also update declared check ownership and generated copies when their sources change.

**Tests.** Reject malformed fences, the four-draft Brevitas command, substitutions and injected commands without side effects or arbitrary imports. Accept declared finite per-file loops. Bind command bytes, adapters, CLI source, report substitutions and results; replay refuses any drift. Preserve source-owned Elenchus syntax and report bytes. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `elenchus.unittest.v1`; report file: `.hexaemeron/reports/step-6-elenchus.json`. Counts are observed when run.

**Disciplines.** phylax: parsing cannot invoke arbitrary target code. ephoros: name the command and stale source on refusal. metron: use bounded grammar and input sizes. elenchus: retain the actual arity counterexample. hypomnema: document the registered grammar and adapter extension rules.

## Step 7: Joined demonstration

**Goal.** Demonstrate the complete confined exhausted-audit replacement lifecycle and publish the reviewed contracts.

**Entry.** Step 6 is green and all three step:7 conformance reports pass.

**Exit.** Execute whole-path-demonstration before integration: exhaust, export, retire, reconstruct, inoculate, independently audit and admit integration only with matching launch/gate evidence. Run `python3 scripts/run_checks.py --full` and the exact whole-path resolver. Every named conformance report must exist and pass.

**Files.** plugins/hexaemeron/tests/prove_issue_508.py; plugins/hexaemeron/tests/test_issue508_lifecycle.py; plugins/hexaemeron/skills/fiat/SKILL.md; plugins/hexaemeron/skills/fiat/EVOLUTION.md; plugins/hexaemeron/skills/protasis/SKILL.md; plugins/hexaemeron/skills/protasis/EVOLUTION.md; docs/fiat-508-residual/; generated installation copies and Horos artefacts. Also update declared check ownership and generated copies when their sources change.

**Tests.** Run joined real-process specimens and controller lifecycle fixtures, including missing/mismatched receipts and producer reports. Fixture audit results prove transition handling only; the product step receives its own independent Warden audit. Do not claim production model backend, VM deployment or protection of this conversation tools. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `elenchus.unittest.v1`; report file: `.hexaemeron/reports/step-7-elenchus.json`. Counts are observed when run.

**Disciplines.** phylax: hostile specimens cross each declared authority. ephoros: demonstrate actionable refusal and recovery evidence. metron: retain measured limits without general performance claims. elenchus: complete lifecycle guards supplement independent audit. hypomnema: publish usage, decisions and exact limitations.

### Amendment -- 2026-09-13

**What changed.** Complete replacement Tests: Schema fixtures cover malformed requests, carryover manifests and command declarations. No positive report may stand in for an absent executor. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/reports/step-1-elenchus.json`. Counts are observed when run.

**Why.** Elenchus accepts unittest-json-v1 as its format option; elenchus.unittest.v1 names the emitted JSON schema. The test command and report destination stay unchanged.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-09-13

**What changed.** Complete replacement Tests: Test supported-host preflight, clean environment, closed inherited descriptors, default-deny filesystem/network/IPC policy, descendant lifetime, bounded streams and descriptor-bound no-follow regular-file snapshots. Exercise deadline and output-cap boundaries with real processes. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/reports/step-2-elenchus.json`. Counts are observed when run.

**Why.** Elenchus accepts unittest-json-v1 as its format option; elenchus.unittest.v1 names the emitted JSON schema. The test command and report destination stay unchanged.

**Steps touched.** Step 2.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-09-13

**What changed.** Complete replacement Tests: Exercise shell, Python, patch, symlink, origin writes, live .hexaemeron and shared Git metadata, inherited descriptors, network/IPC deputies, nested policy loosening and setsid descendants. Resolve report destinations absolutely; preserve source declarations. Verify private snapshot stability, refusal on receipt mismatch and preservation/resnapshot of unattributed user drift. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/reports/step-3-elenchus.json`. Counts are observed when run.

**Why.** Elenchus accepts unittest-json-v1 as its format option; elenchus.unittest.v1 names the emitted JSON schema. The test command and report destination stay unchanged.

**Steps touched.** Step 3.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-09-13

**What changed.** Complete replacement Tests: Test the 64 MiB cap, metadata/path/symlink/special-file refusals, complete cumulative payload, raw repeated findings with normalised identities, unknown legacy fields, monotonic issue-CARRYOVER[-N].md numbering, packet digest, attachment URL/identity, archived controller evidence and locally verified signed fixed-tree ref. Never auto-close PRs, delete remote branches or merge. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/reports/step-4-elenchus.json`. Counts are observed when run.

**Why.** Elenchus accepts unittest-json-v1 as its format option; elenchus.unittest.v1 names the emitted JSON schema. The test command and report destination stay unchanged.

**Steps touched.** Step 4.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-09-13

**What changed.** Complete replacement Tests: Test full reconstruction before any test/lint/acceptance, transformed/conflicted path mappings, missing prior occurrence, stale source and duplicate identity, interrupted admission and retained originals. Discovery-only, skipped, replaced and lifecycle-suppressed guards refuse. Distinguish replacement from checkpoint restore and require a new independent audit after inoculation. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/reports/step-5-elenchus.json`. Counts are observed when run.

**Why.** Elenchus accepts unittest-json-v1 as its format option; elenchus.unittest.v1 names the emitted JSON schema. The test command and report destination stay unchanged.

**Steps touched.** Step 5.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-09-13

**What changed.** Complete replacement Tests: Reject malformed fences, the four-draft Brevitas command, substitutions and injected commands without side effects or arbitrary imports. Accept declared finite per-file loops. Bind command bytes, adapters, CLI source, report substitutions and results; replay refuses any drift. Preserve source-owned Elenchus syntax and report bytes. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/reports/step-6-elenchus.json`. Counts are observed when run.

**Why.** Elenchus accepts unittest-json-v1 as its format option; elenchus.unittest.v1 names the emitted JSON schema. The test command and report destination stay unchanged.

**Steps touched.** Step 6.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-09-13

**What changed.** Complete replacement Tests: Run joined real-process specimens and controller lifecycle fixtures, including missing/mismatched receipts and producer reports. Fixture audit results prove transition handling only; the product step receives its own independent Warden audit. Do not claim production model backend, VM deployment or protection of this conversation tools. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/reports/step-7-elenchus.json`. Counts are observed when run.

Complete replacement Files: plugins/hexaemeron/tests/prove_issue_508.py; plugins/hexaemeron/tests/test_confined_replacement_lifecycle.py; plugins/hexaemeron/skills/fiat/SKILL.md; plugins/hexaemeron/skills/fiat/EVOLUTION.md; plugins/hexaemeron/skills/protasis/SKILL.md; plugins/hexaemeron/skills/protasis/EVOLUTION.md; docs/fiat-508-residual/; generated installation copies and Horos artefacts. Also update declared check ownership and generated copies when their sources change.

**Why.** Elenchus accepts unittest-json-v1 as its format option; elenchus.unittest.v1 names the emitted JSON schema. The test command and report destination stay unchanged. The planned lifecycle test filename now describes behavior, as the repository naming check requires.

**Steps touched.** Step 7.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.
