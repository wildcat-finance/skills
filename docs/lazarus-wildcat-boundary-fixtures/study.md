# Study: fixed-block fixtures at the sealed Wildcat captures' finalized boundaries

Task: https://github.com/wildcat-finance/skills/issues/1384 (`kickoff/lazarus-34`).
Run branch `fiat/1384-lazarus-34-fixed-block-fixture-at-a-sealed`, cut from
`main` at `2dbfe40e08ee41429c521e0089a31ed872a1890d`. Surveyor: this study's
author, working from the value map under `docs/kickoff/1384/` and fresh reads of
public Ethereum state on 2026-09-27. No capture, proof or release is claimed
here; every number below is a measurement or a count, and `lazarus verify` is
what turns a word into proof.

Assuming, unless corrected:

1. Two fixtures, one per estate, each at the boundary its capture reports:
   Wildcat V1 at block 22074622 and Wildcat V2 at block 26022093. The value map
   and both proof-target lists cover both estates, and #1374 bound one dataset
   statement per estate.
2. 22074622 is a scope bound, not a finality observation. The maintainer ruled
   on 2026-09-26 that V1 ends where the last Wintermute V1 market closed
   (`MarketClosed` on `0x50ebdf73a0df61b782cea489e8102b3bfde0bda6`, transaction
   `0xb0cf59e6246f304b1ce723cd920791f50c1eb775bd6b9f091eaccec6fdc4c6de`, in that
   block) and that later V1 activity is neither a gap nor a reason to widen
   anything. `docs/kickoff/1384/values.md` labels both blocks "Finalized boundary
   reported by the capture"; this run re-reads each header by number and does not
   re-derive a finality choice from chain.
3. The interpreter is the one `.python-version` names, 3.14.6, with Lazarus's
   pinned `plugins/lazarus/requirements.lock` installed. Foundry 1.7.1 was used at
   study time only, to compile storage layouts from public pinned sources; no
   step needs it.
4. The Wildcat gateway remains the capture route, read through the environment
   variables `ALEXANDRIA_COMPOUND_RPC_URL` and `ALEXANDRIA_RPC_BEARER` from
   `~/.config/alexandria/rpc.env`, sourced in a subshell and never written down.
   The local archive node stays as configured; it serves headers, receipts, code,
   calls and storage but refuses historical proofs, and nobody restarts it.
5. Fixture bytes live outside the skills tree. The maintainer ruled on 2026-09-26
   for the #1924 run that Wildcat fixture custody is Miskatonic and its R2 buckets,
   through a handoff pull request under `storage/r2/handoffs/`. On 2026-09-27 the
   maintainer confirmed that custody for these fixtures and declined a public
   copy; section 12 records both answers.
6. This is ordinary delivery. The Lazarus ledger is mature at `lazarus-v3.2.0`;
   any shipped Lazarus change is a generation bump declared in the runbook's
   `version-relations` block, and the frontier sentence and held job stay
   byte-identical. Ariadne's tree is not expected to change.

## 1. Problem statement

**What.** One Lazarus plan-v3 fixture per Wildcat estate on Ethereum mainnet,
at the block where that estate's sealed interval capture reports its finalized
boundary, proving under EIP-1186 every storage word behind every number the
accepted value map says a consumer will print, proving the code at every subject
address against its `codeHash`, recording the value map's finite request
inventory byte for byte as `recorded-rpc` evidence, and carrying one ordered
receipt witness whose target receipt and filtered-log projection reconstruct
`receiptsRoot` offline. Each fixture is released unsigned with an Ariadne
`state-fixture/v2` statement and a Lazarus release-v2 binding, and admitted into
an Alexandria release as a `proof-backed-state` capture so downstream views can
name it as input. Every value in the map gets a row saying whether its relation
is proved, header-bound or merely recorded.

**Who.** The Miskatonic consumers named on the issue (W03 and the fixed-block
part of W06/D02), the Tabularium and Probitas standing views that take
`--lazarus-fixture` beside an Alexandria release, and the opening-state (#1386)
and repayment-window (#1393) work that starts from these boundaries.

**Working prototype.** Both fixtures verify offline from local bytes, both
releases verify, both statements verify, altered bytes are refused, and a
stranger with the skills checkout plus the release archives can repeat all of it
without a network. From the repository root:

```bash
python3 plugins/lazarus/examples/wildcat-boundary-v0/plan_v3.py --generation v1 \
  --probe plugins/lazarus/examples/wildcat-boundary-v0/probe-v1.json --out <fresh-v1-plan>
python3 plugins/lazarus/examples/wildcat-boundary-v0/plan_v3.py --generation v2 \
  --probe plugins/lazarus/examples/wildcat-boundary-v0/probe-v2.json --out <fresh-v2-plan>
python3 plugins/lazarus/scripts/lazarus.py verify "$WILDCAT_BOUNDARY_V1_RELEASE/fixture"
python3 plugins/lazarus/scripts/lazarus.py verify "$WILDCAT_BOUNDARY_V2_RELEASE/fixture"
python3 plugins/lazarus/scripts/lazarus.py verify-release "$WILDCAT_BOUNDARY_V1_RELEASE"
python3 plugins/lazarus/scripts/lazarus.py verify-release "$WILDCAT_BOUNDARY_V2_RELEASE"
python3 plugins/ariadne/scripts/ariadne.py verify "$WILDCAT_BOUNDARY_V1_RELEASE/statement.json"
python3 plugins/ariadne/scripts/ariadne.py verify "$WILDCAT_BOUNDARY_V2_RELEASE/statement.json"
python3 plugins/lazarus/examples/wildcat-boundary-v0/demo.py mutations
python3 plugins/lazarus/examples/wildcat-boundary-v0/demo.py verify-preserved
```

Success criteria, each checked by a command:

1. Both generated plans are byte-identical to the digests the example commits
   (`sha256` printed by `plan_v3.py`), and `lazarus.py validate plan` exits 0 on
   each. Measured now: V1 `13770a6987eed0c819809c6d68c8874a1fe243b148021a9cbee29511b736fa1c`,
   196,264 bytes, 434 requests, 21 proof targets, 244 slots; V2
   `0dcfbc330633ceb29e4c67819e33639681ef58e9ce4a0628bb7de316f20c285a`, 7,041,376
   bytes, 14,561 requests, 151 proof targets, 9,080 slots.
2. `lazarus.py verify` exits 0 on each fixture and reports `proof_backed` equal
   to targets plus slots (V1 265, V2 9,231), `header_bound` 1, `recorded_rpc`
   equal to the request count, and `receipt_trie_proved` 2.
3. `verify-release` and `ariadne.py verify` exit 0 on each release and statement,
   and the statement's four evidence counts equal the verify report's.
4. `demo.py mutations` exits 0 only when, for each estate, a changed storage
   value, a changed code byte and a changed receipt byte each make `verify` exit
   non-zero (six refusals), and the unchanged fixture still verifies.
5. `demo.py verify-preserved` exits 0 offline from the committed digests and
   reports alone, and refuses when a committed digest is edited.
6. The per-value relation report lists all 61 map rows for each estate with one
   class each (`proved`, `header-bound`, `recorded`, `unsupported`) and the
   proof target or request that backs it; a row without a backing entry fails
   the example's own check.
7. The root suite, the Lazarus suite and the Ariadne suite are green at every
   step exit: `python3 -m unittest discover -s tests`,
   `python3 plugins/lazarus/tests/run_tests.py`,
   `python3 plugins/ariadne/tests/run_tests.py`, and
   `python3 scripts/run_checks.py` selects and passes its checks.

**Demo path.** The last step runs the block above and records each command's
exit and output digest in `docs/lazarus-wildcat-boundary-fixtures/proof.md`. The
bounded negative observations are the six mutation refusals and one edited-digest
refusal; the demonstration claims nothing about canonical-chain membership,
provider independence or values the map marks unsupported.

**Step sketch.** Four steps, in dependency order: Step 1 scaffolds (committed
study, runbook, design record, the decision draft, and the example directory with
the probe, slot module, generator, boundary summaries and a test that regenerates
both plans to their digests); Step 2 captures and verifies both fixtures over the
gateway and writes the relation report; Step 3 writes the Ariadne statements,
Lazarus releases and Alexandria admissions and the mutation demonstration; Step 4
raises the Miskatonic handoff pull request, records digests, bumps the Lazarus
generation and runs the demo path. The runbook decides the exact split; the two
pending conformance cells in the design record are due at integration.

## 2. Prior art

**In this repository.**

- Lazarus plan v3 and the receipt witness: `plugins/lazarus/schemas/plan-v3.json`,
  `plugins/lazarus/schemas/receipt-witness-v1.json`,
  `plugins/lazarus/scripts/lazarus_lib/receipts.py` (the scoped relation yields
  exactly two proved relations, and the projection is computed over every receipt
  in the block against the declared filter),
  `plugins/lazarus/scripts/lazarus_lib/capture.py` (one `eth_getProof` per target
  with its whole slot list, then `eth_getCode`; a hash selector with number
  fallback; nothing written until final verification passes). The shipped scoped
  example is `plugins/lazarus/examples/aave-v4-spoke-v1/` (177 receipts, target
  index `0x3f`); the empty shape is
  `plugins/lazarus/tests/fixtures/ethereum-genesis-empty-receipts-v1/`.
- Ariadne state-fixture/v2: `plugins/ariadne/docs/state-fixture.md`,
  `plugins/ariadne/docs/capturing-a-state-fixture.md`; the capture copies the
  manifest's counts and never recounts. `plugins/lazarus/docs/preservation-release.md`
  explains why `release` holds the statement to what `verify` recomputed.
- Alexandria's `proof-backed-state` class:
  `plugins/alexandria/examples/proof-backed-state-v0/input/capture-plan.json`
  embeds a Lazarus fixture as components with `role` `lazarus-manifest` and
  `lazarus-fixture-file`; `verify release` reconstructs the fixture and reruns
  Lazarus.
- The value map: `docs/kickoff/1384/values.md`, `values.json` (61 rows),
  `scope.json` (16 V1 and 137 V2 subjects, both anchors, source pins),
  `population.json`, `request-spec.json`, `selectors.json`,
  `capture_requests.py` (431 V1 and 14,558 V2 requests, all `recorded-rpc`,
  including `eth_getCode` and an empty-slot `eth_getProof` per subject), and
  `proof-targets-v1.json` / `proof-targets-v2.json` (account and code checks
  only; the map states that absolute slots were not established there).
- The sealed captures and their statements:
  `plugins/alexandria/examples/wildcat-v1-interval-v0/` and
  `wildcat-v2-interval-v0/` (issue #1731, PR #1838, merge
  `104f6f82c390003fb61039d3023d07c1abe05086`), and
  `plugins/ariadne/examples/wildcat-datasets-v0/` (issue #1374, PR #1850), whose
  runbook carries a `version-relations` block for a generation bump and whose
  README keeps full releases outside the tree.
- The #1924 run's custody design, in that run's `.hexaemeron/runbook.md`
  amendment of 2026-09-26: a handoff directory under `storage/r2/handoffs/` with
  each archive's size and SHA-256 and a proposed source-register row, uploaded
  only through Miskatonic's custody tooling after the operator accepts the row.
  The existing handoff of that shape is the Lemma corpus one named on #1359.

**Last two merged pull requests touching Lazarus.** PR #1833 (merged
2026-09-22, `e9e95b891b3ae642516e017c46b97a18a1480164`) touched
`plugins/lazarus/` only through merges from `main` (package versions, the
generated Promise Machine copy, the test runner); it carried nothing for
fixtures. PR #1820 (merged 2026-09-21, `0882ae10d068d810ab481834305658a227eafe74`)
fixed the runner's aliased `--elenchus-report` path and left one item open by
name: invoked through a symlinked absolute script path,
`test_runner_discovers_tests_from_the_plugin_root` fails because `main()` uses
`os.path.abspath(__file__)`. That stays open; this run does not invoke the
runner through a symlink and does not change the runner. The last merged pull
request that changed fixtures and witnesses is PR #1457 (issue #1360, merged
2026-09-07, `b4f59134e4cf8e8d8da17f908bcfe5275c4559a5`), whose carryover row is
`none`. PR #665 (issue #383) before it added the scoped witness.

**Carried forward from the prerequisite deliveries.** PR #1850's one carryover
is a Tabularium test that expects an unquoted report path
(`plugins/tabularium/tests/test_schemas.py:795`); outside this run. PR #1838's
carryover names, among others, `fiat-1350-boundary-leads` (an unconfirmed
finality-boundary comparison lead) and twelve unknown V1 deployment blocks; both
stay as recorded, because this run reads each boundary header by number and
proves state at it without claiming finality or deployment history. PR #1900's
carryover routes the final-boundary state here and the opening state, repayment
control windows, native event mapping, withdrawal policy, end-account attribution
and display contract to #1386, #1393, #1378, #1495, #1497 and #1389; none is
picked up here.

**Audit records.** `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the worktree root on 2026-09-27 and exited 0 with every row
`committed=match`, so each verified synopsis was the reading view; every source
stays authoritative. Lazarus has no plugin-level `audit/` directory; its rounds
are under the root `audit/rounds/`. Sources were found by `grep -rli lazarus audit/`
and by name.

| Source | View read | Rounds, finding rows | Open or accepted items and leads |
| --- | --- | --- | --- |
| `audit/rounds/fiat-1360-empty-block-receipt-witness.md` | synopsis | 5, 2 | both fixed (S1-R1-01 Hypomnema H008 study bridge; S3-R1-01 proof prose); leads: live-provider recapture stays outside an offline audit, 16 Brevitas B023 glossary signals in Lazarus docs |
| `audit/rounds/fiat-383-prove-receipts-against-the-captured-header-s.md` | synopsis, plus a source grep for S2-R1-03 | 33, 86 | S1-R1-01 (witness called transaction hashes header identities) closed under the amended consensus-only boundary; S2-R1-03 (replay omitted `eth_getBlockReceipts`) closed under the receipted Step 2 replay amendment; all other rows fixed |
| `audit/rounds/fiat-386-record-a-structured-multi-provider-chain-anc.md` | synopsis | 3, 0 | leads name runtime controls owned by its later steps; none open |
| `audit/rounds/fiat-387-pin-rpc-boundary-failures-into-lazarus-fixtu.md` | synopsis | 1, 0 | lead: a synopsis-pair count fixed in digest-bound text |
| `audit/rounds/fiat-407-emit-an-ariadne-ready-release-statement.md` | synopsis | 3, 4 | all fixed; leads none |
| `audit/rounds/fiat-881-macos-path-repair-clean-run.md` | synopsis | 8, 7 | all fixed (Lazarus `paths.py`, `release.py`, workflow, Goldfinch tests) |
| `audit/rounds/fiat-621-isolate-disposable-fixture-signing.md` | synopsis | 12, 13 | S4-R2-01 low open: cleanup missing from that runbook's exit blocks; not Lazarus code, outside this run |
| `audit/rounds/fiat-622-*.md` (four files) | synopsis of `carryover-3`; the others by name only | 12, 128 | rows concern `scripts/run_checks.py`; found by the grep because their Not-checked lines name Lazarus; outside this run's subject |
| `audit/rounds/fiat-1374-bind-the-sealed-wildcat-captures-to-dataset.md` | synopsis | 2, 0 | lead: the Tabularium quoted-path test above |
| `audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.md` | synopsis | 30, 42 | open: W1-R1-02 (docs), W6-R4-01 (schema restoration blocked by the portable package), W7-R1-01 and W8-R1-01 (runbook amendments, W8 corrected by a dated erratum); Elenchus verdicts inconclusive or unguarded as recorded; all Alexandria, none touched here |
| `audit/rounds/fiat-1355-fresh-seal-wildcat-v2-layouts-and-selectors.md` | synopsis | 14, 14 | all fixed |
| `audit/rounds/fiat-402-implement-the-grounded-agent-predicate.md` | synopsis | 40, 76 | eleven Step 3 rows carry a status other than fixed in their round snapshot; grounded-agent subject, not state-fixture; outside this run |
| `plugins/ariadne/audit/AUDIT.md` | `AUDIT_SYNOPSIS.md` | 21, 23 | all fixed; accepted leads: homoglyph keys and one subject standing in for another (recorded in `plugins/ariadne/docs/conformance.md`), short key formats, replay is a guard not a sandbox; `[missing legacy field: …]` entries stay unknown |
| `audit/AUDIT.md` | keyword grep of the source; its synopsis covers the root pair | not counted | the 2026-08-19 state-fixture rounds' lead about the Lazarus README frontier sentence, since governed by the Lazarus ledger; legacy fields missing |

**Known failures.** No in-scope source names an open failure in a Lazarus or
Ariadne code path this run exercises: the open rows above are documentation,
runbook, package and other-skill items. The study therefore carries no
known-failure inventory, and the runbook carries no assignment.

**Outside.** EIP-1186 (`eth_getProof`), EIP-1898 block-hash selectors,
EIP-1967 proxy storage slots, ERC-7201 namespaced storage, the ZeppelinOS
implementation slot used by Circle's proxies, and the Reth `--rpc.eth-proof-window`
flag, whose default refuses a proof more than zero blocks behind the tip.

## 3. Constraints and non-goals

**Starting ref.** `2dbfe40e08ee41429c521e0089a31ed872a1890d` on `main`; run
branch `fiat/1384-lazarus-34-fixed-block-fixture-at-a-sealed`; controller
hexaemeron 1.6.84 (`fiat-v6.75.1`); Python 3.14.6; Lazarus skill `lazarus-v3.2.0`
and package 1.1.6; Ariadne skill `ariadne-v3.5.0` and package 1.3.6; Alexandria
package as on `main`. Source pins for slot derivation: `wildcat-finance/wildcat-protocol`
at `da74452aa7d1a0f024d99efd22cc6d950a8116b7` and `wildcat-finance/v2-protocol`
at `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657`, as `docs/kickoff/1384/evidence/sources.json`
names them; a compiled layout describes source, so every derived word was
checked against the deployed getter (section 4).

**Boundaries.**

| Header field | V1 | V2 |
| --- | --- | --- |
| Block | 22074622 (`0x150d4fe`) | 26022093 (`0x18d10cd`) |
| Hash | `0x8250ddca64f965fb77cb75a42d2054f9fcd3e4fd13aa657e1dcbfa04e4807a47` | `0x1cfd09b6dfaa2af921e367d94f24e2b1e6b7f910a7a6f4276576f09aeb3f5cb9` |
| `stateRoot` | `0xfd8d82efd16449c6edb1beda49c71ea906d8e5fa1175940a94dd7c55eb7b0c8d` | `0xbad68837d5e230b2301cacc598a139a89c57b936757bcf0f7ca6b57417343c8c` |
| `receiptsRoot` | `0xb227237b8674350bbabbc7578a23cb1db8225ac17f8c354c5c449457c45b5aba` | `0xf5c61d54d9e67401bebc8e22d823d47ab8782201226c66ec2d013395bc33feb1` |
| Timestamp | 1742311271 | 1789947863 |
| Transactions, logs | 226, 298 | 216, 483 |

Both hashes equal the value map's anchors. The local archive reported head
26064148 and finalized 26054743 at probe time, which is why the V1 block is a
scope bound rather than a finality reading.

**Rulings carried, not re-derived.** Interval ends are scope bounds; both
estates; capture bytes and corpus bytes stay private and never enter this tree
or this study; fixture bytes do not get vendored into the tree; public prose is
written as if the protocol data is to hand; the gateway token is sourced only in
a subshell; the local archive is not restarted or reconfigured; no frontier or
held job changes.

**Measured route facts, 2026-09-27.** The local archive (Reth 1.11.0) served
headers, block receipts, code, calls and storage at both boundaries and refused
`eth_getProof` at both with `distance to target block exceeds maximum proof
window`, while serving it at `latest`. The gateway served `eth_getProof`, block
receipts, code and calls at both boundaries, including the largest V2 market's
2,496 slots in one call (7,309,344 bytes in 4.25 s) and batches of ten. One
keyless public archive route served the same proofs but caps a call at 1,024
storage keys and refuses batches above three; another keyless route refuses
every archive read with a token demand while serving block receipts. The
capture therefore runs with the gateway as primary and the two archive routes as
anchor sources named by opaque ids (`local-archive`, `public-archive`); provider
URLs stay in environment variables and enter no artefact.

**Limits the plans carry.** `max_requests` is twice the request-plus-proof
count plus 64 (V1 1,048; V2 29,794); `max_component_bytes` 134,217,728;
`max_total_bytes` 536,870,912; `max_elapsed_seconds` 3,600 for V1 and 7,200 for
V2, against projected captures of 25.9 s and 598 s at the measured 36 ms per
request. Lazarus's default batch size of three fits every route probed.

**Always.** Both suites and the root suite before a commit. Imprimatur on every
shipped document. A recorded measurement before any performance change. The
request inventory checked against `request-spec.json` before a plan is written.

**Ask first.** Adding a dependency. Changing a Lazarus or Ariadne schema. Touching
CI. Any home for fixture bytes other than the one selected. Any capture route
other than the gateway. Restarting or reconfiguring the local archive node.

**Never.** Commit an RPC credential, a provider URL or a raw provider error.
Copy capture, corpus or other private-repository bytes into this tree, this study
or a fixture. Call an `eth_call` result proved. Edit a receipted digest. Delete a
failing test to make a suite pass. Claim a command ran when it did not.

**Non-goals.** Opening state, constructor evidence and settled-batch history
(#1386). The two repayment control windows (#1393). Any value the map marks
`unsupported` (borrower debt, reserves, borrowability, the five `withdrawal.*`
rows and the six `display.*` rows): they get no proof target and no claim.
Market `name` and `symbol` (not numbers). Canonical-chain membership and
provider independence. A signed statement. Re-deriving the boundary. Changing
Lazarus verification or its evidence classes.

## 4. Design options

All four candidates share the value-to-word map below; they differ in how much
of it is proved and where the bytes live. The record at
`.hexaemeron/design-evidence.json` selects; this prose explains.

**The map.** Every supported row resolves to one of four sources:

| Rows | Source at the boundary | Class |
| --- | --- | --- |
| the 13 (V1) or 14 (V2) `state.*` rows and everything `currentState()` derives from them (`credit.totalLenderClaims`, `credit.accruedFees`, all `native.*` aggregates) | the four `_state` words: V1 slots 3 to 6, V2 slots 0 to 3, with `protocolFeeBips` packed into V2's fourth word | proved word, recorded view |
| `credit.totalAssets` | the underlying token's balance word for the market address | proved word |
| `native.unpaidExpiries` | the queue head word (V1 slot 8, V2 slot 5: `startIndex` low, `nextIndex` high) and one data word per live index (V1 base 9, V2 base 6) | proved words |
| `native.scaledBalance`, `native.balance` | `_accounts[account]` (V1 base 7 with `AuthRole` in byte 0, V2 base 4) | proved word, recorded view |
| `native.batch.*` | two words per expiry under `batches` (V1 base 10, V2 base 7) | proved words |
| `native.account.*`, `native.availableWithdrawal` | one word under `accountStatuses[expiry][account]` (V1 base 11, V2 base 8) | proved word, recorded view |
| `credit.asset`, `config.*`, `native.assetDecimals`, `native.delinquencyFee`, `native.gracePeriod`, `native.batchDuration`, V1 `config.protocolFeeBips`, V2 `config.hooks` | immutables in the market's runtime code | proved code, recorded call |
| `credit.observedAt` | the header timestamp | header-bound |

The bases come from `forge inspect src/market/WildcatMarket.sol:WildcatMarket
storageLayout` over the pinned sources (V1 also holds `_reentrancyGuard` at 0,
`name` at 1, `symbol` at 2 and `allowance` at 12; V2 holds `allowance` at 9). The
probe then read every derived word from the local archive at the boundary and
compared it with the deployed getter: V1 91 state fields over 7 markets, 30
account words, 61 status words, 7 queues and 54 of 55 batch pairs agreed; V2
1,120 state fields over 80 markets, 2,312 account words, 3,098 batch words as
1,549 pairs, 3,175 status words and 80 queues agreed. The one V1 disagreement is
market `0x605309f21c1864bb0522781a2f97b91fe3a48601`, expiry 1742310239, which
is that market's `pendingWithdrawalExpiry` and had passed 1,032 s before the
boundary: `getWithdrawalBatch` simulates the expired pending batch as paid,
while the stored words hold the pre-payment amounts. That is the map's own
warning that a view can simulate, and the relation report will mark that pair
as proved word with a differing recorded view.

Underlying tokens: V1 uses WBTC (balance base 0), USDC (base 9, behind a
ZeppelinOS proxy pointing at `0x43506849d7c04f9138d1a2050bbf3a0c054402dd`), WETH
(base 3) and USDT (base 2). V2 adds EURC (base 9, same implementation as USDC),
USDe (base 2), cbBTC (base 9, proxy to `0x7458bfdc30034eb860b265e6068121d18fa5aa72`),
sUSDe (base 4, recognised through a recent holder because its one market holds
zero at the boundary), SOL (base 5, beacon `0x3ee18b2214aff97000d974cf647e7c347e8fa585`)
and USST (an ERC-7201 `openzeppelin.storage.ERC20` namespace behind an EIP-1967
proxy to `0x1497a376d4c0d9bea9682070b131e921d3e5375d`). Each proxy's pointer word
and each implementation's code are proof targets too, so the layout a balance
word is read under is itself pinned. Twelve USDC and nine USDT V2 markets hold a
zero balance at the boundary; those words are proved absent, which is a result.

The full plans validate under `lazarus.py validate plan` and under capture's own
plan acceptance. V1: 434 requests, 21 targets, 244 slots, words state 28, queue
heads 7, queue entries 0, accounts 30, batches 110, statuses 61, balances 7,
pointers 1, implementations 1. V2: 14,561 requests, 151 targets, 9,080 slots,
words state 320, queue heads 80, queue entries 10 (four markets), accounts
2,312, batches 3,098, statuses 3,175, balances 80, pointers 5, implementations
4. One V1 call and four V2 calls revert at the boundary and stay recorded
errors; their rows report unsupported coverage.

**Receipt witness.** V1's block holds one receipt with a market log: index 224,
the closing transaction above, 5 logs; the filter is the seven V1 market
addresses at the block hash and projects 3 logs. V2's block holds no market
log, so the rule falls through to the lowest-index receipt carrying a log from a
V2 underlying asset: index 0, transaction
`0x426ffe56369a9569f5e08d4a0d5d0b90afaed5971fa76fadc18b3d24333bb5be`, 7 logs;
the filter is the eighty V2 market addresses and projects zero logs, which is
the proved statement that no market event sits in the boundary block. Both
witnesses yield the scoped shape's two relations; transaction hashes stay
recorded.

**Candidates.**

1. `full-map-r2-handoff` (selected). Everything above, captured over the
   gateway, with each estate's fixture, Lazarus release and Alexandria release
   archived and handed to Miskatonic through a pull request adding a directory
   under `storage/r2/handoffs/` in the shape of the Lemma handoff: archive
   sizes, SHA-256s and a proposed source-register row. Skills keeps the
   generator, slot module, probe summaries, digests, relation report and
   demonstration (156,744 bytes measured). Trade: a stranger needs Miskatonic
   access to fetch the bytes; the upload waits on the operator accepting the
   row, so the run carries it forward by name if that has not happened by
   integration.
2. `full-map-archive-repo`. The same fixtures with archives committed to the
   private archive repository beside the interval captures. Identical
   measurements; loses on the 2026-09-26 ruling, which moved fixture custody to
   R2.
3. `full-map-in-tree`. The same fixtures under `plugins/lazarus/examples/`. The
   fixture and release copies measure 117,913,418 bytes against a portable
   package margin of 2,256,023 bytes; fails the space gate and the vendoring
   ruling.
4. `state-words-in-tree`. Prove only the state words, queue heads and code and
   leave accounts, batches, statuses and balances as recorded calls. It still
   measures 78,480,052 bytes in-tree, because the recorded calls and code
   dominate, and it fails `mapped-words-proved` because the map's per-account and
   per-batch numbers would no longer be proved.

**How the record selects.** Nine selection criteria across the five concerns:
`mapped-words-proved` and `unexplained-getter-mismatches` (correctness),
`projected-capture-milliseconds` (time, 620,524 ms for the full map against the
plan ceiling of 86,400,000), `in-tree-bytes-within-margin` and the metric
`in-tree-bytes` (space), `capture-route-serves-boundary`, `plan-validates` and
`no-provider-coordinate-in-plan` (compatibility), and
`interrupted-capture-leaves-nothing` (recovery, which runs three Lazarus
capture guards by name). Candidates 3 and 4 fail gates; 1 and 2 tie on the one
metric, so the rule is `user-policy` with the 2026-09-26 custody ruling as
`policy_ref`. Two conformance cells stay pending until integration for every
candidate: `altered-bytes-refused` (`demo.py mutations`) and
`state-fixture-v2-binds` (`demo.py verify-releases`), both resolved by
`.hexaemeron/design/resolve.py` against the release trees named by
`WILDCAT_BOUNDARY_V1_RELEASE` and `WILDCAT_BOUNDARY_V2_RELEASE`. The design-lock
check exited 0 on 2026-09-27.

**A fifth home the record does not contain.** A public copy of these fixture
bytes, which are fresh reads of public chain state keyed by addresses already
public in `population.json`, for example as an asset on a skills release. The
maintainer declined it on 2026-09-27, as section 12 records.

## 5. Risk register seed

```risk-register
slot-derivation | the compiled layout against the deployed accounts | every proof-target word is one the probe compared with a deployed getter at the boundary, and the generator refuses a market whose word counts differ from the probe's
view-versus-stored | rows whose getter simulates state | the relation report marks each such row as proved word with a recorded view and never copies the view into the proved column
token-layout | balance words under fourteen token layouts, four behind proxies | each balance word was recognised by equality with balanceOf at the boundary, each pointer word and implementation is a target, and an unrecognised layout refuses generation
inventory-identity | the 431 and 14,558 request rows | the generator checks the expanded bytes against request-spec.json before appending the three witness rows, and a test regenerates both plans to their digests
receipt-target | the witness target and filter per estate | V1's target is the closing transaction and V2's is the lowest-index asset-log receipt; the filter is every market address at the block hash and the projection count is asserted
provider-secret | the bearer and every provider URL | read from named environment variables in a subshell, never in argv, plans, fixtures, reports, prose or logs; Lazarus's secret scan runs over staged bytes
route-limits | one eth_getProof per target with up to 2,496 keys | the gateway served that call; an anchor route that caps keys is never the primary; a refusal leaves no fixture
capture-atomicity | the staging directory during a ten-minute V2 capture | the three interruption guards in test_capture pass and the plan limits bound time and bytes
size-limits | 55 MB of V2 fixture against Lazarus and Ariadne limits | components stay under max_component_bytes and the statement under Ariadne's 8 MiB reader bound, checked by verify and ariadne verify
custody | where fixture bytes go and who may read them | no fixture byte enters this tree; the handoff PR carries digests and sizes only; upload happens through Miskatonic tooling after the operator accepts the register row
digest-binding | the committed digests against external bytes | verify-preserved checks committed digests and reports offline and refuses an edited digest; full verification names the release trees by environment variable
statement-counts | the four evidence counts in each statement | release holds the statement to what verify recomputed; a mutated count fails the release
mutation-demo | the six negative observations | demo.py mutations changes one slot value, one code byte and one receipt byte per estate and requires a verify refusal for each
resolver-writes | the design resolvers copied into the example | they write only to caller-named paths that must not exist, refuse symlinks, and never write under .hexaemeron/
docs-copy-lint | the study, runbook and Python copies under plugins/ | imprimatur, hypomnema, phylax and ephoros exit 0 on the committed copies, not only on the .hexaemeron originals
generation-bump | the Lazarus ledger and package | one generation row through the runbook's version-relations block, frontier sentence and held job byte-identical, package bumped once per step PR
private-bytes | the study, README and handoff prose | no capture pipeline, corpus or private-repository content beyond what values.md already names
```

A round logs each id as reviewed or not applicable. Solidity is out of scope:
the run writes none, and the security suite waiver on the run state records it.

## 6. Glossary seeds

- Boundary. The block a sealed interval capture reports as its finalized end; a scope bound for this run, not a finality claim.
- Estate. One Wildcat generation's set of subjects on mainnet, V1 or V2.
- Word. One 32-byte storage slot value at the boundary, named by its slot key.
- Proof target. An address plus sorted unique slot keys that capture proves under EIP-1186 and whose code it hashes against `codeHash`.
- Recorded call. An `eth_call` result kept byte for byte as `recorded-rpc`; never proved, even inside a verified fixture.
- Relation report. The per-value table naming each map row's class and backing entry.
- Scoped witness. The plan-v3 receipt witness with a target receipt and a filtered-log projection; two proved relations.
- Queue head. The `FIFOQueue` word holding `startIndex` and `nextIndex` for unpaid batches.
- Pointer word. A proxy's implementation or beacon slot, proved so the layout of a balance word is pinned.
- Handoff. The Miskatonic pull request that lists archive sizes and digests and proposes a source-register row; not the upload.
- Anchor source. An opaque plan id mapped at runtime to an environment variable holding an RPC URL, used for header cross-checks only.

## 7. Sources

- Issue #1384 and its Miskatonic consumer comment: https://github.com/wildcat-finance/skills/issues/1384
- Prerequisites: https://github.com/wildcat-finance/skills/issues/1360, https://github.com/wildcat-finance/skills/issues/1374, https://github.com/wildcat-finance/skills/issues/1359, https://github.com/wildcat-finance/skills/issues/1493, https://github.com/wildcat-finance/skills/issues/1731
- Pull requests read: https://github.com/wildcat-finance/skills/pull/1457, https://github.com/wildcat-finance/skills/pull/1820, https://github.com/wildcat-finance/skills/pull/1833, https://github.com/wildcat-finance/skills/pull/1838, https://github.com/wildcat-finance/skills/pull/1850, https://github.com/wildcat-finance/skills/pull/1900
- The value map at the starting commit: https://github.com/wildcat-finance/skills/blob/2dbfe40e08ee41429c521e0089a31ed872a1890d/docs/kickoff/1384/values.md, with `scope.json`, `population.json`, `request-spec.json`, `selectors.json`, `capture_requests.py`, `proof-targets-v1.json`, `proof-targets-v2.json` and `evidence/sources.json` beside it
- Lazarus contract and schemas at the starting commit: https://github.com/wildcat-finance/skills/blob/2dbfe40e08ee41429c521e0089a31ed872a1890d/plugins/lazarus/skills/lazarus/SKILL.md, https://github.com/wildcat-finance/skills/blob/2dbfe40e08ee41429c521e0089a31ed872a1890d/plugins/lazarus/schemas/plan-v3.json, https://github.com/wildcat-finance/skills/blob/2dbfe40e08ee41429c521e0089a31ed872a1890d/plugins/lazarus/docs/preservation-release.md, https://github.com/wildcat-finance/skills/blob/2dbfe40e08ee41429c521e0089a31ed872a1890d/plugins/lazarus/docs/chain-anchors.md
- Ariadne state-fixture guide: https://github.com/wildcat-finance/skills/blob/2dbfe40e08ee41429c521e0089a31ed872a1890d/plugins/ariadne/docs/state-fixture.md and https://github.com/wildcat-finance/skills/blob/2dbfe40e08ee41429c521e0089a31ed872a1890d/plugins/ariadne/docs/capturing-a-state-fixture.md
- Alexandria proof-backed-state example: https://github.com/wildcat-finance/skills/blob/2dbfe40e08ee41429c521e0089a31ed872a1890d/plugins/alexandria/examples/proof-backed-state-v0/README.md
- Pinned protocol sources: https://github.com/wildcat-finance/wildcat-protocol/blob/da74452aa7d1a0f024d99efd22cc6d950a8116b7/src/market/WildcatMarketBase.sol and https://github.com/wildcat-finance/v2-protocol/blob/a70f297fbd1b1ab597e0e9a3458a2d13a34b4657/src/market/WildcatMarketBase.sol, with `MarketState.sol`, `Withdrawal.sol` and `FIFOQueue.sol` under each `src/libraries/`
- Standards: https://eips.ethereum.org/EIPS/eip-1186, https://eips.ethereum.org/EIPS/eip-1898, https://eips.ethereum.org/EIPS/eip-1967, https://eips.ethereum.org/EIPS/eip-7201
- Reth proof window: https://reth.rs/cli/reth/node (`--rpc.eth-proof-window`)
- Study-time measurements: `.hexaemeron/design/probe.py` with outputs `probe-v1.json` and `probe-v2.json`, `plan_v3.py` with the four plan summaries under `.hexaemeron/design/plans/`, `resolve.py` with 36 reports under `.hexaemeron/design/reports/`, and `wildcat_slots.py`; compiled layouts from Foundry 1.7.1 are recorded in that module's constants
- Package measurement: `python3 scripts/portable_promise_machine.py measure` at the starting commit (18,715,497 bytes against a 20,971,520-byte line)
- Audit sources as tabled in section 2; the #1924 run's custody amendment in its worktree runbook, dated 2026-09-26

## 8. Signals, and the questions behind them

Nothing here runs unattended: capture, release, admission and the handoff are
operator commands, and the demonstration runs in a suite. The questions still
come, from whoever reruns a ten-minute V2 capture months later:

1. Which stage did the capture stop at and which limit tripped? Lazarus's
   terminal result already names the stage (`transport`, `rpc-capture`,
   `receipt-set-binding`, `state-proof`, `block-bracket`, `chain-anchor`,
   `component-write`, `final-verification`) and the request, byte and elapsed
   counts, with provider identities redacted; Step 2 records it in `proof.md`.
2. Which route answered and did the anchors agree? The manifest's anchor
   records and the verify report's anchor coverage answer it; no URL is ever
   part of the answer.
3. Do the committed digests still match the archive somebody restored?
   `demo.py verify-preserved` and `verify-release` answer it offline; the
   handoff directory's `SHA256SUMS` answers it before download.

No new event, metric or alert is added; the ephoros contract at
`plugins/hexaemeron/skills/ephoros/SKILL.md` governs what a signal carries, and
`ephoros.py` exits 0 on the design scripts.

## 9. Boundaries, per capability

- **RPC transport.** Worth taking: the bearer and the gateway URL. Control: read
  from named environment variables inside the process, redirect-refusing
  transport in Lazarus, union secret scan over staged bytes, no URL in argv,
  plan, fixture, report or prose.
- **Plan generation.** Worth taking: an inventory row or slot that differs from
  the map. Control: the request bytes are checked against `request-spec.json`;
  word counts are checked against the probe; the generator reads only files
  under `docs/kickoff/1384/` and its own directory and writes only to a fresh
  `--out`.
- **Resolvers and demonstration.** Worth taking: a shell or an unpinned
  subprocess. Control: pinned argv lists, no shell, refusal when a named path or
  environment variable is missing, fresh output paths only, symlinks refused.
- **Release trees named by environment variable.** Worth taking: a tree that is
  not the one the digests describe. Control: every consumer verifies digests
  before reading, and `verify-preserved` needs no external tree at all.
- **Handoff prose.** Worth taking: a private byte or coordinate in a public
  repository. Control: the handoff carries sizes, digests and a proposed row;
  the study and README name nothing beyond what `values.md` already names.

The phylax contract at `plugins/hexaemeron/skills/phylax/SKILL.md` owns the
list and the controls; `phylax.py` exits 0 on the four design scripts.

## 10. The budget, or its absence

Two budgets, both measured by commands that already exist:

1. Capture elapsed time stays under each plan's `max_elapsed_seconds` (3,600 s
   V1, 7,200 s V2). Measured by `lazarus.py capture` itself, which refuses at
   the limit and reports elapsed seconds in its terminal result; projected from
   the probe at 25.9 s and 598 s.
2. Bytes added to the portable package stay under the line. Measured by
   `python3 scripts/portable_promise_machine.py measure`; the design adds
   156,744 bytes against a 2,256,023-byte margin, and the package file count
   stays below the 1,600 tripwire.

Verify time is recorded, not budgeted: nothing consumes it under a deadline. The
metron contract at `plugins/hexaemeron/skills/metron/SKILL.md` governs how a
measurement is taken and compared.

## 11. The fail-closed posture

What stops the run: a plan whose inventory bytes differ from the spec; a market
whose derived word count differs from the probe; a token whose layout is not
recognised; a route that refuses a proof, a receipt set or a code read; any
Lazarus capture failure, which leaves no fixture; a verify, release or statement
refusal; a mutation that verify does not refuse; a committed digest that does not
match; a missing environment variable at a conformance cell. None of these is
repaired by narrowing a plan or editing a digest.

Guard convention: a fix lands with a test that fails without it, run through
the runners the suites already expose:
`python3 plugins/lazarus/tests/run_tests.py --elenchus-report <report>` and
`python3 plugins/ariadne/tests/run_tests.py --elenchus-report <report>`, both
`elenchus.unittest.v1`, plus `python3 -m unittest discover -s tests` for the root.
The three capture guards the record names
(`test_interrupted_finalisation_leaves_no_fixture_or_staging_directory`,
`test_elapsed_time_limit_leaves_no_output`,
`test_plan_v3_interruption_after_staging_removes_the_stage`) are the model. The
elenchus contract at `plugins/hexaemeron/skills/elenchus/SKILL.md` owns the
triage order. No known failure is carried, as section 2 states.

## 12. Decisions and their homes

1. **Where fixture bytes live** (expensive to reverse once consumers name a
   custody path). Home: `docs/decisions/drafts/keep-wildcat-boundary-fixtures-in-miskatonic-custody.md`,
   created by Step 1, numberless until merge.
2. **How a word is named** (compiled layout confirmed against the deployed
   getter, with the view-versus-stored rule). Home: the example's `README.md`
   and `wildcat_slots.py` docstring, since it is method rather than policy.
3. **Which receipt is the target** (market log first, else the lowest-index
   asset-log receipt, else index 0; filter is every market at the block hash).
   Home: `probe.py`'s recorded `selection_rule` and the README.
4. **Two estates at their own boundaries.** Home: this study's assumptions and
   the ledger row.
5. **Generation bump.** Home: `plugins/lazarus/skills/lazarus/EVOLUTION.md`
   through the runbook's `version-relations` block; Ariadne's ledger only if a
   step changes Ariadne's tree.

The hypomnema contract at `plugins/hexaemeron/skills/hypomnema/SKILL.md` owns
which decisions earn a record and where each lives.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | full-map-r2-handoff
record | docs/decisions/drafts/keep-wildcat-boundary-fixtures-in-miskatonic-custody.md
```

**Maintainer answers, 2026-09-27.** Two questions were put before this study
was receipted. Custody: Miskatonic R2, as selected, over the private archive
repository. Public copy: none; the archives stay in custody only, so a stranger
needs Miskatonic access to fetch the bytes and the upload waits on the operator
accepting the register row.
