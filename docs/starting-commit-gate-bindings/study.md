# Study: Let supersede-commit admit a run initialised under an older controller

Task: [skills#2042](https://github.com/wildcat-finance/skills/issues/2042). Starting ref `dd2e6939ed460dcd987457a398a2765822349588` (`main`, 2026-09-30, Hexaemeron 1.6.92, `fiat-v6.78.1`). Written 2026-09-30 by the study worker of this run.

Assuming, unless corrected:

1. Run #1872 is the acceptance target and stays out of scope: its own driver applies the shipped fix. The issue's `carryover` row says so, and this study keeps it verbatim in section 3.
2. Every Fiat run worktree is a Git checkout of the target repository with that repository's history, so `git cat-file` can read any file at the run's starting commit. A target outside this repository has no registered module in its tree, so the rule this study selects never fires there.
3. The Hexaemeron suite runs under Python 3.14.6 (`.python-version`, `requires-python = "==3.14.*"`) through `python3 plugins/hexaemeron/tests/run_tests.py`, with `CHECKPOINT_COSIGN` naming the pinned Cosign 3.1.3 release asset. No hosted job runs it; the local checked runner does.
4. Unit fixtures reconstruct historical bytes from the current tree, as #2014's S1-R1-02 fix did, while released-adapter tests read older Git objects by design (`plugins/hexaemeron/tests/test_gate_deferred_registration.py` lines 113 to 124). The suite fixture here takes the first route; the demonstration takes the second.
5. The "older controller" in the suite fixture is a copy of the current controller whose adapter carries one different module pin and therefore a different adapter digest, committed at the fixture's base commit. It is not the literal 1.6.77 bytes; the demonstration uses those.

## 1. Problem statement

`hexctl supersede-commit` (PR #2039, closing #2014) cannot reach a run initialised under an earlier Hexaemeron release. The user is the driver of such a run, concretely #1872 at Step 7's `push`, who needs the controller built from `main` to verify the run, record a `fiat-commit-supersession/v1` mapping, push, and integrate.

What refuses, and where. `main()` in `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` (lines 32326 to 32345) runs `gate_recovery_preflight(..., allow_source_drift=False)` before every mutating command except `init`, `halt`, `resume`, `reset` and `amend runbook`; `supersede-commit` also calls `verify_run` itself (line 16292); `cmd_verify` and `cmd_status` run the same preflight. It reaches `verify_gate_commands` (line 15325), which calls `adapter.replay` (line 15401) on the latest gate record. `replay` in `plugins/hexaemeron/skills/protasis/scripts/gate_commands.py` (lines 833 to 861) recomputes `validate` under the controller's own adapter; `interface` (line 280) calls `parser_bindings` (lines 253 to 277), which refuses `unregistered-cli-module-bindings` when a registered module's AST digest differs from this controller's `MODULE_BINDINGS` pin (line 101). `gate_commands_module()` (line 14259) always loads the adapter that sits beside the running `hexctl.py`, never one from the target tree. `next` runs none of this, which is why it still answered for #1872.

What init records. Observed in run #1872's `init` event and in `cmd_init` (lines 3728 to 3746): `topic`, `base`, `integration_branch`, `run_branch`, `contracts`, `controller_currency`, `task_issue_contract`, `starting_commit`, `run_anchor_sha256` and `task_issue`. `controller_currency` holds `ledger_version fiat-v6.74.1`, `route git-backed`, `pin d162d0952782f09659370b6a554c9cd4511b8db9`, equal to `base`. No module binding is recorded anywhere. The gate receipt (`done:runbook` plus 17 `amend:runbook` events) records `adapter_sha256` (a whole-file digest of `gate_commands.py`, here `ac527913dc737184f2a918cdd693aa4be2e16d813736060f870a17b98fdfd119`) and, per invocation, `cli.sha256` and `declarations_sha256`. So the "bindings its own init recorded" exist only as the starting commit itself: `d162d095:plugins/hexaemeron/skills/protasis/scripts/gate_commands.py` has that same digest and carries the pins the run was validated under. That is what the selected design reads.

Facts about #1872 (read-only, 2026-09-30): 68 ledger entries; `verify` under 1.6.77 exits 0; under 1.6.92 it refuses as quoted in the issue. Its gate receipt binds 25 commands: 15 invocations of the locally declared `plugins/alexandria/tests/run_tests.py`, 8 of `scripts/run_checks.py`, 1 of `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`, 1 of `plugins/hexaemeron/skills/protasis/scripts/protasis.py`. Between 1.6.77 and 1.6.92 three registered pins moved: `protasis.py` (PR #1915, 1.6.79), `ephoros.py` (PR #1947, 1.6.84), `plugins/hexaemeron/tests/run_tests.py` (PR #2021, 1.6.89). Only `protasis.py` is named by the runbook; the refusal names all three because `registered_module_skew` (line 15135) scans every registered module, not the runbook. All eight registered modules in the run tree equal their blobs at `d162d095`.

Working prototype. The controller built from `main` verifies, accepts `supersede-commit` for, pushes and integrates a run whose registered modules are unchanged since its starting commit and whose gate receipts carry that commit's adapter digest, with no ledger edit, no script ported into the product tree, and every run initialised under 1.6.92 verifying exactly as before.

Success criteria, each with its check:

1. A run initialised under a skewed older controller in a disposable fixture: `verify` refuses `controller-pin-skew` under the unfixed controller and exits 0 under the fixed one; `supersede-commit` then records a tree-identical replacement and `verify` exits 0. Check: `python3 plugins/hexaemeron/tests/fiat_starting_commit_bindings_proof.py --candidate base-commit-bindings --criterion older-controller-supersession-fixture --report <fresh path>` writes `value: true`.
2. The literal base controller: `git archive d162d0952782f09659370b6a554c9cd4511b8db9 plugins/hexaemeron` yields `hexctl.py` `fa2cfc3dda1e3cef1a8a1829dbebee7e17cdd1887e0ee54e38e1c38fa2ea35f3` and the adapter `ac527913…`; it initialises and receipts a disposable signed run; the `main` controller then records a supersession and verifies it. Check: `python3 docs/starting-commit-gate-bindings/demonstrate.py --candidate base-commit-bindings --criterion base-commit-controller-demonstration --report <fresh path>` writes `value: true`.
3. Existing replay evidence still holds: `python3 -m unittest plugins.hexaemeron.tests.test_gate_commands plugins.hexaemeron.tests.test_gate_deferred_registration` from the repository root, and `python3 plugins/hexaemeron/tests/run_tests.py`, each exit 0.
4. Negative controls under the fixed controller: a registered module edited inside the run refuses with the existing `module-edited-in-run` diagnosis; a receipt whose `adapter_sha256` is neither reviewed nor the starting commit's refuses `gate-receipt-drift`; a run without `contracts.gate_commands` stays legacy.
5. Selection evidence already in hand: the prototype of the selected rule verifies a replica of #1872 (report `main-controller-replays-1872` true, 1,378 ms), see section 4.

## 2. Prior art

In this repository at the starting ref:

- `REPLAY_COMPATIBLE_ADAPTERS` (`gate_commands.py` lines 39 to 51), from [PR #1754](https://github.com/wildcat-finance/skills/pull/1754), lets `replay` substitute a reviewed released adapter digest and then requires every other field to match (lines 855 to 861). Its `carryover` row was `checkpoint-authority-protocol | duplicate | #1676`; not this subject.
- `prior_runner_bindings` (lines 269 to 277) already admits two historical `(AST digest, source digest)` pairs for one module, `plugins/hexaemeron/tests/run_tests.py`, so a pin table keyed by path, AST digest and source digest has precedent.
- `registered_module_skew`, `gate_source_recovery` and `gate_source_refusal` (lines 15135 to 15245), from [PR #1785](https://github.com/wildcat-finance/skills/pull/1785), diagnose `controller-pin-skew` and tell the driver to use the recorded controller. That recovery is what #2042 cannot follow, because the recorded controller lacks `supersede-commit`.
- Adapter digests by first-parent merge on `main`: 1.6.45 `8116b2c0…` (unlisted), 1.6.50 `18eb52e7…`, 1.6.58 `c2d14b0f…`, 1.6.59 `00d4c9f2…`, 1.6.62 to 1.6.69 `d7e49768…`, 1.6.70 to 1.6.71 `3549ce4a…`, 1.6.72 to 1.6.78 `ac527913…` (unlisted), 1.6.79 to 1.6.82 `14a857dc…`, 1.6.84 `6f50cd84…`, 1.6.86 to 1.6.88 `550ac4de…`, 1.6.89 to 1.6.91 `c3facf15…` (unlisted), 1.6.92 `90ad7967…`. Three released adapters are unlisted, so a run initialised under 1.6.89 to 1.6.91 refuses `gate-receipt-drift` under 1.6.92 even where every pin agrees.
- The reference [gate-commands.md](https://github.com/wildcat-finance/skills/blob/dd2e6939ed460dcd987457a398a2765822349588/plugins/hexaemeron/skills/protasis/references/gate-commands.md) lists the reviewed digests (lines 148 to 160), requires "review of that released source and regression evidence" before adding one (lines 168 to 169), and states that the 1.6.72 to 1.6.78 adapter `ac527913…` "is not admitted" (lines 185 to 188).

The last two merged pull requests that changed each subject file:

- `gate_commands.py`: [PR #2039](https://github.com/wildcat-finance/skills/pull/2039) (merge `dd2e6939`, 2026-09-30) and [PR #2021](https://github.com/wildcat-finance/skills/pull/2021) (merge `f93add29`, 2026-09-30).
- `hexctl.py`: PR #2039 and [PR #2022](https://github.com/wildcat-finance/skills/pull/2022) (merge `a9d5fa11`, 2026-09-30).

What they carried. PR #2039 carried one row, `run-1872-step-7-push | none | #1872 waits on this issue; its own recommit and push are recorded in that run, not here`; this study keeps that boundary (section 3). Its integration note says the composed controller "accepts the intermediate runner receipt under the current optional runner mode", the `321189fc…` entry in `RUNNER_SINGLE_PROCESS_ADAPTERS`. PR #2021 carried nothing and re-pinned `run_tests.py`, moving the adapter to `c3facf15…` without admitting it, which is the pattern [skills#1968](https://github.com/wildcat-finance/skills/issues/1968) names. PR #2022 carried nothing and did not run the Hexaemeron suite. [PR #1975](https://github.com/wildcat-finance/skills/pull/1975) (#1944, merge `769a6383`) carried `released-adapter-gap-1-6-72 | filed | #1968` and `adapter-replay-admission-lag | filed | #1968`. Issue #1968 is open, `Fiat-Required: 0`, and asks for two things: a repository check that fails when an adapter change leaves its predecessor digest neither admitted nor refused, and a decision on `ac527913…`. This study answers the second by rule for runs whose starting commit carries that adapter (section 4) and hands the first back as `adapter-replay-admission-lag | duplicate | https://github.com/wildcat-finance/skills/issues/1968`. [skills#1666](https://github.com/wildcat-finance/skills/issues/1666) (a checked record of a mid-run controller switch) stays open and untouched.

Audit records. `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited 0 from the target root on 2026-09-30, so each synopsis was the reading view; no authoritative source was read directly.

- `audit/rounds/fiat-2014-supersede-receipted-commits-retry.md` via `audit/rounds/fiat-2014-supersede-receipted-commits-retry.synopsis.md` (source `0eb2c382…`, 5 rounds). S1-R1-01 medium, fixed; S1-R1-02 low, fixed (a runner fixture reconstructs bytes instead of reading the init-base Git object); S2-R1-01 medium, fixed (atomic ledger publish). Elenchus verdicts: guarded, null, inconclusive, null, null. Not checked: live GitHub readback was mocked; native checkpoint archive restoration not driven. Leads not pursued: "the released-adapter tests still read older Git objects by design"; the Elenchus runner's workers received `EPERM` under containment; `main` at 1.6.91 against the product's 1.6.89, left to integration.
- `audit/rounds/fiat-1944-gate-commands-for-a-repository-with-no-runn.md` via its synopsis (source `7ea24e73…`, 9 rounds). S2-R1-01 low, S2-R1-02 low, S2-R2-01 low, S2-R3-01 low, S3-R1-01 medium, S3-R2-01 low, all fixed. Elenchus verdicts: null, inconclusive (five rounds), null, null, null. `replay-allowlist-widening` was reviewed in every applicable round: "the allowlist gains exactly `14a857dc…` and `6f50cd84…`". Leads kept: a test reads `6f4312c3` from Git with `check=True`, so a clone without `main`'s history errors; `registered_module_skew` reads built-in paths only; a checkpoint restore of a success-criteria run refuses `admission-drift` until "a later release admits its adapter" (carried as #1969).
- `audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.md` via its synopsis (30 rounds; verdicts 14 inconclusive, 11 null, 5 unguarded). Step 1 round 3 records `gate-receipt-drift` after the controller moved mid-session, a runbook amendment as the recovery, and one finding from that recovery: the amendment reached only `.hexaemeron/runbook.md` and left the published copy under `plugins/alexandria/docs/wildcat-interval/` at 66,221 bytes against the amended 69,087, re-synced in the round. Its other finding ids and statuses stay in that synopsis; none concerns the adapter code.
- `plugins/hexaemeron/audit/AUDIT.md` via `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` (2 rounds, 2026-08-15). F-01 medium, F-02 medium, F-03 to F-09 low, all fixed; F-10 info, accepted. Legacy fields `audit-schema`, `covered`, `not-checked` and `elenchus-verdict` are missing and stay unknown.

Outside the repository: the pattern is trust on first use pinned to a commit, the way `pip --require-hashes` pins to a reviewed hash and SSH `known_hosts` keeps the first key; the selected rule pins to the run's own starting commit, which the ledger already anchors.

## 3. Constraints and non-goals

- Starting ref `dd2e6939ed460dcd987457a398a2765822349588`. Interpreter 3.14.6 per `.python-version`; stdlib `unittest`; the Hexaemeron suite through `python3 plugins/hexaemeron/tests/run_tests.py` with `CHECKPOINT_COSIGN` set; the checked runner `python3 scripts/run_checks.py` before every push, and `--plan` first so every changed path has an owner.
- This run is driven by Hexaemeron 1.6.92 from the plugin cache. The fix ships in the repository and cannot govern the run that writes it.
- Commit identity for every step: author and committer `Dr Laurence E. Day <laurence@wildcat.finance>`, locally signed, GitHub verified. No other identity anywhere.
- No hand edit of any run's `state.json` or `ledger.jsonl`. No Hexaemeron script ported into a run's product tree. Replay of receipted history stays byte-exact. The fix widens two things: which adapter digest `replay` substitutes and which module pin `parser_bindings` admits. A command result still has to equal current validation field by field.
- A run initialised under 1.6.92 or earlier and replaying today must replay identically after the fix. A run without `contracts.gate_commands` stays legacy.
- Two controllers on one run: the 1.6.77 reader accepts a ledger carrying a synthetic `commit:supersede` entry (`ok: 69 ledger entries` on a replica) and is blind to its content, while the fixed reader refuses a record that disagrees with its receipts. Do not drive a run with the older controller after a supersession is recorded.
- Versions: the Hexaemeron package rises above every number any ref claims; Fiat and Protasis each take a generation row through a `version-relations` block in the runbook, with no literal `fiat-v` or `protasis-v` token outside it. Surfaces a bump moves: `plugins/hexaemeron/.claude-plugin/plugin.json`, `plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `plugins/hexaemeron/skills/fiat/SKILL.md` `metadata.version` and the agent-instruction fixture it re-pins, `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` in `hexctl.py` (line 488), `tests/test_phylax_model_proxy.py`, `tests/fixtures/promise-machine/runtime/` and `tests/promise_machine_coverage.json`, and `.horos/census.json`.
- Boundaries. Always: both the root suite and the Hexaemeron suite before a commit; `imprimatur.py` then `brevitas.py` on every shipped document; `hypomnema.py` on the decision draft. Ask first: any change to a receipt schema, ledger event or `contracts` marker; any widening of `REPLAY_COMPATIBLE_ADAPTERS` beyond the rule this study selects; touching CI. Never: edit a run's ledger; delete a failing test; commit a `.hexaemeron/design/fixtures` snapshot (it carries local paths and another run's state); claim a command ran when it did not.

Non-goals:

- Applying the fix to #1872. Kept verbatim from the issue: `none | none | This issue is limited to admitting supersession for runs initialised under an earlier controller; applying it to run #1872 stays with that run`.
- The repository check #1968 asks for. Carried as `adapter-replay-admission-lag | duplicate | https://github.com/wildcat-finance/skills/issues/1968`.
- A checked record of a mid-run controller switch (#1666).
- Success-criteria execution through local registrations (#1967) and checkpoint relocation of a success-criteria run (#1969).
- Admitting an adapter that is neither reviewed nor the run's starting commit's, for example a run captured by an in-repo controller at a commit other than its base. Such a run keeps today's refusal.

## 4. Design options

Four candidates were built or measured against a replica of #1872: the tree at `5d5ec5e142d83140a0967fe13ad3498df3df2015` (Step 7 audit head, PR #2013) with the run's state snapshot (state `95cb93ec…a6f0`, ledger `499080ad…7916`) beside it. The resolver is `.hexaemeron/design/resolve.py`; each report is one `protasis-design-report/v1` file under `.hexaemeron/reports/design/`. Two hand experiments framed them: adding `ac527913…` to the reviewed list alone still refused `unregistered-cli-module-bindings`, and adding the `protasis.py` prior pin as well made `verify` exit 0 with `ok: 68 ledger entries` in 1.31 s and `status` report `current`.

1. `base-commit-bindings` (selected). When the controller's pin refuses a registered module, `hexctl` reads that module's blob and `plugins/hexaemeron/skills/protasis/scripts/gate_commands.py` at `state.base` through `bounded_run` git, parses the historical `MODULE_BINDINGS` assignment with `ast.literal_eval` (no import), and admits the module when its worktree bytes equal the base blob and its AST digest equals the base pin. Replay admits the receipt's `adapter_sha256` when it equals the digest of the base adapter blob, and keeps the reviewed list for every other digest. Every other field of the receipt must still match. Trade: two bounded git reads on the refusal path only, and a new adapter keyword threaded through `validate`, `validate_with_criteria`, `replay`, `interface` and `parser_bindings`, with `hexctl` and `criteria_execution.py` passing it at `capture_gate_commands` (line 14395), the binding capture (line 15530), `verify_gate_commands` (line 15401), the criteria recovery admission (lines 14654 to 14666 and 14791 to 14793) and `criteria_execution.py` lines 246 and 281. No table grows per release. The derivation on the replica admitted all eight registered modules and the adapter digest, and `verify` exited 0.
2. `reviewed-prior-pins`. Add `ac527913…` to `REPLAY_COMPATIBLE_ADAPTERS` and a `PRIOR_MODULE_BINDINGS` triple for `protasis.py` (`0d3742b8…`, source `41737559…`), generalising `prior_runner_bindings`. Trade: no git reads and a small diff, but every later older controller needs another reviewed row set, and the list is already three releases behind the cache. It also verifies the replica.
3. `runbook-scoped-pins`. The pin check is already scoped to modules the runbook names, so this candidate only changes the diagnosis to say which skewed modules the runbook names. Trade: honest message, no admission; the replica still refuses because `protasis.py` is named.
4. `recorded-controller-fork`. Rebuild the recorded controller from `d162d095` (`git archive`) and backport `supersede-commit` into it. Trade: the run finishes on a controller no release shipped, `main`'s controller still refuses the run at integration, and the backport is the porting the issue rules out.

Criteria. Every concern is covered: `main-controller-replays-1872` (correctness gate, boolean true), `edited-module-refuses` (correctness gate), `unknown-adapter-refuses` (recovery gate), `verify-writes-no-state` (space gate, at most 0 bytes changed), `verify-wall-ms` (time gate, at most 5,000 ms) and `reviewed-rows-per-release` (compatibility metric, minimise). Time is a gate rather than a metric because the measured spread between the two admitting candidates (65 ms) is below the run-to-run noise of one candidate (1,313 to 1,378 ms across three runs) and a 3 per cent timing difference should not outvote a per-release maintenance duty; the measured values are in the reports.

Results (all 24 selection cells resolved, reports digest-bound in `.hexaemeron/design-evidence.json`):

| candidate | replays 1872 | edited refuses | unknown refuses | bytes written | verify ms | rows per release |
| --- | --- | --- | --- | --- | --- | --- |
| `base-commit-bindings` | true | true | true | 0 | 1,378 | 0 |
| `reviewed-prior-pins` | true | true | true | 0 | 1,313 | 2 |
| `runbook-scoped-pins` | false | true | true | 0 | 632 | 0 |
| `recorded-controller-fork` | false | true | true | 0 | 1,324 | 0 |

`runbook-scoped-pins` and `recorded-controller-fork` fail the correctness gate (for the fork, `main`'s controller is measured; its own rebuilt controller verifies in 1,324 ms). Under `unknown-adapter-refuses`, the unpatched adapter refuses the forged digest as `unregistered-cli-module-bindings` before it reaches the digest comparison; the others refuse `gate-receipt-drift`. Between the two survivors the one metric decides: 0 against 2 rows. Selection rule `unique-frontier`, candidate `base-commit-bindings`; `design_evidence.py --transition design-lock` exits 0.

Conformance cells, pending at `integration` for the selected candidate: `older-controller-supersession-fixture` (the suite proof), `base-commit-controller-demonstration` (the literal 1.6.77 controller rebuilt from `d162d095`) and `released-adapter-tests-green`. The resolvers are named in the record; a step creates each script.

Edge cases the selected rule must state and test: the base adapter blob is absent (target outside this repository, or a base before PR #1670 added the adapter) or its `MODULE_BINDINGS` is unreadable, so nothing is admitted and today's refusal stands; the module's bytes differ from the base blob, so `module-edited-in-run` stands; the base pin itself disagrees with the module (a stale pin on `main` at the base), so `controller-pin-skew` stands; the receipt's adapter is neither the base adapter nor reviewed (an in-repo-source controller at another commit), so `gate-receipt-drift` stands. `registered_module_skew` and `gate_stale_status` apply the same derivation, so `status` and the refusal never disagree.

Fixture decision. The suite fixture follows `skewed_controller()` in `plugins/hexaemeron/tests/test_gate_commands.py` (lines 480 to 493): copy the current `fiat` and `protasis` scripts, change one pin and the ledger version, commit that adapter and a matching modified registered module at the fixture's base, and drive `init`, `done study`, `done runbook` and `done implement` under the copy, with signed commits from `fixture_tools.native_signing_tools` as `plugins/hexaemeron/tests/test_fiat_commit_supersession.py` does. It needs neither the plugin cache nor Git history and reproduces the #1872 condition exactly: receipt adapter equal to the base adapter, module unchanged since base, current pin different. The demonstration rebuilds the literal controller with `git archive` from the run worktree, asserts both digests before running it, and is recorded as a document, not a suite test, because the checked runner's snapshot carries no Git history for it to read.

## 5. Risk register seed

```risk-register
base-ref-trust | state.base read from run state and passed to git argv | the value is checked against COMMIT_RE before use, git runs through bounded_run with no shell, GIT_TIMEOUT and GIT_OUTPUT_MAX, and a failed read admits nothing
historical-adapter-parse | the base adapter blob read from Git | it is parsed with ast.parse and one ast.literal_eval of the MODULE_BINDINGS assignment under the 2 MiB source cap, never imported or executed, and any other shape admits nothing
module-equality | a registered module in the run worktree | admission requires byte equality with the base blob read through the no-follow read_source and AST equality with the base pin; an edited module still refuses module-edited-in-run
adapter-provenance | the receipt's adapter_sha256 | it is accepted only when equal to the base adapter digest or a reviewed digest, and every other receipt field must still equal current validation; a forged digest refuses gate-receipt-drift
current-run-unchanged | every run initialised under 1.6.92 | the fast path runs no git read and produces byte-identical results; test_gate_commands and test_gate_deferred_registration stay green
legacy-isolation | runs without contracts.gate_commands | no marker means no derivation and no fabricated evidence, as today
diagnostic-honesty | status and the refusal text | status names when a replay admitted starting-commit bindings and which modules, and the skew list marks the modules the runbook names
dual-controller | a run touched by two controllers | the older reader is blind to commit:supersede; the fixed reader refuses a record that disagrees with receipts; the Fiat SKILL states the rule
fixture-history-dependency | the demonstration's git archive of the base commit | the suite fixture reads no history; the demonstration asserts both digests and refuses on a mismatch
version-surfaces | the package and ledger bump | all surfaces in section 3 move in the step that last edits hexctl.py, and plugin_release.py checks the rise
partial-write | resolver and proof reports | each report is created with O_EXCL at a caller-named path and nothing under .hexaemeron/ is rewritten
replay-list-lag | REPLAY_COMPATIBLE_ADAPTERS | the reviewed list stays authoritative for adapters that are not a run's own base; the repository check stays with skills#1968
```

The two lines the audit loop should look hardest at are `adapter-provenance` and `module-equality`: together they are the whole of what the rule adds, and a mistake in either widens what a receipt may claim.

## 6. Glossary seeds

- adapter: `plugins/hexaemeron/skills/protasis/scripts/gate_commands.py`, the inert command-interface validator a controller loads from beside itself.
- adapter digest: SHA-256 of the whole adapter file, recorded as `adapter_sha256` in a gate receipt.
- module pin: the `MODULE_BINDINGS` entry for a registered module, a SHA-256 of its AST with the parser-builder body emptied.
- starting commit: `state.base`, the commit a run's worktree was cut from and the value `init` records as `starting_commit`.
- starting-commit bindings: the module pins and adapter digest read from the adapter blob at the starting commit.
- reviewed adapter: a digest listed in `REPLAY_COMPATIBLE_ADAPTERS` after review.
- controller-pin-skew: the `gate_source_recovery` cause for a module unchanged since base that fails the running controller's pin.
- supersession: one `fiat-commit-supersession/v1` record mapping a receipted commit to a tree-identical replacement.

## 7. Sources

- Issue: [skills#2042](https://github.com/wildcat-finance/skills/issues/2042); related [skills#1968](https://github.com/wildcat-finance/skills/issues/1968), [skills#1944](https://github.com/wildcat-finance/skills/issues/1944), [skills#1666](https://github.com/wildcat-finance/skills/issues/1666), [skills#1872](https://github.com/wildcat-finance/skills/issues/1872).
- Pull requests: [#2039](https://github.com/wildcat-finance/skills/pull/2039), [#2021](https://github.com/wildcat-finance/skills/pull/2021), [#2022](https://github.com/wildcat-finance/skills/pull/2022), [#1975](https://github.com/wildcat-finance/skills/pull/1975), [#1915](https://github.com/wildcat-finance/skills/pull/1915), [#1947](https://github.com/wildcat-finance/skills/pull/1947), [#1785](https://github.com/wildcat-finance/skills/pull/1785), [#1754](https://github.com/wildcat-finance/skills/pull/1754), [#2013](https://github.com/wildcat-finance/skills/pull/2013).
- Code at the starting ref: [gate_commands.py](https://github.com/wildcat-finance/skills/blob/dd2e6939ed460dcd987457a398a2765822349588/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py), [hexctl.py](https://github.com/wildcat-finance/skills/blob/dd2e6939ed460dcd987457a398a2765822349588/plugins/hexaemeron/skills/fiat/scripts/hexctl.py), [criteria_execution.py](https://github.com/wildcat-finance/skills/blob/dd2e6939ed460dcd987457a398a2765822349588/plugins/hexaemeron/skills/fiat/scripts/criteria_execution.py), [test_gate_commands.py](https://github.com/wildcat-finance/skills/blob/dd2e6939ed460dcd987457a398a2765822349588/plugins/hexaemeron/tests/test_gate_commands.py), [test_gate_deferred_registration.py](https://github.com/wildcat-finance/skills/blob/dd2e6939ed460dcd987457a398a2765822349588/plugins/hexaemeron/tests/test_gate_deferred_registration.py), [test_fiat_commit_supersession.py](https://github.com/wildcat-finance/skills/blob/dd2e6939ed460dcd987457a398a2765822349588/plugins/hexaemeron/tests/test_fiat_commit_supersession.py), [gate-commands.md](https://github.com/wildcat-finance/skills/blob/dd2e6939ed460dcd987457a398a2765822349588/plugins/hexaemeron/skills/protasis/references/gate-commands.md), [Fiat SKILL.md](https://github.com/wildcat-finance/skills/blob/dd2e6939ed460dcd987457a398a2765822349588/plugins/hexaemeron/skills/fiat/SKILL.md) ("Runbook command evidence", lines 1195 to 1254), [the #1944 study](https://github.com/wildcat-finance/skills/blob/dd2e6939ed460dcd987457a398a2765822349588/docs/deferred-runner-binding/study.md) (line 107), [its decision draft](https://github.com/wildcat-finance/skills/blob/dd2e6939ed460dcd987457a398a2765822349588/docs/decisions/drafts/bind-a-step-created-runner-at-its-push.md).
- Audit views: `audit/rounds/fiat-2014-supersede-receipted-commits-retry.synopsis.md`, `audit/rounds/fiat-1944-gate-commands-for-a-repository-with-no-runn.synopsis.md`, `audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.synopsis.md`, `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`.
- Run #1872 state, read-only on 2026-09-30: its `state.json` and `ledger.jsonl` (digests above), `verify` under the 1.6.77 and 1.6.92 cache controllers. The snapshot the resolver reads is `.hexaemeron/design/fixtures/run-1872/`, untracked and not for publication; `.hexaemeron/design/evidence/` holds each cell's controller digests, derived rows, output tail and timing.
- Historical controllers: `git archive d162d0952782f09659370b6a554c9cd4511b8db9 plugins/hexaemeron` (Hexaemeron 1.6.77 per its `plugin.json`), digests in section 1.

## 8. Signals, and the questions behind them

Nothing here runs unattended; `hexctl` is invoked by a driver at a terminal and exits. Two questions still need an answer from the controller's own output rather than from reading code:

1. "Why does this run replay under a newer controller, and what exactly was admitted?" The step that changes `gate_stale_status` adds a `provenance` object to `status --field gate_command_status` when a replay admitted starting-commit bindings: the starting commit, the base adapter digest and the admitted module paths. A current run keeps the existing fields unchanged.
2. "Which of the modules the refusal names does this runbook use?" The same step marks each `modules[]` entry of the skew list with `named_by_runbook: true|false`, so the driver of a run like #1872 sees one named module, not three.

No metric, trace or alert is added: a refusal is a non-zero exit with a cause token, and the cause tokens already exist. Ephoros owns what a signal must carry; these two are fields on an existing derived observation, not a new emitter.

## 9. Boundaries, per capability

1. Run state as input to git. `state.base` and `starting_commit` come from files the driver's session wrote. Control: `COMMIT_RE.fullmatch` before the value enters argv; `bounded_run` with fixed argv, no shell, the existing timeout and output cap; a non-zero status admits nothing.
2. Historical source as data. The base adapter blob is repository history, not authority. Control: `ast.parse` and `ast.literal_eval` of exactly one `MODULE_BINDINGS` assignment of `str` to `str`; never `importlib`, `exec` or attribute access on the parsed tree; the 2 MiB `MAX_SOURCE` cap; anything else admits nothing.
3. The worktree module. Control: read through the adapter's no-follow `read_source`, compared byte for byte with the base blob, then AST-digested with the adapter's own `parser_bindings` logic; equality with the base pin is the only admission.
4. The receipt's adapter digest. It is data written by an earlier controller. Control: equality with the base adapter blob's digest or membership of the reviewed list, then the unchanged full-record comparison in `replay`; the reviewed list is not widened by this rule.
5. Fixtures and demonstrations. The 1872 state snapshot under `.hexaemeron/design/fixtures/` holds local paths and another run's briefs; it stays untracked and the Step 1 copy carries only the resolver and reports. The demonstration runs a rebuilt historical controller only inside a disposable fixture after asserting its digests, with the signing keys `native_signing_tools` generates.
6. No new network, credential or dependency. Phylax owns the boundary list; `phylax.py` and `ephoros.py` exit 0 on `.hexaemeron/design/resolve.py` at this ref.

## 10. The budget, or its absence

`verify` runs before every mutating command, so it carries a budget: at most 5,000 ms wall time on the #1872 replica, measured by `python3 .hexaemeron/design/resolve.py --candidate base-commit-bindings --criterion verify-wall-ms --report <fresh path>`. Measured on 2026-09-30: selected rule 1,378 ms, reviewed rows 1,313 ms, the 1.6.77 controller on the same replica 1,219 to 1,324 ms, the unfixed 1.6.92 refusal 582 to 632 ms. The rule adds two `git cat-file` reads on the refusal path only; the fast path for a current run is unchanged. Metron owns the budget's form; a step that changes `verify`'s cost re-measures with the same command before and after.

## 11. The fail-closed posture

What stops the run: any of the five edge cases in section 4 leaves today's refusal in place with its existing cause (`controller-pin-skew`, `module-edited-in-run`, `module-pin-unverified`, `gate-receipt-drift`); a derivation that cannot read its inputs admits nothing and names nothing new. There is no partial admission: a module is admitted whole or not at all, and the adapter digest likewise.

Guard convention: every fix lands with a test that fails on the parent and passes on the fix, recorded in the audit round as the hand counterfactual, in `plugins/hexaemeron/tests/test_gate_commands.py` for the adapter and `plugins/hexaemeron/tests/test_gate_deferred_registration.py` or a new module for the controller. The release-adapter reconstruction test (`GateReceiptTests.test_released_criteria_admission_replays_through_consecutive_amendments`, asserting `d7e49768…`) needs a `source.replace` line for every changed constant, or it fails on a digest mismatch. Elenchus command for every step: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, format `unittest-json-v1`. Two audit records in section 2 show this suite's runner returning `inconclusive` under the containment boundary (skills#1765); when that recurs, the round logs the hand counterfactual and claims no guard. Elenchus owns the triage order and the guard rule.

## 12. Decisions and their homes

Expensive to reverse:

1. Replay provenance comes from the run's starting commit, not only from a reviewed list. This changes the doctrine [gate-commands.md](https://github.com/wildcat-finance/skills/blob/dd2e6939ed460dcd987457a398a2765822349588/plugins/hexaemeron/skills/protasis/references/gate-commands.md) states at lines 163 to 169 and the sentence at lines 185 to 188 that `ac527913…` is not admitted. Home: `docs/decisions/drafts/admit-starting-commit-gate-bindings.md`, a numberless draft Step 1 creates, numbered at integration against the actual base. The reference, the Fiat SKILL "Runbook command evidence" section, the Protasis `protasis-gate-command-validation` stanza and both `EVOLUTION.md` generation rows record the consequence; the draft carries the reasoning and the alternatives above.
2. The adapter's public keywords grow by one (the admitted bindings the caller derived). Home: the same draft and the reference's keyword list.
3. The `status` `provenance` field. Home: the reference's inspection paragraph and the Fiat SKILL section.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | base-commit-bindings
record | docs/decisions/drafts/admit-starting-commit-gate-bindings.md
```

Hypomnema owns which decisions earn a record and where each lives; the draft follows the shape of `docs/decisions/drafts/bind-a-step-created-runner-at-its-push.md`.
