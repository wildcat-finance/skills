# Two pinned Wildcat V2 entry-point maps

Assuming, unless corrected:

1. Issue #1363 requests a preserved source comparison for adapter reviewers. It does not authorise a protocol change, deployment, capture, or safety conclusion.
2. The accepted inputs at Skills commit `95dca9d0f04353856f4e1684333b3ed94e85de87` govern the comparison: `docs/kickoff/1359/targets.json` and `docs/kickoff/1372/eventdecision.json`.
3. Both complete logical `src/` trees are inspected independently. The X-Ray exclusions for interfaces, vendored libraries, and mocks apply to its entry-point scope; every excluded file still receives an explicit source-inventory disposition. Declaration kind and executable behaviour control that decision: `IHooks.sol` is an abstract contract with implemented `onCreateMarket`, so its `I` prefix cannot remove that action. The comparison covers the entire release difference, including changes beyond indexed actors.
4. Coverage failure is a recorded execution gap. It cannot erase enumerated tests or turn a source map into proof of deployed behaviour.

## 1. Problem statement

Produce the two complete X-Ray report sets, their entry-point diff, a reviewed function-to-event linkage, and a semantic action comparison for issue #1363. Tabularium's adapter reviewers and issue #1387 consume the result as a candidate action denominator.

The exact repository is `wildcat-finance/v2-protocol`. The accepted pair is:

| Role | Commit | Meaning |
| --- | --- | --- |
| deployed comparison source | `f5a26146987926f4811b72a795d662813dedfe85` | the source selected by the accepted event decision; the registry supplies the narrower deployment relation |
| proposed candidate | `bea503c2736d47de7fd34130c64f10783dc35b39` | the selected V2.5 event revision; the handoff records a Sepolia deployment and a pursue decision |

A working delivery preserves `x-ray.md`, `entry-points.md`, `invariants.md`, `architecture.json`, and the rendered `architecture.svg` for each role under `docs/kickoff/1363/`. Each report states its exact commit, source scope, omissions, execution results, and evidence limits. The four X-Ray views are freshly produced for each commit.

The supplemental linkage keys each state-changing public or external action by source contract and canonical function signature. It retains source locations, inherited or internal call paths where needed, access restrictions, state effects, value flows, directly or conditionally reached events, actor meanings, and explicit absent or unresolved event coverage. The mapping must include functions with no event; a missing row cannot mean no event. Overloads stay distinct. Constructors and initializers are separately identified. Expand the callable surface through inheritance or provide an explicit reviewed inheritance map: imported `Ownable` and ERC20 actions remain visible, and `WildcatMarketRevolving`'s internal overrides change the effects of inherited actions. Direct function-definition counts and regex matches alone cannot establish that denominator.

The semantic diff enumerates added, removed, changed, and unchanged actions. A changed action names the changed access, state effect, value flow, or event relation and cites both sources. The accepted indexed-actor table is a cross-check, not the whole denominator. Preserve a literal `entry-points.diff` alongside that semantic comparison.

The final demonstration runs `python3 scripts/kickoff_xray_1363.py check` over the retained pair. It checks the closed artifact inventory, digests, source identities, complete linkage dispositions, action-set comparison, required report sections, and recorded review. It then runs `python3 -m unittest tests.test_kickoff_xray_1363` with refusals for a missing report, changed digest, swapped commit, dropped action/linkage row, and semantic-diff omission. The conformance command writes the selected `complete-pair` report only after those checks succeed. Warden separately judges the source reading and semantic linkage; the checker does not prove their truth.

## 2. Prior art and carried work

The last two merged pull requests changing the accepted V2 estate evidence were read directly, along with the pull request that fixed the comparison pair:

| Pull request | Landed commit | Consumed result and retained limit |
| --- | --- | --- |
| [#1736](https://github.com/wildcat-finance/skills/pull/1736) | `0dd41be5c10bc83d3df33c9fdca3d385264059ba` | fee-recipient compilation closes the step missed by #1735; deployed and creation bytecode match the recorded compiler output, with a 1,649-byte runtime and no immutables |
| [#1735](https://github.com/wildcat-finance/skills/pull/1735) | `b2f528e9bee8dc4bd4d1653f7f66fe6b1de93bc0` | V2 estate source map at finalized block 26006289: 3 hooks templates, 42 hooks instances, 80 markets, 32 role providers, 137 contracts; later deployments remain outside that observation |
| [#1714](https://github.com/wildcat-finance/skills/pull/1714) | `9182d0adcb7e9a5330c259d9dc1e044b511711c2` | the exact source pair and actor decision; source comparison and maintainer intent supply no candidate audit or mainnet deployment |

The current record comes from #1714. The open historical PR #1712 does not replace it. The registry's equality claim for `f5a2614` covers in-tree blobs of named verification inputs. Other files and deployment epochs differ. The third FixedTermHooks template, later lens, wrapper, and external registry, sanctions, role-provider, fee-recipient, and collateral sources retain their own pins and exclusions. This run does not relabel the entire `f5a2614` tree as one deployed checkout.

The event decision's `evidence/review.json` was read directly. Round 1 findings 1 through 7 and round 2 finding 1 are recorded as corrected or resolved. Their implications remain requirements here: preserve the SphereX pragma difference, the seven-carrier survey's dated scope, the selected branch relation, the five changed topic pairs, the five SphereX emitters, and the candidate's permissionless `executePendingAnnualInterestBipsReduction` path. In that path the actor is a caller, while `DebtRepaid.from` is a payer. The report's remaining untracked-file note was resolved by merged #1714. Its branch survey is historical evidence, not a fresh branch-state claim.

The whole-set command `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited 0 before the following verified synopsis views were read in full. Each authoritative source remains unchanged:

| Authoritative source | View actually read | Disposition |
| --- | --- | --- |
| `audit/rounds/fiat-510-reuse-source-bound-x-ray-analysis-across-fia.md` | its sibling `.synopsis.md`, source SHA-256 `e09531bb1bf5349d7dc0c88532167c75e0e1af737798d8fdc34b9edfb7ab39f5` | all 13 rounds retained; no reuse is selected here |
| `audit/rounds/fiat-1361-emitter-versus-declaration-check-at-a-pinne.md` | its sibling `.synopsis.md`, source SHA-256 `5a9ed2250779a10b7247992f71c8f713d20eb765b1d840109a6c03f822283a58` | all 6 rounds retained; its emitter comparison is optional corroboration, not this run's action inventory |

For #510, findings `S1-R1-01` through `S1-R1-03`, `S1-R2-01`, `S1-R3-01`, `S1-R3-02`, `S1-R4-01`, `S1-R5-01`, `S1-R6-01`, `S1-R7-01` through `S1-R7-03`, `S2-R1-01`, `S2-R1-02`, `S2-R2-01`, and `S3-R1-01` through `S3-R1-04` are recorded fixed. The final no-finding rounds carry null Elenchus verdicts. The retained leads include local-writer races, arbitrary destination confinement, post-replacement failure, and the inability of a digest to prove model fact truth or regeneration. This run avoids its cache interface, checks source bytes again before handoff, and makes no performance or semantic proof claim from its tests.

For #1361, `S1-R1-01`, `S1-R1-02`, `S2-R1-01`, `S3-R1-01`, and `S3-R2-01` are fixed; `S1-R2-01` is accepted under [#1861](https://github.com/wildcat-finance/skills/issues/1861). Its unpursued leads retain the HTTPS-only added-file gap, source-reader memory limits, runner root and transitive-pin gaps, Tabularium's then-observed Keccak padding issue, and [#869](https://github.com/wildcat-finance/skills/issues/869). `S3-R1-01` has an inconclusive Elenchus result; `S3-R2-01` has passed, with direct parent evidence and the recorded test-only overlay limit. Those statuses are not upgraded here. The new handoff enumerates local immutable Git trees and needs no copied Keccak implementation or inherited emitter reporter. Repairs to those separate tools remain outside #1363.

No in-scope open failure requires a pre-product repair of a reused implementation, so no known-failure inventory is declared. The new verification refusals belong to this delivery's tests. The source repositories have audit-scope documents but no `audit/AUDIT.md` or Fiat round source in the inspected tracked audit paths. The candidate's `audits/README.md` records earlier external reviews and says no complete finding-to-fix and retest map has been reconstructed. Its `docs/releases/v2.5-audit-scope.md` names source freeze `7fad3deffb2f4cb185c466bd539f9bc200d19bc7`, not this comparison's selected commit. Preserve both facts as lineage limits.

Outside this repository, the pinned upstream X-Ray instruction is `pashov/skills@aadee2ca49cae20246af378ef791d2d4f941e237`, path `x-ray/SKILL.md`. Ethereum event declarations and `logN` emitters supply source evidence; actual log capture and deployed-code reproduction belong to their existing producers. No new parser or general analysis framework is needed.

## 3. Constraints and non-goals

The Skills start is `95dca9d0f04353856f4e1684333b3ed94e85de87` on the issue's Fiat worktree. Python is the repository's exact `3.14.6` pin. The target Foundry files both pin Solidity 0.8.25 and Cancun; preserve their distinct profiles. The deployed verification inputs used 50,000 optimizer runs and via IR; the candidate default uses 44 runs, via IR, and disabled CBOR metadata. Record the actual Forge version and coverage invocation rather than substituting a deployment profile silently.

The two source roots are `.hexaemeron/sources/deployed` and `.hexaemeron/sources/candidate`. Their tracked Solidity inputs are 62 files / 406,379 bytes and 108 files / 810,956 bytes. These are raw source counts, not X-Ray nSLOC or entry-point counts. The local X-Ray instruction digest must equal `b23bb94517805c1b8ce717d0e1e0282b0b5c14c7b16f4c32e73940292d3d4a41` before its operation starts. Preserve the existing vendored instruction and templates.

**Always.** Use immutable source commits; record each current source digest and its inclusion disposition; run both X-Ray workflows fully; preserve failed or unavailable coverage honestly; review event linkage against function bodies; run the repository's selected checks and regenerate Horos artifacts before a green commit.

**Ask first.** A new source pair, protocol edit, deployment, additional dependency, changed public ABI, widened external source scope, or replacement of a released digest needs a separate decision. None is required by the selected construction.

**Never.** Use candidate event topics to decode deployed historical logs; overwrite either accepted input; reuse a final X-Ray view from the other commit; edit vendored skills; copy credentials or private-source payloads into the report bundle; describe an inferred source relation as observed chain behaviour.

This delivery changes no skill frontier, package version, protocol source, deployment state, or capture. Its one issue-specific verifier reads retained public evidence and reports mismatches. It does not certify safety or close #1372, #1387, #1861, or #869.

## 4. Designs and checked selection

| Candidate | Construction | Trade |
| --- | --- | --- |
| `source-bound-reports` | fresh reports, explicit source manifests, linkage, diff, digests, and a small verifier | source rereading needs the immutable Git objects; the publication avoids a second source archive |
| `reports-and-source-archive` | the same delivery plus an uncompressed archive of every selected Solidity source | the archive permits source recovery from the bundle and duplicates the public source bytes |

Both candidates were exercised by `.hexaemeron/design-selection/probe.py`. For each, it checked both HEADs, compared all 170 working source files with native Git blobs, wrote and reopened the manifest, and tested the stated recovery route. The archive candidate also wrote and reopened an actual tar archive; no extraction into the target repository occurred.

Five selection criteria cover correctness, time, space, compatibility, and recovery. The manifest-only package measured 43,414 bytes; adding the archive measured 1,395,094 bytes. Packaging time, rounded upward to whole milliseconds, was 1 ms and 3 ms in the recorded probes, both below the 5,000 ms study-probe ceiling. These are single local packaging observations, excluding Git reads and future reports; they imply no production speed result. Both passed the identity, JSON/tar format, and recovery checks. The sole comparative metric minimizes retained probe bytes, so `source-bound-reports` is the unique frontier.

`.hexaemeron/design-evidence.json` contains all 12 matrix cells: 10 resolved selection reports and 2 pending conformance cells. Each resolved report records the actual zero-exit command. Both pending cells block `integration`; the selected resolver is `python3 scripts/kickoff_xray_1363.py conformance --candidate source-bound-reports --report .hexaemeron/design-reports/source-bound-reports-complete-pair.json`. It must check the complete delivery, write the closed `protasis-design-report/v1` result, and refuse absent or failed evidence. It must not claim to have produced the X-Ray analyses.

One product step is coherent here: scaffold the delivery paths and committed study/runbook copies, produce both independently scoped reports, assemble their one comparison handoff, and run the demonstration. Neither half satisfies the issue alone. This step changes evidence and its narrowly scoped checks, with no protocol implementation. An isolated skeleton PR would supply no usable handoff.

## 5. Risk register

```risk-register
source-role-swap | source pair and deployment registry | exact commits and role labels stay distinct and a swapped-role specimen refuses
scope-omission | complete current logical source tree | every source has a disposition and every eligible state-changing action has a map and linkage row
inherited-action-gap | public entry points through inherited helpers | overloads imported base actions and internal override effects retain implementation locations and callers
event-path-gap | function bodies and emitters | direct and conditional call paths are reviewed and eventless or unresolved actions remain explicit
actor-confusion | payer caller borrower and principal fields | all reaching paths preserve their actor class including permissionless APR execution
release-diff-narrowing | deployed and candidate action sets | additions removals and state value or access changes beyond indexed actors are retained
deployment-overclaim | source comparison and recorded chain evidence | uncertainty epochs external sources and scope exclusions survive in both reports and the handoff
stale-analysis | source reads and final report views | all four views are produced afresh per commit and source digests are rechecked before handoff
coverage-overclaim | source test inventory and coverage execution | failed or pending coverage never becomes absent tests or completed coverage
partial-bundle | manifest report files and comparison data | missing files digest drift omitted rows and incomplete review refuse
model-output | drafted maps and verifier inputs | output is reviewed data and never command or path authority
vendor-drift | canonical X-Ray instruction | instruction digest and unchanged vendored bytes are checked
```

## 6. Glossary seeds

**Action:** one state-changing public or external function reachable through a scoped contract, distinguished by signature and owning source.

**Linkage:** the reviewed relation from an action through its call path to zero or more event emissions, with conditional and unresolved cases retained.

**Deployed comparison source:** the accepted source commit with a separately recorded, narrower deployment relation.

**Semantic diff:** changes to actions, access, state effects, value flows, and event relations; source line movement alone is not a semantic change.

**Complete report pair:** both complete X-Ray outputs and their source, linkage, comparison, digest, execution, and review evidence.

## 7. Sources

- [Issue #1363](https://github.com/wildcat-finance/skills/issues/1363), including its Miskatonic consumer comment: the source action denominator is a bounded input; comparison still requires both reports.
- [Accepted target registry](https://github.com/wildcat-finance/skills/blob/95dca9d0f04353856f4e1684333b3ed94e85de87/docs/kickoff/1359/targets.md) and [machine record](https://github.com/wildcat-finance/skills/blob/95dca9d0f04353856f4e1684333b3ed94e85de87/docs/kickoff/1359/targets.json).
- [Accepted event decision](https://github.com/wildcat-finance/skills/blob/95dca9d0f04353856f4e1684333b3ed94e85de87/docs/kickoff/1372/eventdecision.md), [machine record](https://github.com/wildcat-finance/skills/blob/95dca9d0f04353856f4e1684333b3ed94e85de87/docs/kickoff/1372/eventdecision.json), and [independent review](https://github.com/wildcat-finance/skills/blob/95dca9d0f04353856f4e1684333b3ed94e85de87/docs/kickoff/1372/evidence/review.json).
- [Deployed source](https://github.com/wildcat-finance/v2-protocol/tree/f5a26146987926f4811b72a795d662813dedfe85) and [candidate source](https://github.com/wildcat-finance/v2-protocol/tree/bea503c2736d47de7fd34130c64f10783dc35b39).
- [Canonical X-Ray](https://github.com/wildcat-finance/skills/blob/95dca9d0f04353856f4e1684333b3ed94e85de87/plugins/hexaemeron/skills/x-ray/SKILL.md) and [bounded overlay](https://github.com/wildcat-finance/skills/blob/95dca9d0f04353856f4e1684333b3ed94e85de87/plugins/hexaemeron/PROMISES.md).
- The verified audit views named in section 2; `.hexaemeron/prerequisite-inspection.json` records this run's source-file comparisons and registry exits `0`, `0`, `1`, with the last being the expected wrong-generation refusal. `.hexaemeron/design-reports/` holds the actual selection reports.

## 8. Signals and questions

There is no unattended service or alert surface. Under [Ephoros](https://github.com/wildcat-finance/skills/blob/95dca9d0f04353856f4e1684333b3ed94e85de87/plugins/hexaemeron/skills/ephoros/SKILL.md), retain only the command results needed to answer: which source pair was read, which outputs passed verification, and which coverage or review gaps remain. Step 1 records command, source role, tool version, exit, and output digest. It reports a failed check by artifact and field. No wallet-indexed telemetry is introduced.

## 9. Trust boundaries

[Phylax](https://github.com/wildcat-finance/skills/blob/95dca9d0f04353856f4e1684333b3ed94e85de87/plugins/hexaemeron/skills/phylax/SKILL.md) governs local Git objects, file paths, subprocess arguments, and model-produced evidence. Pin Git sources, use argument arrays, keep report paths inside the fixed issue directory, reject linked or escaping evidence files, and bound JSON and file reads. Preserve external sources as citations and explicit unknowns. Fixed tool paths and validated identifiers determine commands; report text does not. The deployment input registry stays an input, never a mutable inference target.

## 10. Performance budget

No runtime, gas, or throughput improvement is promised, so [Metron](https://github.com/wildcat-finance/skills/blob/95dca9d0f04353856f4e1684333b3ed94e85de87/plugins/hexaemeron/skills/metron/SKILL.md) has no product performance campaign. The only time bound is the 5,000 ms packaging probe in section 4, measured by the exact command in each design report. Record long tool failures and unavailable coverage; do not replace source analysis with a timing shortcut.

## 11. Failure and recovery

Missing or mismatched input identity blocks report production. Missing source reads, incomplete action/linkage dispositions, absent required reports, digest drift, or an incomplete comparison blocks handoff and integration. Retain the refused evidence, restore the named source or output, and rerun that check. Coverage failure remains an explicit report gap under the X-Ray contract and does not authorise a coverage claim.

[Elenchus](https://github.com/wildcat-finance/skills/blob/95dca9d0f04353856f4e1684333b3ed94e85de87/plugins/hexaemeron/skills/elenchus/SKILL.md) owns any new verifier failure: reproduce it, identify its cause, and demonstrate the guard on the failing and fixed forms. The fixture tests listed in section 1 exercise real missing or contradictory evidence. The runbook must declare the exact structured reporter Warden uses for a fix; an absent surface or infrastructure failure is not a successful parent guard.

## 12. Decisions and homes

The durable decision is to publish the source-bound pair with an explicit action/linkage denominator and recoverable Git pins, keeping source, deployed, and candidate evidence separate. Its alternatives are recorded in section 4. Under [Hypomnema](https://github.com/wildcat-finance/skills/blob/95dca9d0f04353856f4e1684333b3ed94e85de87/plugins/hexaemeron/skills/hypomnema/SKILL.md), Step 1 writes the short decision draft at `docs/decisions/drafts/keep-wildcat-xray-reports-bound-to-two-source-commits.md`; integration assigns its number. The study and runbook copies live in `docs/kickoff/1363/`, and the handoff, scope, recovery command, and limitations live in its `README.md` and manifest. No skill ledger decision changes.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | source-bound-reports
record | docs/decisions/drafts/keep-wildcat-xray-reports-bound-to-two-source-commits.md
```

The draft is a Step 1 deliverable and is absent at design lock. Run Hypomnema's explicit study check after that file exists and before the study copy ships. Design readiness authorises the controller to derive the runbook; production and integration still need their own checks.
