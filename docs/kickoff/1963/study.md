# Issue 1963 study: Wildcat V1 entry points and event linkage

Assuming, unless corrected:

1. This is the historical V1 map requested by [issue 1963](https://github.com/wildcat-finance/skills/issues/1963). It needs one admitted V1 estate, with component-specific source bindings. It needs no upgrade candidate or V2 comparison.
2. The accepted V1/V2 corpus archive remains private. This delivery publishes V1 source identifiers, digests, locations and analysis. Raw archive members, compiler inputs, compiler outputs and corpus text remain in ignored local research. A quotation is publishable only after a public V1 source independently supplies the same bytes.
3. The accepted registry and corpus define the historical estate. Their source exceptions and deployment-evidence limits survive this map. No new chain read, deployment claim or source-to-bytecode claim is needed.
4. The controller remains pinned to Skills `1f772fc01bb50c90fe0f254fec8ed088fbe6ab13`. Python 3.14.6 and Node.js v26.6.0 are available. The accepted archive contains the pinned solc-js 0.8.22 compiler. No package installation is required.
5. Independent semantic review means a reviewer other than the linkage producer reads the selected source and reviews the final linkage digest. A schema check cannot supply that judgement or authenticate the reviewer.

## 1. Problem statement

Tabularium needs the V1 callable denominator and the function-to-event relations missing from the completed V2 work. Produce a separate `docs/kickoff/1963/` bundle for [issue 1378](https://github.com/wildcat-finance/skills/issues/1378) and [issue 1387](https://github.com/wildcat-finance/skills/issues/1387). A working prototype is one complete V1 source inventory, independently derived callable inventory, current X-Ray report set, reviewed semantic linkage, and an offline checker that rejects the named omissions and contradictions.

The scope has seven concrete runtime or creation contexts: `WildcatMarket`, `WildcatMarketController`, `WildcatMarketControllerFactory`, `WildcatArchController`, `WildcatSanctionsSentinel`, `WildcatSanctionsEscrow` and `MarketLens`. Escrow is a creation target reached through the sentinel. Its presence does not invent a deployed escrow census. Abstract bases, interfaces and libraries remain in the source inventory and contribute inherited declarations or transitive effects; they are not counted as separately deployed contracts. External ERC20 tokens, Chainalysis, SphereX engines and an arbitrary controller selected at runtime remain external dependencies with named limits.

The accepted V1 catalog has 16 registry entries, including seven markets, three controllers and two init-code storage entries. Those address and storage counts differ from source-context counts. A fresh study probe compiled the four accepted V1 inputs for AST and ABI only. Their selected ABIs contain 68 state-changing or constructor entries and 148 read entries. `WildcatMarket` has no ABI constructor row, so AST/source analysis must add its implicit creation path and inherited constructor effects. These are reconnaissance counts; the final checked denominator owns its exact totals.

The public bundle contains `sources.json`, `denominator-inputs.json`, `actions.json`, `linkage.json`, `review.json`, `manifest.json`, execution records, and the five X-Ray outputs: `x-ray.md`, `entry-points.md`, `invariants.md`, `architecture.json` and `architecture.svg`. A short README gives reproduction and recovery commands. The source manifest separates admitted inclusions, dependencies and exclusions. `denominator-inputs.json` preserves the public callable-signature and creation projection with compiler/source identities, independently of the authored linkage. It contains no copied private source text. Its derivation records retain the exact original and prepared compiler-input digests, compiler identity, output digest and command.

One action identity includes input identity, concrete context, canonical signature and creation/callable kind. Read paths remain enumerable. Every state-changing or creation action has exactly one `mapped`, `conditional`, `eventless` or `unresolved` disposition. A linkage row records guard and role evidence, source locations, state effects, asset/value flows, direct and transitive event relations, conditions, dynamic callees and uncertainty. An unknown does not become an eventless result. The required flow families are funding, token transfers, borrowing, repayment, fee movement, withdrawal queueing, batch funding, execution, sanctions, escrow release, closure and administration. `DebtRepaid` identifies a payer; amount-only borrowing and closing remain pool-scoped. Registry-derived debtor identity stays an inference.

The demonstration driver will be `python3 scripts/kickoff_xray_1963.py demo --bundle docs/kickoff/1963 --report .hexaemeron/v1-demo.json`. It must run without a network, validate the final public bundle, preserve its output counts and refuse changed source identity, omitted action, mismatched signature, missing disposition, stale source location, stale review digest and an incomplete review. Source-byte admission is also exercised against the four private accepted inputs locally; the public demonstration uses bounded synthetic source specimens and publishes no source payload. The driver records command, input identities, exit and result digest. Fiat retains controller receipts separately.

The exact criterion command below is a registered repository runner. New tests make its green result depend on the named assertions. Multiple descriptors may share one observed command; neither that join nor a zero exit proves criterion sufficiency.

```success-criteria
{"schema":"protasis-success-criteria/v1","criteria":[{"id":"checked-scaffold","claim":"The V1 checker and focused reporter enforce closed inputs, exact source membership, path bounds and incomplete-product refusal.","step":1,"command":"python3 scripts/run_checks.py --base 1f772fc01bb50c90fe0f254fec8ed088fbe6ab13 --scope root --format json"},{"id":"independent-denominator","claim":"The completed V1 bundle reconciles every selected callable and creation context from its independent compiler/source projection, retaining inherited, overloaded, read and eventless entries.","step":2,"command":"python3 scripts/run_checks.py --base 1f772fc01bb50c90fe0f254fec8ed088fbe6ab13 --scope root --format json"},{"id":"reviewed-linkage","claim":"The final V1 linkage covers all scoped action identities and has a separate source-semantic review bound to its exact bytes, with conditions, unknowns and attribution limits retained.","step":2,"command":"python3 scripts/run_checks.py --base 1f772fc01bb50c90fe0f254fec8ed088fbe6ab13 --scope root --format json"},{"id":"offline-refusals","claim":"The final offline demonstration records the accepted bundle and every named hostile specimen with its expected refusal.","step":3,"command":"python3 scripts/run_checks.py --base 1f772fc01bb50c90fe0f254fec8ed088fbe6ab13 --scope root --format json"},{"id":"publication-boundary","claim":"The checked public bundle contains no copied private corpus or compiler payload and the retained V2 reports remain byte-identical to the starting tree.","step":3,"command":"python3 scripts/run_checks.py --base 1f772fc01bb50c90fe0f254fec8ed088fbe6ab13 --scope root --format json"}]}
```

## 2. Prior art

Read the two latest merged deliveries touching this subject: [PR 1977](https://github.com/wildcat-finance/skills/pull/1977), merged at `1f772fc01bb50c90fe0f254fec8ed088fbe6ab13`, and [PR 1921](https://github.com/wildcat-finance/skills/pull/1921), merged at `df56bfeec3f67bf689d0b083c4994fc329477905`. The first supplies V1 emitter declarations and the separate V1 fidelity campaign. The second supplies the V2 report/checker pattern. Also read [PR 1750](https://github.com/wildcat-finance/skills/pull/1750) and [PR 1751](https://github.com/wildcat-finance/skills/pull/1751) for the V1 source exceptions and instance reads. PR 1751 corrects PR 1750's factory-deployment timestamp to 2023-11-30T22:27:35Z; it leaves the five equivalent commits unresolved.

PR 1977 carries `arch-interface-event-variants` and `v1-fidelity-report-link` to issue 1378. Keep both. Its 26 emitters and 37 emitter/declaration rows are an event input, not a callable denominator. The ten unused `IWildcatArchController` declarations and four declaration disagreements remain visible. Use the concrete arch-controller ABI and emitted declarations for linkage. Its runtime campaign remains bounded to its own harness and explored inputs. Its full local Hexaemeron suite was not clean; this study does not recast that as a pass.

PR 1921 carries `adapter-reconciliation` to issue 1387. Its four failed protocol coverage attempts, inconclusive parent replay with 585 infrastructure errors and unexplained hosted Git cleanup failure remain recorded limitations of that delivery. They do not establish V1 test coverage. The V2 checker fixes for open review findings, artifact omission and decision-link relocation are requirements for the V1 checker as well. Three existing review/omission guards were rerun during this study and passed. No current failure was manufactured from those fixed historical cases.

The whole-set `audit_synopsis.py --check .` ran from this target and exited 0 before any synopsis was used. Read both complete verified views: `audit/rounds/fiat-1363-entry-point-maps-at-two-pinned-wildcat-v2-c.synopsis.md` and `audit/rounds/fiat-1361-emitter-versus-declaration-check-at-a-pinne.synopsis.md`. Their authoritative `.md` sources remain unchanged. The research directory retains source/view digests and the currency log. The root synopsis search found no record of this V1 mapping subject; no separate 1962 audit-round file exists in the starting tree. The Hexaemeron legacy plugin synopsis was read as controller context; its missing legacy fields remain unknown and its controller repairs are outside this product.

The 1363 view retains `S1-R1-01`, `S1-R1-02` and `S1-R1-03` as fixed, all 12 risk dispositions, the original inconclusive Elenchus result and the later no-fix round. The 1361 view retains fixed `S1-R1-01`, `S1-R1-02`, `S2-R1-01`, `S3-R1-01` and `S3-R2-01`; accepted `S1-R2-01` belongs to [issue 1861](https://github.com/wildcat-finance/skills/issues/1861). The subtest-counter concern was recorded under [issue 869](https://github.com/wildcat-finance/skills/issues/869). This run does not repair their reporters, cryptographic helper or controller. Use complete source membership, preserve anonymous-event handling and reject false clean rendering. Keep the recorded HTTPS tree-listing and memory-bounding limits visible when borrowing an acquisition helper. Do not infer coverage from those helpers. Historical `guarded`, `passed`, `inconclusive` and null verdicts remain distinct.

The accepted corpus is the exact `lemma-1359-wildcat-reviewed-2026-09-26.zip`, SHA-256 `c2933988f0619b2874c5880211ef0f6d3586f3a463515b317ff8a7f609785fe1`, 21,728,910 bytes. The archive was freshly checked, safely extracted and all 149 member digests verified. Its three V1 partitions contain 1,505 chunks. The older catalog fields that still say acceptance is incomplete remain historical bytes: the later [issue 1359 acceptance](https://github.com/wildcat-finance/skills/issues/1359) supersedes them for this exact archive without inventing a Fiat receipt. The [private handoff](https://github.com/wildcat-finance/miskatonic/blob/fb814e389805d0fceb463c112411f820d4edc03f/storage/r2/handoffs/wildcat-v1-v2-lemma-20260926/README.md) governs custody and its V1 lens exception.

Outside Skills, the accepted inputs use Solidity standard JSON, compiler ABI and AST source locations. These are the compiler's interfaces for callable discovery; neither a compiler ABI nor Lemma chunks explain all transitive effects. X-Ray supplies the pre-audit reports. Surveyor owns source/estate attribution and linkage review; Tabularium owns downstream adapter reconciliation. Keep those owners separate.

## 3. Constraints and non-goals

The exact starting Skills commit is `1f772fc01bb50c90fe0f254fec8ed088fbe6ab13`, on the managed run branch `fiat/1963-wildcat-v1-entry-points-and-event-linkage`. The source distribution and controller use that same commit. The accepted V1 registry at the start has SHA-256 `2a3ec081f9a74bdcc60a57ee3cab3f11d33ce8be22001bdf4c6f5a8c218ce625`. The current V1 emitter table has SHA-256 `7fb47cb94b14a851df12406a454810ff3d22620751b78f96fbd53feffcf37cff`. Bind the relevant row and input records rather than treating later unrelated registry edits as new V1 source authority.

| Input | Exact accepted input SHA-256 | Source relation |
| --- | --- | --- |
| `WildcatMarketControllerFactory` | `dbeb245c5fc0a44f8ca7d001ddf801ec00176e838eae9487c8d65f2b9bdc8706` | Core `da74452aa7d1a0f024d99efd22cc6d950a8116b7`; includes market and controller creation code |
| `WildcatArchController` | `cb9136ec6740226c91e8d85268a0bbf7c8a5e81edb57b4bb332cc72a7e2b60db` | Core `da74452aa7d1a0f024d99efd22cc6d950a8116b7` |
| `WildcatSanctionsSentinel` | `45055f0b576dc6a607e4d8165711b144d1d1776d14939f74b46c4960273d8cb6` | `6164ddd4c75ef6da2181e5623b99795b9829e31c`; includes escrow creation |
| `MarketLensMixed` | `fe06195c86502900d64692619da8e1275ebc7720087e59d81b2c8dd651648377` | Exact verified input; no matching whole-tree Git commit |

The lens's closest commit is `488b30d08c73a93be3e4bf99128c774997411d3a`: 40 of 46 selected source files match it. Four other files require the pre-licence state and two have comment bytes absent from all examined commits. Preserve the accepted exception, the selected-source comparison scope and each exact input digest. The factory's five equivalent commits cannot identify the deployer's checkout.

The compiler is solc `0.8.22+commit.4fc1097e`, Shanghai, optimizer enabled with 200 runs, via IR, and no bytecode metadata hash. The retained solc-js file has SHA-256 `92d283c545395b91a656fa1ec94d567a464bca55aebcdbb99debf42b43026845`. An AST/ABI request may change `outputSelection` only, preserving and recording both input identities. Its success is separate from protocol builds, tests and coverage. X-Ray coverage attempts must retain their real command, status and failure output; a failed build cannot become a coverage percentage.

Always preserve source membership, component identity, eventless actions, uncertainties, private custody and exact review bindings. Ask before widening the estate, publishing private source bytes, altering the protocol, changing capture/access policy or taking a new external action outside this issue. Never substitute V2 or unreleased v2.5 declarations, infer an emitted debtor from a payer, edit the existing V2 reports or claim protocol safety. No skill frontier, controller, vendored skill, adapter, historical capture or research answer changes here.

## 4. Design options

The two constructions keep the same four input identities and seven context bindings. `shared-input-index` stores each input's source-reference manifest once and makes each context name that record. `component-copies` stores a complete source-reference manifest in every context, making each context readable alone at the cost of repeated identity records. Neither publishes source content or changes the evidence boundary.

The measured selection prototype is `.hexaemeron/research/design_probe.py`. It reads the verified accepted inputs and builds only path/digest/size/compiler/source-reference recipes. It writes one actual `protasis-design-report/v1` result per cell. Source files, signature completeness, semantic correctness and final bundle behavior are implementation obligations; the prototype establishes none of them.

| Selection criterion | Shared input index | Component copies |
| --- | --- | --- |
| Seven context/input bindings equal the declared scope | true | true |
| Median of seven samples, each parsing and hashing its recipe 100 times | 4 ms | 7 ms |
| Serialized reference recipe | 16,678 bytes | 29,333 bytes |
| Reference records contain no copied source payload or V2 records | true | true |
| Recoverable input identities retained | 4 | 4 |

The 1,000 ms parse ceiling is only a selection-probe budget. Serialized recipe bytes are the sole comparative metric; the remaining criteria are gates. The selected `shared-input-index` is the unique frontier and avoids repeated source identity records. The design checker at `design-lock` exits 0. These observed values are specific to this prototype, machine and method.

The closed record is `.hexaemeron/design-evidence.json`, with 2 candidates, 8 criteria and 16 cells. Ten selection cells are resolved. For each candidate, `checked-scaffold` remains pending until `step:2`, `reviewed-map` until `step:3`, and `offline-demonstration` until `integration`. Every pending cell names `scripts/kickoff_xray_1963.py design-report`, its exact candidate and criterion, and a future report path. Only the selected candidate's due gates authorise progress. Generate each report from the actual checker or demonstration result; do not type a success value into it.

Use three dependent steps. Step 1 scaffolds the bounded checker, focused report runner, input/source manifest contract, meaningful hostile-input tests, specification copies and decision record. It must reject an unfinished bundle. Step 2 derives the complete independent denominator, runs X-Ray over the admitted V1 sources, authors the semantic linkage and obtains a distinct review of its exact final bytes. Step 3 executes the offline demonstration, rechecks source-byte admission with the accepted private inputs, records hostile outcomes and publishes the consumer handoff. Each step exits through the registered checked runner. The existing licence, Python pin, workflows and hook policy remain the scaffold's infrastructure.

The new focused reporter is `tests/emit_kickoff_xray_1963_report.py`, with parser builder `build_parser`, declared as `step:1` in the runbook's command-interface block. Warden uses `python3 tests/emit_kickoff_xray_1963_report.py --report {report}`, format `unittest-json-v1`, with one unique `.elenchus/fiat-1963-step-N.json` path per step. It runs the named real test module, reports errors honestly and never fabricates an assertion failure when a suite is absent. Criteria execution uses the registered root runner, because local command registration supplies interface validation only.

## 5. Risk register seed

```risk-register
estate-scope | source inventory to V1 estate | include seven concrete contexts and all declared source/dependency exclusions without equating contexts with 16 registry entries
component-binding | source and compiler identities | preserve four exact inputs, sentinel pin, five equivalent core commits and mixed-source lens exception
independent-denominator | compiler/source projection to action rows | derive separately from linkage and reject joint omissions, inherited gaps, overload mismatches and implicit creation loss
eventless-actions | action coverage to disposition | keep eventless and unresolved actions in the denominator with distinct evidence and reasons
transitive-events | internal and external call relations | review modifier, helper, inherited and cross-contract paths with conditions and dynamic-callee limits
party-attribution | source events to consumer interpretation | retain payer versus debtor, pool-only debt events, registry inference and escrow identity
arch-event-variants | interface declarations to actual emitter | retain the four disagreements and use concrete arch-controller declarations for emitted variants
semantic-review | authored linkage to accepted record | bind a distinct reviewer to exact final bytes, complete action coverage, resolved finding ids and an empty open-finding set
artifact-membership | bundle manifest to retained evidence | require a separately fixed complete artifact set and reject omissions even after manifest rebinding
private-source | accepted archive to public bundle | publish references and analysis only and independently bind any public source quotation
input-boundary | files and process arguments | reject duplicate JSON keys, unsafe paths, links, oversized input and source drift without executing content
execution-truth | command output to reported result | retain failed builds and coverage, record real exits and keep AST-only success separate from protocol tests
v2-preservation | V1 output to completed V2 records | keep docs/kickoff/1363 and V2 emitter records byte-identical to the starting tree
decision-location | study choice to durable decision | use one stable decision identity through draft-to-number assignment and check its resolved links
```

## 6. Glossary seeds

- Source partition: one admitted source/compiler identity family, including the separately accepted mixed-source lens input.
- Concrete context: one runtime or creation contract with its own effective callable surface, including inherited members.
- Callable denominator: independently derived set of read, state-changing and creation identities against which authored rows are reconciled.
- Conditional linkage: an event relation whose recorded path or branch condition must hold; it is not an observation that the branch executed.
- Unresolved linkage: a named source, dynamic-callee or attribution gap that remains in the action inventory and limits downstream interpretation.

## 7. Sources

The study preserves live issue and PR snapshots, verified input-member hashes, compiler observations, audit source/view identities and selection reports under `.hexaemeron/research/`. These are research records, not phase receipts.

- [Starting Skills tree](https://github.com/wildcat-finance/skills/tree/1f772fc01bb50c90fe0f254fec8ed088fbe6ab13), including `docs/kickoff/1359/targets.json`, `docs/kickoff/1962/`, `scripts/emitter_declarations_v1.py`, `scripts/kickoff_xray_1363.py` and their tests.
- [V1 core source](https://github.com/wildcat-finance/wildcat-protocol/tree/da74452aa7d1a0f024d99efd22cc6d950a8116b7), [sentinel source](https://github.com/wildcat-finance/wildcat-protocol/tree/6164ddd4c75ef6da2181e5623b99795b9829e31c), and [verified lens input](https://sourcify.dev/server/v2/contract/1/0xf1d516954f96c1363f8b0ae48d79c8dde6237847?fields=stdJsonInput).
- [Accepted corpus handoff](https://github.com/wildcat-finance/miskatonic/blob/fb814e389805d0fceb463c112411f820d4edc03f/storage/r2/handoffs/wildcat-v1-v2-lemma-20260926/README.md), with the exact archive and input digests recorded above.
- [V2 map audit source](https://github.com/wildcat-finance/skills/blob/1f772fc01bb50c90fe0f254fec8ed088fbe6ab13/audit/rounds/fiat-1363-entry-point-maps-at-two-pinned-wildcat-v2-c.md) and [emitter audit source](https://github.com/wildcat-finance/skills/blob/1f772fc01bb50c90fe0f254fec8ed088fbe6ab13/audit/rounds/fiat-1361-emitter-versus-declaration-check-at-a-pinne.md); the verified synopses were the reading views.
- [Canonical X-Ray instruction](https://github.com/wildcat-finance/skills/blob/1f772fc01bb50c90fe0f254fec8ed088fbe6ab13/plugins/hexaemeron/skills/x-ray/SKILL.md), SHA-256 `b23bb94517805c1b8ce717d0e1e0282b0b5c14c7b16f4c32e73940292d3d4a41`, and its first-party overlay in `plugins/hexaemeron/PROMISES.md`. Apply the complete report templates and visually inspect the architecture SVG when the reports are produced.

## 8. Signals, and the questions behind them

The [Ephoros contract](https://github.com/wildcat-finance/skills/blob/1f772fc01bb50c90fe0f254fec8ed088fbe6ab13/plugins/hexaemeron/skills/ephoros/SKILL.md) governs signals. This is a finite offline CLI, so it has no unattended service, paging target or production metric. The retained result must answer three operator questions: which exact input failed, which action or artifact is missing, and whether a source/review binding changed. Emit stable refusal codes, bounded paths and ids, expected/actual digests, counts, command exit and the bundle digest. Do not log raw source inputs or credentials. Step 1 establishes refusal shape; Steps 2 and 3 retain real execution records and demonstrate it.

## 9. Boundaries, per capability

The [Phylax contract](https://github.com/wildcat-finance/skills/blob/1f772fc01bb50c90fe0f254fec8ed088fbe6ab13/plugins/hexaemeron/skills/phylax/SKILL.md) governs input handling. The trust boundaries are the private archive, compiler/input files, published manifests, model-authored linkage, reviewer records and subprocesses. Verify accepted archive/member identities before reading selected inputs. Accept closed schemas, bounded sizes and exact path membership; reject linked or escaping paths. Run commands as argument lists with time limits. Preserve the private/public split when creating projections. Source text and model output remain data. The checker never executes a report, source comment or reviewer instruction. Missing semantic evidence refuses acceptance while leaving inspection and regeneration available.

## 10. The budget, or its absence

The [Metron contract](https://github.com/wildcat-finance/skills/blob/1f772fc01bb50c90fe0f254fec8ed088fbe6ab13/plugins/hexaemeron/skills/metron/SKILL.md) governs measurements. There is no product throughput target or optimisation claim. The selection probe records actual reference-layout bytes and seven parse/hash samples of 100 iterations each; it does not estimate final checker performance. Its exact command is preserved in each design report. Input-size and timeout limits are denial-of-service controls, not performance results. Record actual demonstration duration without promising that another machine reproduces it.

## 11. The fail-closed posture

The [Elenchus contract](https://github.com/wildcat-finance/skills/blob/1f772fc01bb50c90fe0f254fec8ed088fbe6ab13/plugins/hexaemeron/skills/elenchus/SKILL.md) governs observed failures. Stop the dependent transition on wrong input or compiler identity, missing accepted source, malformed manifest, missing callable, mismatched canonical signature, invalid disposition, stale location/digest, private payload in public output, missing independent review, unresolved review findings or an unexpected demo result. Preserve the command and result before repair. Tests must fail by an assertion on the reproduced defect and pass after the fix; an import or infrastructure error remains an error. A declared unresolved dynamic call may remain a bounded map result with its explicit consumer limitation; it cannot satisfy an attribution claim it does not support.

The reviewed historical failures are already fixed in unchanged code, and the focused replay is green. They supply regression requirements and inspection targets for this new checker. This study claims no new failure, no guard verdict and no clean-history assertion. If implementation exposes a present failure, apply the named discipline to its actual mechanism. Never alter a failed protocol test or coverage observation to make the map look complete.

## 12. Decisions and their homes

The [Hypomnema contract](https://github.com/wildcat-finance/skills/blob/1f772fc01bb50c90fe0f254fec8ed088fbe6ab13/plugins/hexaemeron/skills/hypomnema/SKILL.md) governs durable decisions. Step 1 writes one draft at `docs/decisions/drafts/keep-v1-action-linkage-bound-to-component-inputs.md`. It records the shared input index, separate denominator and semantic-review authority, private evidence boundary and rejected duplicated layout. This is an issue-specific product choice, so no skill ledger advances. Use the stable decision identity after the draft exists; integration assigns its number. Put recovery commands and consumer limitations in `docs/kickoff/1963/README.md` and schema/CLI behavior next to the checker interface.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | shared-input-index
record | docs/decisions/drafts/keep-v1-action-linkage-bound-to-component-inputs.md
```

The decision record does not exist during study. Its explicit bridge becomes due when Step 1 ships the study. Readiness here permits runbook derivation only; no implementation, semantic acceptance, phase receipt or public delivery is established by this document.
