# Study: inject known-failure guards before production changes

## Assumptions

Assuming, unless corrected:

1. The controller packet is authoritative. The target is `/Users/c0rtexzer0/Projects/wildcat-skills-live/tmp/fiat/fiat-453-inject-known-failure-guards-before-productio`, the starting ref is `main` at `5bc2494c4f5802efcd8a92e58554809ac4b9f147`, and this study may write only controller evidence below `.hexaemeron/`.
2. Issue [#453](https://github.com/wildcat-finance/skills/issues/453), including its 26 August 2026 current-review block, is the scope authority. Issues #327, #429, and #369 are satisfied prerequisites; issue #363 stays untouched and is the first intended consumer after this work lands.
3. “Known failure” means a failure named by the source-bound Protasis inventory at study time. It does not mean every defect that could exist, and a green result does not establish a defect-free tree.
4. The inventory is complete because Surveyor closes it against the checked audit views. Fiat checks its structure, source bindings, assignments, and receipts; it does not rediscover audit meaning during implementation.
5. A test-only commit may be red only inside one open implementation step. It is never a completed step, push candidate, hand-off to the next step, expected failure, or passing claim.
6. The installed controller that owns this run cannot enforce a phase it does not yet contain. This run therefore bootstraps each product edit with the same test-first evidence as a source-bound procedure, then proves actual enforcement with the checked-in controller in a disposable repository. The study does not claim the installed controller enforced its own replacement.
7. “Product path” at the inoculation boundary means every changed path not listed for that finding as a test, fixture, runner adapter, or structured-report support path. The controller compares committed Git objects; it does not claim to observe an editor’s uncommitted timeline.
8. The change uses the repository’s existing Python and JSON machinery. It adds no dependency, no Solidity, no network call, and no CI edit.

These readings follow the issue, current controller, and prerequisite audit records. The build order or selected design would change if assumptions 3, 4, 6, or 7 were rejected.

## 1. Problem statement, user, prototype, and demonstration

Fiat currently receipts a runbook and opens Step 1 directly in `implement`. Mason receives a runbook step, branch, parent, plugin root, and design binding, but no known-failure inventory. Elenchus can compare changed tests with a commit’s parent and return `guarded`, `unguarded`, `passed`, or `inconclusive`; the audit receipt records only the returned string. It neither retains the report bytes nor stops production implementation on a non-`guarded` result.

Build a pre-production inoculation boundary for Fiat contributors and reviewers. Protasis supplies one immutable, audit-source-bound inventory. Before Mason may change product paths for a consuming step, Mason commits only the declared tests, fixtures, adapters, and report support; Elenchus runs every entry against that step’s exact unfixed parent; and Fiat receipts only a complete set of fresh `guarded` results. The implementation then continues on the same step branch. Before the step finishes, the same cases must report clean on the fixed tree beside both repository suites.

A working prototype meets these checkable conditions:

1. `python3 -m unittest plugins.hexaemeron.tests.test_issue_453_known_failure_inventory -v` accepts the closed inventory and names omitted, duplicate, malformed, stale, and unassigned entries without state or ledger drift.
2. `python3 -m unittest plugins.hexaemeron.tests.test_issue_453_inoculation_lifecycle -v` proves `done runbook` opens `inoculate`, `done implement` refuses before inoculation, a guard-only commit cannot contain any undeclared path, and a complete inoculation receipt alone opens `implement`.
3. `python3 -m unittest plugins.hexaemeron.tests.test_issue_453_guard_evidence -v` binds every finding id, exact parent commit, guard commit, declared test bytes, test command, report format, retained report bytes and digest, result, and consuming step. Import error, timeout, empty run, stale or malformed report, infrastructure error, unexpected assertion, `unguarded`, `passed`, and `inconclusive` each refuse by name.
4. `python3 -m unittest plugins.hexaemeron.tests.test_issue_453_recovery -v` proves status, next, verification, checkpoint restore, and post-compaction reconstruction retain the same remaining inventory; it also proves the explicit no-findings route and refuses a red finished step.
5. `python3 plugins/hexaemeron/docs/known-failure-inoculation/proof.py` drives the checked-in controller in a disposable repository from runbook receipt through inoculation, implementation, audit, and final verification. It includes one early-product refusal, all non-guard verdict refusals, one no-findings step, a resume, and a final tree whose injected guards and existing suites pass.
6. `python3 plugins/hexaemeron/tests/run_tests.py` and `python3 -m unittest discover -s tests` pass on the final tree. `python3 scripts/run_checks.py --base 5bc2494c4f5802efcd8a92e58554809ac4b9f147` selects and passes every affected check.

The proving demo is condition 5 followed by condition 6. It proves the new checked-in controller, not this run’s older controller.

## 2. Prior art, audit record, and open work

### Repository state

`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` defines `STEP_PHASES = ["issue", "implement", "audit", "prose", "push"]`. `done_runbook` sets the first step to `implement`; `_next_directive` returns that phase; `delegation_packet` gives Mason no inventory; and `done_implement` verifies a signed Git range before moving to audit. These are the exact insertion points. The existing design-evidence transition supplies the pattern for immutable records, due-at-transition reports, receipt digests, and verification replay.

`plugins/hexaemeron/skills/elenchus/scripts/elenchus.py` already overlays changed tests on the fix parent, confines a fresh report, accepts `unittest-json-v1`, `forge-junit-v1`, and `node-test-json-v1`, and maps missing, stale, malformed, incomplete, zero-test, mixed error/assertion, timeout, interrupted, and unsafe-path results to `inconclusive`. `--require-guard` exits 1 unless the result is exactly `guarded`. The missing part is durable per-finding evidence and Fiat’s pre-edit gate, not a second classifier.

The subject’s last two merged pull requests were read:

- [PR #1249](https://github.com/wildcat-finance/skills/pull/1249), product commit `982146571a317d16f8f9d812469c90a1332bb4c2`, merge `f2bfe5ca1cc8816c77c82c1d51da72986726d7d9`, makes exact runbook-heading and `steps.json` parity a pre-receipt condition. Its body has no `## Carried forward` or carryover line. Keep its mutation ordering: refuse before receipt, design transition, state write, or ledger append. Its boundary is legacy mismatched receipts, which this work does not rewrite.
- [PR #1002](https://github.com/wildcat-finance/skills/pull/1002), product commit `c5e9bdd02022373805f833dfebe8ed41cdb94ab5`, merge `c79d6781e2278642d1653d50671acdabb5867ef8`, locks `protasis-design-evidence/v1` and checks later obligations at their named step or integration transition while leaving legacy states unchanged. Its body also has no carryover line. Keep its immutable-record, report-digest, progressive-stop, and legacy-preservation pattern. Its partial generated-runtime Hypomnema link boundary is unrelated and remains open under its existing owner.

[PR #493](https://github.com/wildcat-finance/skills/pull/493) is the direct predecessor contract. It preserves the four Elenchus declarations and says #453, not #327, owns signed report-byte binding and a production `guarded` gate. That item is carried into this study. It leaves #363 untouched; this study does too.

### Audit read mode and inventory

From the target root, `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited 0 for all 65 discovered source/view pairs: each passed its line budget and matched the committed bytes. The following current synopses were read as the normal views. Their headers bind the authoritative source digests; this study does not claim the source files were read in place of those views.

| authoritative source | read view | source SHA-256 | view SHA-256 | retained result |
| --- | --- | --- | --- | --- |
| `audit/AUDIT.md` | `audit/AUDIT_SYNOPSIS.md` | `d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d` | `82dc1d43e0fa9ee7a4cd7044aadeeb4049a1980e57943486809bc1d14533d0ee` | issue-327 rounds below; legacy schema, Covered, Not checked, and formal Elenchus fields remain unknown |
| `audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.md` | sibling `.synopsis.md` | `51891eaf4a387acb79ab65c9508c09cb84828cb40c475a3b363fddcecd74fe8d` | `937417919bb6c27ab5a47a8d5adadef2eb088592d2937f0154e7868a133f0a50` | 29 v1 rounds; all findings fixed; #453 repeatedly excluded |
| `audit/rounds/fiat-429-recover-issue-429-from-pull-request-552.md` | sibling `.synopsis.md` | `aedafae71bf2e254d2f5cc37a40fcf150f80a17fa478bfec4c7a2d2d39a40213` | `6bb3c81d841bc54adac3678f567393b92adc9596614057022601afc94968a548` | four v2 rounds; two findings fixed; #453 remains outside |
| `audit/rounds/fiat-369-read-audit-synopsis-resigned.md` | sibling `.synopsis.md` | `a5bbc01858fb95cb5334a503285c73418e2ee4a7618f66920f89c1aafa94f784` | `f6a9c8c82d4eeaefd6c836f574d6497611a3bed40baa72bc5e10d049b4ab90a6` | one clean v2 round; issue-453 behaviour expressly not checked |
| `plugins/hexaemeron/audit/AUDIT.md` | `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` | `8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f` | `2e919d920cd952a837bee6069251b710a9543df37514d7248a996d61766138cd` | `F-01` through `F-09` fixed; `F-10` accepted; legacy structured fields unknown |

The issue-327 root records retain these ids and statuses: `S1-R1-01` fixed, `S1-R1-review` clean, `S1-R1-records` clean; `S1-R2-01` and `S1-R2-02` fixed, `S1-R2-review` and `S1-R2-records` clean; `S1-R3-review`, `S1-R3-guards`, and `S1-R3-records` clean; `S2-R1-review`, `S2-R1-inherited`, and `S2-R1-runtime` clean; `S3-R1-01` and `S3-R1-02` fixed, `S3-R1-review` and `S3-R1-release` clean; `S3-R2-01` and `S3-R2-02` fixed, `S3-R2-review` and `S3-R2-round1` clean; `S3-R3-review`, `S3-R3-proof`, and `S3-R3-round2` clean. Each record’s formal `Audit schema`, `Covered`, `Not checked`, and `Elenchus verdict` is `[missing legacy field: ...]` and stays unknown. Its risk tables cover `fix-claim-confusion`, `enum-drift`, `command-substitution`, `legacy-round-breakage`, `receipt-overclaim`, `downstream-loss`, and `frontier-drift`. Leads retain operating-system-authority and partial-file limits, the runbook terminal-byte discrepancy, old-controller self-hosting limits, and documentation-only `unguarded` results. The directly carried lead is #453’s report-byte binding and production gate; #429, #369, and #363 remain separately owned where each record says so.

The issue-429 v1 view retains every finding id. Step 1 rounds contain `S1-R1-01..03`, `S1-R2-01..04`, `S1-R3-01..03`, `S1-R4-01..04`, `S1-R5-01..03`, `S1-R6-01..03`, `S1-R7-01..05`, `S1-R8-01..05`, `S1-R9-01..02`, `S1-R10-01..02`, and `S1-R11-01..04`; round 12 is clean. Step 2 contains `S2-R1-01..04`, `S2-R2-01..03`, `S2-R3-01..07`, `S2-R4-01..03`, `S2-R5-01..03`, `S2-R6-01..03`, `S2-R7-01`, `S2-R8-01..02`, `S2-R9-01`, `S2-R10-01..03`, `S2-R11-01..02`, `S2-R12-01`, `S2-R13-01`, and `S2-R14-01`; round 15 is clean. Step 3 contains `S3-R1-01..03`; round 2 is clean. Every named finding is recorded fixed, with exact qualifications retained in the view: `S1-R2-03`, `S1-R3-02`, `S1-R5-02`, `S1-R6-03`, `S1-R7-04`, `S1-R7-05`, and `S1-R11-03` lack an independent Elenchus guard or use a separate non-Elenchus gate. All other finding rounds record `guarded`; clean rounds record `null`. Step 1’s Covered map marks the step-2 parser, synopsis, lead, partial-write, and Horos concerns not applicable; Step 2 and Step 3 review all 13 registered concerns. The recurring Not checked and Leads fields retain the non-Solidity waiver, installed-controller self-hosting limit, sibling-write rather than whole-set atomicity, post-final-check mutation, unsupported-platform limits, and separately owned #453, #369, and #363 work. In particular, no #429 round claims report-byte or production-gate coverage for #453.

The #429 recovery view records `S1-R1-01` fixed and `guarded`, a clean `null` round, `S2-R1-01` fixed and `guarded`, then a clean `null` round. Its Covered map reviews signed lineage, receipt provenance, merge-parent order, base drift, conflict resolution, controller regression, audit-prefix integrity, relocation, synopsis naming and currency, schema topology, partial writes, path boundaries, attribution, scope, and integration-key behaviour; version collision moves from not applicable to reviewed in Step 2. Not checked retains the Solidity waiver, Windows, live integration, hard termination between outputs, release propagation, and publication. Leads retain per-sibling rather than cross-file atomicity, synopsis candidates outside Horos’s hard boundary, and issues #557, #608, #453, #369, and #363 under their owners.

The #369 view has no finding. Its `Covered` field marks `revoked-ancestry`, `receipt-reuse`, `replacement-key-drift`, `key-disclosure`, `source-view-confusion`, `umbrella-omission`, `stale-view`, `fallback-overclaim`, `legacy-gap-inference`, `decision-loss`, `frontier-drift`, `generated-record-order`, and `scope-creep` reviewed. `Not checked` retains the Solidity waiver, key material, a live third-party fallback, hosted CI, controller receipt, push, publication, and issue-453 behaviour. `Elenchus verdict` is `null`; `Leads not pursued` is `none`.

The Hexaemeron plugin view keeps `F-01..F-09` fixed and `F-10` accepted. Both records have legacy unknowns for schema, Covered, Not checked, and verdict. Its leads retain cross-filesystem replacement after a user-created state-directory symlink, same-state-directory concurrency, machine-facing ANSI JSON, and non-applicable Solidity tools. This design preserves the single-driver boundary and does not claim an operating-system lock.

Audit records for unrelated plugins are outside the Fiat/Protasis/Elenchus lineage. The whole-set check still established that their views were current; this study did not treat them as evidence for the design.

### Organisation and external prior art

A live GitHub code search across `wildcat-finance` found no second implementation of a pre-production known-failure gate. It found this repository’s issue-369 study and the read-only Wave Atlas entry for #453. The private marketplace mirror repeats the same bytes and is distribution, not independent prior art. An earlier local assessment of Clawpatch 0.7.2 mapped only 11 of 229 tested paths and missed plugin, skill, and Solidity boundaries; the executable or repository was unavailable for a live recheck on 5 September 2026. Its finding records and revalidation shape are useful vocabulary only, not reusable evidence or a selected dependency.

[in-toto layouts](https://in-toto.io/docs/getting-started/) are the closest external record pattern: named steps bind authorised actors, materials, and products, then verification checks the resulting link metadata. [PIT’s mutation-testing model](https://pitest.org/quickstart/basic_concepts/) supplies the relevant test property: an effective test fails when the fault is present. [SLSA source verification](https://slsa.dev/spec/v1.2/verifying-source) shows why a digest must bind the exact revision rather than a nearby run. These are design analogies. No external package enters the implementation.

### Complete known-failure inventory for this run

The source refs below point into the checked views above. The inventory ids are stable within this study. The future Protasis parser will read this exact object and refuse any shape or source drift before runbook receipt.

```known-failure-inventory
{
  "schema": "protasis-known-failure-inventory/v1",
  "source_views": [
    {"id": "issue-327-root", "path": "audit/AUDIT_SYNOPSIS.md", "source_sha256": "d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d", "view_sha256": "82dc1d43e0fa9ee7a4cd7044aadeeb4049a1980e57943486809bc1d14533d0ee"},
    {"id": "issue-429-schema", "path": "audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.synopsis.md", "source_sha256": "51891eaf4a387acb79ab65c9508c09cb84828cb40c475a3b363fddcecd74fe8d", "view_sha256": "937417919bb6c27ab5a47a8d5adadef2eb088592d2937f0154e7868a133f0a50"},
    {"id": "issue-369-consumer", "path": "audit/rounds/fiat-369-read-audit-synopsis-resigned.synopsis.md", "source_sha256": "a5bbc01858fb95cb5334a503285c73418e2ee4a7618f66920f89c1aafa94f784", "view_sha256": "f6a9c8c82d4eeaefd6c836f574d6497611a3bed40baa72bc5e10d049b4ab90a6"}
  ],
  "findings": [
    {
      "id": "kf-453-01",
      "source_ref": "issue-429-schema: every round excludes issue 453 report-byte binding; issue 453 acceptance 2 and 7",
      "failure": "an omitted, duplicate, malformed, stale, or unassigned inventory can reach a runbook without a named refusal",
      "guard_paths": ["plugins/hexaemeron/tests/test_issue_453_known_failure_inventory.py", "plugins/hexaemeron/tests/emit_issue_453_guard_report.py", "plugins/hexaemeron/tests/fixtures/issue-453/inventory.json"],
      "test_command": "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-01 --report {report}",
      "report_format": "unittest-json-v1",
      "report_file": ".elenchus/issue-453-kf-453-01.json",
      "expected_guard_verdict": "guarded",
      "green_command": "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-01 --report .elenchus/issue-453-kf-453-01-green.json",
      "consuming_step": 1
    },
    {
      "id": "kf-453-02",
      "source_ref": "issue-327-root:341 carries issue 453 production gating; issue 369 Not checked names issue-453 behaviour",
      "failure": "done runbook opens implement directly and done implement is callable without an inoculation receipt",
      "guard_paths": ["plugins/hexaemeron/tests/test_issue_453_inoculation_lifecycle.py", "plugins/hexaemeron/tests/emit_issue_453_guard_report.py"],
      "test_command": "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-02 --report {report}",
      "report_format": "unittest-json-v1",
      "report_file": ".elenchus/issue-453-kf-453-02.json",
      "expected_guard_verdict": "guarded",
      "green_command": "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-02 --report .elenchus/issue-453-kf-453-02-green.json",
      "consuming_step": 2
    },
    {
      "id": "kf-453-03",
      "source_ref": "issue-327-root:341 says the receipt is a declaration, not report-byte attestation; issue-429-schema leaves binding to issue 453",
      "failure": "Mason receives no source-bound inventory and Fiat binds no finding, parent, test bytes, command, report bytes, or consuming step",
      "guard_paths": ["plugins/hexaemeron/tests/test_issue_453_guard_evidence.py", "plugins/hexaemeron/tests/emit_issue_453_guard_report.py", "plugins/hexaemeron/tests/fixtures/issue-453/guard-evidence.json"],
      "test_command": "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-03 --report {report}",
      "report_format": "unittest-json-v1",
      "report_file": ".elenchus/issue-453-kf-453-03.json",
      "expected_guard_verdict": "guarded",
      "green_command": "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-03 --report .elenchus/issue-453-kf-453-03-green.json",
      "consuming_step": 3
    },
    {
      "id": "kf-453-04",
      "source_ref": "issue-327-root:338-344 preserves passed and unguarded declarations without a production block; issue 453 acceptance 4",
      "failure": "a non-guard outcome, stale report, zero run, unexpected assertion, or infrastructure failure can be mistaken for inoculation",
      "guard_paths": ["plugins/hexaemeron/tests/test_issue_453_guard_evidence.py", "plugins/hexaemeron/tests/emit_issue_453_guard_report.py", "plugins/hexaemeron/tests/fixtures/issue-453/guard-outcomes.json"],
      "test_command": "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-04 --report {report}",
      "report_format": "unittest-json-v1",
      "report_file": ".elenchus/issue-453-kf-453-04.json",
      "expected_guard_verdict": "guarded",
      "green_command": "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-04 --report .elenchus/issue-453-kf-453-04-green.json",
      "consuming_step": 3
    },
    {
      "id": "kf-453-05",
      "source_ref": "issue-327-root:341 carries the production guarded gate; issue 453 acceptance 1 and 5",
      "failure": "a guard commit containing an undeclared product path can be receipted before guard evidence",
      "guard_paths": ["plugins/hexaemeron/tests/test_issue_453_inoculation_lifecycle.py", "plugins/hexaemeron/tests/emit_issue_453_guard_report.py", "plugins/hexaemeron/tests/fixtures/issue-453/path-boundary.json"],
      "test_command": "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-05 --report {report}",
      "report_format": "unittest-json-v1",
      "report_file": ".elenchus/issue-453-kf-453-05.json",
      "expected_guard_verdict": "guarded",
      "green_command": "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-05 --report .elenchus/issue-453-kf-453-05-green.json",
      "consuming_step": 3
    },
    {
      "id": "kf-453-06",
      "source_ref": "issue-369-consumer: Not checked includes issue-453 behaviour; issue 453 acceptance 7 and 8",
      "failure": "resume can forget remaining findings, while an empty inventory can be accepted without a bound no-known-findings claim",
      "guard_paths": ["plugins/hexaemeron/tests/test_issue_453_recovery.py", "plugins/hexaemeron/tests/emit_issue_453_guard_report.py", "plugins/hexaemeron/tests/fixtures/issue-453/recovery.json"],
      "test_command": "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-06 --report {report}",
      "report_format": "unittest-json-v1",
      "report_file": ".elenchus/issue-453-kf-453-06.json",
      "expected_guard_verdict": "guarded",
      "green_command": "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-06 --report .elenchus/issue-453-kf-453-06-green.json",
      "consuming_step": 4
    },
    {
      "id": "kf-453-07",
      "source_ref": "issue-327-root:342-344 records documentation-only unguarded fixes; issue 453 acceptance 6 and 9",
      "failure": "a deliberately red guard commit can be treated as a finished step or hidden as an expected failure instead of becoming fixed-tree green",
      "guard_paths": ["plugins/hexaemeron/tests/test_issue_453_recovery.py", "plugins/hexaemeron/tests/emit_issue_453_guard_report.py", "plugins/hexaemeron/tests/fixtures/issue-453/final-green.json"],
      "test_command": "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-07 --report {report}",
      "report_format": "unittest-json-v1",
      "report_file": ".elenchus/issue-453-kf-453-07.json",
      "expected_guard_verdict": "guarded",
      "green_command": "python3 plugins/hexaemeron/tests/emit_issue_453_guard_report.py --case kf-453-07 --report .elenchus/issue-453-kf-453-07-green.json",
      "consuming_step": 4
    }
  ],
  "no_known_findings": null
}
```

This run has seven known findings, so `no_known_findings` is null. Future empty inventories must replace it with a non-null claim binding every checked source view, its digest, the consuming step, and the Surveyor assertion that no finding applies. An empty array by itself never authorises implementation.

## 3. Constraints, non-goals, and authority

The exact entry is `main` at `5bc2494c4f5802efcd8a92e58554809ac4b9f147` on `fiat/453-inject-known-failure-guards-before-productio`. The pinned interpreter is `.python-version` 3.14.6; the observed tools are CPython 3.14.6, Apple Git 2.50.1, Node v26.6.0, stdlib unittest, and existing repository scripts. Current governed versions are Fiat `v5.52.1`, Protasis `v5.10.0`, Elenchus `v1.3.0`, and Hexaemeron package `1.6.24`. The runbook should use version relations for Fiat, Protasis, and Elenchus rather than guessing their integration-base labels.

Included: the Protasis inventory contract and parser; a Fiat `inoculate` phase and receipt; source-bound Mason packets; retained Elenchus report bytes and one closed evidence manifest; path, parent, freshness, completeness, verdict, resume, legacy, no-findings, and final-green checks; tests, docs, release surfaces, and a disposable proof.

Excluded: unknown-failure discovery; changing Elenchus’s four verdict meanings; changing audit severity; rewriting any audit record or legacy receipt; a service or hosted telemetry system; CI; dependencies; Solidity; issue #363; publication; and an operating-system guarantee against a same-UID process rewriting Git or controller files.

Authority boundaries:

- Always: keep all seven ids and their source bindings; run both repository suites before a commit; run Imprimatur on every shipped document; capture a measurement before any performance change; keep a red test-only commit inside its open step; verify signatures, provenance, exact parentage, report bytes, and final green state.
- Ask first: add a dependency; touch CI; change a public schema, storage layout, state version, or trust boundary beyond the declared report and Git-object reads; change the four Elenchus verdicts; edit an audit source; widen allowed inoculation paths.
- Never: infer a missing legacy field; accept an empty inventory as success; treat `passed`, `unguarded`, or `inconclusive` as inoculation; count import or infrastructure failure as a guard; delete or skip a failing test; push a red step; expose a credential; let Surveyor receipt the phase.

## 4. Candidate designs and checked choice

### Candidate A: `receipted-inoculation`

Add one explicit `inoculate` phase before `implement`. Protasis supplies the immutable inventory; Mason creates one signed guard-only commit whose parent is the exact step parent; Elenchus retains the raw reports and emits a closed per-finding manifest; Fiat checks declared paths and receipts the complete set before it exposes `implement`. `done implement` then requires fixed-tree clean reports for the same ids.

Trade: one extra controller round trip and three durable record kinds: the inventory, retained report/manifest set, and receipt. It gives the controller a real stop point, preserves Mason and Warden roles, and makes resume reconstructible.

### Candidate B: `two-commit-implement`

Keep the existing phase list. Mason creates a test-only commit followed by product commits, and `done implement` checks their order at the end.

Trade: no new transition and one combined receipt, but the controller learns about the order only after product edits exist. A restart cannot distinguish a guard-only state from an early product edit. It fails the pre-edit and recovery gates.

### Candidate C: `audit-prologue`

Run an audit round before implementation and ask Warden to inject the guards, then reuse the audit receipt as permission to implement.

Trade: one extra round trip and two record kinds, with a reconstructible stop. It reverses the current audit-after-implementation phase order and makes Warden author Mason’s test artefacts. It fails worker-role compatibility.

The selection source table is closed and is the input each design report checks:

| candidate | pre-edit-refusal | new-controller-round-trips | new-record-kinds | worker-role-compatibility | inventory-resume-parity |
| --- | --- | ---: | ---: | --- | --- |
| receipted-inoculation | true | 1 | 3 | true | true |
| two-commit-implement | false | 0 | 1 | true | false |
| audit-prologue | true | 1 | 2 | false | true |

The complete machine record is `.hexaemeron/design-evidence.json`; its 15 reports are under `.hexaemeron/design-reports/`. `pre-edit-refusal`, `worker-role-compatibility`, and `inventory-resume-parity` are selection gates. The two count metrics expose time and space trades but cannot rescue a failed gate. `receipted-inoculation` is the only eligible candidate, so `unique-frontier` selects it. The record contains no pending selection or conformance claim; implementation behaviour remains governed by the success commands in item 1 rather than predicted in the design matrix.

The five-step decomposition for the runbook is:

| module id | responsibility | depends on |
| --- | --- | --- |
| `inventory-contract` | Scaffold the schema, parser, source bindings, reporter, and inventory refusals | none |
| `inoculation-transition` | Add the phase, state, directive, Mason packet, and no-findings branch | `inventory-contract` |
| `guard-evidence` | Bind exact parent, allowed guard paths, test bytes, raw reports, verdicts, and the pre-edit refusal | `inoculation-transition` |
| `recovery-and-final-green` | Replay receipts across resume/checkpoint/verify and require the same guards clean before a step can finish | `guard-evidence` |
| `release-demonstration` | Ship governed prose, versions, portable copies, and the disposable end-to-end proof | all prior modules |

Step 1 must scaffold and finish green. Within each open step, the seven inventory entries require a transient test-only commit and `guarded` parent evidence before its product changes. Step 5 is the proving demo. No module may be cut without changing the prototype promise.

## 5. Risk register seed

```risk-register
inventory-omission | the Protasis study-to-runbook boundary | every known id appears once, is source-bound, and is assigned to exactly one real step
source-view-drift | the authoritative audit source and checked synopsis join | source and view digests match the receipted inventory and stale views refuse
parent-substitution | the Git commit selected as the unfixed tree | the guard commit has exactly the receipted step parent and native Git reads ignore replacement objects
guard-path-escape | the test-only commit range | every changed path is one declared test, fixture, adapter, or report-support path and any product path refuses
report-substitution | Elenchus output crossing into Fiat evidence | a fresh bounded regular file is retained byte-for-byte and its digest, format, counters, command, and finding id agree
verdict-confusion | Elenchus classification crossing into permission | only exact guarded admits inoculation; all other verdicts and runner faults refuse by name
partial-inoculation | the set of reports for one consuming step | the receipt is atomic over the complete assigned id set and no subset advances state
preedit-bypass | the inoculate-to-implement transition | done implement and every product-bearing receipt refuse until the complete inoculation receipt exists
resume-loss | state, ledger, checkpoint, and delegation reconstruction | status, next, verify, restore, and compacted continuation derive the same remaining ids and source digest
empty-success | the step with no assigned finding | an explicit digest-bound no-known-findings claim is required and an empty list alone refuses
red-step-handoff | the transient guard commit and finished step boundary | a red commit is neither pushed nor completed, and every guard plus both suites are clean at step exit
self-hosting-overclaim | the installed controller building its checked-in successor | the disposable new-controller proof is separate from the old controller receipt and names which one enforced each gate
```

Warden must enumerate all 12 ids. The highest-risk joins are `guard-path-escape`, `report-substitution`, `partial-inoculation`, `preedit-bypass`, and `self-hosting-overclaim`.

## 6. Glossary seeds

- **Known failure:** one inventory entry fixed at study time, not every possible defect.
- **Inventory:** the closed `protasis-known-failure-inventory/v1` object bound by the study receipt.
- **Guard-only commit:** the signed single-parent commit containing only an entry’s declared test, fixture, adapter, or report-support paths.
- **Step parent:** the exact commit from which the consuming step branch begins, before its guard-only commit.
- **Inoculation:** complete `guarded` evidence for every finding assigned to a step, receipted before product changes are admissible.
- **Retained report:** the exact structured runner bytes copied into controller evidence before Elenchus removes its detached worktree.
- **Final-green evidence:** fresh clean runner reports for the same inventory ids on the step’s final commit.
- **No-known-findings claim:** a non-empty source-bound assertion that no inventory item applies to one step; it is not an empty successful run.
- **Product path:** any changed path outside the inventory entry’s closed guard-path set.
- **Bootstrap proof:** a disposable run under the new checked-in controller; it does not retrofit enforcement into this run’s installed controller.

## 7. Sources

- Controller packet and state: `.hexaemeron/state.json`, state fingerprint `25e080690952dff7b77fcebcbd6445894aab95646d33dc4257993813ad7a80c2`.
- Scope: [wildcat-finance/skills issue #453](https://github.com/wildcat-finance/skills/issues/453), read 5 September 2026.
- Latest subject changes: [PR #1249](https://github.com/wildcat-finance/skills/pull/1249) and [PR #1002](https://github.com/wildcat-finance/skills/pull/1002); direct predecessor [PR #493](https://github.com/wildcat-finance/skills/pull/493).
- Fiat controller: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, especially `STEP_PHASES`, `done_runbook`, `done_implement`, `done_push`, `delegation_packet`, and `_next_directive` at the starting ref.
- Elenchus contract and runner: `plugins/hexaemeron/skills/elenchus/SKILL.md`, `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py`, and `plugins/hexaemeron/tests/test_elenchus_checker.py`.
- Protasis contract and design checker: `plugins/hexaemeron/skills/protasis/SKILL.md`, `plugins/hexaemeron/skills/protasis/scripts/protasis.py`, and `plugins/hexaemeron/skills/protasis/scripts/design_evidence.py`.
- Audit sources and exact checked views: the five rows in item 2. The whole-set currency command and its 65/65 result are part of the read evidence.
- Prior delivery study: `plugins/hexaemeron/docs/elenchus-audit-round-verdict/study.md`; audit-schema study: `plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/study.md`; synopsis-consumer study: `docs/protasis-audit-synopsis-read-view-study.md`.
- External analogies: [in-toto getting started](https://in-toto.io/docs/getting-started/), [PIT basic concepts](https://pitest.org/quickstart/basic_concepts/), and [SLSA source verification](https://slsa.dev/spec/v1.2/verifying-source), read 5 September 2026.

## 8. Signals and the questions behind them

This remains an interactive controller, not an unattended service. No daemon metrics, trace backend, or alerting system is warranted. [Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns signal content; the implementation should expose bounded state, JSON evidence, and named refusals already retained by the controller.

The operator questions are:

1. “Which known findings still block this step?” `next` and `status --json` show the inventory digest, assigned count, completed ids, remaining ids, and current phase.
2. “What exactly failed inoculation?” the refusal names the finding id, failure class, command identity, report path/digest when available, and leaves state and ledger bytes unchanged.
3. “Which parent and test bytes earned permission to edit product code?” the inoculation receipt and verification replay show the step parent, guard commit, path/blob digests, retained report digest, and `guarded` result.
4. “Is the red interval still contained?” status distinguishes transient guard-only state from finished implementation; push and step-completion directives remain unavailable until final-green evidence exists.

Steps 2 and 3 add these controller signals; Step 4 checks their recovery; Step 5 demonstrates them. Report contents and arbitrary stderr are evidence, never instructions, and must not be printed without their existing bounds.

## 9. Trust boundaries and controls

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the capability-boundary rules. Four boundaries apply:

1. Study inventory to controller parser: bounded UTF-8 and strict JSON shape, duplicate-key refusal, capped depth/count/bytes, portable repository-relative paths, source/view digest checks, and exact step assignments.
2. Declared test command to subprocess: reuse Elenchus’s argv path with one exact `{report}` token, no shell, fixed timeout, cleared inherited report variable, bounded diagnostics, and no command inferred from filenames.
3. Git object and guard-path reads: native replacement-free commit resolution, exact single parent, bounded sorted paths, no symlink traversal, regular-file/stability checks, and SHA-256 over the exact blobs consumed.
4. Retained report and manifest writes: controller-owned `.hexaemeron/steps/<n>/inoculation/`, no-follow descriptor access, fresh-file requirement, bounded bytes, atomic replacement, identity recheck, and digest verification before state or ledger mutation.

No credential, network URL, GitHub token, or private key is an input to inoculation. Signature verification remains Fiat’s existing Git boundary. A malicious same-UID writer after the final identity check remains outside the promise and is stated rather than hidden.

## 10. Performance budget or its absence

No latency or throughput claim is part of this interactive state transition, so no Metron performance budget applies. [Metron](../plugins/hexaemeron/skills/metron/SKILL.md) remains the owner if implementation changes performance. Resource bounds are correctness controls, not speed claims: at most 128 inventory findings, at most 4,096 guard paths, the existing 1 MiB Elenchus report ceiling, and existing controller source/state caps. `python3 -m unittest plugins.hexaemeron.tests.test_issue_453_known_failure_inventory -v` enforces the new count and shape ceilings.

If a performance edit becomes necessary, stop and record a baseline before changing it. The comparison command will be `python3 -m timeit -n 10 -r 5 -s 'from plugins.hexaemeron.skills.fiat.scripts import hexctl' 'hexctl.load_state(".hexaemeron")'` only after a stable fixture path is supplied in the runbook; this study makes no result claim for that command.

## 11. Fail-closed posture and guard convention

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns failure triage and the guard rule. Each inventory item starts as one assertion-safe case added in the guard-only commit. The inventory’s exact test command runs through Elenchus with `--require-guard` against that commit, whose sole parent is the receipted step parent. Only `guarded` counts. The raw structured report is retained before detached-worktree cleanup and is hashed into the manifest.

Missing or extra inventory ids; duplicate keys; bad source digests; wrong step; wrong parent; more than one guard commit; undeclared paths; changed product paths; missing test bytes; command drift; missing, stale, malformed, oversized, incomplete, or zero-test reports; import errors; timeouts; interruption; infrastructure errors; unexpected successes; mixed assertion/error results; and `unguarded`, `passed`, or `inconclusive` all stop before state mutation and before `implement` is emitted. Diagnostics name the class without promoting stderr or exit text to verdict evidence.

After product changes, the same per-id commands run on the final step tree and must be complete, non-skipped, error-free, and assertion-free. Both repository suites must also pass. The transient red guard commit remains inside the open step ancestry; it is never the pushed head or the claimed green result. A new audit finding discovered later follows ordinary Elenchus and enters the next attempt’s durable inventory rather than silently changing this receipted one.

## 12. Expensive decisions and their homes

[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) decides which choices need durable records and where they live. Three decisions are expensive to reverse:

1. The new phase order, atomic receipt boundary, red-intermediate rule, and old-controller bootstrap limit belong in one Hypomnema-assigned ADR under `docs/decisions/` titled “Require inoculation before implementation”, cited by Fiat’s skill and evolution row.
2. The inventory schema, completeness authority, step assignment, and explicit no-findings form belong in `plugins/hexaemeron/skills/protasis/SKILL.md`, its tests, and the Protasis evolution row. The committed delivery study and runbook remain the decision’s concrete source example.
3. Retaining exact report bytes and binding them to Elenchus classification belongs in `plugins/hexaemeron/skills/elenchus/SKILL.md`, its runner tests, and the Elenchus evolution row. Fiat’s receipt schema cites rather than duplicates that classification contract.

Changing any of those after the study receipt requires an appended study amendment before code. Changing the selected candidate has no current design-amendment transition, so it requires a fresh run rather than an in-place edit of `.hexaemeron/design-evidence.json`.
