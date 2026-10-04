# Issue 1363 runbook: two pinned Wildcat V2 action maps

This runbook derives from study SHA-256 `a2843ed9cf1dd9a44d8015d530d4caa225b0df72711df5c6fda0df15a580422c`. The run starts at Skills `95dca9d0f04353856f4e1684333b3ed94e85de87` and selects `source-bound-reports`. Python is 3.14.6. The existing repository licence, CI, toolchain pin and hooks cover this evidence delivery.

The source pair is `wildcat-finance/v2-protocol` at deployed comparison source `f5a26146987926f4811b72a795d662813dedfe85` and candidate `bea503c2736d47de7fd34130c64f10783dc35b39`. Their deployment relations remain those stated by the accepted registry and event decision. Neither protocol checkout is changed. No vendored skill, public ABI, deployment, capture or skill frontier changes.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 130202d63cf6fbd1c9cfa1a1ca3b5161e4976b722e897660e65b0d6dfdf397cf
candidate | source-bound-reports
```

```command-interfaces
schema | protasis-command-interfaces/v1
tests/run_tests.py | report_target | aa577d63846e947944c04506ca9985b18bf3bac21c6d360bdbc18fd1f8360258
```

## Step 1: Produce and verify both source-bound X-Ray report sets

**Goal.** Deliver complete fresh reports for both commits and the reviewed action-to-event comparison consumed by issue #1387.

**Entry.** The run branch at `95dca9d0f04353856f4e1684333b3ed94e85de87`, with the study and runbook receipted, both immutable source trees available, and the selected design passing its step-entry gate.

**Exit.** The issue directory contains committed specification copies, a short handoff, source and artifact manifests, the two complete report sets, a literal entry-point diff, a semantic action comparison, a reviewed function-to-event linkage, and execution and review evidence. Each report set includes x-ray.md, entry-points.md, invariants.md, architecture.json and a visually inspected architecture.svg. Every source file has a scope disposition. Every state-changing callable action, including inherited actions and internal override contexts, has one reviewed linkage row or an explicit unresolved disposition. Constructors and initialization are separate. The comparison accounts for every action as added, removed, changed or unchanged, with citations for changed access, effects, value flows and event relations. Failed coverage remains an execution gap. The fixed-input checker demonstrates completeness and digest consistency; its refusal specimens demonstrate missing or contradictory evidence. The selected complete-pair conformance report passes before integration. Prove the repository exit with:

```sh
python3 scripts/run_checks.py --base fiat/1363-entry-point-maps-at-two-pinned-wildcat-v2-c --scope root --format json
```

**Files.** Create `docs/kickoff/1363/study.md`, `docs/kickoff/1363/runbook.md`, `docs/kickoff/1363/README.md`, `docs/kickoff/1363/design-evidence.json`, `docs/kickoff/1363/design-reports/`, `docs/kickoff/1363/manifest.json`, `docs/kickoff/1363/sources.json`, `docs/kickoff/1363/deployed/`, `docs/kickoff/1363/candidate/`, `docs/kickoff/1363/linkage.json`, `docs/kickoff/1363/comparison.json`, `docs/kickoff/1363/comparison.md`, `docs/kickoff/1363/entry-points.diff`, `docs/kickoff/1363/evidence/`, `scripts/kickoff_xray_1363.py`, `tests/test_kickoff_xray_1363.py`, and `docs/decisions/drafts/keep-wildcat-xray-reports-bound-to-two-source-commits.md`. Update `tests/check-map-v1.json` when required by ownership, and regenerate `.horos/boundary.json` and `.horos/census.json` before recording a green tree. All retained public evidence stays under the issue directory; temporary source checkouts and controller state remain ignored.

**Tests.** Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-1.json`
Add meaningful checker refusals for a missing report, altered digest, swapped source role, duplicate or dropped action, absent linkage disposition, omitted semantic comparison, mismatched literal diff, absent review, and unsafe evidence path. The committed positive bundle is checked through the root suite. The checker must compare independently declared action inventories with linkage and comparison membership; agreement among two equally truncated lists is insufficient. Warden reviews source semantics independently from the checker.

**Disciplines.** phylax: bound local evidence reads, reject symlink and path escapes, accept only the fixed inventory, and never execute report text. ephoros: retain command, source role, tool version, exit and output digest, and name each failed record or field. metron: no product performance claim; preserve only the measured packaging selection. elenchus: reproduce any checker defect and guard the failing and fixed forms through the declared root-suite reporter. hypomnema: explain the source-bound packaging decision in its draft and keep recovery commands and limitations beside the reports.
