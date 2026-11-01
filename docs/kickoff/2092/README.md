# Wildcat V2 wrapper subjects specification

## Source bundle

This bundle preserves the receipted #2092 study, runbook and selected design record as exact byte copies. It also holds the design model, the builder that computed the 24 selection reports, those reports and the conformance resolver. `study.md` has SHA-256 `35ee6b0f2816d49d4cf2fd775c413ba47d0f76054c169e423ee5d4d1056c5e88`, `runbook.md` `406f7b923eb18806ad1bf277d4bcc84de220a3dfc303fd5aca1566eada54307a` and `design-evidence.json` `fef4c019110a7146d94eff005b4d20cac8a39caa1d31d3fa3b036e60fe6a8f25`. Each report under `design/reports/selection/` carries the digest the design record declares for it. Controller state stays local and isn't in this bundle.

## Selection and conformance

`design/build_design_evidence.py` computes every selection value from the declared facts in `design/model.json` and runs no product code. The reports keep their original command identities, which name `.hexaemeron/design/`. To reproduce them, stage `design/` under `.hexaemeron/` in a fresh worktree at Skills `50d71a2e8c1777f8eb26db32dd8adeadb34063bd` and run that command. The builder refuses rather than replace a report that differs.

`design/conformance.py` resolves the four conformance cells the design record leaves pending by running named assertions in `plugins/alexandria/tests/test_wildcat_wrappers.py`: `LegacyIdentityTests` from Step 1, `WrapperReleaseTests` and `WrapperRefusalTests` from Step 3 and `PortableBudgetTests` from Step 4. The driver ran the resolver once per criterion at `b817990295fc906184e38a61cb2c02edeeb100cb`, and the four reports under `design/reports/conformance/` are byte-exact copies of that run. The audit fixes `1721ffe76ff9dec71a5006a956e6b2d90b0b8459` and `49622be03c7b0a864bb70f6bbd51701623df720f` then changed `PortableBudgetTests`, so the `portable-payload-within-budget` report predates them. At `49622be03c7b0a864bb70f6bbd51701623df720f` the resolver's `execute` for that criterion still passed in process; the script itself was not re-run.

## Steps

Run each Step's focused tests from the repository root with Python `3.14.6`, replacing `N` with the Step number:

```sh
python3 plugins/alexandria/tests/emit_wrapper_report.py --step N --report .hexaemeron/steps/N/focused.json
```

Step 1 adds the registered runner `plugins/alexandria/tests/emit_wrapper_report.py`, its implementation `plugins/alexandria/tests/wrapper_reports.py`, the runner and bundle tests in `plugins/alexandria/tests/test_wrapper_report_runner.py`, `LegacyIdentityTests` in `plugins/alexandria/tests/test_wildcat_wrappers.py` and this bundle. The runner runs the named Step's classes in process, launches no subprocess itself and writes `unittest-json-v1` with the actual test, failure, error and skip counts to a fresh path under `.elenchus/` or `.hexaemeron/`. With `--retained` it exits 2 and writes no report unless `ALEXANDRIA_WILDCAT_V1_STAGING` and `ALEXANDRIA_WILDCAT_V2_STAGING` are both set. Any skipped test makes it exit non-zero.

`LegacyIdentityTests` pins the constructed V2 release `sha256:f2b94e967c761a871129f5889fd372e992d62de87104fb5d5a4480338f9915a1` and V1 release `sha256:cbbacc59170bdf549c56347f8a962a869a6632868606a1ce3a0e1b37c0ae3def`, both built through the fake transport at the starting commit, plus the three registry digest constants and the generated registry bytes.

Step 2 adds the `wildcat_v2_wrappers` plan field with rule `wrapper-deployed/v1`, the pure derivation of the wrapper set from preserved `WrapperDeployed` logs in `plugins/alexandria/scripts/alexandria_lib/wildcat_wrappers.py`, the `alexandria-wildcat-v2-wrapper-subjects/v1` component and the bounded gap sentences for discovered wrappers the plan does not declare.

Step 3 wires declared wrappers through collect, reconcile, build and `check`: each declared wrapper joins every shard's address filter, its epoch opens at its `WrapperDeployed` block, and `check` re-derives the `wrapper-subjects` component and lists each wrapper. Build and `check` refuse by name an unknown market, a declared wrapper with no `WrapperDeployed`, a declared wrapper's `WrapperDeployed` log whose block hash differs from the header read of its block, a declared wrapper with no code at its first block and a wrapper log before its epoch.

Step 4 adds `plugins/alexandria/tests/wrapper_demo.py`, which runs the constructed specimen and the four refusal cases through `usdc_interval.py`'s CLI, and `PortableBudgetTests`, which measures what Steps 1 to 3 add to the portable payload. `WrapperDemonstrationTests` also runs that script under `python3 -I`, and `PortableBudgetTests` runs `git` and the payload's Horos scan, so a Step 4 run launches subprocesses; the V2 and V1 retained modules run their example's `demo.py`. `demonstration.md` records the commands, the constructed release, the refusals, the payload measurement and the retained rebuild of the preserved V2 and V1 releases.

## What stays unestablished

No real wrapper has been collected, so only constructed data has exercised wrapper subjects. Wrapper immutability and single-factory provenance are not established, and every wrapper release states both as gaps. The preserved releases declare no wrappers, so their retained rebuild shows only that legacy identities hold. Tabularium's wrapper contexts stay with the issue's `tabularium-wrapper-context` carryover.

The selected design and the three rejected candidates are recorded in `adr/admit-wildcat-v2-wrappers-as-declared-subjects`, numberless until integration assigns it.
