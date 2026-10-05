# Wildcat V1/V2 canonical adapter runbook

This runbook implements issue 1378's receipted study, SHA-256 `f7956d890d7bab59b75ae6e511624e997e6dc815ea558cff64bb4c1e09d75f1a`, from Skills `b4af9c748a764287ccb9978937021e45cc81fc2d`. The selected construction maps preserved native logs by generation, emitter role and concrete deployed signature. Python `3.14.6`, stdlib production code, signed commits and the repository's checked runner remain required. Accounting replay and function reconciliation remain with issues 1386 and 1387.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 80282666266db259f1afb600ee981f28928fde0b077cf333967501672a04bb50
candidate | role-qualified
```

```command-interfaces
schema | protasis-command-interfaces/v1
plugins/tabularium/tests/prove_wildcat_v3.py | build_parser | step:1
plugins/tabularium/tests/emit_wildcat_v3_report.py | build_parser | step:1
```

```version-relations
tabularium | plugins/tabularium/skills/tabularium/EVOLUTION.md | next-generation-after-integration-base
```

Step 1 supplies both thin declarative interfaces. Their complete bytes stay fixed after its push; later behavior belongs in imported proof and focused-test modules. The proof interface accepts the design record's exact candidate, criterion and report arguments. The Elenchus interface accepts a Step number and report path and runs only that Step's focused tests without subprocesses. Registration validates declarations and arguments, not execution or safety.

The generation relation preserves the existing Compound Phase 1 frontier. Step 2 adds one evidenced generation row and matching skill metadata; integration rechecks the exact current base and resolves any generation drift through the controller's signed sync/revalidation path. Do not advance the evolution or replace the held job.

The study's checked inventory has no current assigned failure. Each Step still requires its controller-issued inoculation packet and exact no-known-findings record before product edits. Historical fixed cases become meaningful regression specimens; missing new code supplies no parent-failure or guarded verdict. A real failure follows Elenchus and, where it changes a receipted requirement, the append-only specification repair.

Before every commit, finish the required written-record sequence, regenerate portable installation copies when canonical sources change, and regenerate Horos boundary/census evidence before staging the green tree. Keep all six shipped Aave/Euler release directories byte-identical to the starting tree. Private captures, corpus members and generated private releases stay outside Git. Audit uses the recorded non-Solidity waiver, independent review, the repository suite and all three discipline lints; it supplies no Solidity-security claim.

## Step 1: Scaffold focused Wildcat evidence reporters

**Goal.** Supply stable proof/report interfaces and commit the admitted specification without claiming the adapter already exists.

**Entry.** The controller's exact Step 1 parent at the starting tree, with study/design receipts, the green baseline and the completed zero-assignment inoculation receipt.

**Exit.** The scaffold and its honest readiness/refusal tests pass `python3 scripts/run_checks.py --base b4af9c748a764287ccb9978937021e45cc81fc2d --scope tabularium --format json`.

Create thin registered parser files and imported proof/report implementations. The proof runner emits no passing semantic, schema or reproduction report before it executes the corresponding implementation checks. Unknown candidates/criteria, absent required artifacts, malformed arguments and unexpected infrastructure errors refuse. Focused Elenchus output uses actual unittest results and preserves errors separately from failed assertions. Its Step selection cannot silently expand into a broad suite or launch subprocesses. Retain the complete protected study/runbook/design bytes, selection observations, audit-reading index, capture-admission summary and source-pin inventory in the public specification bundle. Publish digests and bounded counts, never recovered payloads or credential-bearing response bytes.

**Files.** Add `plugins/tabularium/tests/prove_wildcat_v3.py`, `plugins/tabularium/tests/emit_wildcat_v3_report.py`, imported proof/report modules and focused scaffold tests. Add `docs/kickoff/1378/` specification/report copies and an honest README, plus `docs/decisions/drafts/keep-wildcat-canonical-events-bound-to-native-roles.md`. Update `tests/check-map-v1.json` only for necessary ownership and regenerate `.horos/boundary.json` and `.horos/census.json`.

**Tests.** Exercise real passing/failing/error unittest specimens, Step filtering, command argument refusal, stable report formats and unavailable conformance refusal. Check copied specification digests and absence of private payloads. The observed count belongs in the execution record. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_v3_report.py --step 1 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/fiat-1378-step-1.json`. Run the Exit command before handoff.

**Disciplines.** phylax: bound report paths, source-copy membership and private publication. ephoros: retain real test counts, error classes and exits. metron: none, no speed claim or optimization. elenchus: reproduce any actual scaffold failure through the focused reporter. hypomnema: record native-role dispatch, evidence classes and the self-contained release decision before implementation.

## Step 2: Implement native mappings and self-contained verification

**Goal.** Build the selected Wildcat adapters, precise schema branches and offline reproducible release path.

**Entry.** The green, audited and pushed Step 1 tree, both report interfaces bound to its exact source bytes, and the current Step's zero-assignment inoculation receipt.

**Exit.** Semantic/schema tests and old-release compatibility pass `python3 scripts/run_checks.py --base b4af9c748a764287ccb9978937021e45cc81fc2d --scope tabularium --format json`.

Before opening Step 3, execute the selected design's exact semantic-conformance and schema-parity resolvers; retain their real reports under `.hexaemeron/design-reports/`.

Add `wildcat-canonical --alexandria-release DIR --release ID --out NEW_DIR` and Wildcat-aware `verify coverage.json`. Reuse checked Alexandria readers deliberately, consume full native journals and bind generation, concrete ABI and emitter role to preserved registry/source evidence. Copy the verified raw release into `source/raw-release/`; bind it through `source.json`, retain complete original native logs, and reproduce canonical rows, mapping provenance, coverage and class-qualified supporting selectors from those bytes. New descriptors cannot bless altered parties or classes by merely rebinding hashes. Reject source/output aliases, links, unsafe paths, duplicate identities/keys, mismatched responses, conflicting metadata, malformed supported ABI, wrong epochs and partial output; maintain the study's byte/record caps and fresh atomic release completion.

Map all seventeen primary contexts with the study's actual parties and exact units. Deposit assets/scaled claims, withdrawal requests/payments, market-token transfers and wrapper assets/shares remain distinct. Preserve zero-address mint/burn and queue-custody endpoints. Borrow/closure have only observed pool parties; repayment records emitted payer without inventing debtor. Only the exact Wildcat market-closed tuples admit an empty financial amount list; timestamps stay native state. Old adapters and every financial action retain their original cardinality rules.

An unambiguous sanctions-routing companion retains beneficiary versus escrow recipient and both source selectors, with an explicit join-inference class and no second cash count. Missing or ambiguous companions remain qualified. Every scoped role/topic has one primary, supporting-routing, unsupported-canonical-meaning or unsupported-decode disposition. Attribution gaps may overlap mapped records, so document and verify their qualified counts separately from omitted events.

The retained V2 capture has fourteen recorded factory deployment bindings and 172 market transfers with wrapper counterparties, but no wrapper instance registry entries/epochs or native wrapper journal coverage. Use recorded factory context only at its declared evidence strength; do not invent runtime-code checks. Wrapper-native positives require source-bound constructed fixtures with the relevant admitted context; real capture reports keep the absent-coverage limitation. Wrapper assets are the market token and shares the wrapper token; no shareholder look-through or underlying cash-flow inference is allowed.

**Files.** Extend `plugins/tabularium/scripts/tabularium.py`, `plugins/tabularium/scripts/tabularium_lib/` adapter/build/verify/validation modules, both v3 schema files, imported proof modules and focused semantic/schema tests. Add `plugins/tabularium/docs/wildcat-canonical.md` and mapping/source/disposition records under `docs/kickoff/1378/`. Add the generation row in `plugins/tabularium/skills/tabularium/EVOLUTION.md`, matching `SKILL.md` metadata and required plugin metadata. Refresh affected portable copies and Horos metadata. Keep registered interface bytes fixed.

**Tests.** Assert actual-party mappings, pool-only amount events, third-party payer, executor versus account, wrapper instruments, mint/queue/burn semantics, exact empty-amount qualification, sanctions joins/ambiguity, all qualified dispositions and complete source reproduction. Mutate payer/borrower, units, selector, class, role, ABI arity/indexing/width/padding, unreleased indexed-actor declaration, source digest, duplicates and output aliases independently. Run JSON-Schema/Python parity with the locked oracle, and rebuild/verify all six unchanged older examples. Missing parity execution fails. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_v3_report.py --step 2 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/fiat-1378-step-2.json`. Run the Exit command and both due design resolvers before handoff.

**Disciplines.** phylax: verify untrusted raw files, decoder limits, sibling loading and atomic writes. ephoros: emit bounded release/generation counts, digests and named refusals. metron: none, preserve bounds without promising throughput. elenchus: reproduce and guard actual decoder/validator failures. hypomnema: explain tuple compatibility, native units, qualified gaps and recovery in the stable decision and user guide.

## Step 3: Publish constructed V1 and V2 release specimens

**Goal.** Ship immutable public releases that exercise all primary contexts and representative unsupported paths honestly.

**Entry.** The green, audited and pushed Step 2 implementation, selected semantic/schema reports admitted at `step:3`, stable interfaces and the current Step's zero-assignment inoculation receipt.

**Exit.** Both constructed releases reproduce byte-for-byte and pass `python3 scripts/run_checks.py --base b4af9c748a764287ccb9978937021e45cc81fc2d --scope tabularium --format json`.

Create deterministic constructed Alexandria inputs and canonical outputs for V1/V2. Label their synthetic status in source scope, manifests and READMEs. Include market deposits, queue/execution, transfers, draw/repayment/closure; V2 wrapper wrap/unwrap/share transfers; registry-derived debtor context; third-party payer; sanctions routing; and decoded/undecoded unsupported examples. Bind actual generated digests and per-event mapping/disposition rows. Construction establishes no historical chain activity. Every canonical row resolves to its complete raw log and reproducible mapping context. Keep deployment/interface-only variants and real capture limitations separate from these fixtures.

**Files.** Add `plugins/tabularium/examples/wildcat-v1-v0/` and `plugins/tabularium/examples/wildcat-v2-v0/`, bounded deterministic fixture builders and reproduction/refusal tests. Extend only imported proof modules, mapping documentation and affected demonstration/front-door records necessary to expose the shipped capability. Regenerate portable copies and Horos metadata where required. Preserve the original six example trees and registered interfaces.

**Tests.** Independently rebuild each public fixture in a fresh directory, compare every declared release file, verify without external input paths and exercise stale source/mapping/coverage/party mutations. Refuse synthetic evidence represented as a real capture, omitted event/disposition rows, mislabeled wrapper assets, duplicated support cash and mutable published-release overwrite. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_v3_report.py --step 3 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/fiat-1378-step-3.json`. Run the Exit command before handoff.

**Disciplines.** phylax: confine fixture construction and immutable output writes. ephoros: retain bounded example identities, mapping counts and real refusal exits. metron: none, no performance claim. elenchus: reproduce any reproduction or fixture-integrity failure. hypomnema: label constructed evidence and give exact consumer recovery commands.

## Step 4: Demonstrate offline public and preserved-capture reproduction

**Goal.** Deliver executed offline acceptance/refusal evidence and the bounded consumer handoff for issue 1378.

**Entry.** The green, audited and pushed Step 3 public specimens, all earlier bindings intact and the current Step's zero-assignment inoculation receipt.

**Exit.** Execute `python3 plugins/tabularium/tests/prove_wildcat_v3.py --candidate role-qualified --criterion release-reproduction --report .hexaemeron/design-reports/role-qualified-release-reproduction.json` and `python3 scripts/run_checks.py --base b4af9c748a764287ccb9978937021e45cc81fc2d --scope tabularium --format json`.

Run the study's build/verify demo path on both public fixtures and both admitted preserved captures with network use disabled in the demonstrated execution path. Retain actual argv, positive exits, source/release digests, generation/native/canonical/disposition counts, input/output bytes and measured durations. Move completed releases away from their original inputs and verify self-contained reproduction. Alter copies' party, amount shape, selector, mapping class and raw source independently; unexpected acceptance or infrastructure failure is a failed demo. The selected release-reproduction report must reflect actual executed checks before integration. Private raw/canonical outputs and detailed ledgers remain outside Git; publish bounded digests/counts and explicit coverage limits only.

Update the user guide and public front door to the delivered operation. Draft the run-level PR with recognised `Closes wildcat-finance/skills#1378`, exact validation evidence, audit pointer and a fenced carried-forward disposition block. Draft the task-issue closing comment with explicit integration URL/status placeholders, then fill and recheck the complete publication sequence at integration. Accounting and downstream research conclusions remain with their existing owners. Fiat owns all audit/prose/push/checkpoint/merge receipts and final controller cleanup.

**Files.** Complete bounded execution/handoff/recovery reports in `docs/kickoff/1378/`, user/front-door documentation, imported demonstration/proof code and focused tests. Finish required generation/plugin consistency and generated metadata. Preserve source-bound specification/selection files and the registered parsers; regenerate digest-bound derived records only through their owning builder.

**Tests.** Run the actual CLI entry and parser in the demonstrated offline path, require all expected refusals, check moved-release reproduction and ensure private payloads are absent from the public inventory. Keep wrapper-native noncoverage, provider/finality limitations, recorded/inferred classes and unsupported attribution explicit in both real-capture summaries. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_v3_report.py --step 4 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/fiat-1378-step-4.json`. Run both Exit commands before handoff.

**Disciplines.** phylax: enforce offline execution and private/public custody. ephoros: record every observed acceptance/refusal with exact bounded identities. metron: retain measured duration/bytes without a speedup claim. elenchus: preserve unexpected acceptance and report infrastructure errors honestly. hypomnema: publish recovery, handoff and remaining coverage limits with the final capability.
