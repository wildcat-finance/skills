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

### Amendment -- 2026-09-13

**What changed.** Complete replacement Files: plugins/hexaemeron/skills/fiat/scripts/worker_exec.py; plugins/hexaemeron/tests/test_worker_exec.py; plugins/hexaemeron/tests/prove_issue_508.py; plugins/hexaemeron/tests/test_delivery_contract_fixtures.py; plugins/hexaemeron/skills/fiat/SKILL.md; plugins/hexaemeron/skills/fiat/EVOLUTION.md; docs/fiat-508-residual/README.md; docs/fiat-508-residual/amended-runbook.md. In plugins/hexaemeron/skills/fiat/scripts/hexctl.py, add only the current relation-resolved Fiat version to CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS. Also update declared check ownership and generated copies when their sources change.

**Why.** Step 2's standalone worker changes advance Fiat to the generation declared by its version relation. The checkpoint restore tests refuse that version because the finite compatibility set still ends at the anchor version. This step has changed no controller state shape, receipt schema, configuration shape or checkpoint serialization. Adding the current version preserves the identity checks and refusal of unsupported versions. The other named paths record the implemented scope, maintain the existing resolver fixtures and preserve this amendment.

**Steps touched.** Step 2.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-09-14

**What changed.** Complete replacement Files: plugins/hexaemeron/skills/fiat/scripts/hexctl.py; plugins/hexaemeron/skills/fiat/scripts/worker_exec.py; plugins/hexaemeron/tests/test_worker_exec.py; plugins/hexaemeron/tests/prove_issue_508.py; plugins/hexaemeron/agents/mason.md; plugins/hexaemeron/skills/fiat/EVOLUTION.md; docs/fiat-508-residual/README.md; docs/fiat-508-residual/amended-runbook.md. In EVOLUTION.md, update only the current relation-resolved Fiat row to describe the delivered controller admission. In the README, update the current admission status while preserving historical observations and limits. Preserve this amendment in the byte-identical committed runbook copy. Also update declared check ownership and generated copies when their sources change.

**Why.** Step 3 implements controller launch and admission, while the current Fiat row and README still say admission is pending. Those statements would misdescribe the implemented step. This correction permits their status refresh and the committed amendment copy, within the same version relation and held frontier.

**Steps touched.** Step 3.

**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.

### Amendment -- 2026-09-14

**What changed.** Complete replacement Files: plugins/hexaemeron/skills/fiat/scripts/carryover.py; plugins/hexaemeron/skills/fiat/scripts/hexctl.py; plugins/hexaemeron/tests/test_carryover.py; plugins/hexaemeron/tests/fixtures/issue508/; plugins/hexaemeron/skills/fiat/SKILL.md; plugins/hexaemeron/skills/fiat/references/carryover-packet.md; plugins/hexaemeron/skills/fiat/EVOLUTION.md; docs/fiat-508-residual/README.md; docs/fiat-508-residual/amended-runbook.md. In SKILL.md and references/carryover-packet.md, change only the cumulative export and validation format and custody documentation; replacement admission remains unavailable until Step 5. In EVOLUTION.md, update only the current relation-resolved Fiat row. In the README, update only the current Step 4 status and amendment count while preserving historical observations and limits. Preserve the exact canonical amended-runbook copy. Also update declared check ownership and generated copies when their sources change. Goal, Entry, Exit, Tests and Disciplines remain unchanged, as do the original study and design topology.

**Why.** Step 4's new packet and export interface needs canonical format and custody documentation, current delivery status and an exact amendment copy. The added documentation stays within the same version relation and held frontier.

**Steps touched.** Step 4.

**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.
### Amendment -- 2026-09-14

**What changed.** Complete replacement Files: plugins/hexaemeron/skills/fiat/scripts/carryover.py; plugins/hexaemeron/skills/fiat/scripts/hexctl.py; plugins/hexaemeron/tests/test_carryover.py; plugins/hexaemeron/tests/fixtures/issue508/; plugins/hexaemeron/skills/fiat/SKILL.md; plugins/hexaemeron/skills/fiat/references/carryover-packet.md; plugins/hexaemeron/skills/fiat/EVOLUTION.md; docs/fiat-508-residual/README.md; docs/fiat-508-residual/amended-runbook.md; tests/promise_machine_coverage.json; tests/fixtures/promise-machine/runtime/fiat-cumulative-carryover-custody.json. In SKILL.md and references/carryover-packet.md, change only the cumulative export and validation format and custody documentation; replacement admission remains unavailable until Step 5. In EVOLUTION.md, update only the current relation-resolved Fiat row. In the README, update only the current Step 4 status and amendment count while preserving historical observations and limits. Preserve the exact canonical amended-runbook copy. In tests/promise_machine_coverage.json, add only the new custody promise's P/R/M/O/S coverage cases and native reader declaration. In tests/fixtures/promise-machine/runtime/fiat-cumulative-carryover-custody.json, retain truthful structural reader specimens with operation_ran:false and the domain-operation-not-run unknown. Actual behavior tests remain in the already authorized test_carryover.py. Also update declared check ownership and generated copies when their sources change. Goal, Entry, Exit, Tests and Disciplines remain unchanged, as do the original study and design topology.

**Why.** The new cumulative custody operation needs authored Promise Machine coverage and structural reader specimens. These specimens record that the domain operation did not run; the existing implementation tests own behavioral evidence. The added paths stay within the same version relation and held frontier.

**Steps touched.** Step 4.

**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.
### Amendment -- 2026-09-14

**What changed.** Complete replacement Files: plugins/hexaemeron/skills/fiat/scripts/carryover.py; plugins/hexaemeron/skills/fiat/scripts/hexctl.py; plugins/hexaemeron/tests/test_carryover.py; plugins/hexaemeron/tests/fixtures/issue508/; plugins/hexaemeron/skills/fiat/SKILL.md; plugins/hexaemeron/skills/fiat/references/carryover-packet.md; plugins/hexaemeron/skills/fiat/EVOLUTION.md; docs/fiat-508-residual/README.md; docs/fiat-508-residual/amended-runbook.md; tests/promise_machine_coverage.json; tests/fixtures/promise-machine/runtime/fiat-cumulative-carryover-custody.json; tests/promise_machine_id_history.json; tests/test_promise_machine_contract.py; docs/promise-machine/obligation-gates/demonstration-run.json; docs/promise-machine/obligation-gates/demonstration-evidence.md. In SKILL.md and references/carryover-packet.md, change only the cumulative export and validation format and custody documentation; replacement admission remains unavailable until Step 5. In EVOLUTION.md, update only the current relation-resolved Fiat row. In the README, update only the current Step 4 status and amendment count while preserving historical observations and limits. Preserve the exact canonical amended-runbook copy. In tests/promise_machine_coverage.json, add only the new custody promise's P/R/M/O/S coverage cases and native reader declaration. In tests/fixtures/promise-machine/runtime/fiat-cumulative-carryover-custody.json, retain truthful structural reader specimens with operation_ran:false and the domain-operation-not-run unknown. Actual behavior tests remain in the already authorized test_carryover.py. In tests/promise_machine_id_history.json, add only the new custody promise's current and history row. In tests/test_promise_machine_contract.py, update only the active-history and runtime-count assertions from 98/47 to 99/48; preserve the historical entry_count of 80. In docs/promise-machine/obligation-gates/demonstration-run.json and docs/promise-machine/obligation-gates/demonstration-evidence.md, update only the recomputed current promise/history/runtime counts of 99/48 and current input descriptors and digests. Preserve every historical command, status, date, model, outcome and the historical entry_count of 80. Also update declared check ownership and generated copies when their sources change. Goal, Entry, Exit, Tests and Disciplines remain unchanged, as do the original study and design topology.

**Why.** The new custody promise also needs its authored identity history, matching active-history and runtime-count assertions, and current demonstration counts and input bindings. These paths keep the current coverage records consistent while preserving historical evidence, the same version relation and held frontier.

**Steps touched.** Step 4.

**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.
### Amendment -- 2026-09-14

**What changed.** Complete replacement Files: plugins/hexaemeron/skills/fiat/scripts/carryover.py; plugins/hexaemeron/skills/fiat/scripts/hexctl.py; plugins/hexaemeron/tests/test_carryover.py; plugins/hexaemeron/tests/fixtures/issue508/; plugins/hexaemeron/skills/fiat/SKILL.md; plugins/hexaemeron/skills/fiat/references/carryover-packet.md; plugins/hexaemeron/skills/fiat/EVOLUTION.md; docs/fiat-508-residual/README.md; docs/fiat-508-residual/amended-runbook.md; tests/promise_machine_coverage.json; tests/fixtures/promise-machine/runtime/fiat-cumulative-carryover-custody.json; tests/promise_machine_id_history.json; tests/test_promise_machine_contract.py; docs/promise-machine/obligation-gates/demonstration-run.json; docs/promise-machine/obligation-gates/demonstration-evidence.md. In SKILL.md and references/carryover-packet.md, change only the cumulative export and validation format and custody documentation; replacement admission remains unavailable until Step 5. In EVOLUTION.md, update only the current relation-resolved Fiat row. In the README, update only the current Step 4 status and amendment count while preserving historical observations and limits. Preserve the exact canonical amended-runbook copy. In tests/promise_machine_coverage.json, add only the new custody promise's P/R/M/O/S coverage cases and native reader declaration. In tests/fixtures/promise-machine/runtime/fiat-cumulative-carryover-custody.json, retain truthful structural reader specimens with operation_ran:false and the domain-operation-not-run unknown. Actual behavior tests remain in the already authorized test_carryover.py. In tests/promise_machine_id_history.json, add only the new custody promise's current and history row. In tests/test_promise_machine_contract.py, update only the active-history and runtime-count assertions from 98/47 to 99/48, and add fiat-cumulative-carryover-custody to the expected Fiat set in test_hexaemeron_contract_population_is_complete; preserve the historical entry_count of 80 and the exact population equality assertion. In docs/promise-machine/obligation-gates/demonstration-run.json and docs/promise-machine/obligation-gates/demonstration-evidence.md, update only the recomputed current promise/history/runtime counts of 99/48 and current input descriptors and digests. Preserve every historical command, status, date, model, outcome and the historical entry_count of 80. Also update declared check ownership and generated copies when their sources change. Goal, Entry, Exit, Tests and Disciplines remain unchanged, as do the original study and design topology.

**Why.** The normal root gate failed because the explicit expected Fiat population omitted the new custody promise. The focused reproduction confirms that omission. This amendment permits adding that one member while retaining the exact population check, existing cardinality updates and historical count.

**Steps touched.** Step 4.

**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.
### Amendment -- 2026-09-14

**What changed.** Complete replacement Files: plugins/hexaemeron/skills/fiat/scripts/carryover.py; plugins/hexaemeron/skills/fiat/scripts/hexctl.py; plugins/hexaemeron/tests/test_carryover.py; plugins/hexaemeron/tests/prove_issue_508.py; plugins/hexaemeron/skills/fiat/scripts/replacement.py; plugins/hexaemeron/skills/fiat/scripts/inoculation.py; plugins/hexaemeron/skills/fiat/scripts/worker_exec.py; plugins/hexaemeron/tests/test_worker_exec.py; plugins/hexaemeron/skills/fiat/SKILL.md; plugins/hexaemeron/skills/fiat/references/carryover-packet.md; plugins/hexaemeron/skills/fiat/EVOLUTION.md; docs/fiat-508-residual/README.md; docs/fiat-508-residual/amended-runbook.md; tests/promise_machine_coverage.json; tests/promise_machine_id_history.json; tests/test_promise_machine_contract.py; tests/fixtures/promise-machine/runtime/fiat-replacement-admission.json; tests/fixtures/promise-machine/runtime/fiat-cumulative-carryover-custody.json; docs/promise-machine/obligation-gates/demonstration-run.json; docs/promise-machine/obligation-gates/demonstration-evidence.md. In replacement.py, implement reconstruction, admission and replay; in inoculation.py, add the fixed guard adapter; in worker_exec.py and test_worker_exec.py, add and test only the bounded internal copy of read-only input. In SKILL.md and references/carryover-packet.md, document the Step 5 replacement interface and its boundaries. Keep replacement admission separate from cumulative custody, and preserve historical custody receipts that recorded admission as unavailable. In EVOLUTION.md, update only the current Fiat 5.56.1 row. In the README, update only current Step 5 status, conformance resolvers and the amendment count of fourteen while preserving every historical observation and limit. After admission, preserve the exact canonical amended-runbook copy. If the distinct fiat-replacement-admission promise lands, update its P/R/M/O/S coverage cases, native reader declaration, current identity and history row, exact expected Fiat population member in test_hexaemeron_contract_population_is_complete, and current counts together: active, coverage and history from 99 to 100, and runtime from 48 to 49. Keep the equality assertions exact and preserve the historical entry_count of 80. The new fiat-replacement-admission.json reader specimens must state truthfully whether the domain operation ran; structural specimens retain operation_ran:false and the domain-operation-not-run unknown. Refresh only the current source binding in fiat-cumulative-carryover-custody.json. In demonstration-run.json and demonstration-evidence.md, update only the recomputed current counts, input descriptors and digests. Preserve every historical command, status, date, model, prompt, answer and outcome; no historical execution or result is rerun or rewritten by this amendment. Also update source-owned generated copies and digests and declared check ownership when their sources change. Goal, Entry, Exit, Tests and Disciplines remain unchanged, including the effective unittest-json-v1 Tests correction, as do the original study, selected design, version relations and held frontier.

**Why.** Step 5's existing reconstruction and executed-guard goal needs separate reconstruction and guard-adapter modules plus a bounded worker input copy. The same interface needs canonical instructions, current status and consistent Promise Machine coverage, history and consumer bindings. These paths implement the selected design without changing its admission criteria or adding a new design. Steps 1 through 4 are completed. The added paths serve the existing Step 5 contract; they do not change the completed steps or any pending entry or exit. Unbuilt exits remain requirements, not claims that their checks have run.

**Steps touched.** Step 5.

**Still holding.** Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.
### Amendment -- 2026-09-14

**What changed.** Complete replacement Files: plugins/hexaemeron/skills/fiat/scripts/carryover.py; plugins/hexaemeron/skills/fiat/scripts/hexctl.py; plugins/hexaemeron/tests/test_carryover.py; plugins/hexaemeron/tests/prove_issue_508.py; plugins/hexaemeron/skills/fiat/scripts/replacement.py; plugins/hexaemeron/skills/fiat/scripts/inoculation.py; plugins/hexaemeron/skills/fiat/scripts/worker_exec.py; plugins/hexaemeron/tests/test_worker_exec.py; plugins/hexaemeron/tests/test_filing_decision_provenance.py; plugins/hexaemeron/skills/fiat/SKILL.md; plugins/hexaemeron/skills/fiat/references/carryover-packet.md; plugins/hexaemeron/skills/fiat/EVOLUTION.md; docs/fiat-508-residual/README.md; docs/fiat-508-residual/amended-runbook.md; tests/promise_machine_coverage.json; tests/promise_machine_id_history.json; tests/test_promise_machine_contract.py; tests/fixtures/promise-machine/runtime/fiat-replacement-admission.json; tests/fixtures/promise-machine/runtime/fiat-cumulative-carryover-custody.json; docs/promise-machine/obligation-gates/demonstration-run.json; docs/promise-machine/obligation-gates/demonstration-evidence.md. In replacement.py, implement reconstruction, admission and replay; in inoculation.py, add the fixed guard adapter; in worker_exec.py and test_worker_exec.py, add and test only the bounded internal copy of read-only input. In SKILL.md and references/carryover-packet.md, document the Step 5 replacement interface and its boundaries. Keep replacement admission separate from cumulative custody, and preserve historical custody receipts that recorded admission as unavailable. In EVOLUTION.md, update only the current Fiat 5.56.1 row. In the README, update only current Step 5 status, conformance resolvers and the amendment count of fifteen while preserving every historical observation and limit. After admission, preserve the exact canonical amended-runbook copy. If the distinct fiat-replacement-admission promise lands, update its P/R/M/O/S coverage cases, native reader declaration, current identity and history row, exact expected Fiat population member in test_hexaemeron_contract_population_is_complete, and current counts together: active, coverage and history from 99 to 100, and runtime from 48 to 49. Keep the equality assertions exact and preserve the historical entry_count of 80. The new fiat-replacement-admission.json reader specimens must state truthfully whether the domain operation ran; structural specimens retain operation_ran:false and the domain-operation-not-run unknown. Refresh only the current source binding in fiat-cumulative-carryover-custody.json. In demonstration-run.json and demonstration-evidence.md, update only the recomputed current counts, input descriptors and digests. Preserve every historical command, status, date, model, prompt, answer and outcome; no historical execution or result is rerun or rewritten by this amendment. Also update source-owned generated copies and digests and declared check ownership when their sources change. In test_filing_decision_provenance.py, change only the verify_run and load_state test doubles in VerifyFlagCompositionTests.test_the_observations_flag_does_not_swallow_the_filing_check to keyword-only stubs that assert allow_pending_replacement is True, record observation and filing events, and assert the ordered events ["observations", "filing"]. Preserve both CLI flags and the try/finally restoration; do not relax or remove the existing comparison assertions. Goal, Entry, Exit, Tests and Disciplines remain unchanged, including the effective unittest-json-v1 Tests correction, as do the original study, selected design, version relations and held frontier.

**Why.** The completed 12-worker suite ran 2,766 tests with zero failures, one error and zero skips. The existing combined-flag test double rejects the allow_pending_replacement keyword introduced for pending replacement inspection. This narrow repair keeps that comparison test compatible while checking the keyword and both ordered effects. Steps 1 through 4 remain completed. The selected design and all Step 5 requirements remain unchanged; the failed run stays preserved and Step 5 is incomplete. Unbuilt exits remain requirements, not claims that current checks passed.

**Steps touched.** Step 5.

**Still holding.** Step 5: entry holds; exit holds. Step 6: entry holds; exit holds. Step 7: entry holds; exit holds.
