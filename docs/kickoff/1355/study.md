# Issue 1355: protected Wildcat V2 layouts and selectors

Ready for runbook derivation with test-only preparation as a separate first
step. The selected construction is `prepared-source-group`; design-lock is
clean. Original V1 and V2 suites remain red. Five conformance gates prevent
those results from becoming a baseline or delivery claim. No Hermes baseline
has been sealed and no Gate 5 rejection has been demonstrated.

Assuming, unless corrected:

1. The approved subject remains `wildcat-v2-ethereum-mainnet` at block
   `26006289`, hash `0x3d069f254a10d98ad19eff0f397cf28db3613fd98bff1df48c798920552f4ec5`,
   on Ethereum chain `1`. Later deployments are outside this dated claim.
2. Delivery belongs in `docs/kickoff/1355/` in Skills. Target clones are
   disposable research and demonstration inputs. Negative candidate patches
   never enter deployed production source.
3. A baseline matrix may cover several exact source and build states; each
   canonical Hermes run still covers exactly one clean repository state.
4. Private fee-recipient and role-provider source remains restricted. Access
   to a repository does not establish permission to publish its source copies.
5. Test-only preparation is included in this Fiat delivery before any Hermes
   baseline. Each prepared revision must retain every deployed production blob,
   configuration and dependency pin, record its original source pin separately,
   and carry a verified signature. The study permits no production repair.

## 1. Problem and proving path

The operator requests the evidence in
[issue 1355](https://github.com/wildcat-finance/skills/issues/1355): a complete
protected-contract inventory, reproducible Gate 1 baselines, and two separate
Gate 5 rejection demonstrations. Reviewers must be able to trace an observed
contract to its source, qualified identifier, compiler settings, baseline and
comparison output.

Completion requires every admitted source/build group to run canonical
`plugins/hermes/skills/hermes/scripts/hermes.py baseline` successfully with
all its protected contracts passed through repeated `--protected-contract`.
For each negative demonstration, `verify` must pass Gates 2, 3 and 4, exit
`50`, and identify the intended layout or selector difference at Gate 5.
A Gate 2 refusal or a red Foundry test does not satisfy this criterion.

The final demonstration must invoke the canonical Hermes controller against
one separate disposable copy for each candidate. Retain its complete command,
environment, patch, gate records, comparison output and exit status, then
prove that each target's production blobs equal the recorded clean baseline.
The estate-wide inventory must refuse a missing group, identifier, instance
mapping, source digest, owner handoff or negative result. These final checks
have not run; no delivery checker is implemented by this study.

## 2. Prior art and inherited work

The accepted target registry is `docs/kickoff/1359/targets.json`, SHA-256
`417f727d018ecbfa86efb23ea8c9cdfc53d429cf3f4a6285543ae24e89fc40ea`.
It maps this issue to the approved Ethereum V2 estate: 137 recorded contracts,
including 42 hooks instances and 80 markets, three templates and one shared
pull provider among 32 provider addresses. Its observation and source matching
remain recorded evidence. Its checker establishes registry consistency;
it supplies neither a Lazarus fixture nor an Alexandria release.

The two merged source-map changes read were
[PR 1735](https://github.com/wildcat-finance/skills/pull/1735) and
[PR 1736](https://github.com/wildcat-finance/skills/pull/1736).
PR 1735 completed the V2 map while retaining the limits on exact deployer
checkout, current chain state and downstream captures. PR 1736 then compiled
the fee-recipient verification input and reproduced its 1649-byte runtime.
The older statement that this reproduction was missing is superseded by that
second result. Collateral instance enumeration remains an explicit exclusion.

The two merged changes read for Hermes's operative harness were
[PR 358](https://github.com/wildcat-finance/skills/pull/358) and
[PR 353](https://github.com/wildcat-finance/skills/pull/353).
They added the rule corpus, scope checks and refusal handling. The harness
requires one supported rule and one optimisation class, a saving for each
named gas target, no deterministic regression, unchanged test sources and
matching measurement sets before Gate 5 can execute.

The latest two merged V2 source PRs were also read:
[PR 169](https://github.com/wildcat-finance/v2-protocol/pull/169), the Foundry
1.8.3 update, and
[PR 166](https://github.com/wildcat-finance/v2-protocol/pull/166), the
Daybreak Blue remediation. Both postdate the deployed source pins. Their
existence does not allow substitution of current main for deployed code.
The pinned target README directs reviewers to Yul type access and custom
error/event parameter ordering when changing types.

Audit reading used `audit/AUDIT_SYNOPSIS.md` only after
`python3.14 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exited zero over the whole source set. The authoritative source is
`audit/AUDIT.md`; its Hermes rule-corpus rounds 1 through 6 were read through
the verified synopsis. That view preserves fixed findings `S3-R1-01`,
`S3-R1-02`, `S3-R1-03`, `S5-R1-01`, `S5-R1-02` and `S5-R1-03`.
Legacy `audit-schema`, `covered`, `not-checked` and `elenchus-verdict` fields
remain unknown where the synopsis marks them missing.
The surviving class-vocabulary gap, authored corpus judgements and
20-character obligation-answer limit remain outside this baseline delivery.
The transcription-extractor lead was closed for transcribed fields in step 3;
this study does not reopen it. The Horos file-count lead belongs to Horos.
No Hermes-local audit source exists under `plugins/hermes/`.

Readiness tests exposed a new test-oracle failure in the V1 dependency source,
recorded below. That failure is separate from the inherited fixed Hermes
findings. External prior art is the pinned Solidity standard-JSON compiler
output and Foundry's `snapshot`, `test` and `inspect` interfaces consumed by
the canonical harness. No new compiler or compatibility algorithm is proposed.

## 3. Constraints and source states

Skills starts at `8b0a7abbf80e2466dc32e477733e1aa7471d7af7` on base `main`.
The run worktree fingerprint is `issue/16777231-910376746`.
Python is `3.14.6`. The inspected Hermes skill is `0.1.1`; its script SHA-256
is `36e80da4405645486e4f34caf6fa59ed795d864c685e04a9b37a959bc43c1805`.
Readiness used Forge `1.7.1`; compatibility with each historical test suite
must be established before fixing the baseline toolchain.

The registry names these nine source states across five repositories:

| Repository | Commit | Required source roles |
| --- | --- | --- |
| `wildcat-finance/v2-protocol` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | HooksFactory, market, OpenTermHooks, 365-day FixedTermHooks, original MarketLens |
| `wildcat-finance/v2-protocol` | `5838b2f3f5c0bb3489cd2ff16bb31ddd5194c7fa` | 730-day FixedTermHooks and its eleven instances |
| `wildcat-finance/v2-protocol` | `e1f77540fef65736374de6c847743d8ca2233fb4` | application-facing MarketLens |
| `wildcat-finance/v2-protocol` | `c7be4039f8f383a9dda4e45f63331c17d63f9ed9` | Wildcat4626WrapperFactory and dependent wrapper type |
| `wildcat-finance/wildcat-protocol` | `da74452aa7d1a0f024d99efd22cc6d950a8116b7` | shared WildcatArchController |
| `wildcat-finance/wildcat-protocol` | `6164ddd4c75ef6da2181e5623b99795b9829e31c` | shared WildcatSanctionsSentinel and dependent escrow type |
| `wildcat-finance/fee-recipient-contract` | `ac73bda3642c9a7c8de64e39856b31af53f06068` | WildcatFeeRecipient; private source |
| `wildcat-finance/collateral-contract` | `46dba596fa111f868200358f551796e8f73b5fd7` | WildcatMarketCollateralFactory, SimpleMarketCollateralMultiParty init code, CollateralLens |
| `wildcat-finance/chainalysis-ofac-role-provider` | `5d7f8c889a8d29935838a3906172feb8d9861807` | OpenAccessRoleProvider; private source |

Each Foundry root is the repository root. The main V2 build uses solc
`0.8.25`, Cancun, via IR, 50000 optimiser runs and bytecode hash `none`.
The newer lens uses 200 runs with via IR; the wrapper factory uses 200 runs
without via IR. Fee and pull-provider builds use solc `0.8.25`, Cancun,
via IR, 200 runs and bytecode hash `none`. Collateral uses solc `0.8.28`,
Cancun, via IR and 50000 runs. The two V1 dependencies use solc `0.8.22`;
their exact deployed optimiser settings remain to be qualified.

Conservative protection must include inherited storage through the concrete
qualified contract. The market's assembly call to the sentinel and the
sentinel's CREATE2 escrow construction require an explicit
`src/WildcatSanctionsEscrow.sol:WildcatSanctionsEscrow` disposition. The wrapper
factory creates `src/vault/Wildcat4626Wrapper.sol:Wildcat4626Wrapper`.
The source relationships justify protecting both types while their deployed
instance coverage is checked; absence from the 137-row list is not exclusion.
No final protected inventory has been approved.

Keep the registry's named exclusions: borrower-owned push providers, owner
Safe, Chainalysis oracle, SphereX engine, Bebop settlement, undeployed
arch-controller delegator, V1 lens and collateral instances. Preserve each
owner and reason. Dependency interfaces and immutable values still need
source/selector checks even when their external implementation is excluded.
No test exclusion, fuzz-bound reduction, modified production source, synthetic
replacement estate, new Hermes rule or tool bypass belongs to this delivery.
Only the named test repairs and migration below are admitted for preparation;
new failures require Elenchus evidence and a reviewed study change.

## 4. Design options and checked selection

The initial unmodified-source construction failed design-lock: the recorded
V1 suite was red and several groups had not run. Its study, matrix and reports
remain under `.hexaemeron/research/unmodified-construction/`. That refusal is
unchanged. The new construction adds separate, signed test-only preparation;
it does not call either failing historical tree green.

`prepared-per-address` prepares the required harnesses, then creates one
baseline job for each of the 137 registry addresses. It preserves address
attribution, but repeats source records and Foundry suites for instances
sharing one source and build state.

`prepared-source-group` uses the same preparation, then maps each address to a
protected qualified type in its exact source/build group and seals one
baseline per group. Nine source pins are distinct. It removes repeated
baseline work while making the instance-to-evidence mapping a reviewed
obligation. A compiler/profile distinction must split a group even if its
source SHA is shared. The present registry projection needs no additional
split; final dependency coverage still requires review.

`.hexaemeron/research/measure_design.py` computes both projections from the
registry. Both preserve 137 addresses, keep one source SHA per job and assign
independent evidence directories. It counts 137 versus 9 baseline jobs and
137 versus 9 source-record copies. These are finite work and duplication
counts, not measured runtime, memory or disk consumption. The new construction
also requires separate original and signed harness refs, test-path-only
changes, unchanged configuration/dependency pins, preserved assertions and
fuzz domains, and green suites before Gate 1.

The reporter checks the two retained proposed oracle patches with
`git apply --check`, verifies their digests and confirms their changed paths
are beneath `test/`. Both checks exit zero without applying either patch.
This establishes their patch shape and applicability only. It establishes no
passing repaired suite. `.hexaemeron/research/preparation-construction.json`
records that boundary and the separate legacy-test migration obligation.
The 12 selection reports are under `.hexaemeron/design-reports/` and bound
by `.hexaemeron/design-evidence.json`. Design-lock exits zero and selects
`prepared-source-group` by `unique-frontier`.

The actual readiness results stay visible. V1 at `da74452a` exits `1`:
338 pass and 7 fail. Six failures are legacy `testFail` names rejected by
Forge 1.7.1. `EscrowTest.testFuzzReleaseEscrow` also fails with
`CanNotReleaseEscrow`; the isolated rerun exits `1`. The test expects release
from borrower status alone, while the contract requires the sentinel sanction
decision to permit release. Upstream commit
`488b30d08c73a93be3e4bf99128c774997411d3a` already corrects that condition to
`if (sanctioned)` in `test/EscrowTest.sol`. Its exact one-file diff was read;
the current-source hunk is retained as `research/v1-escrow-preparation.patch`
under the design directory. This identifies a test-oracle repair, not a
production vulnerability.

V2 at `a70f297f` runs 723 tests: 721 pass and 2 inherited variants of
`test_updateState_HasPendingExpiredBatch` fail. The isolated rerun runs both
and fails both; the earlier zero-test match remains recorded separately.
`test/market/WildcatMarket.t.sol:47` caches `block.timestamp` before a warp,
but via-IR compilation emits the expected event with timestamp `1714909830`
after the warp; the contract's event carries `1714737030` from before it.
The pinned `lib/forge-std/src/Vm.sol:385` documents
`vm.getBlockTimestamp()` for this exact compiler assumption. The retained
`research/v2-timestamp-preparation.patch` changes only that time read;
event values and assertions remain unchanged. Behaviour after applying it
has not yet been measured.

The private provider, fee-recipient and collateral readiness results pass
5, 19 and 48 tests respectively without skips. These are prerequisite tests,
not Gate 1 receipts. Other source/build groups remain untested.

Step 1 must scaffold the evidence checker and separately prepare the harnesses
on pinned source copies. Prefer the installed, recorded Forge 1.7.1 over a
second historical toolchain. Migrate the six active legacy `testFail` variants
in `test/helpers/BaseERC20Test.sol` into named revert tests with
`expectRevert` immediately before the intended failing token call. Preserve
all pre-call assertions, fuzz assumptions and bounds. The entire-function
legacy convention does not justify discarding those assertions.

Five future conformance results are pending, with exact resolver commands and
report paths in the design matrix. `scripts/kickoff_hermes_1355.py` is a planned
Step 1 evidence checker, not a shipped command. Its `conformance` command must
emit the closed report schema only after executing the stated checks:

| Criterion | Due before | Required checked result |
| --- | --- | --- |
| `prepared-state` | Step 2 | Every required source/build group has a green full suite, fixed seed and reviewed regression evidence; each changed harness revision verifies its signature; original versus prepared Git trees differ only in admitted test files, with zero difference in every other tracked path, submodule pin and compiler setting |
| `owner-handoffs` | Step 3 and any Gate 1 | Exact producer/reviewer/digest records for scope, mapping, verified Lazarus fixture, verified Alexandria release and reviewed protected inventory; complete instance/type coverage and explicit exclusions |
| `sealed-baselines` | Step 4 | Every inventoried group has a canonical successful Gate 1 record and all required layout/method snapshots, bound to its original source pin and exact prepared harness revision |
| `separate-rejections` | Integration | Independent layout and selector candidates each passed Gates 2 to 4 and exited 50 at intended Gate 5, with patches, offending contracts, diffs and source-restoration checks |
| `restricted-delivery` | Integration | Every evidence object has an appropriate access class, exact digest and retrievable authorised destination; private source is absent from public output |

Runbook ordering must preserve those stops: scaffold/preparation first,
capture/mapping second, baseline third, rejection demonstrations fourth and
final reproduction last. Each phase retains its own review and receipts.
If test-only recovery cannot preserve source equivalence, stop this delivery
before Gate 1 and route the production repair separately. Repaired suites,
source parity and successful demonstrations are unknown until their named
commands run.

## 5. Risk register

```risk-register
source-epoch-collapse | one deployed estate spans source and compiler states | retain each qualified source and build identity
protected-set-gap | factory dependencies and shared implementations | account for every recorded address plus escrow and wrapper types
chain-evidence-upgrade | recorded RPC and proved state | retain Lazarus evidence classes and declared finite coverage
private-source-disclosure | complete Hermes source snapshots | keep restricted objects outside public Skills publication
red-baseline | historical Foundry suites | refuse sealing until each prepared signed harness passes with production-source parity
oracle-weakening | test-only preparation | preserve all assertions and fuzz domains and retain a failing-parent regression
wrong-gate-negative | intended layout and selector specimens | require passed Gates 2 to 4 and exit 50 with intended diff
candidate-class-mixing | negative candidate source edits | name one corpus rule and ensure every hunk belongs to its class
source-restoration | disposable candidate worktrees | compare production blobs to the clean baseline after each rejection
partial-evidence | multi-group evidence directories | require complete digests and preserve failed results without success claims
```

## 6. Glossary

A source group is one repository commit and compiler/profile identity.
A protected type is a qualified Solidity `path:Contract` whose layout and
method identifiers cannot change under Hermes. Instance coverage maps deployed
addresses to that type's evidence. A source pin identifies the original
production bytes; a harness revision would identify separately admitted test
preparation. A rejected candidate is evidence of one exercised refusal only.

## 7. Sources and owner handoffs

Source pointers are pinned to
[the Skills starting tree](https://github.com/wildcat-finance/skills/tree/8b0a7abbf80e2466dc32e477733e1aa7471d7af7).
`.hexaemeron/research/source-digests.json` records the exact local digests.
The source state table above supplies immutable upstream revision identifiers;
all source paths in this document refer to those commits.

| Owner and reviewer | Artefact and digest | Current handoff status |
| --- | --- | --- |
| target maintainer Dave Coleman; scope recorded by kethcode | `docs/kickoff/1359/evidence/scope-approval.json`, SHA-256 `df147d44ba5cfbff58df62c91afc6937358701773ca760f84ff32ce7dcf73450` | complete for estate choice; no capture-spend or redistribution grant |
| Surveyor under Protasis; PR 1735/1736 review context | `docs/kickoff/1359/evidence/source-match-1590.json`, SHA-256 `0bd8d53d351e46082dbb625a499bc7c6cebe1f1f43ab4c9ef2498f23fb79282e` | reusable recorded mapping; #1355 protected-set review still required |
| original chain-capture producer; target maintainer reviews interpretation | `docs/kickoff/1359/evidence/ethereum-mainnet-1590.json`, SHA-256 `b7ce1e66f343a480ac64f8b6259e108638dc1fe473607b77f728980846d6ca70` | recorded chain observations; not a Lazarus fixture |
| Lazarus; Warden checks scope and verification | no #1355 fixture or digest yet | blocked handoff until finite fixed-block capture and `lazarus.py verify` succeed |
| Alexandria; Warden checks release coverage | no #1355 raw release or digest yet | blocked handoff until admitted inputs are ingested and `alexandria.py verify` succeeds |
| Hermes; Warden reviews inventory, baselines and rejections | no accepted inventory or sealed baseline digest | pending conformance after separate signed test-only preparation and protected-set completion |
| Warden and Fiat | no #1355 audit or phase receipt | not started; this worker writes no controller receipt |

Lazarus supports the finite Ethereum code, account proofs and exact requests
required here. Use block `26006289` and the registry's hash, with explicit
account/slot lists and bounded requests/bytes/time. Historical creation
receipts at other blocks remain separately scoped recorded inputs unless their
own receipt proof is captured. Alexandria can preserve the admitted local
source bytes and verified fixture; use recorded and proof-backed captures as
separate classes and preserve access/redistribution restrictions. Neither owner
certifies the deployment-to-source interpretation. No fixture, archive release,
proof or final review is claimed by this study.

## 8. Operational questions and signals

The [Ephoros contract](https://github.com/wildcat-finance/skills/blob/8b0a7abbf80e2466dc32e477733e1aa7471d7af7/plugins/hexaemeron/skills/ephoros/SKILL.md)
owns signals. This is a bounded operator-run reproduction rather than an
unattended service, so no alert deployment is needed. Its output must answer:
which source group failed, which canonical gate ran, which required evidence
is absent, and whether source restoration passed. The manifest, command logs,
exit statuses and exact gate records must answer those questions.

## 9. Trust boundaries

The [Phylax contract](https://github.com/wildcat-finance/skills/blob/8b0a7abbf80e2466dc32e477733e1aa7471d7af7/plugins/hexaemeron/skills/phylax/SKILL.md)
owns subprocess, input, output and credential controls. Git objects, provider
responses and inherited build scripts are separate trust boundaries. Pin input
objects, invoke argument arrays, retain source/build settings, bound capture
responses and keep provider secrets out of logs. Check snapshot destination
access before archiving private source. The canonical owner verifies each
fixture/release; a success string from a wrapper is insufficient.

## 10. Performance and resource accounting

The [Metron contract](https://github.com/wildcat-finance/skills/blob/8b0a7abbf80e2466dc32e477733e1aa7471d7af7/plugins/hexaemeron/skills/metron/SKILL.md)
owns non-gas measurement. This study claims no runtime or memory improvement.
Its exact structural measurement command is
`python3.14 .hexaemeron/research/measure_design.py --candidate prepared-source-group --criterion baseline-work-count`.
The output is a work count. Runtime and evidence volume remain unknown until
all real groups execute. Capture plans must declare their finite limits before
capture; they may not describe an exhausted limit as successful coverage.
Hermes alone owns the later gas-target measurement and rejection decision.

## 11. Failure and recovery

The [Elenchus contract](https://github.com/wildcat-finance/skills/blob/8b0a7abbf80e2466dc32e477733e1aa7471d7af7/plugins/hexaemeron/skills/elenchus/SKILL.md)
owns reproduction and guard evidence. The observed V1 and V2 failures stop the clean
baseline transition. Preserve full and isolated failures, source locations
and counterexamples. Apply only the admitted test preparation in Step 1,
retain a failing-parent regression for each oracle repair, sign each harness
revision and show zero production/build-input difference before a new baseline.
Do not exclude failing tests or silently change the fuzz seed/bounds.

Missing source, incomplete owner handoffs, a red baseline, changed protected
set or an earlier-gate negative failure also stops the dependent transition.
Failed runs remain evidence; fresh attempts use new directories. Rejection
patches live only in disposable copies and are removed after their exact
patches and comparison records have been retained. No run directory may be
called sealed until its own canonical Gate 1 reports success.

## 12. Decisions and their homes

The [Hypomnema contract](https://github.com/wildcat-finance/skills/blob/8b0a7abbf80e2466dc32e477733e1aa7471d7af7/plugins/hexaemeron/skills/hypomnema/SKILL.md)
owns durable decisions. A successful continuation must record the source-group
split, protected-set inclusions/exclusions and any test-only preparation in
`docs/kickoff/1355/study.md`; exact reproduction commands and access boundaries
belong in `docs/kickoff/1355/README.md` with a machine-readable inventory.
A change to the owner's general promise or Hermes harness is outside this
application delivery and needs its own decision record and review.

All twelve sections are present and design-lock is clean for the revised
construction. This permits a runbook beginning with separate test-only
preparation; it does not permit Gate 1 yet. The protected set remains unreviewed
and capture, archive, baseline, rejection and restricted delivery evidence
remain pending at their explicit stops. No additional approval is required
for this local test-only preparation under the delivery request. Public
redistribution of private source still requires separately established
authority and an appropriate destination.

### Amendment -- 2026-09-22

**What changed.** Step 1 now admits three further, separately preserved
test-only preparations. For V2 pins
`5838b2f3f5c0bb3489cd2ff16bb31ddd5194c7fa` and
`e1f77540fef65736374de6c847743d8ca2233fb4`, and V1 pins
`da74452aa7d1a0f024d99efd22cc6d950a8116b7` and
`6164ddd4c75ef6da2181e5623b99795b9829e31c`,
`test/helpers/BaseERC20Test.sol` may replace the six active legacy
`testFail` methods with explicit arithmetic-panic assertions immediately
before their intended token calls. The insufficient-allowance fuzz case may
also constrain approval to `[minimum, maximum - 1]` and amount to
`[approval + 1, maximum]`; that preserves the full valid insufficient-
allowance domain and prevents a pre-call arithmetic or range failure from
standing in for the intended token failure. This is the focused semantic
repair from upstream commit `84b17dc`, not a general test-suite migration.

For pin `5838b2f3f5c0bb3489cd2ff16bb31ddd5194c7fa`,
`test/access/FixedTermHooks.t.sol` may change the invalid fixed-term input
from 366 days to 731 days. The production predicate at
`src/access/FixedTermHooks.sol` rejects terms strictly greater than its
unchanged `MaximumLoanTerm` of 730 days, so 731 days retains the asserted
greater-than-maximum condition. For V2 pin
`c7be4039f8f383a9dda4e45f63331c17d63f9ed9`, no source, configuration or
submodule patch is admitted: the two legacy failure methods live in the
vendored `erc4626-tests` submodule. After its archive SHA-256 and extracted
binary SHA-256 are recorded, an isolated local Foundry `0.3.0` binary may run
the unchanged, fixed-seed wrapper suite. It is a candidate runner only until
that download, digest verification and full result exist.

**Why.** Fixed-seed parent-red specimens isolate twelve inherited legacy
failure-convention cases for each of the two V2 BaseERC20 pins, one stale
fixed-term maximum-boundary case for pin
`5838b2f3f5c0bb3489cd2ff16bb31ddd5194c7fa`, two vendored wrapper cases for
pin `c7be4039f8f383a9dda4e45f63331c17d63f9ed9`, and one pre-call
`amount too large` failure in the same insufficient-allowance fuzz case for
each V1 pin. Their logs and localisation records are retained under the
restricted Step 1 evidence root. The earlier admitted timestamp and V1
preparations cannot make these groups green. Excluding methods, changing the
project test configuration, changing a dependency pin, or editing vendored
source would weaken or breach the source-parity gate.

**Steps touched.** Step 1 admits the named V1 and V2 test preparations and
the isolated historical-runner attempt. Step 3 must record the actual runner
version and verified binary digest for the wrapper group if it reaches a
baseline. Steps 2, 4 and 5 retain their existing entries and exits.

All production Solidity, build configuration, dependency pins, deployed source
identities and submodule gitlinks remain fixed. Every parent-red and prepared-
green result keeps its fixed seed, exact command, counts, digest, original pin
and signed prepared revision. No Gate 1, fixture, archive release, Gate 5
candidate or restricted delivery claim is admitted by this amendment.

**Still holding.**

Step 1: entry holds; exit holds.
Step 2: entry holds; exit holds.
Step 3: entry holds; exit holds.
Step 4: entry holds; exit holds.
Step 5: entry holds; exit holds.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | prepared-source-group
record | docs/decisions/drafts/prepare-signed-source-groups-for-hermes-estate-baselines.md
```
