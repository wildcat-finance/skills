# Wildcat fee-event runbook

Assuming, unless corrected: the receipted study governs issue 2089 at starting commit `8b4e137917d754a7b7c3d5e74d141c0bedf70aa2`. Selected `versioned-native` adds adapter `1.1.0` and preserves starting-tree `1.0.0`; canonical schema stays 3. The three steps are scaffold, mapping, then demonstration. A pending user decision about absent historical positives blocks integration, while implementation and constructed conformance can proceed.

Always: preserve old releases and raw source, exact native units, source selectors and gaps; run declared checks and sign commits; apply the repository written-record sequence. Ask first: new dependencies, a new envelope, live collection, private publication or downstream scope. Never: invent a fee recipient, classify fees as repayment, silently upgrade old mapping bytes, publish retained payloads or counts, or claim an unrun check.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 741975cb879ab744283f579160a84cb2b6e74b308204fb3c7e7900878a0a0c2f
candidate | versioned-native
```

```version-relations
tabularium | plugins/tabularium/skills/tabularium/EVOLUTION.md | next-generation-after-integration-base
```

```command-interfaces
schema | protasis-command-interfaces/v1
plugins/tabularium/tests/prove_wildcat_fees.py | parser | step:1
plugins/tabularium/tests/emit_wildcat_fee_report.py | parser | step:1
```

The source-bound no-known-findings claim consumes Step 1. Fixed historical vacuity and subject-binding defects remain regression requirements; existing runner repair stays with issue 2103. No assigned parent-red finding is invented.

Each new parser is a thin immutable entrypoint with a literal `parser` builder. The proof runner accepts the three design candidates and all four conformance criteria; its implementation helpers may evolve later. The report runner accepts steps 1, 2 and 3 and writes `unittest-json-v1`. Both resolve local imports under safe-path and isolated Python, use fresh bounded report leaves, and retain distinct assertion, error and skip counters. Step 1 tests parser choices, report confinement and occupied-output refusal before parser bytes freeze.

Retained staging is supplied privately through the two established staging variables. Validate both complete inventories, rebuild raw releases with the public Alexandria example builders, then build and verify fresh canonical releases outside the repository. Public records carry release identifiers, digests and outcomes only. Qualified retained conformance requires an actual target event overall and correct rows for every target present; missing signatures stay explicit absences. It does not close the separate historical-positive acceptance question.

## Step 1: Scaffold fee proof runners and specification records

**Goal.** Establish the fixed runner interfaces, regression controls and committed specification without changing fee semantics.

**Entry.** The run branch at the recorded starting commit after its no-known-findings inoculation receipt; the existing study decision draft is authorised design prose.

**Exit.** Commit the specification, model reports, decision draft, thin runners and scaffold tests; update package metadata through its owner and regenerate derived copies and Horos metadata as required. Prove scaffold behaviour with `python3 plugins/tabularium/tests/emit_wildcat_fee_report.py --step 1 --report .hexaemeron/step-1-check.json`. Run `python3 scripts/run_checks.py --base 8b4e137917d754a7b7c3d5e74d141c0bedf70aa2 --scope root --scope tabularium --scope repo-lints --format json`.

**Files.** Create `plugins/tabularium/tests/prove_wildcat_fees.py`, `emit_wildcat_fee_report.py`, `wildcat_fee_reports.py` and `test_wildcat_fee_scaffold.py`; add `docs/kickoff/2089/` study, runbook, design evidence, selection model and report copies; retain `docs/decisions/drafts/version-wildcat-fee-native-events.md`. Update Tabularium package manifests, marketplace manifests and generated metadata only through the existing owners.

**Tests.** At least eight scaffold controls cover candidate and criterion choices, step selection, real test counters, safe-path imports, isolated imports, absent proof implementation, occupied reports and unsafe output paths. Pending product criteria refuse instead of returning a guessed success. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_fee_report.py --step 1 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2089-step-1.json`.

**Disciplines.** phylax: report paths and subprocess arguments remain bounded data. ephoros: criterion, source and exit distinguish refusal from failure. metron: no speed claim or performance edit. elenchus: reproduce any observed failure and preserve a guard. hypomnema: record versioned fee meaning and specification pointers.

## Step 2: Map fee events with immutable version dispatch

**Goal.** Add the three exact fee rules under version 1.1.0 while reconstructing version 1.0.0 byte for byte.

**Entry.** Step 1's verified push head and its bound thin parser bytes; the checked design remains versioned-native.

**Exit.** Build and verify both public constructed fee specimens; implement version propagation through CLI, mapping, provenance, capture, coverage, validation and reconstruction. Resolve the selected semantic, schema and legacy reports with `python3 plugins/tabularium/tests/prove_wildcat_fees.py --candidate versioned-native --criterion semantic-conformance --report .hexaemeron/design-reports/versioned-native-semantic-conformance.json`, `python3 plugins/tabularium/tests/prove_wildcat_fees.py --candidate versioned-native --criterion schema-parity --report .hexaemeron/design-reports/versioned-native-schema-parity.json`, and `python3 plugins/tabularium/tests/prove_wildcat_fees.py --candidate versioned-native --criterion legacy-conformance --report .hexaemeron/design-reports/versioned-native-legacy-conformance.json`. Prove the step with `python3 plugins/tabularium/tests/emit_wildcat_fee_report.py --step 2 --report .hexaemeron/step-2-check.json` and `python3 scripts/run_checks.py --base 8b4e137917d754a7b7c3d5e74d141c0bedf70aa2 --scope root --scope tabularium --scope repo-lints --format json`.

**Files.** Change `plugins/tabularium/scripts/tabularium.py`, relevant modules under `plugins/tabularium/scripts/tabularium_lib/`, `plugins/tabularium/schemas/canonical-event-v3.json`, `coverage-manifest-v3.json`, existing Wildcat rebuild programs and their tests. Add fee fixture, semantics, parity and compatibility helpers/tests and fresh `plugins/tabularium/examples/wildcat-v1-fees-v0/` and `wildcat-v2-fees-v0/`. Update `plugins/tabularium/docs/wildcat-canonical.md`, skill metadata and generation ledger while preserving its held frontier; update package and generated metadata through owners. Published release data remains untouched.

**Tests.** Cover V1/V2 fee amounts, sole pool party, recipient gap, missing asset context, V2 native Bips with no amount, co-occurring independent actions, malformed and reordered records, wrong generation or role, unknown mapping version, old/new rule confusion, all old committed releases and a starting-runtime fee-containing legacy control. Python and JSON Schema must agree on valid and hostile tuples; rebinding superficial digests cannot bless changed generated bytes. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_fee_report.py --step 2 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2089-step-2.json`.

**Disciplines.** phylax: version and native-log ingress stay closed and source-bound. ephoros: exact versions and attribution gaps explain each result. metron: no speed claim or performance edit. elenchus: guard each reproduced semantic or compatibility failure. hypomnema: document immutable dispatch and the exact limits of legacy reconstruction.

## Step 3: Demonstrate constructed and qualified retained fee releases

**Goal.** Execute the successor build and verify path and report retained observations without strengthening absence.

**Entry.** Step 2's verified push head, the three green Step 3 conformance reports and both manifest-verified retained staging trees.

**Exit.** Execute both specimen rebuilds, old-release reproduction, named refusal controls and the real offline retained resolver; remove its temporary releases on success and refusal. Resolve `python3 plugins/tabularium/tests/prove_wildcat_fees.py --candidate versioned-native --criterion retained-conformance --report .hexaemeron/design-reports/versioned-native-retained-conformance.json`. Run `python3 plugins/tabularium/tests/emit_wildcat_fee_report.py --step 3 --report .hexaemeron/step-3-check.json` and `python3 scripts/run_checks.py --base 8b4e137917d754a7b7c3d5e74d141c0bedf70aa2 --scope root --scope tabularium --scope repo-lints --format json`. Record all observed boundaries and prepare the run PR and checked task-comment draft. Integration remains stopped until the user resolves the missing historical positives or additional preserved evidence supplies them.

**Files.** Complete fee retained resolver and demonstration helpers/tests; add `docs/kickoff/2089/reproduction.md` and sanitized executed reports. Update the canonical guide, fresh specimen documentation, package surfaces and owner-generated metadata. Keep controller artifacts and private retained reports untracked.

**Tests.** Actual V2 retained fee collection must execute. Both staging inventories and full generated outputs verify; absent V1 fee collection and V2 protocol-fee updates remain qualified. All-empty retained inputs refuse; missing or unreadable custody, changed staging bytes, altered generated outputs, unknown versions and interrupted output leave no accepted partial result. Public reports contain no private paths or retained counts. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_fee_report.py --step 3 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2089-step-3.json`.

**Disciplines.** phylax: private custody and cleanup are checked without network access. ephoros: reports separate mapping success, absence and refusal. metron: no production performance claim. elenchus: guard failures observed by the demonstration. hypomnema: record reproduction, unknowns and the integration acceptance boundary.

