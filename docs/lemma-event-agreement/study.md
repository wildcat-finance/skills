# Study: Solidity event AST and ABI agreement

Status: design selected; the user authorised the bounded implementation scope on 2026-09-26. Study receipt is not yet recorded. This study reports no product implementation, deployment check or completed issue.

Assumptions, unless corrected:

1. The target is `wildcat-finance/skills` at `df56bfeec3f67bf689d0b083c4994fc329477905`, integration base `main`, in the worktree identified by `issue/16777231-1025915135`.
2. The user approved implementing the generic event validator and validating Wildcat V1/V2 now to unblock the Wildcat work in #1378. The issue still requires every declared venue corpus; that requirement has not been waived.
3. The accepted Wildcat archive is available for private local rebuilding. Its source bytes and accepted release remain unchanged, and its acceptance does not cover another venue.
4. Compiler-derived AST and ABI are two representations from the same pinned compiler. Agreement establishes their checked relation, never deployed log fidelity or compiler honesty.

## 1. Problem, user and proving path

Lemma's event chunks preserve declarations, but `plugins/lemma/chunkers/solidity.py:768` explicitly excludes events from callable comparison. Tabularium and #1378 need checked indexed positions, event identity, ordered parameter types and anonymous status before consuming that metadata.

The existing CLI accepts a synthetic compiler result with one ABI `indexed` bit changed while the AST remains fixed. Both commands exit 0 and write chunks and provenance; their chunks files have the same SHA-256 `acf9e41d5ad8453e8269a4df5643e796d75cfd8766179aa99e815934d7df1345`. The executed report is `/Users/c0rtexzer0/Downloads/lemma-1366-6bOLSX/indexed-probe/report-with-parent.json`. The earlier `report.json` is inconclusive because its output parent did not exist; it supplies no refusal evidence.

A working prototype compares every selected contract, interface and library against its emitted ABI before any corpus delivery. It rejects missing or extra events, overload loss, parameter order/type changes, anonymous changes and every indexed-bit divergence. It also rejects absent or malformed membership/type evidence rather than treating it as an empty inventory.

The demonstration runs the same CLI as production, with a valid `--source-ref`, a precreated output directory, the exact compiler and fresh destinations. The control must succeed. Each single-field mutation must exit nonzero, name the affected event or unsupported shape, and leave neither a new corpus nor provenance. A late failure in a second compilation unit must leave no first-unit delivery. Existing accepted files must retain their original digests after a refused rebuild.

The planned source-owned reporter is `python3 plugins/lemma/tests/emit_issue_1366_report.py --case event-conformance --report .hexaemeron/reports/compiler-membership-full-type-and-refusal-conformance.json`. This command does not exist at entry: inoculation prepares the reporter and parent-failing guard before Step 1. Step 1 adds the minimal event agreement validator, scaffold and specification copies, and closes `kf-1366-indexed-bit` with a passing guard. Step 2 broadens strict wire-type and CLI refusal conformance. Step 3 demonstrates full conformance and rebuilds the accepted Wildcat V1/V2 corpora twice with the successor Lemma binding, checking their event inventories, schema and identifiers. Corpus bytes may change only for a separately explained intended format change; this design adds validation without changing the chunk schema.

On 2026-09-26, the user explicitly approved implementing the generic event validator and validating the accepted Wildcat V1/V2 bundle now, while keeping #1366 open until the seven remaining venue handoffs and rebuilds are complete. The current bounded tranche ends with the generic validator, verified Wildcat outputs and a reviewed deliverable.

The approved staging changes implementation order only. Full issue and integration completion remain blocked until the other venue results pass: Aave V3; Maple V1, V2 fixed-term and V2 open-term; Euler V1 and V2; and Centrifuge V3's hub and corresponding spokes. Their accepted corpus inputs are not present in this study. Source resolution for Aave V3 does not establish corpus acceptance. The Wildcat tranche cannot establish passing results for those missing corpora.

## 2. Prior art and audit history

The entry implementation compiles AST and ABI together at `plugins/lemma/chunkers/solidity.py:525`. `chunk()` builds declarations, resolves inheritance and adds callable surfaces before `build()` returns. `main()` calls delivery only after all compilation units and schema checks pass. `surface_chunks()` checks only concrete contracts with callable lines; adding events solely there would miss event-only contracts, interfaces, abstract contracts and libraries.

`canonical_type()` deliberately preserves source-level names. It is suitable for chunk identities but cannot independently prove ABI wire types: a struct's identity is not its tuple components, a contract encodes as an address, an enum as an integer and a user-defined value type as its underlying type. The event checker therefore needs a separate AST-to-ABI type resolver. Callable return types and mutability remain the held Lemma frontier and stay outside this extension.

The last two merged PRs changing `solidity.py` or its test file were read from GitHub: [#1908](https://github.com/wildcat-finance/skills/pull/1908), merged 2026-09-24, corrects Ariadne parser documentation and preserves the remaining comma refusal; [#1159](https://github.com/wildcat-finance/skills/pull/1159), merged 2026-09-03, removes unused bindings and explicitly leaves its report baseline and false-positive classes outside that change. Keep the comma-refusal guards. No work in either PR authorises a provenance schema change or a dead-code cleanup here.

The in-scope Lemma audit source is `audit/rounds/fiat-409-chunk-corpora-carry-dataset-provenance.md`. The whole-set command `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited 0 over 108 sources with no mismatch. The authoritative Lemma source was read directly because its verified synopsis is still about 90 KB on 12 physical lines. Its 11 rounds retain all finding IDs, statuses, Covered, Not checked, Elenchus verdict and Leads not pursued; they have not been rewritten or promoted to new results.

The fixed finding groups remain fixed historical evidence: `S1-R1-01` through `S1-R1-05`, `S1-R2-01` through `S1-R2-04`, `S1-R3-01`, `S2-R1-01` through `S2-R1-06`, `S2-R2-01` through `S2-R2-04`, `S2-R3-01` through `S2-R3-04`, `S2-R4-01` through `S2-R4-05`, and `S3-R1-01` through `S3-R1-02`. Fix-bearing rounds recorded `inconclusive` Elenchus verdicts; the no-finding rounds recorded `null`. Those historical values are not replaced by this study's observations.

Carry forward the audit's caller rules: one corpus per output directory, source-ref refusal before compilation, the exact diagnostic in refusal assertions, unchanged source/provenance stamping, both chunker suites, and current generated counts. Keep the standing exclusions named: concurrent output-directory writers, two corpora sharing the default provenance name, post-print release-path changes, provenance schema expansion, Markdown directory enumeration and duplicate-unit validation, harmless unused output flags, blank-pin wording and frontmatter-format strictness. The old Ariadne duplicate-key and userinfo leads are superseded only to the extent #1908 reports #1639's fixes; the surviving comma-key ambiguity remains guarded by refusal. These are separate provenance or Markdown boundaries, not reasons to broaden an event-validation patch.

`scripts/emitter_declarations.py` and issue #1361 supply adjacent source-emitter analysis. This design imports no implementation from that tool and makes no runtime-log claim. Its separate audit record is not treated as a Lemma implementation audit. Matches in the #390, #499, #556 and #856 audit logs concern other products, router examples or shared versioning and are not event-check audit sources.

Outside this repository, solc 0.8.25's `ABI.cpp` builds event ABI records from `interfaceEvents()`, while `ASTJsonExporter.cpp` exports that relation as `usedEvents`. `AST.cpp` includes declarations through inheritance plus events reached in the compiler's creation/deployed call graphs. Three local synthetic probes, with 0.8.22, 0.8.25 and 0.8.28, confirm inherited, library and qualified interface event membership. See the pinned sources in section 7 and `.hexaemeron/probes/event-membership.json`.

## 3. Constraints and non-goals

Use Python `3.14.6`, recorded in `.python-version` and verified locally. The probe compilers are `0.8.22+commit.4fc1097e`, `0.8.25+commit.b61c2a91` and `0.8.28+commit.7893614a`; the accepted archive binds their JavaScript compiler and wrapper bytes. Compiler output is untrusted input to the checker even when its binary and version are pinned. Support is decided by the checked AST/ABI shape; a missing `usedEvents`, unresolved ID, malformed boolean or unsupported type must be a named refusal.

The private archive `lemma-1359-wildcat-reviewed-2026-09-26.zip` has SHA-256 `c2933988f0619b2874c5880211ef0f6d3586f3a463515b317ff8a7f609785fe1`, 21,728,910 bytes and 150 members matching the extracted bundle. The controller's baseline report, SHA-256 `49a2add79b21a21bcf3713d6491f95b00e6966de72424760c6c493d48da1d4ed`, rebuilds all 10 Wildcat partitions to 4,209 chunks and the accepted bytes, with 382 event declarations including 249 interface declarations. The bundle's old tool-source binding remains historical; changed-validator runs use an explicit successor tool binding in a new destination. Do not edit the accepted manifest or copy private source into this repository.

Always: preserve unrelated work, validate before delivery, pin inputs and compiler outputs, retain the held frontier, run both Lemma suites plus compiler-backed cases, then use the checked affected-scope runner. Its current `lemma-solidity` entry runs without `--solc`, so it alone cannot establish compiler integration. Regenerate portable copies and both Horos artefacts before a green commit.

Ask first: widening acceptance beyond the decided corpus scope, changing chunk/provenance schemas, adding a dependency, changing CI, publishing private inputs or making a deployment claim. The approved staged scope is recorded in section 1. Preparing evidence and the source-owned guards is our work.

Never: publish private compiler input, rewrite accepted bytes, infer a passing compiler shape from an empty event list, claim all venues from Wildcat coverage, or count a nonzero CLI exit caused by a missing flag/output parent as the intended event refusal.

Non-goals: Solidity source-emitter correctness, Yul log decoding, deployed-bytecode agreement, protocol economics, lender completeness, event retrieval, return/mutability validation, network capture, Ariadne schema changes and concurrent output publication.

## 4. Candidates and selected construction

`declaration-walk` gathers event declarations along `linearizedBaseContracts`. It is smaller, but misses the `Lib` and `External` events included by all three probed compilers and misses externally declared duplicate events. It also has no way to refuse when the compiler's membership field disappears.

`compiler-membership` resolves every ID in each selected contract's `usedEvents` against a compilation-wide AST index, including excluded dependency files. It compares the resolved declaration descriptors with that contract's ABI before chunk construction or output. It needs a strict type resolver and a clear refusal for older or unsupported shapes, but it follows the compiler's event inventory without inventing a call graph.

The complete record is `.hexaemeron/design-evidence.json`. `python3 .hexaemeron/probes/design_selection.py` produced every resolved report from the preserved compiler outputs. Both candidates require zero additional compiler calls after parsing. The probe's largest retained event-reference list is 4 for the declaration walk and 6 for compiler membership. These are measurements of the study algorithms, not product performance claims. `compiler-membership` is the sole surviving candidate under the correctness and missing-membership gates. The design-lock checker exits 0; product type/refusal conformance remains pending at `step:3`.

Implement the selected construction as one validator called by `chunk()` immediately after source selection and before chunk emission. Its own event scope includes selected contracts, abstract contracts, interfaces and libraries, including those with zero callable functions. Build a compilation-wide ID index, but validate only selected owning contracts; imported declarations may still be necessary evidence for their membership. Reject a selected source lacking its expected AST/ABI representation.

Resolve ordered AST parameter types independently into canonical ABI types: elementary types and aliases, array dimensions, tuple component types through struct IDs, contract addresses, enum widths for the supported compiler shape, user-defined value-type underlyings and external function types. Validate `type`, `components` and explicit booleans on the ABI side. Do not trust `internalType` alone: mutating `type` while retaining `internalType` must fail. Detect unresolved and cyclic type references. Bounds on recursive type expansion and diagnostics must be explicit and tested.

The comparison key includes event name, anonymous status and ordered parameter descriptors, with parameter names retained to reproduce compiler multiplicity, canonical wire types, tuple components and indexed flags. Preserve multiplicity: the probe's `Copies` contract has three referenced declarations and three ABI rows, including two with equal names and types. A set would hide a deliberately duplicated ABI row. Use a multiset over complete descriptors; do not collapse by name, selector, source signature or indexed count. No topic hash computation is needed for this agreement check.

Compiler membership is recorded compiler evidence. It includes inherited declarations that never emit, and excludes an unused library event from the caller. It establishes neither reachable execution nor complete deployed logs. The callable checker and existing source-signature IDs retain their own contracts.

## 5. Risks and known failure

```risk-register
event-membership | selected contracts and compilation-wide event ids | cover inherited, library, qualified interface, event-only and empty-event contracts and reject missing membership
event-multiplicity | repeated ABI event descriptors | preserve duplicates and overloads and reject a missing or injected row
wire-types | AST type nodes and ABI type/components | resolve aliases, arrays, structs, enums, contracts and value types independently and reject hidden type mutation
ordered-flags | parameter arrays and explicit booleans | flip every indexed position and anonymous status and reject coercions or reordered parameters
selection-evidence | include patterns and imported AST dependencies | validate selected owners without losing referenced excluded declarations
unsupported-shape | compiler output fields and recursive references | name malformed or unsupported evidence and stop before delivery
partial-corpus | multi-unit build and delivery boundary | reject late event mismatch with no new corpus/provenance and preserve existing accepted files
guard-discrimination | test oracle and real CLI invocation | prove a healthy control and the intended event refusal separately from flag/compiler/output-path failures
private-handoff | accepted source archive and successor output | preserve original digests and keep private input bytes outside Git
scope-claim | Wildcat results and all-venue acceptance | retain every missing venue and block full issue completion until its corpus rebuild passes
performance-bound | event-index and type expansion | measure one compiler-output pass and bound recursion without extra compilation
held-frontier | governed Lemma prose and version ledger | preserve return/mutability frontier while documenting the event extension
```

`kf-1366-indexed-bit` is the new executed study reproduction, not a historical Warden finding. Inoculation must prepare an official source-owned guard before Step 1 that fails on the starting product and proves a healthy control. Step 1 adds the minimal validator and closes the finding with that guard passing only when the event check rejects the changed ABI bit before writing. The guard/report files are planned as `plugins/lemma/tests/test_events.py`, `plugins/lemma/tests/emit_issue_1366_report.py` and a synthetic fixture under `plugins/lemma/tests/fixtures/issue-1366/`. The reporter must emit `unittest-json-v1`; the expected verdict is `guarded`. Its exact finding-specific command is `python3 plugins/lemma/tests/emit_issue_1366_report.py --case kf-1366-indexed-bit --report {report}`. No official guard or Elenchus verdict has run yet.

The closed known-failure inventory binds the truthful study-inspection source and the synopsis generated and checked by the existing renderer, plus their exact digests. Such a source records inspection only; it creates no Fiat audit round or receipt. The runbook must assign `kf-1366-indexed-bit` to Step 1 and check the inventory with that independent expected ID before product edits.

```known-failure-inventory
{
  "schema": "protasis-known-failure-inventory/v1",
  "source_views": [
    {
      "id": "issue-1366-study-inspection",
      "path": ".hexaemeron/study-evidence/audit/AUDIT_SYNOPSIS.md",
      "source_sha256": "5c25885c2e0ac5548a898b09f7959cd3551f8d751bb082bf7f13f2b0b7f851c7",
      "view_sha256": "6325edf1d8c8a8f7a462b5fe199e992d339350be1c87294226a0f08cb0eb1dff"
    }
  ],
  "findings": [
    {
      "id": "kf-1366-indexed-bit",
      "source_ref": "issue-1366-study-inspection: Indexed-bit mutation at the starting product; reproduced production CLI acceptance with AST unchanged",
      "failure": "The production CLI accepts one divergent ABI indexed bit and writes a corpus and provenance instead of refusing the mismatch before delivery.",
      "guard_paths": [
        "plugins/lemma/tests/emit_issue_1366_report.py",
        "plugins/lemma/tests/test_events.py",
        "plugins/lemma/tests/fixtures/issue-1366/event-input.json",
        "plugins/lemma/tests/fixtures/issue-1366/compiler-0.8.25.json"
      ],
      "test_command": "python3 plugins/lemma/tests/emit_issue_1366_report.py --case kf-1366-indexed-bit --report {report}",
      "report_format": "unittest-json-v1",
      "report_file": ".elenchus/issue-1366-indexed-bit.json",
      "expected_guard_verdict": "guarded",
      "green_command": "python3 plugins/lemma/tests/emit_issue_1366_report.py --case kf-1366-indexed-bit --report .elenchus/issue-1366-indexed-bit-green.json",
      "consuming_step": 1
    }
  ],
  "no_known_findings": null
}
```

## 6. Glossary

Event declaration: a source AST `EventDefinition`, preserving ordered parameter metadata.

Event membership: the event declaration IDs solc places in one contract's `usedEvents`.

Wire type: the ABI encoding type after resolving source aliases and user-defined types.

Agreement: equality of the checked AST-derived and ABI event descriptor multisets for one compiler output.

Corpus acceptance: an explicitly scoped handoff decision for exact corpus and input bytes.

## 7. Sources and reproducibility

- [Issue #1366](https://github.com/wildcat-finance/skills/issues/1366) and [accepted #1359 scope](https://github.com/wildcat-finance/skills/issues/1359): snapshots are `.hexaemeron/issue-1366.json` and `.hexaemeron/issue-1359.json`; their digests are in `.hexaemeron/input-observations.json`.
- [Starting chunker](https://github.com/wildcat-finance/skills/blob/df56bfeec3f67bf689d0b083c4994fc329477905/plugins/lemma/chunkers/solidity.py), [tests](https://github.com/wildcat-finance/skills/blob/df56bfeec3f67bf689d0b083c4994fc329477905/plugins/lemma/tests/test_solidity.py), [invariants](https://github.com/wildcat-finance/skills/blob/df56bfeec3f67bf689d0b083c4994fc329477905/plugins/lemma/INVARIANTS.md) and [audit source](https://github.com/wildcat-finance/skills/blob/df56bfeec3f67bf689d0b083c4994fc329477905/audit/rounds/fiat-409-chunk-corpora-carry-dataset-provenance.md).
- [Solidity 0.8.25 ABI event rules](https://docs.soliditylang.org/en/v0.8.25/abi-spec.html#events), [ABI writer](https://github.com/ethereum/solidity/blob/v0.8.25/libsolidity/interface/ABI.cpp), [AST exporter](https://github.com/ethereum/solidity/blob/v0.8.25/libsolidity/ast/ASTJsonExporter.cpp) and [event membership implementation](https://github.com/ethereum/solidity/blob/v0.8.25/libsolidity/ast/AST.cpp).
- [Private accepted handoff](https://github.com/wildcat-finance/miskatonic/blob/fb814e389805d0fceb463c112411f820d4edc03f/storage/r2/handoffs/wildcat-v1-v2-lemma-20260926/README.md): local archive and compiler bindings are recorded in sections 1 and 3; private availability is not public-source availability.
- Study experiments: `python3 .hexaemeron/probes/probe_events.py`, then `python3 .hexaemeron/probes/design_selection.py`. Their outputs live beside those scripts. Both commands ran; neither edits production code.

## 8. Questions and signals

Follow [Ephoros](https://github.com/wildcat-finance/skills/blob/df56bfeec3f67bf689d0b083c4994fc329477905/plugins/hexaemeron/skills/ephoros/SKILL.md).

This is an invoked local command, so no daemon alert or metric service is needed. Its operator must be able to answer which input/compiler/contract failed, whether the mismatch concerns membership, type, order or a flag, and whether any new delivery exists. Step 1's bounded `ChunkError` names the source path, contract and event identity. Step 2 extends strict wire-type and CLI refusal conformance; Step 3's report binds input, compiler, tool and output digests plus the exact exit and file-state result. Successful reports count checked owners and event rows, making an empty denominator distinguishable from a checked empty contract.

## 9. Trust boundaries and controls

Follow [Phylax](https://github.com/wildcat-finance/skills/blob/df56bfeec3f67bf689d0b083c4994fc329477905/plugins/hexaemeron/skills/phylax/SKILL.md).

The added boundary reads compiler JSON: strict field types, bounded diagnostics, checked ID resolution, cycle detection and finite type traversal prevent malformed evidence from becoming success. The existing subprocess remains argv-based with the same pinned executable; no new shell, network, dependency or secret is required. Private standard JSON stays in the verified external bundle. Successor outputs use fresh directories and a separate explicit tool binding. A refused compiler shape remains named in the all-venue report rather than being skipped.

## 10. Performance budget

Follow [Metron](https://github.com/wildcat-finance/skills/blob/df56bfeec3f67bf689d0b083c4994fc329477905/plugins/hexaemeron/skills/metron/SKILL.md).

No wall-clock improvement is promised. The design budget is zero additional solc compilations and one AST index per compilation unit. The probe command measures retained event references after the same compiler output; it does not measure product runtime or peak RSS. Step 3 will record end-to-end duration and output sizes on the same 10 Wildcat partitions, against the preserved baseline, without turning that observation into an unrequested speed target. Any later optimisation needs its own before/after measurement.

## 11. Refusal and guard convention

Follow [Elenchus](https://github.com/wildcat-finance/skills/blob/df56bfeec3f67bf689d0b083c4994fc329477905/plugins/hexaemeron/skills/elenchus/SKILL.md).

Missing inputs block their corpus rebuild and full issue and integration completion. The approved scope permits the generic validator and Wildcat tranche. Missing or malformed compiler evidence blocks that corpus; a mismatch blocks the entire build before delivery. Inspection, input repair and rerunning the exact command remain available. Never overwrite a preserved failed specimen to obtain a clean result.

Each refusal guard names its mutation, passes a healthy control and checks the specific event diagnostic, nonzero exit, absence of new output and preservation of old output when supplied. A passing failure case must not depend on an absent compiler, invalid source-ref or absent output parent. The recorded parent defect must fail under the official assertion before the production fix, and pass afterwards. Handcrafted malformed fields complement real compiler fixtures; they do not substitute for the pinned compiler-shape cases.

## 12. Decisions and their homes

Follow [Hypomnema](https://github.com/wildcat-finance/skills/blob/df56bfeec3f67bf689d0b083c4994fc329477905/plugins/hexaemeron/skills/hypomnema/SKILL.md).

The standing decision belongs in `plugins/lemma/skills/lemma/EVOLUTION.md`: use compiler event-membership IDs and independent wire-type descriptors, reject unsupported evidence, and preserve the held return/mutability frontier. Record the rejected declaration walk and its compiler counterexample there when implementation ships. This is one governed skill's decision, so no competing ADR is needed.

The source explanation and refusal boundary belong next to the new validator and in `plugins/lemma/INVARIANTS.md`; usage and honest limits belong in the canonical Lemma skill. Step 1 commits study/runbook copies to the established documentation tree under the approved scope. The all-venue acceptance requirement and the 2026-09-26 staging authorisation remain separate from the technical design record. No missing venue becomes completed by changing a version or rewriting prose.

## Implementation decision record

The selected compiler-membership design and the rejected inheritance walk are recorded in Lemma's governed ledger. The receipted study above remains unchanged.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | compiler-membership
record | plugins/lemma/skills/lemma/EVOLUTION.md
```
