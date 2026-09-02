# Runbook: assign ADR numbers at merge

Derived from the receipted study and selected design `base-owned-gate`.
The run starts from `main` at `ff47f3070c8dce05c767b6c0dad65234c56870de`.
No step rewrites an existing numbered record. The final integration binds one
exact base commit and one ordered assignment report before the run-level merge.

```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
hypomnema | plugins/hexaemeron/skills/hypomnema/EVOLUTION.md | next-generation-after-integration-base
```

```design-lock
schema | protasis-design-evidence/v1
sha256 | cf649ce4f68c42bfc3e46b5d6d050e01232f9013294aa87ec6cca5e6d9a35d54
candidate | base-owned-gate
```

## Step 1: Commit the specification and unnumbered record

**Goal.** Put the accepted study, runbook, and stable unnumbered decision record in durable repository paths without changing executable behaviour.
**Entry.** Clean run branch at `ff47f3070c8dce05c767b6c0dad65234c56870de` with the study and design lock receipted.
**Exit.** Tracked study and runbook equal their receipts; `docs/decisions/drafts/assign-adr-numbers-at-merge-not-at-authoring.md` has a stable slug, a decision H1, no assigned number, and the repository's status and alternatives. Prove it with `cmp .hexaemeron/study.md docs/adr-merge-assignment/study.md`, `cmp .hexaemeron/runbook.md docs/adr-merge-assignment/runbook.md`, `python3 -m unittest tests.test_decision_records -v`, `python3 scripts/run_checks.py`, and `git diff --check`.
**Files.** Create `docs/adr-merge-assignment/study.md`, `docs/adr-merge-assignment/runbook.md`, and `docs/decisions/drafts/assign-adr-numbers-at-merge-not-at-authoring.md`. Regenerate `.horos/boundary.json` only when its owning scan changes it.
**Tests.** No product test is added. The audit-fix runner is `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}` with `elenchus.unittest.v1` output at `.elenchus/fiat-888-recovery-step-1.json`.
**Disciplines.** phylax: none, because this step adds bounded Markdown only. ephoros: none, because no unattended path changes. metron: none, because there is no performance claim. elenchus: none, because no executable failure is repaired. hypomnema: the unnumbered record is the durable home for the policy before assignment.

## Step 2: Add stable references and deterministic allocation

**Goal.** Teach Hypomnema to validate stable `adr/<slug>` identities and to derive a bounded `max(exact base)+1` mapping from immutable Git objects.
**Entry.** Step 1's signed, audited, green head on the branch named by the controller, with the draft still unnumbered.
**Exit.** The allocator accepts prospective slugs, preserves all non-path and non-first-heading bytes, orders at most 32 drafts by ASCII bytes, refuses malformed or hostile paths and replacement Git objects, and emits a closed `fiat-decision-assignments/v1` report with base, product, result tree, blobs, mapping, limits, and replay data. Legacy numbered records remain valid. Prove it with the focused Hypomnema assignment suite, `python3 -m unittest tests.test_decision_records -v`, the Phylax and Hypomnema lints, the Promise Machine and portable checks, the Hexaemeron suite, the root suite, `scripts/run_checks.py`, the Horos check, and `git diff --check`.
**Files.** Change the Hypomnema contract, ledger, checker, portable and package metadata, and the legacy decision-record test. Create `plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py`, its focused fixtures and tests. Update generated copies only through their owning commands, plus the configured audit record and boundary.
**Tests.** Start with parent-red cases for duplicate, dangling, non-ASCII, traversal, oversize, shallow, wrong-type, replacement, report-drift, and rollback inputs. The audit-fix runner is `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report} plugins/hexaemeron/tests/test_hypomnema_decision_assignments.py` with `elenchus.unittest.v1` output at `.elenchus/fiat-888-recovery-step-2.json`.
**Disciplines.** phylax: Git objects, paths, bytes, and configuration are untrusted, so fixed argv and bounded descriptor-safe reads are required. ephoros: the report names exact objects, mapping, limits, and bounded refusal codes. metron: none, because this is correctness work. elenchus: parent-red allocator cases must turn green only through cause-level guards. hypomnema: the stable identity and placement policy live in the owning skill and ADR.

## Step 3: Bind assignment evidence to Fiat composition

**Goal.** Make Fiat replay the assignment report, signed trailers, sync ancestry, and supersession history before a mapping is receipted or integrated.
**Entry.** Step 2's signed, audited, green head with the allocator and report schema fixed.
**Exit.** A read-only verifier checks immutable base, product, candidate, tree, blobs, ordered mapping, exact assignment trailers, signature, and active supersession. Missing, stale, moved, unsigned, duplicate, extra, or dirty evidence refuses before ledger mutation. Prove it with the focused Fiat assignment and integration-path suites, Fiat tests, all bundled lints, the Promise Machine and portable checks, root suite, run checks, Horos, and `git diff --check`.
**Files.** Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, its contract, ledger, push discipline, tests, generated copies, package metadata, and Promise Machine coverage. Create `plugins/hexaemeron/tests/test_fiat_decision_assignments.py`. Permit only the configured audit record, synopsis, and boundary alongside those paths.
**Tests.** Parent-red fixtures cover stale base, altered result tree, mismatched blobs, unordered or extra trailers, missing signature, moved head, dirty worktree, partial receipt, recovery replay, and superseded sync. The audit-fix runner is `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report} plugins/hexaemeron/tests/test_fiat_decision_assignments.py` with `elenchus.unittest.v1` output at `.elenchus/fiat-888-recovery-step-3.json`.
**Disciplines.** phylax: reports, Git objects, signatures, and inherited state are untrusted, so parsing is closed and substitution is disabled. ephoros: receipts name the exact base, product, candidate, mapping, head, and supersession. metron: none, because no performance claim is introduced. elenchus: every malformed evidence form has a parent-red guard. hypomnema: Fiat records transition evidence and does not duplicate the ADR home.

## Step 4: Add the base-owned gate and demonstrate stale-base exclusion

**Goal.** Publish an unprivileged repository workflow and local proof that a same-base losing candidate must recompute before it can land.
**Entry.** Step 3's signed, audited, green head with allocator and controller evidence complete; the live ruleset remains observed rather than changed.
**Exit.** The workflow checks out only the protected base, treats candidate code as data, binds pending and terminal statuses to the exact event head, and refuses incomplete history, moved heads, stale assignments, malformed evidence, and final records without active composition. The local two-candidate demo shows both initially choose the same next number, one lands, the other is stale, and the rebuilt candidate receives the next number. Prove it with the workflow and allocator focused suites, decision-record suite, Hexaemeron suite, root suite, Promise Machine and portable checks, Phylax, Ephoros, Hypomnema, audit-synopsis, Imprimatur, run checks, Horos, and `git diff --check`.
**Files.** Create `.github/workflows/adr-assignments.yml`, `tests/test_adr_assignment_workflow.py`, and `docs/adr-merge-assignment/local-proof.md`; update `tests/check-map-v1.json`, exact workflow assertions, generated metadata, the configured audit synopsis, and `.horos/boundary.json` only through their owning commands. Do not change a live ruleset, status policy, permission, bypass, issue, or merge method.
**Tests.** Cover stale-base mutation, exact-head status lifecycle, base-only checkout, candidate-as-data, hostile hooks/config/scripts, shallow history, moved head, wrong integration id, bounded output, and missing status. The audit-fix runner is `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}` with `elenchus.unittest.v1` output at `.elenchus/fiat-888-recovery-step-4.json`.
**Disciplines.** phylax: event fields and remote Git objects are untrusted, so protected-base checkout and least privilege are mandatory. ephoros: statuses expose head, base, mapping, and qualification without secrets. metron: none, because ceilings are fixed and no speed claim is made. elenchus: the two-candidate stale-base mutation is the causal regression. hypomnema: the local proof points to the standing draft and governed skill rows rather than copying their policy.
