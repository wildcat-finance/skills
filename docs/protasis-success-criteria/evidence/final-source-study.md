# Settle declared study criteria with recorded command results

Assuming, unless corrected:

1. The user authorised a fresh run for #1273 and the Protasis reopening. The signed starting commit is `eaab110104d186bdd0b1d362dd583a2e72ecc21a`; `main` is the integration branch. The worktree fingerprint is `issue/16777233-660647541`. The discarded older run supplies no receipts.
2. The issue's promise is limited: each accepted criterion names its consuming step and settling Exit command; completion needs recorded execution and a successful result. This proves neither criterion sufficiency nor that the command tests the criterion. A vacuous passing command can satisfy the declaration.
3. The active Fiat controller, version `6.61.1`, stays outside this target in the source distribution. It cannot enforce the successor contract this run builds. A separate disposable run using the new checked-in controller must demonstrate that contract.
4. The interpreter is Python `3.14.6`, exactly as `.python-version` requires. The feature adds no dependency, remote service, credential or model call.
5. #1670's command validation records `operation_ran:false`. That is not execution evidence. #1681 repaired the prerequisite source pins and no-known-findings recovery edge; #1673 and #1674 are closed.

These readings follow the issue, signed reopening and current packet. No design-changing ambiguity remains.

## 1. Problem statement

A maintainer finishing a Fiat run needs to know whether a declared test actually ran. Today study/runbook acceptance does not later join every declared success criterion to an actual successful command result. Protasis owns the declaration; Fiat owns execution custody, receipts and completion.

A working prototype accepts one closed declaration, binds each row to the effective Exit command at its named step, records actual execution, and refuses completion when required evidence is missing, failed or mismatched. Unmarked historical runs retain their old contract without invented declarations or receipts.

The proving path will be `docs/protasis-success-criteria/proof.py`. It must use the new controller in disposable runs and demonstrate success, absent execution, nonzero exit, wrong criterion or step, changed command/source, interrupted execution, checkpoint replay, legacy behavior and a deliberately vacuous passing command. Its readback must identify the controller actually executed. Completion of the outer run is not this proof.

### Accepted success criteria

These are the exact planned step Exit commands. The present controller does not enforce this new fence. The derived runbook must keep this mapping or use an admitted amendment. Feature tests must be included in the full Hex suite before its result is cited for them; a green suite does not prove test sufficiency.

```success-criteria
{
  "schema": "protasis-success-criteria/v1",
  "criteria": [
    {"id":"declared-exit-join","claim":"Closed criteria bind to exactly the effective Exit command at their declared step; malformed or ambiguous joins refuse.","step":2,"command":"python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-2-exit.json"},
    {"id":"observed-execution","claim":"Only controller-observed execution with command, source, step and criterion bindings settles a criterion; inert interface records do not.","step":3,"command":"python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-3-exit.json"},
    {"id":"interrupted-is-unmet","claim":"Startup failure, nonzero exit, timeout, overflow, source drift and an interrupted unsettled attempt remain unmet with bounded reasons.","step":3,"command":"python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-3-exit.json"},
    {"id":"completion-refuses-gaps","claim":"Consuming-step gates, the integration directive and its completion receipt refuse missing, failed, forged or mismatched evidence before authorising their transitions.","step":4,"command":"python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-4-exit.json"},
    {"id":"amendment-custody","claim":"Unrelated amendments preserve exact completed descriptors; deleting, changing or reassigning one refuses, while unbuilt changed descriptors need new evidence.","step":4,"command":"python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-4-exit.json"},
    {"id":"legacy-preserved","claim":"Unmarked historical runs retain their prior verification route with no fabricated criterion or execution receipt.","step":4,"command":"python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-4-exit.json"},
    {"id":"replay-preserves-bindings","claim":"Status, verification and checkpoint replay preserve original command, source and result identity and reject substitution without rerunning the command.","step":4,"command":"python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-4-exit.json"},
    {"id":"bounded-demo","claim":"A separate run of the new controller observes the required refusal cases and permits vacuous success without claiming semantic correctness or criterion sufficiency.","step":5,"command":"python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-5-exit.json"}
  ]
}
```

Several criteria intentionally share one execution of a step command. Record the observation once and name each descriptor it settles. Step 1 is scaffolding and earns no feature-completion claim.

## 2. Prior art

### Merged subject work

The latest two merged PRs changing this subject are [#1681](https://github.com/wildcat-finance/skills/pull/1681) and [#1670](https://github.com/wildcat-finance/skills/pull/1670). Freshly fetched full bodies are preserved unchanged in `.hexaemeron/evidence/pr-1681.json` and `.hexaemeron/evidence/pr-1670.json`.

| Source | Established behavior | Retained boundary |
| --- | --- | --- |
| #1681, merge `1d4e4eebcba1825d0eb3192bf08a6c509bdc0d74`, repair `051addd73685a189cc9a982a43196760c2ae3928` | Reviewed CLI/AST pins and the two precise no-known-findings pending-dispatch recovery windows. Both prerequisites closed. | No general state-mutation escape or execution contract. Old receipts unchanged; adapter adoption still uses the existing amendment path. The earlier failed aggregate report remains evidence. |
| #1670, merge `fd3486012e0e134a2a04ccdf8969619905ace22d` | Full CLI/adapter source identity, original argv roots and inert `operation_ran:false`; private native worker admission and cumulative carryover. | #872, #873, #875 and #878 remain separate programme work: signed launch requests, disposable VM enforcement, trusted adapters and hostile whole-path pilots. |

#1670's other limits remain attributed to that delivery: global metadata and `/dev/null` access; unproved detached-child termination and aggregate resource/scratch ceilings; namespace observations without atomic rollback; native-proof/private-storage replay dependence; possible operator restoration after partial promotion; distinct 64 MiB packet, 2 MiB native-Git, 25 MB provider and 25 MiB reader limits; ASCII paths; and a 30-second acceptance window that is not a total DNS/trickle deadline. Its unexplained SIGTERM and intermittent source-change observations stay unknown. Historical model answers were retallied, not newly generated. Zero suppressions with a degraded analyser did not prove complete analysis. #1273 inherits none of these as a new guarantee.

During study, [#1685](https://github.com/wildcat-finance/skills/pull/1685) advanced `main` to `aea6176b99f0c62c5acfebbbd4029766aadedc5a`. It allows appended amendments to inherited numbered ADRs only when the complete base prefix, mode and path survive; it does not approve their meaning. Hypomnema `5.11.0` and Hex package `1.6.43` need final-sync reconciliation: this starting tree already uses package `1.6.43`. The exact run source and external controller remain fixed. Its body is preserved in `.hexaemeron/evidence/pr-1685.json`.

### Audit history actually read

Before synopsis reading, the exact target's whole-set currency check exited zero for 92 source/view pairs. `.hexaemeron/evidence/audit-currency.log` records that execution. The manifest at `.hexaemeron/evidence/audit-reading-manifest.json` binds seven in-scope views to their source/view SHA-256 values and exact read ranges. `.hexaemeron/evidence/audit-excerpts.json` preserves those rows unchanged, including identifiers/statuses, Covered, Not checked, Elenchus verdict and Leads not pursued. Missing legacy fields remain unknown.

These were verified synopsis reads, not direct reads of the larger source files. Scope: criterion declaration, study/runbook acceptance, command admission, amendments, recovery and completion. The shared-root read covered relevant rows; the other six views were read completely. Unrelated plugin delivery histories are outside scope.

| Authoritative source, read through its synopsis | Retained finding or decision | #1273 disposition |
| --- | --- | --- |
| `audit/AUDIT.md`; view rows 163 to 172, 240 to 248, 254 to 255, 322 to 324, 414 to 415 | Fixed `FSA-S2-R1-01`, `FSA-S2-R1-02`, `FSA-S2-R1-03`: partial amendment writes, broken-step refusal, fence state. Later fixed `S2-R1-01`, `S2-R1-02`: four-space fences and replacement Exit with no command. Installed-controller drift was real. | Reuse bounded parsing; validate before writes; exercise amendments and exact Exit joins. Full CommonMark and semantic quality of prose remain outside the check. |
| `plugins/hexaemeron/audit/AUDIT.md` | Fixed `F01`, `F03`, `F04`, `F05`, `F06`, `F08`, `F09`: fingerprints, malformed JSON/ledger/steps, round limits, titles and reserved receipts. `F10` accepted the hook boundary. | Strict bounded result types and reserved ownership; no hook or single-driver concurrency redesign. |
| `audit/rounds/fiat-453-inject-known-failure-guards-before-productio.md` | Fixed `S1-R1-01`: actual design-record home; `S1-R1-02`, `S4-R1-01`: correct audit prose mode; `S2-R1-01`: test authority. Step 3 found loader-environment injection. Accepted `S4-R2-01`: weak `missing_surface_suite` classification. Accepted `S4-R2-02`: full Hex Elenchus inconclusive under its child-process boundary. | Step 1 publishes the standing draft and explicit bridge. Do not reuse that reporter. Close the executor environment. A full-suite pass is separate from an earned `guarded` verdict. The older proof's post-buffer cap, PATH mismatch, raw OSError, multi-id/resume omissions and authored verdict text are not this feature's evidence. |
| `audit/rounds/fiat-508-restudy-residual-carryover-confinement-and-g.md` | `S1-R1-01` corrected CLI format to `unittest-json-v1`. Fixed `S6-R1-01` exposed the command gate in plain status. Four failures in a parent run did not isolate the status reproducer. | Use the actual CLI format and test plain/JSON readback. Preserve inert validation and the broader worker limits. |
| `audit/rounds/fiat-1264-rebind-runbook-amendments-across-a-study-am.md` | Fixed `S1-R1-01`: Git-less tar snapshots; `S2-R1-01`: duplicate amendment digests after writes; `S2-R1-02`: completed-step handling. Accepted `S2-R2-01`: aggregate state growth outside that feature. | Use Git-backed test snapshots, unique amendment digests and completed history. Bound added result data without claiming a global state-size repair. Split test modules below the source-read ceiling. |
| `audit/rounds/fiat-1086-gate-study-and-runbook-links-before-their-d.md` | Fixed `S1-R1-01`, `S2-R1-01`, `S2-R1-02`, `S2-R1-03`: record homes, fences, mirrors, quadratic scan. `S2-R2-01` remains open: immutable audit prose names an absent stable record. Step 3 corrected proof order, digest disclosure and pointer claims. | Future homes are code paths until published. Preserve frozen audit bytes; the old dangling reference is not a criterion-execution defect. Keep mirrors aligned. A timeout bound is not a throughput claim. |
| `audit/rounds/fiat-608-bind-the-integrate-gate-to-the-sync-receipt.md` | Earlier study/runbook file-home disagreement was unchecked. Integration depends on actual sync/version rows. | Bind declared command/step data only; do not certify every sentence's agreement. Re-read the actual integration base and version projection. |

Parent preflight reported 2,017 root tests passing and a separate full Hex run of 3,345 tests, zero failures/errors, five skips and one expected failure, in 464.81 seconds with twelve workers. A combined run hit Hex's 1,800-second limit with five workers and remains inconclusive. The committed suppression check reported 273 candidates, zero suppressions and degraded analysis. Surveyor did not rerun or relabel these as a new-controller demonstration.

### Known-failure decision

No additional unresolved present failure in this bounded surface needs inoculation before production edits. The listed parser, mutation and binding faults were fixed and guide regression coverage in Steps 2 to 4. #1273's missing feature was not an earlier controller promise. The open immutable-audit reference, accepted reporter weakness, Elenchus process boundary and aggregate-state limit concern unchanged mechanisms and remain excluded above. This is not a claim that the repository has no known faults.

The independent expected finding-id set is empty. Step 1 consumes the source-bound assertion through the existing no-known-inoculation route, including #1681's recovery repair. No guard result is fabricated. This study checks assignment against `.hexaemeron/study-step-topology.md`; Fiat must repeat the check against the complete derived runbook.

```known-failure-inventory
{
  "findings": [],
  "no_known_findings": {
    "consuming_step": 1,
    "source_views": [
      {
        "id": "root-audit",
        "source_sha256": "d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d",
        "view_sha256": "82dc1d43e0fa9ee7a4cd7044aadeeb4049a1980e57943486809bc1d14533d0ee"
      },
      {
        "id": "hex-audit",
        "source_sha256": "8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f",
        "view_sha256": "2e919d920cd952a837bee6069251b710a9543df37514d7248a996d61766138cd"
      },
      {
        "id": "known-guards",
        "source_sha256": "9f502b9a4635c50966602ed73de4b739f5bac29c5bcc6fe60ea6942a1e7ceac4",
        "view_sha256": "7bb90fe87595cb73b27fd890ec3a52a3b43105875ad4386a3877f74cf9790f64"
      },
      {
        "id": "command-records",
        "source_sha256": "47ad26907f9e8e686e2182ec52b8b5334a9f0353f10ff603697980d038785a0e",
        "view_sha256": "88cc98ea65c453e987947add97f6227d76b008d342fdf8fd5decbd4e2c9dc668"
      },
      {
        "id": "study-amendments",
        "source_sha256": "42a71b9f1298e40f21858171c2e58940ef9eba88a2fc21a2ad3b9e4a0e60d806",
        "view_sha256": "78a76684d35d313f92d622ca682c6e6b94c9a7bcee697b53f93dfdfa13f82f60"
      },
      {
        "id": "study-pointers",
        "source_sha256": "5bc607fa5a21df5f742a02f205868ef65bed1c45d432c11a6cb8d421ba6ed19a",
        "view_sha256": "31c1618e5e782789dd874b9822d85619d2396b9e36fd1b473ef98c0b6d124b17"
      },
      {
        "id": "integration-sync",
        "source_sha256": "f74d407497496f4583503a1fe9582aebe5d5ba9f69cbd142048def14e648fc0c",
        "view_sha256": "ab553a1949acbde3a9bcf25359df3648a5260f391cf0de818730e1b31df3f2ec"
      }
    ],
    "surveyor_assertion": "no-known-findings"
  },
  "schema": "protasis-known-failure-inventory/v1",
  "source_views": [
    {
      "id": "root-audit",
      "path": "audit/AUDIT_SYNOPSIS.md",
      "source_sha256": "d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d",
      "view_sha256": "82dc1d43e0fa9ee7a4cd7044aadeeb4049a1980e57943486809bc1d14533d0ee"
    },
    {
      "id": "hex-audit",
      "path": "plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md",
      "source_sha256": "8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f",
      "view_sha256": "2e919d920cd952a837bee6069251b710a9543df37514d7248a996d61766138cd"
    },
    {
      "id": "known-guards",
      "path": "audit/rounds/fiat-453-inject-known-failure-guards-before-productio.synopsis.md",
      "source_sha256": "9f502b9a4635c50966602ed73de4b739f5bac29c5bcc6fe60ea6942a1e7ceac4",
      "view_sha256": "7bb90fe87595cb73b27fd890ec3a52a3b43105875ad4386a3877f74cf9790f64"
    },
    {
      "id": "command-records",
      "path": "audit/rounds/fiat-508-restudy-residual-carryover-confinement-and-g.synopsis.md",
      "source_sha256": "47ad26907f9e8e686e2182ec52b8b5334a9f0353f10ff603697980d038785a0e",
      "view_sha256": "88cc98ea65c453e987947add97f6227d76b008d342fdf8fd5decbd4e2c9dc668"
    },
    {
      "id": "study-amendments",
      "path": "audit/rounds/fiat-1264-rebind-runbook-amendments-across-a-study-am.synopsis.md",
      "source_sha256": "42a71b9f1298e40f21858171c2e58940ef9eba88a2fc21a2ad3b9e4a0e60d806",
      "view_sha256": "78a76684d35d313f92d622ca682c6e6b94c9a7bcee697b53f93dfdfa13f82f60"
    },
    {
      "id": "study-pointers",
      "path": "audit/rounds/fiat-1086-gate-study-and-runbook-links-before-their-d.synopsis.md",
      "source_sha256": "5bc607fa5a21df5f742a02f205868ef65bed1c45d432c11a6cb8d421ba6ed19a",
      "view_sha256": "31c1618e5e782789dd874b9822d85619d2396b9e36fd1b473ef98c0b6d124b17"
    },
    {
      "id": "integration-sync",
      "path": "audit/rounds/fiat-608-bind-the-integrate-gate-to-the-sync-receipt.synopsis.md",
      "source_sha256": "f74d407497496f4583503a1fe9582aebe5d5ba9f69cbd142048def14e648fc0c",
      "view_sha256": "ab553a1949acbde3a9bcf25359df3648a5260f391cf0de818730e1b31df3f2ec"
    }
  ]
}
```

### Organisation and external precedent

Within the organisation's checked-in suite, Ariadne's digest-bound evidence and Fiat's source-bound receipts are the relevant precedents. Neither proves criterion adequacy. No other organisation repository was needed or claimed as reviewed.

[in-toto run](https://in-toto.readthedocs.io/en/latest/command-line-tools/in-toto-run.html) records an executed command and return value beside optional stream data and file hashes. Its optional no-command mode also shows why metadata alone cannot establish execution. This feature adds no in-toto dependency or claim of equivalent signing/isolation.

## 3. Constraints and non-goals

The starting commit is `eaab110104d186bdd0b1d362dd583a2e72ecc21a`; pre-reopening base was `7d9c9844c3ee0242b4b54f37cfb84025582282dd`. `main` names the integration branch, not a substitute starting tree. Protasis starts at `5.12.1`, with open frontier `success-criteria-evidence-join`, held #1273 and reopening digest `ead1097456cde02cbebfe9a1ddee2ada5b98058e19e74935c89e86293f07fd23`. User authority is already preserved. Surveyor neither initialises nor receipts the run.

The current command registry admits literal `python3` and eight scripts: checked runner, Hex runner, Brevitas, Protasis, Imprimatur, Phylax, Ephoros and Hypomnema. It refuses `python3 -m unittest`, arbitrary future scripts and shell composition; only its bounded finite literal loop is supported. A design resolver is a separate evidence operation, not a future custom Exit command.

AST source bindings exclude only the parser-builder body. A new top-level binding in `protasis.py` breaks the old module pin. Even a comment-only CLI change invalidates an old full-byte receipt. `.hexaemeron/evidence/gate-interface-probe.json` records actual scratch-copy refusals: `unregistered-cli-module-bindings` and `gate-receipt-drift`.

Keep runbook Exit and Tests commands on the unchanged Hex and checked runners. They discover the changed feature's tests. The target Protasis module and target adapter can then change/re-pin without changing the fixed external adapter. Do not include direct invocations of the changing Protasis CLI in those fields. Changing a registered runner requires the existing admitted amendment process, not weaker validation or a silent controller swap.

Every step earns a full implement/audit/prose/push loop. The present capture-aware `done implement` also runs root and Hex suites under a closed environment with a 5,400-second timeout, separately from the combined checked runner. Plan for both.

Every step PR changing any `plugins/hexaemeron/` byte, including prose, needs a package increment against that PR's own base. Update both plugin manifests, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `tests/test_version_propagation.py` and `plugins/hexaemeron/tests/test_phylax_model_proxy.py`. A final-only bump is insufficient. Governed skill versions are separate. Root-only Step 1 can avoid a plugin change while publishing the study/decision/scaffold at their proper homes.

Non-goals: semantic correctness, criterion sufficiency, completeness of the declared set, arbitrary shell execution, hostile-host attestation, a new sandbox, broad worker programme delivery, global transaction or state-size repair, rerunning all old commands at integration, frozen-audit repair, CI redesign and retroactive enforcement. A successful execution describes its recorded command and implementation commit; it does not certify later edits or the final tree.

## 4. Design options

### Closed selection

`.hexaemeron/design-evidence.json` holds three candidates, eleven criteria and all 33 cells: eighteen observed selection results and fifteen pending conformance results. `.hexaemeron/selection_probe.py` ran eighteen times; `.hexaemeron/evidence/selection-executions.json` preserves actual argv, working directory, process exit and output. Each report is closed `protasis-design-report/v1` data bound by digest.

These are policy specimens, not the product controller. Their descriptor uses synthetic source values. A real child writes a sentinel and returns zero or seven. The capture model uses an in-process owned-record set: that tests the proposed custody choice, not production ledger security. It also executes a vacuous successful child. Production conformance remains pending.

| Criterion and concern | Controller capture | Producer report | Terminal replay |
| --- | --- | --- | --- |
| Unexecuted result refused; correctness gate | true | false | true |
| Descriptor mismatch refused; correctness gate | true | true | true |
| Launches for one build and two inspections; time metric, minimise | 1 | 1 | 3 |
| Largest sample record; space gate at most 4,096 bytes | 345 bytes | 345 bytes | 345 bytes |
| Legacy state and launch count unchanged; compatibility gate | true | true | true |
| Failed result remains unmet; recovery gate | true | true | true |

`controller-capture` wins `unique-frontier`. `producer-report` offers simpler integration but accepts a fabricated successful report before any child runs, failing a required gate. `terminal-replay` observes execution but launches the command on each inspection: three observed launches instead of one. Controller capture keeps verification read-only at the cost of durable custody and recovery handling. The 345-byte result is one specimen, not a production storage estimate. Invocation count is not a latency benchmark.

### Selected construction

1. **Declaration.** Add a pure `plugins/hexaemeron/skills/protasis/scripts/success_criteria.py` module. Decode exactly one column-zero `success-criteria` fence with schema `protasis-success-criteria/v1`; row fields are exactly `id`, `claim`, `step`, `command`. Reject duplicate keys/ids, unknown fields, unsupported schema, empty strings, wrong types including boolean integers, excessive bounds and ambiguous placement. Use the existing 256 KiB study ceiling and at most 128 criteria.
2. **Exit join.** At runbook admission, use existing effective-step/amendment parsing to join the exact literal command to one executable Exit declaration in its step. Tests-only, wrong-step, superseded, absent or ambiguous duplicates refuse. Reuse the registered command grammar and finite argv limits. Multiple criterion descriptors may share one unambiguous command observation.
3. **Contract marker.** New-controller init records an immutable `contracts.success_criteria` marker in state and the init ledger. State alone cannot add or remove it. An old init without it selects legacy behavior. Accepted declaration bytes, descriptor digests and study/runbook source prefixes use existing receipt custody.
4. **Execution.** Add `run-exit --criterion <id>` during the named implementation step. Require a clean signed committed product source and valid command admission. Execute exact expanded argv without a shell, with the pinned interpreter, closed environment and target context. Settle all descriptors sharing that step command from one observation. Record original argv and resolved executable separately; never import caller-authored success as execution authority.
5. **Result.** Record attempt id, run/init identity, descriptors, step, study/runbook identities, raw command, expanded argv, CLI/adapter digests, product commit/tree, timing, return status and bounded stream counts/digests. Distinguish launch from startup failure. Only an observed completed zero exit without timeout, overflow, source drift or receipt mismatch can settle a criterion. The inert interface record retains `operation_ran:false`; a launch alone is not success.
6. **Bounds and interruption.** Append attempt/result events under existing state/ledger custody. Limit added records to 512 attempts and 4 MiB aggregate canonical result data. Read streams incrementally without retaining raw output; terminate and record unmet above 4 MiB observed on either stream or a 1,800-second attempt deadline. Truncated digests explicitly cover the observed prefix. Validate before completion writes. An interrupted start with no settled result remains unknown/unmet; an explicit retry can observe a new attempt. There is no automatic rerun, invented success, at-most-once side-effect promise or global rollback claim.
7. **Gates.** Before `done implement --commit`, require matching successful evidence for criteria due at that step and that implementation commit. Before `next` emits the integration directive, join every accepted descriptor; repeat the join at `done integrate`. The GitHub merge precedes that completion receipt, so a receipt-only check would be too late. A missing or tampered result must withhold the integration directive. Status and `verify` replay results without running commands. Wrong run, descriptor, step, command, source or ledger prefix refuses. Later audit edits do not turn a historical implementation result into final-tree correctness evidence; existing later test gates remain necessary.
8. **Amendment and restore.** Freeze completed descriptors: removal, reassignment or changed claim/step/command refuses before mutation. Unbuilt rows can change through admitted amendments, then need new matching evidence. Unrelated study amendments preserve exact completed rows through a validated historical chain; comparing old evidence blindly to the newest whole-study hash would break safe amendments. Preserve unique amendment digests and original bytes. Checkpoints carry new evidence under versioned inventory and relative storage paths; original argv stays historical. A new restore root never authorises executing an old absolute path.

Keep new helpers and test modules separate from large existing files. Move CLI source pins, contract/checkpoint fixtures and generated copies with their source changes. These changes do not close older aggregate-state, operating-system or worker boundaries.

### Pending conformance

The record names each exact future resolver and absent report. Commands run from the repository root; for the selected candidate the form is `python3 docs/protasis-success-criteria/proof.py --candidate controller-capture --criterion <criterion> --report .hexaemeron/reports/controller-capture-<criterion>.json`, with literal values in each cell. The future helper does not exist yet. It must execute the named product checks and bind source identity before emitting a report; a placeholder cannot declare success. The resolver is not a runbook Exit command.

| Criterion | Required observed evidence | Stop point |
| --- | --- | --- |
| `design-home` | Step 1 publishes standing draft, study/design records and refusing scaffold; explicit Hypomnema bridge and selection replay pass. | Before Step 2: `step:2` |
| `declaration-contract` | Step 2 checks malformed/duplicate input, effective amendments, wrong step/field and target adapter admission. | Before Step 3: `step:3` |
| `execution-custody` | Step 3 observes launch, failure, interruption, strict source/argv bindings, resource bounds and due-step refusal; supplied and inert reports fail. | Before Step 4: `step:4` |
| `terminal-compatibility` | Step 4 observes withheld integration directives and completion refusal for unsettled or tampered evidence, frozen completed descriptors, exact checkpoint replay and unchanged legacy behavior; inspection launches nothing. | Before Step 5: `step:5` |
| `joined-demonstration` | Step 5 executes the new controller separately, reads back the required positive/negative cases and vacuous success, and reconciles actual integration evidence. | Before integration: `integration` |

Only selected-candidate pending cells become due. Losing alternatives remain unimplemented; no false reports are needed for them. Missing, failed or mismatched due evidence stops the named transition.

### Proposed runbook units

This is an outline for derivation, not a receipted runbook. Each unit needs its own finite Files set, Entry/Exit, Tests, discipline gates and full audit loop.

| Step | Work and file homes | Exit |
| --- | --- | --- |
| 1. Scaffold | Publish `docs/protasis-success-criteria/study.md`, `design-evidence.json`, selection probe/reports and `proof.py` that refuses unimplemented operations. Publish `docs/decisions/drafts/settle-study-criteria-from-recorded-execution.md`. Add root scaffold test and ownership in `tests/check-map-v1.json`. No feature enforcement yet. | `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-1-exit.json` |
| 2. Declaration | Add pure parser, effective Exit join and focused small Hex test file; wire readiness and update only target adapter's reviewed AST pin. Extend proof declaration operation. | `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-2-exit.json` |
| 3. Execution | Add controller marker, bounded executor, attempt/result schema, due-step check, failure/interruption/resource tests and actual child proof cases. | `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-3-exit.json` |
| 4. Completion | Join integration admission and receipt, status/verify, amendments, checkpoint and legacy paths with negative fixtures and proof cases. Preserve the no-known recovery repair. | `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-4-exit.json` |
| 5. Demonstration | Complete the joined new-controller proof and refusal specimens; record actual results and boundaries; update promises/ledgers/frontier and generated copies; reconcile final integration. | `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-5-exit.json` |

The published study/design snapshot keeps report copies under `docs/protasis-success-criteria/reports/`; the active controller consumes `.hexaemeron/design-evidence.json` and its local reports. When a conformance report is earned, copy its unchanged bytes into the matching published report home before checking that published snapshot at the same transition. Never rewrite the controller's historical receipts to make a documentation copy current.

The supporting checked command is `python3 scripts/run_checks.py --scope hexaemeron --jobs 26 --report .hexaemeron/reports/step-N-checked.json`, expanded to a literal step number in the runbook. The interface probe accepted the Step 1 form without running it. Twenty-six is a proposed process budget giving nested Hex twelve workers, not a measured combination. The host reports eighteen CPUs. Keep current timeouts and observe the actual result.

Forecast affected derived files into each step's actual Files set: both plugin manifests/listings and two package expectations; changed governed ledger/header/promises and Hex summaries; generated `.agents/skills/promise-machine/runtime/`; `.horos/boundary.json`; ownership map; source/coverage digest fixtures; relevant checkpoint/contract expectations; and the synopsis after append-only audit records. Do not treat this list as permission for unrelated edits. Run the checked runner, current lints, portable-copy check, source census and every selected owner check on the exact candidate; source identity changes invalidate previous reports.

## 5. Risk register seed

Warden must enumerate each id per round. This register covers the new join and its direct compatibility surfaces; the unchanged programme limits in Section 2 stay excluded.

```risk-register
declaration-shape | untrusted study fence and JSON | reject duplicate keys ids unknown fields wrong types unsupported versions and oversized declarations
exit-identity | criterion to effective amended step | bind exact registered Exit and consuming step and refuse Tests-only superseded absent or ambiguous matches
execution-authority | interface report versus actual run | only controller-observed execution can settle and operation_ran false never counts
source-binding | argv executable CLI adapter and product commit | pin declared identities and reject substitution or tracked source drift
subprocess-input | process environment argv and streams | use no shell pinned runtime closed environment bounded incremental reads and explicit deadline
partial-result | attempt start result ledger and state | interrupted writes stay unmet and retries never fabricate completion or at-most-once execution
amendment-history | descriptors and historical source chain | preserve unique digests and refuse completed descriptor edits before durable mutation
completion-gap | due-step integration directive and completion receipt | enumerate every accepted criterion and refuse missing failed or mismatched evidence before authorising integration or completing
legacy-replay | immutable init marker and old state | marker absence stays legacy with no backfill or state-only activation
checkpoint-context | restored evidence and old roots | preserve recorded bytes and relative storage without executing old roots or treating restore as new execution
resource-growth | added attempts result data and streams | enforce per-run and per-attempt ceilings and keep overflow distinct from success
self-hosting | external controller and target successor | demonstrate new controller separately and preserve registered outer runner and adapter admission
release-copies | package increments and derived sources | update all exact projections and regenerate evidence when identity changes
claim-boundary | successful command and criterion meaning | demonstrate vacuous success without claims of sufficiency semantic correctness or final-tree correctness
```

## 6. Glossary seeds

- **Criterion:** stable id, claim, consuming step and exact command in the accepted declaration.
- **Descriptor:** the closed row whose canonical digest identifies it for the mechanical join.
- **Consuming step:** the step whose implementation completion makes the result due.
- **Exit command:** the exact admitted executable declaration in that step's effective Exit field.
- **Interface record:** source/argument validation that records `operation_ran:false`.
- **Execution result:** controller-owned observation of a command group, its context and outcome.
- **Unmet:** absent, failed, interrupted, oversized, stale or mismatched evidence, without semantic judgement.
- **Legacy run:** a run whose init ledger lacks the new immutable marker.
- **Conformance report:** observed evidence for a selected design obligation at its due transition.

## 7. Sources

Repository links are pinned to the starting commit. Paths elsewhere name local or future homes, not claims that future files already exist. Audit source/view digests and read ranges are in the manifest from Section 2.

- [Issue #1273](https://github.com/wildcat-finance/skills/issues/1273), preserved as `.hexaemeron/evidence/issue-1273.json`.
- [Root instructions](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/AGENTS.md), [Promise Machine](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/PROMISE_MACHINE.md), [router](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/.agents/skills/promise-machine/SKILL.md).
- [Surveyor brief](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/agents/surveyor.md), [Protasis](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/skills/protasis/SKILL.md), [reopening ledger](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/skills/protasis/EVOLUTION.md), [versioning](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/skills/VERSIONING.md).
- [Controller](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/skills/fiat/scripts/hexctl.py), [command adapter](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py), [command reference](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/skills/protasis/references/gate-commands.md), [design checker](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/skills/protasis/scripts/design_evidence.py), [known-failure checker](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py).
- [Root audit view](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/audit/AUDIT_SYNOPSIS.md), [Hex audit view](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md), [#453 view](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/audit/rounds/fiat-453-inject-known-failure-guards-before-productio.synopsis.md), [#508 view](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/audit/rounds/fiat-508-restudy-residual-carryover-confinement-and-g.synopsis.md), [#1264 view](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/audit/rounds/fiat-1264-rebind-runbook-amendments-across-a-study-am.synopsis.md), [#1086 view](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/audit/rounds/fiat-1086-gate-study-and-runbook-links-before-their-d.synopsis.md), [#608 view](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/audit/rounds/fiat-608-bind-the-integrate-gate-to-the-sync-receipt.synopsis.md).
- [Checked runner](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/scripts/run_checks.py), [Hex runner](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/tests/run_tests.py), [package release gate](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/scripts/plugin_release.py).

## 8. Signals, and the questions behind them

[Ephoros](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/skills/ephoros/SKILL.md) owns signals. A local controller needs no new external alert service, but its operator needs four answers:

| Question | Signal and producer |
| --- | --- |
| Why can this step or run not finish? | Steps 3 to 4 expose criterion id, due step, bounded unmet reason and expected descriptor/command in plain status and JSON verification. |
| Did the command run, fail to start or stop halfway? | Step 3 records attempt start, launch state, outcome, elapsed time, return/termination reason and bounded counts/digests. Missing settled results remain visible. |
| Which source and command produced the result? | Steps 3 to 4 expose run/init, implementation commit/tree, source receipts, descriptor and CLI/adapter digests, original and resolved argv. |
| What can be retried after amendment or restore? | Step 4 distinguishes legacy absence, pending attempts, changed unbuilt rows and frozen completed rows; names recovery without running commands from status. |

Use bounded reason codes and ids, not raw output, credentials or unbounded exceptions. Recorded counts, observed bytes and elapsed values suffice; no new metrics service is required. Step 5 checks plain and JSON readback.

## 9. Boundaries, per capability

[Phylax](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/skills/phylax/SKILL.md) owns security review.

| Boundary | Asset and control |
| --- | --- |
| Study/runbook to declaration | Completion obligations: strict bounded parsing, exact effective Exit join and existing pointer/amendment checks. |
| Declaration to process | Execution authority: reviewed CLI/AST, pinned interpreter, argv arrays, no shell, closed environment and bounded streams/deadline. This does not sandbox the admitted tests' own children. |
| Process result to record | Evidence custody: only controller observations count; bind original inputs/source, preserve failures and refuse imported success. |
| Files/state/ledger to verification | Completion authority: bounded stable regular-file reads, safe paths, strict types/digests, reserved fields and historical ledger join. No state-only activation or atomic filesystem guarantee. |
| Amendment/restore to history | Old evidence: freeze completed rows, keep unique source chains and versioned checkpoint inventory, and give historical roots no new execution authority. |

No network access, credential acquisition or dependency is required by the feature. Admitted tests may already hold broader repository capabilities; #1273 does not prove hostile-code confinement. Tests use disposable repositories with closed environments. Secrets and raw process output do not belong in public evidence.

## 10. The budget, or its absence

[Metron](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/skills/metron/SKILL.md) owns measurement. There is no throughput-improvement claim. The selection metric counts launches, not production speed.

Proposed bounds: 128 criteria in the existing 256 KiB study; 512 attempts and 4 MiB canonical new result data per run; 4 MiB observed per output stream and 1,800 seconds per attempt. Cap-minus-one, cap and cap-plus-one cases must distinguish refusal from success. Inspect incremental reads to exclude the older post-buffer-cap failure. Existing finite argv expansion bounds stay in force.

The exact future measurement command is `python3 docs/protasis-success-criteria/proof.py --candidate controller-capture --criterion execution-custody --report .hexaemeron/reports/controller-capture-execution-custody.json`. It must observe boundary cases and preserve supporting counts, bytes and elapsed values before emitting conformance. The registered Step 3 Exit runs the owning tests. No such production report exists yet.

Plan for the measured 464.81-second standalone Hex run and the inconclusive 1,800-second nested run, plus `done implement`'s separate capture suites and 5,400-second timeout. Proposed checked-runner `--jobs 26` remains unmeasured. These facts do not authorise weaker checks or changed timeouts. Investigate a timeout and rerun on the same candidate before drawing a conclusion.

## 11. The fail-closed posture

[Elenchus](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/skills/elenchus/SKILL.md) owns triage and causal guards. A malformed declaration, absent Exit, unregistered source, missing/failed/interrupted result, changed binding, overflow, ledger mismatch or unearned due report stops its dependent transition. Name what is missing, the checked artifact and one corrective action. Inspection, repair and safe exit remain available.

The runbook must name `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}` and the actual CLI format `unittest-json-v1`, with a fresh relative report path for each step. `elenchus.unittest.v1` is not the CLI format name. A future custom reporter gains no admission from being mentioned here.

For an observed implementation failure, preserve the input and failing bytes, reproduce the named failure on its parent, isolate a causal test, fix the cause, and run the fixed-tree check. Separate declaration, execution and terminal/legacy test modules. Fixed historical faults motivate regression coverage; they do not justify fabricated current parent executions.

Full Hex can remain inconclusive under Elenchus's no-child-process boundary; #453's accepted old reporter-classification weakness also remains. Do not promise `guarded` before observing it. A normal suite pass or several unrelated parent failures cannot substitute. If the declared gate cannot earn its verdict, stop and use existing recovery or an admitted amendment, preserving inconclusive evidence.

Writes stay in the target or explicit disposable proof roots. Unexpected source-pin drift, derived changes or a moved integration base need their owner's amendment/sync path. Keep the external controller fixed; never repair controller state by hand.

## 12. Decisions and their homes

[Hypomnema](https://github.com/wildcat-finance/skills/blob/eaab110104d186bdd0b1d362dd583a2e72ecc21a/plugins/hexaemeron/skills/hypomnema/SKILL.md) owns placement. The cross-skill custody choice belongs in `docs/decisions/drafts/settle-study-criteria-from-recorded-execution.md`. Its prepared content is `.hexaemeron/decision-draft.md`; Step 1 publishes that one standing home. No ADR number is allocated. It records the chosen and rejected candidates, historical-result limitation, immutable marker, amendment policy and recovery cost.

The bridge below uses a stable selector that survives number assignment. Its intended standing home is not yet established: this packet permits only `.hexaemeron` writes. Ordinary study pointer readiness and explicit study-mode bridge readiness are separate. The explicit bridge must pass after Step 1 publishes the draft, before that step's prose receipt and before Step 2. A missing home now remains pending, not a clean bridge result.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | controller-capture
record | adr/settle-study-criteria-from-recorded-execution
```

Protasis's declaration promise and frontier closure belong in its existing `SKILL.md` and `EVOLUTION.md`. Fiat's execution/completion contract belongs in its own governed documents and ledger. Protasis's held frontier is exactly #1273: successful closure earns an evolution row, projecting `6.12.1` from this signed opening, subject to the end-of-run material-improvement judgement and actual integration state. A generation-only relation would incorrectly preserve the held job. The current controller supports the generation relation only; use an explicit Protasis frontier target if needed. Supporting Fiat behavior may use `next-generation-after-integration-base`. Do not confuse per-PR package increments with either skill relation.

The checked demonstration and operator examples live in `docs/protasis-success-criteria/`. Interface fields/errors stay next to the Python schemas; existing controller recovery documentation owns unmet-result recovery. Audit records stay append-only, with regenerated synopses and source pins when required. Avoid a parallel record scheme or duplicate semantic decision.

Before integration, fetch the actual base, bring #1685 and relevant intervening changes through ordinary signed sync, rerun source-bound checks, reconcile package/skill projections and let the existing decision-assignment owner allocate a number from that exact base. Its acceptance proves an object transformation, not agreement with this design. Five pending conformance checks and the actual new-controller demonstration remain required after design lock.
