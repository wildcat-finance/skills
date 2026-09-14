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

### Amendment -- 2026-09-05

**What changed.** Known-failure assignment records are one versioned complete
set within runbook Exit authority. Generation zero is the visible baseline
before the first real amendment. Every structurally valid `Complete replacement
Exit:` value replaces the whole set, and the final such value alone is
authoritative even when it contains no records. An amendment that replaces
only another field preserves the current Exit generation. Superseded Exit
records remain readable history but are not counted. The checker derives
amendment, field, and clause spans outside fences; takes Step headings only
from the baseline; refuses assignment-like lines in non-Exit amendment fields,
ambiguous or malformed amendment and replacement boundaries, repeated Exit
clauses, and post-amendment Step headings; then applies the existing exact-line,
assignment-only-block, uniqueness, and step-correlation checks only to the
effective generation. Every later Exit replacement must therefore restate the
whole assignment set. The maintained focused module is renamed from the
issue-numbered guard path to
`plugins.hexaemeron.tests.test_known_failure_inventory` after the signed guard
proof, while the historical guard object and report remain unchanged.

**Why.** The receipted runbook now contains two sequential full Exit
replacements with the same seven records. Treating append-only history as one
simultaneous document-global set returns K010 and makes a valid replacement
amendment impossible. Selecting the last complete Exit generation preserves
the evidence history without allowing an older, partial, or conflicting set to
authorize implementation. The clean detached root suite separately proved
that the maintained issue-numbered module name violates the repository naming
gate.

**Steps touched.** Step 1's Exit and Files.

**Still holding.** Step 1: entry holds; exit broken. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Narrow the assignment projection from the preceding
amendment. Ordinary exact or assignment-like records outside a structurally
valid runbook `Complete replacement Exit:` clause remain active under the
existing document-global fail-closed rules; an amendment cannot hide a stray
record in Files, Why, Steps touched, or Still holding. Only records inside
replacement-Exit clauses are versioned. The effective set is every ordinary
record plus the records in the final valid replacement-Exit clause. Earlier
replacement-Exit records remain readable history and are not counted. A later
amendment that replaces only another field preserves the current Exit clause,
and an empty or incomplete final Exit clause never falls back to an earlier
one. The existing duplicate, malformed, missing, extra, and wrong-step checks
apply to that projected set. This supersedes only the preceding amendment's
statement that a replacement Exit erases generation-zero baseline records;
its parser-boundary, test-module, evidence-history, and broken-exit statements
continue to hold.

**Why.** Independent hostile-case review showed that suppressing every record
outside the final Exit value would weaken the established machine boundary by
letting an amendment hide an extra or conflicting baseline or prose record.
Versioning only the repeated full-field clauses fixes the observed append-only
collision while preserving all earlier refusal cases.

**Steps touched.** Step 1's Exit.

**Still holding.** Step 1: entry holds; exit broken. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** The study inventory projection tolerates unmatched
inline-backtick runs in ordinary prose, including a span whose matching
delimiter appears on a later physical line. It never uses those spans to mask
bytes or machine records. Before applying that prose tolerance, the checker
processes or refuses every column-zero fence candidate; it continues to refuse
raw HTML, image openers, indented fences, malformed fence information, mixed
fence kinds, bad blank isolation, unclosed inventory fences, and anything
other than exactly one inventory block. An adjacent apparent inventory fence
after an open tick therefore fails isolation, while a blank-separated fence is
a real block and participates in exact-one cardinality. The runbook assignment
projection retains its strict single-physical-line inline-code policy, so no
multiline or unmatched span can hide an assignment. This study-only surface
rule joins the effective-Exit projection from the preceding amendment; neither
changes the seven findings, their source bindings, or the selected design.

**Why.** The exact receipted study contains one valid CommonMark code span split
across lines 336 and 337. The shared strict surface returns K001 before reading
the unchanged inventory, even though the span contains no fence, HTML, image,
or machine record. A study-only prose tolerance consumes those historical
bytes without weakening the stricter runbook boundary or the inventory block
rules.

**Steps touched.** Step 1's Exit.

**Still holding.** Step 1: entry holds; exit broken. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Tighten the runbook assignment projection at both its source
surface and its append-only history boundary. On the runbook only, the checker
refuses every `[` byte outside a complete single-physical-line inline code span
or a complete fenced block. A link, image, reference label, or multiline title
therefore cannot supply a hidden amendment heading, field, replacement clause,
or assignment. The study surface keeps its existing rules. `What changed` must
also be the first nonblank, unfenced record after its amendment heading.

Within each complete replacement Exit generation, the checker first applies
the existing exact assignment syntax, unique-id, and real-Step checks, then
derives the set of finding-id-to-Step pairs. Empty Exit generations may precede
the inventory. The first nonempty map locks assignment authority. Every later
Exit generation, including an empty one, must carry the same map; source order
governs, and the lock cannot reset or fall back. Pair order does not matter.
An empty, partial, extra, or reassigned post-lock generation refuses. A
non-Exit amendment neither creates nor changes a generation. Ordinary exact or
assignment-like records outside replacement Exit clauses remain active under
the document-global checks and stay outside the generation-map comparison.
These rules join the preceding effective-Exit and study-surface amendments;
the seven findings, source bindings, selected design, and maintained test name
do not change.

**Why.** Independent hostile-input review placed visible replacement-Exit
authority and an extra assignment before three apparent amendment fields
inside a multiline link title. The parser treated those raw field lines as an
amendment boundary and a later Exit as authoritative, so the extra assignment
disappeared from the effective set. Requiring a link-free runbook machine
surface removes that hidden-field path. The immutable generation map also
refuses any later scope confusion that would erase, add, or reassign known
failure authority, while accepting the receipted history: its first two Exit
generations are empty and its remaining five carry the same seven pairs.

**Steps touched.** Step 1's Exit.

**Still holding.** Step 1: entry holds; exit broken. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Bind the selected `receipted-inoculation` design to its
existing cross-cutting decision record through this single closed bridge:

```design-bridge
schema | hypomnema-design-bridge/v1
decision | receipted-inoculation
record | adr/require-inoculation-before-implementation
```

Hypomnema study mode admits three record forms. Existing portable paths to a
numbered ADR or governed skill ledger retain their current meaning. The stable
form is exactly `adr/<slug>`, where the slug is lowercase ASCII kebab-case and
at most 96 bytes. It resolves only the canonical draft
`docs/decisions/drafts/<slug>.md` and canonical numbered final records named
`docs/decisions/ADR-NNN-<slug>.md`, where `NNN` is exactly three ASCII digits.
The resolver examines that fixed bounded candidate set, follows no symlink,
accepts only an ordinary stable file below the repository root, and requires
exactly one match. Zero matches, a draft and final together, more than one
numbered final, a malformed or oversized slug, a non-canonical placement, an
unsafe path component, a special file, an oversized file, or a changed read
refuses as H008. The ordinary-walk H009 contract remains unchanged.

A direct path to `docs/decisions/drafts/<slug>.md` remains refused as a bridge
record. Such a path disappears when integration assigns the number. The stable
identity instead survives the existing allocator unchanged before and after
that rename. The existing numbered-ADR and governed-ledger forms remain
accepted, and `decision_assignments.py` retains its current plan, apply, and
replay contract.

Step 1 changes Hypomnema's checker, focused tests, skill contract, and
evolution ledger, then refreshes the committed study and runbook copies.
Hypomnema's skill metadata becomes `5.8.0`; its ledger current version and one
new history row use the literal `hypomnema-v5.8.0` with axis `generation`.
The frontier status remains `open`, the frontier revision remains
`duplicate-home-discovery`, and the frontier digest remains
`74714f68f73e5a2f4394b7f40d55b77055336c76a1665884e279a8325bb9eed3`.
The current frontier and held Next Fiat job remain byte-identical. The row
records only stable design-bridge resolution and does not claim that
repository-wide semantic duplicate-home discovery is complete.

Brevitas adds the explicit `fiat-audit-record` value to its existing `--mode`
interface. It starts from report-mode behaviour but suppresses only B010 and
B011. Every other Brevitas rule remains active, including B002 through B007,
B009, B020 through B027, and B030 when a source is supplied. Auto, answer, and
ordinary report modes retain their current behaviour. This adds no subcommand
and no B012 rule.

The `fiat-audit-record` mode is used only after
`audit_synopsis.py --check .` has accepted the exact audit tree. Brevitas does
not parse a `fiat-audit-round/v1` or `fiat-audit-round/v2` record, establish its
schema, compare its finding count with the controller argument, establish risk
coverage, or establish a receipt. The synopsis checker and `hexctl audit-round`
retain those authorities. The explicit mode only prevents the schema-owned
single H2 record heading and findings table from being rejected by generic
minimum-section and minimum-table-size budgets. It requires no dummy heading,
dummy finding row, or deletion of the audit record from the shipped-prose
gate.

Brevitas's skill metadata becomes `0.4.0`; its ledger current version and one
new history row use the literal `brevitas-v0.4.0` with axis `generation`.
The frontier status remains `open`, the frontier revision remains
`held-engineering-corpus`, and the frontier digest remains
`dcff4f6b1397570468dedb18a1ebaa5f45377272bcd2f71cd69ad6818eeb0b62`.
The current frontier and held Next Fiat job remain byte-identical. The history
row cites issue 453 and the committed study and runbook rather than the
separately owned audit file. The Brevitas plugin package remains `0.2.2`; its
manifests, marketplace records, held corpus, version-propagation test, and
check map remain unchanged.

The runbook's existing three-row `version-relations` block remains
byte-identical. Hypomnema and Brevitas are intentionally omitted and therefore
use the two literal generations above, as Protasis permits for omitted targets.
No concrete version token is added for any relation-declared target. Fiat's
`done resolve-versions` receipt continues to cover only those three declared
targets. If the integration base moves in a way that consumes or changes
either literal next generation, integration revalidation must correct that
ledger row and matching metadata before composition; the three-target receipt
must not be described as covering either literal.

The newly confirmed H008 defect and Brevitas Fiat-audit-record defect are
Warden findings, not additional entries in the immutable
`protasis-known-failure-inventory/v1` object. Their regressions follow Warden
and Elenchus without changing the seven finding ids, their source digests,
their assignments, or their reporter commands.

**Why.** The receipted study omitted the machine-readable design bridge even
though item 12 selected a durable ADR home. That omission is a defect in this
study. A direct numbered path cannot repair it because integration owns the
number, and a direct draft path would dangle after assignment. Pointing at a
governed `EVOLUTION.md` would put a cross-cutting decision in the wrong home
while the ADR already holds it, and append-only history would leave that wrong
home in force after integration.

Hypomnema also has a product defect. Its current authoring contract requires
new ADRs to retain one `adr/<slug>` identity from draft through integration,
but H008 accepts only a concrete numbered ADR path or a governed ledger path.
The stable selector closes that internal contradiction without changing the
allocator, admitting arbitrary draft paths, weakening established record
homes, or rewriting any existing receipt.

The exact Fiat audit record cannot satisfy Brevitas's generic B010 and B011
minimums without padding a host-owned record with false structure. Removing
the audit source from Brevitas would instead breach the repository's
shipped-prose rule. An explicit mode, preceded by the existing authoritative
synopsis check and suppressing only those two generic budgets, preserves the
record bytes and every remaining prose check without duplicating Fiat's schema
inside Brevitas.

**Steps touched.** Step 1's Exit, Files, Tests, and Disciplines.

**Still holding.** Step 1: entry holds; exit broken. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.

### Amendment -- 2026-09-06

**What changed.** Step 2 owns the safe join from the Step 1 Protasis inventory
to Fiat. The read-only inventory module adds one public
`load_checked_inventory` operation. It returns either an explicit absent result
when neither an inventory nor an assignment surface exists, the existing K000
through K012 refusal set, or one closed
`protasis-known-failure-inventory-capture/v1` object after the same bounded
reads and final stability checks as the command-line checker. The capture has
exactly `schema`, `study_sha256`, `runbook_sha256`, `inventory_sha256`,
`source_views`, `findings`, `no_known_findings`, and `assignments`. The
inventory digest is SHA-256 over the parsed inventory in Fiat's canonical JSON
form. Assignments are ordered by Step and finding id. The command-line checker
and Fiat consume this one operation; neither reparses a clean result or
reimplements assignment discovery. An attempted, malformed, or partial
inventory never becomes absent.

The operation retains the current runbook machine surface and immutable
generation map unchanged. Ordinary records remain active, replacement Exit
generations remain source ordered, the first nonempty map stays locked, and the
final generation must repeat the same complete seven-pair map. The strict
bracket, amendment-field, replacement-clause, baseline-Step, fence, and
single-line inline-code rules still apply.

For a runbook that yields a clean capture, `done runbook` stores that exact
capture in its receipt and opens the first Step at `inoculate`; `done push`
opens each later Step at the same phase. `next` gives Mason the current
study/runbook digests, capture digest, consuming Step, exact assigned entries,
allowed guard paths, reporter commands, report formats and logical report
files, exact branch and branch parent, and the fixed controller evidence
directory. A pre-contract state whose runbook receipt has no capture retains
its earlier path without an invented inventory or receipt.

The sole receipt command is `hexctl done inoculate`. It takes no
phase-specific argument. Phase-foreign `done` options refuse before mutation.
The receipt schema is `fiat-known-failure-inoculation/v1` with exactly
`schema`, `step`, `study_sha256`, `runbook_sha256`, `inventory_sha256`,
`step_parent`, `assigned_ids`, `source_views`, `no_known_findings`, and
`guard_manifests`. Assigned ids and manifest references are uniquely sorted.
Each future manifest reference has exactly `finding_id`, `path`, and `sha256`.

For a Step with no assigned finding, Mason writes the fixed
`.hexaemeron/steps/<n>/inoculation/no-known-findings.json` record under schema
`fiat-no-known-findings/v1`. It has exactly `schema`, `study_sha256`,
`inventory_sha256`, `source_views`, `consuming_step`, and `assertion`, with
assertion `no-known-findings-for-step`. Fiat accepts that route only when the
checked capture assigns zero ids, the study and source-view digests agree, and
the file is a bounded stable regular file. Its receipt carries the checked
record and an empty `guard_manifests` list.

For a Step with assigned findings, Step 2 captures and reports the complete
declaration but does not call it evidence. `hexctl done inoculate` remains
refused while `guard_manifests` is empty, and `done implement` remains refused
while the Step has no valid inoculation receipt. Step 3 alone retains reports,
checks manifests and fills the nonempty list. This freezes the command and
receipt shape without allowing an id declaration to authorise product work.

The signed `kf-453-02` guard commit still uses exactly the historical
`plugins/hexaemeron/tests/test_issue_453_inoculation_lifecycle.py` path and the
reporter named by the immutable inventory. After the guard result is retained,
the maintained module is renamed to
`plugins/hexaemeron/tests/test_inoculation_lifecycle.py`, and the reporter is
updated to select that numberless module on the fixed tree. The historical
commit, command and report remain unchanged. Step 2 also changes the reporter,
the public inventory loader and its focused tests, and refreshes the committed
study and runbook to the current receipted bytes. Hypomnema names only the four
tracked `.agents` inputs rather than traversing the ignored generated runtime.

**Why.** The current checker returns only a finding list and discards the
accepted object. A controller that first observes a clean result and then
rereads or reparses the study would lose the stable-read boundary and could
diverge from the locked replacement-Exit projection. The original Step 2 Exit
also calls an assigned id set evidence even though Step 3 owns report retention,
Git binding and verdict admission. That would recreate the pre-edit bypass the
selected design must close. The original Files omit the parser and reporter,
retain an issue-numbered maintained test name, and the original Hypomnema
command crosses into ignored generated state. Its Entry also describes Step 1
as merged even though the stack remains open until integration.

**Steps touched.** Step 2's Entry, Exit, Files, Tests, and Disciplines.

**Still holding.** Step 2: entry holds; exit broken. Step 3: entry holds; exit
holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-06

**What changed.** Step 2's model-execution boundary is explicit. Do not run
`agent_instruction.py measure`, `agent_instruction.py parity`, a tokenizer,
either recorded family adapter, Ollama, or any other model process. The
committed measurement and parity records remain byte-for-byte unchanged and
make no claim about the new inoculation text.

The existing `fiat-study-runbook-phase` reviewed span and semantic fixture stay
unchanged. Remove the proposed `inoculate` row from the measured `## The loop`
table. That table continues to describe the implementation-first route for a
runbook receipt without a known-failure capture. The new capture-aware
exception is documented after the existing reviewed envelope: a clean capture
opens `inoculate`, `done inoculate` is the sole receipt command, and a valid
receipt alone reaches the table's `implement` action. The public controller,
Protasis and Mason contracts still carry the complete new behaviour.

Because the authored additions follow the recorded source envelope, the
reviewed bytes and every semantic node remain fixed while the source file's
whole-file digest changes. Reconcile that digest only with
`python3 scripts/prove_agent_instruction_reconciliation.py reconcile --root .`.
This existing offline operation checks that the reviewed span is still at its
recorded offsets, substitutes the one source digest in the canonical model and
source-span record, derives the compact form with `format`, refreshes the
manifest artefact digests, and rebinds the coverage row. It opens no socket and
runs no model. The canonical model's nodes, bindings, questions and mutations,
the manifest schema and count constants, and the measurement and parity records
must otherwise remain unchanged.

**Why.** The preceding amendment treated a model and measurement run as a
required consequence of adding the lifecycle, despite this run's explicit
disabled boundary. Those calls would invoke the pinned tokenizer and two local
model families; they are neither controller evidence nor needed to prove the
known-failure transition. Keeping the reviewed span unchanged preserves the
existing model's actual authority, while the already governed offline
reconciliation prevents a harmless whole-file digest change from leaving a
stale manifest. This narrows the work without weakening the lifecycle,
inventory, guard, receipt, legacy-state, audit, or fixed-tree requirements.

**Steps touched.** Step 2's Exit, Files, Tests, and Disciplines.

**Still holding.** Step 2: entry holds; exit broken. Step 3: entry holds; exit
holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.
