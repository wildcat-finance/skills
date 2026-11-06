# Pinned compiler event membership

Assuming, unless corrected: this run repairs #1983 under the user's explicit Fiat instruction. Python is 3.14.6. The accepted Wildcat tranche stays accepted, and broader #1359/#1366 venue delivery remains separate. Only the two demonstrated compiler build identities may use missing-membership compatibility. The held return/mutability frontier stays unchanged.

## 1. Problem statement

Lemma rejects valid Solidity event evidence from `0.8.10+commit.fc410830` and `0.8.19+commit.7dd6d404` because their contract ASTs omit `usedEvents`. This blocks the Aave V3 corpus work. The same minimal input passes under `0.8.22+commit.4fc1097e`. The prototype must accept the two exact legacy builds through independently reconstructed AST membership while retaining #1366's event descriptor checks and all existing modern refusals.

Success has four checks. The new guard must fail by assertion on the parent and pass after repair. `python3 plugins/lemma/tests/emit_issue_1983_report.py --case production-conformance --report .hexaemeron/reports/pinned-inheritance-production-conformance.json` must report true from executed production tests. `python3 scripts/run_checks.py --scope lemma --scope root` must pass. The final demonstration must run the real CLI with the three pinned compilers and retained Aave set-001/set-034 inputs, then record exact commands, compiler/input/tool digests, exits and output effects in `docs/lemma-compiler-membership/validation.md`. A successful command establishes its stated observation only.

The final demonstration uses the Fiat controller pinned by this run and the production command `python3 plugins/lemma/chunkers/solidity.py`, with explicit `--input`, `--solc`, `--expect-solc`, `--include`, `--source-ref` and `--out` operands. Positive observations cover successful old builds and the modern control. Negative observations cover late-unit descriptor disagreement, unsupported compiler identity and missing modern membership, with fresh and existing output destinations. No observation establishes complete source or runtime fidelity.

## 2. Prior art

`plugins/lemma/chunkers/solidity.py` already indexes all compilation ASTs, resolves event wire types independently and compares descriptor multisets before output. `build()` observes the compiler version once before compiling units; that observed value must reach membership selection. `validate_event_agreement()` currently requires `usedEvents` for every selected contract, interface and library. The accepted modern algorithm stays intact.

The last two merged subject PRs read were [#1946](https://github.com/wildcat-finance/skills/pull/1946) and [#1941](https://github.com/wildcat-finance/skills/pull/1941). Their exact bodies and file lists are retained in `.hexaemeron/evidence/study/`. They delivered the event validator and twice-rebuilt all 10 accepted Wildcat partitions; #1946 expressly limits its integration to that tranche. This study carries the remaining seven venue results under #1366, corpus handoffs under #1359, callable return/mutability work under #388 and suite-list drift under #1942. None is closed by #1983.

The in-scope historical audit source is `audit/rounds/fiat-1366-validate-solidity-event-ast-and-abi-agreeme.md`, read through its checked sibling synopsis and directly for the later rounds. The whole-set `audit_synopsis.py --check .` passed before reading; its exact output is retained in `.hexaemeron/evidence/study/audit-synopsis-check.txt`. There is no Lemma-local audit directory. Root `audit/AUDIT_SYNOPSIS.md` has no Lemma record. The older #409 provenance audit concerns unchanged provenance and capture flags; it supplies adjacent context rather than a new event-membership obligation. Other audit search hits concern unrelated skills and delivery machinery.

All six #1366 findings remain fixed: `S1-R1-01` rejects all 65 Unicode Cc controls; `S1-R1-02` adds discriminating refusal coverage; `S2-R1-01` rejects unsupported external-function signature tags; `S2-R2-01` covers the remaining type-refusal branches; `S3-R1-01` states the Wildcat-only integration decision; `S3-R2-01` corrects the shipped wire-type ledger description. The source's eight rounds retain their Covered sets, Not checked fields, Elenchus verdicts and Leads not pursued. Their verdicts in order are `guarded`, `null`, `guarded`, `passed`, `null`, `unguarded`, `passed`, `null`. No historical verdict is reclassified here.

Carryover dispositions from #1946 remain: broad captured-guard assertions, diagnostic truncation and source-path control characters need no change here; selected diagnostic ordering was repaired; overload-pairing diagnostics remain refusal-safe; the six omitted conformance-list tests run in the full event suite. Private driver custody, recompilation-only compiler-output comparison, the copied conformance report and previous anonymous-flip coverage retain their recorded limits. Deployed-log fidelity, historical step-PR wording and pre-existing comments remain outside this repair. The new suite must run every event test, so the narrower old conformance list cannot silently omit a regression.

Outside this repository, solc's `ContractDefinition::interfaceEvents()` in the exact legacy sources walks `linearizedBaseContracts` and direct event declarations, retaining the first external signature. The corresponding ABI generator uses that list. The retained compiler source and the synthetic probe show that old owners omit an emitted library event from their ABI while 0.8.22 includes it. Applying this inheritance policy to every compiler would therefore weaken modern validation. Sources: [0.8.10 AST.cpp](https://github.com/argotorg/solidity/blob/v0.8.10/libsolidity/ast/AST.cpp), [0.8.19 AST.cpp](https://github.com/argotorg/solidity/blob/v0.8.19/libsolidity/ast/AST.cpp).

## 3. Constraints and non-goals

Starting `main` is `25e1e74cdf312cc4c2603b420f901fa0bd4f2a3d`. The run worktree is `issue/16777231-1113638758`. Use Python 3.14.6 and the existing checked runner. Preserve the user checkout and the separate #1359 run. Read retained input evidence there without changing it; write demonstration outputs only beneath this run's private evidence directory.

Always preserve AST/ABI independence, source bytes, chunk IDs, schema, explicit refusals and accepted outputs after failure. Ask first for a new compiler identity, source-rights boundary or scope that closes another issue. Never infer missing membership from ABI rows, widen to all older compiler versions, add a compiler process merely to validate events, weaken modern missing-`usedEvents` refusal, publish private corpus bytes or claim deployed-log agreement.

The allowed identities are exactly `0.8.10+commit.fc410830` and `0.8.19+commit.7dd6d404`, with only explicitly tested official platform suffix forms accepted. A matching patch number or partial hash is insufficient. Unknown, malformed or absent version evidence refuses when `usedEvents` is absent. A present but malformed `usedEvents` value refuses even for a legacy identity. Direct validator calls without a version retain strict behavior; `build()` carries its already observed version to every `chunk()` call. Standalone `chunk()` callers may provide that explicit observation; they receive no inferred compatibility mode.

No chunk-schema change, new dependency, network access, compiler download, deployment, callable return/mutability work, broad corpus release or revalidation of all seven venues belongs to this run. The compiler reports its identity; this does not prove the executable honest. Demonstration separately checks the retained compiler digests.

## 4. Design options

`pinned-inheritance` keeps `usedEvents` as the normal route and adds one route for the two exact legacy identities when the field is absent. Resolve each selected owner's compiler linearization through the compilation-wide AST index, including excluded dependencies. Each base must be a contract definition with a valid direct node list; require a nonempty, unique, bounded integer linearization beginning with the selected owner. Reject unresolved references, wrong node kinds and malformed event declarations. Preserve first declaration order by external signature. This accepts the observed old compiler outputs while introducing a narrow policy whose correctness needs hostile fixtures.

The signature key contains event name and recursively rendered canonical wire types. It excludes parameter names, component names, indexed flags and anonymous status. Those fields remain in the retained descriptor and the final multiset comparison. Arrays retain dimensions; tuple components contribute their wire types in order. Reuse the existing independent AST resolver without reading ABI fields. Bound all repeated base/declaration visits across the compilation, as well as per-list lengths and existing type-expansion limits. The compatibility route must not write fabricated `usedEvents` into the compiler output.

`strict-used-events` leaves the current algorithm unchanged. It avoids an additional membership policy but continues refusing both demonstrated valid legacy builds, so it fails the required three-compiler acceptance criterion.

`.hexaemeron/evidence/study/design_probe.py` executed both constructions over retained public compiler outputs. The selected prototype accepted all three healthy outputs; strict membership accepted only the modern output. Both refused three indexed-bit corruptions, missing modern membership and an unknown version. The selected experiment inspected at most 10 declaration occurrences and ran zero compiler subprocesses. These are bounded prototype measurements, not production conformance or performance claims.

`.hexaemeron/design-evidence.json` has two candidates, six criteria and 12 cells across correctness, time, space, compatibility and recovery. The zero-extra-compiler-call metric supplies the comparison; the acceptance gate excludes the strict candidate. `design_evidence.py --transition design-lock` computes `pinned-inheritance` as the unique surviving frontier. Production conformance remains pending at `integration`, with its exact reporter command and future report path. The checker consumes due pending evidence only for the selected candidate; the rejected strict candidate needs no implementation or conformance report. Two steps suffice: scaffold and guarded repair, then compiler/CLI demonstration and final evidence.

## 5. Risk register seed

```risk-register
compiler-identity | version observation and fallback selection | accept only the two exact tested identities and suffix policy; unknown and absent identities refuse
membership-independence | AST expectation versus ABI observation | derive membership and signatures without using ABI rows or internalType
legacy-signature | inherited first-definition selection | deduplicate by canonical external signature while retaining the first complete descriptor
modern-membership | existing usedEvents path | preserve qualified library events, multiplicity and every modern missing/malformed refusal
base-evidence | compiler linearization and excluded dependencies | refuse absent, repeated, wrongly typed and excessive base/declaration evidence
bounded-traversal | repeated base scans and type expansion | cap aggregate visits and preserve existing list, recursion and text bounds
whole-build-output | multi-unit validation before delivery | late mismatches write nothing and preserve existing corpus/provenance bytes
regression-guards | old valid input and malformed modern control | parent failures are assertions for the intended compatibility defect, with healthy controls
private-input-custody | retained Aave evidence and public artifacts | keep private bytes outside Git and bind demonstration inputs, tools and outputs by digest
claim-boundary | issue and corpus status | close only the demonstrated compatibility repair and preserve #1359/#1366 obligations
```

The new study finding is `kf-1983-legacy-membership`. The inspection source and generated synopsis below record the executed parent failures without creating a Fiat audit round. Inoculation must supply a source-owned reporter and tests before Step 1; the expected parent result is assertion failure with no runner error or skip. The guard uses retained public outputs for both old builds and the 0.8.22 healthy control. Historical fixed findings are regression obligations, not new parent failures.

```known-failure-inventory
{
  "schema": "protasis-known-failure-inventory/v1",
  "source_views": [
    {
      "id": "issue-1983-study-inspection",
      "path": ".hexaemeron/study-evidence/audit/AUDIT_SYNOPSIS.md",
      "source_sha256": "2b0235c62a413ccc6343a4f99a6941c82c70b00c57ddafb6abfc8265fd04188e",
      "view_sha256": "98ac4c7fd5bfde38f4a7bae8d1db9dfbc1f4edac7b76f9b1b314aebb6b9d98c5"
    }
  ],
  "findings": [
    {
      "id": "kf-1983-legacy-membership",
      "source_ref": "issue-1983-study-inspection: Study reproduction for exact legacy compiler omission at the starting product",
      "failure": "The production CLI refuses valid event-bearing compiler output for exact solc 0.8.10 fc410830 and 0.8.19 7dd6d404 because usedEvents is absent.",
      "guard_paths": [
        "plugins/lemma/tests/emit_issue_1983_report.py",
        "plugins/lemma/tests/test_legacy_events.py",
        "plugins/lemma/tests/fixtures/issue-1983/membership-input.json",
        "plugins/lemma/tests/fixtures/issue-1983/compiler-0.8.10.json",
        "plugins/lemma/tests/fixtures/issue-1983/compiler-0.8.19.json",
        "plugins/lemma/tests/fixtures/issue-1983/compiler-0.8.22.json"
      ],
      "test_command": "python3 plugins/lemma/tests/emit_issue_1983_report.py --case kf-1983-legacy-membership --report {report}",
      "report_format": "unittest-json-v1",
      "report_file": ".elenchus/issue-1983-legacy-membership.json",
      "expected_guard_verdict": "guarded",
      "green_command": "python3 plugins/lemma/tests/emit_issue_1983_report.py --case kf-1983-legacy-membership --report .elenchus/issue-1983-legacy-membership-green.json",
      "consuming_step": 1
    }
  ],
  "no_known_findings": null
}
```

## 6. Glossary seeds

Membership means the declarations included in one compiler-produced ABI. A legacy identity means one of the two exact builds admitted here. External signature means event name plus ordered canonical parameter wire types. Descriptor means that signature plus names, anonymous status, indexed flags and nested component detail. A recorded compiler version is its own reported string, not an attestation about executable bytes.

## 7. Sources

The issue is [#1983](https://github.com/wildcat-finance/skills/issues/1983); the parent obligations are [#1366](https://github.com/wildcat-finance/skills/issues/1366) and [#1359](https://github.com/wildcat-finance/skills/issues/1359). The retained public study inputs, outputs, compiler-source copies, reproduction logs and command record live in `.hexaemeron/evidence/study/reproduction/`. The starting implementation is [solidity.py](https://github.com/wildcat-finance/skills/blob/25e1e74cdf312cc4c2603b420f901fa0bd4f2a3d/plugins/lemma/chunkers/solidity.py), with `plugins/lemma/INVARIANTS.md` and `plugins/lemma/tests/test_events.py` defining the existing event checks.

The private Aave source root is the separate #1359 run's `.hexaemeron/evidence/aave-admission/`; `compiler-probe/` holds the verified launchers and exact compilers. The original parent reproduction at `/private/tmp/lemma-1983-reproduction-20260929` has been copied into this run for custody. Its two full Aave failure reports name set-001 and set-034. No claim relies on a fresh network capture of those inputs.

## 8. Signals, and the questions behind them

Follow `plugins/hexaemeron/skills/ephoros/SKILL.md`. Which compiler policy ran? The recorded compiler version plus explicit named failure distinguishes legacy omission from an unsupported identity. Which relation failed? Existing bounded diagnostics name the owner and event disagreement; new failures name legacy base/membership evidence. Was any output changed? The CLI's refusal statement and output digest checks answer this. No background service, metric collector or alert is introduced.

## 9. Boundaries, per capability

Follow `plugins/hexaemeron/skills/phylax/SKILL.md`. Compiler output remains untrusted structured input: reject malformed identity, AST, reference, list and type fields before comparing descriptors. Compiler invocation remains existing argv-based execution. Private input paths are read-only evidence; generated outputs have separate destinations. Reject before delivery so a malformed later unit cannot replace a previously accepted corpus. No new secret, network or executable-loading boundary is opened.

## 10. The budget, or its absence

Follow `plugins/hexaemeron/skills/metron/SKILL.md`. No speed improvement is claimed. Existing limits remain: 1,000,000 AST containers, 100,000 entries per list, type depth 64, 1,000,000 type expansions, 4,096 type-text characters, 256 name characters and 400 diagnostic-context/reason characters. Add an aggregate legacy membership visit cap of 1,000,000 occurrences, including repeated bases. The design probe's 10 visits are a fixture observation only.

Tests must count compiler invocations through the production build and require one existing version query plus one compilation per input. Boundary tests lower the visit cap to exercise equality and one-past refusal. The final demonstration records elapsed time and bytes for its named inputs without inferring variance or a speed claim.

## 11. The fail-closed posture

Follow `plugins/hexaemeron/skills/elenchus/SKILL.md`. Unknown compiler identity, absent modern membership, present malformed membership, inconsistent inheritance evidence, unsupported types, bound exhaustion and descriptor mismatch stop the build before output. No fallback reads ABI rows to fill a gap. Recovery restores the named missing evidence or selects a supported pinned compiler and reruns the complete build into a fresh destination.

The new reporter runs parent-failing assertions and a healthy modern control for `kf-1983-legacy-membership`, returning `unittest-json-v1`. Its `production-conformance` case produces the required Protasis boolean report only after all named tests execute without failure, error or skip. That case binds candidate `pinned-inheritance` and criterion `production-conformance` to the executed production checks; it cannot take a candidate label from the report filename or relabel evidence for the rejected construction. Cover direct/inherited/excluded-dependency events, anonymous and overloaded events, duplicate external signatures with differing metadata, nested tuples/arrays, emitted library differences, version boundaries, malformed bases and aggregate exhaustion. Retain the existing #1366 event, Markdown and compiler-backed Solidity suites. A negative case must fail for its intended event reason, never an absent compiler, invalid source ref or missing destination parent.

## 12. Decisions and their homes

Follow `plugins/hexaemeron/skills/hypomnema/SKILL.md`. The selected `pinned-inheritance` decision belongs in `plugins/lemma/skills/lemma/EVOLUTION.md`: exact legacy identities, first external-signature selection and the retained strict modern route. Record the rejected universal inheritance route and strict-refusal alternative there. Preserve the held return/mutability frontier. A governed generation update records this changed validation contract; package-version propagation follows the repository's release check.

Step 1 commits this study and its derived runbook under `docs/lemma-compiler-membership/`, describes the behavior in the canonical Lemma skill and S8, and records the decision bridge once the ledger entry exists. Step 2 writes the bounded demonstration record there. Generated reports and controller receipts stay in `.hexaemeron/`; public synthetic fixtures may be committed, private source/corpus bytes may not.

## Standing decision

```design-bridge
schema | hypomnema-design-bridge/v1
decision | pinned-inheritance
record | plugins/lemma/skills/lemma/EVOLUTION.md
```
