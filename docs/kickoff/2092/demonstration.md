# Wildcat V2 wrapper subjects demonstration

Issue #2092, Step 4, run with Python `3.14.6` from the repository root. Every
wrapper record below was constructed in
`plugins/alexandria/tests/test_wildcat_wrappers.py`; none was observed on a
chain.

## Constructed release

```sh
python3 plugins/alexandria/tests/wrapper_demo.py
```

The script calls `usdc_interval.main` once per command. It replaces
`transport_from_environment` with the fake transport from
`plugins/alexandria/tests/test_wildcat_venue.py` and refuses socket
construction, so collect and reconcile reach no network. Paths are relative to
a temporary root the script creates and removes. The specimen plan declares
wrapper A, `0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`, and wrapper B,
`0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`, in `wildcat_v2_wrappers`, each
named by one constructed `WrapperDeployed` log from the wrapper factory
`0xea6de11f8f3f83c79bd9d8db5517fcfdf2bb148a`.

```text
collect --plan specimen/plan.json --staging specimen/staging --registry registry.json
reconcile --plan specimen/plan.json --staging specimen/staging --provider-class "second constructed provider, class only" --registry registry.json
build --plan specimen/plan.json --staging specimen/staging --registry registry.json --created-at 2026-09-20T06:00:00Z --output specimen/release
check specimen/release
```

All four commands exit 0. `build` prints the release identifier
`sha256:9dc8e1d1a585491e3842d5b3a4a815a1f06630dd90fe23b4fbfa09e647516962`, and
`check` reports the same identifier with this `wrappers` listing:

```json
[
  {
    "attributed_logs": 3,
    "declared": true,
    "deployment": {
      "block_number": "25895390",
      "log_index": 5,
      "transaction_hash": "0xc1ba4901003bb228b5f1b9be99f45aca0d8589f0bd45965e6bd8834f1eff8964",
      "transaction_index": 2
    },
    "epoch": {
      "end_block": "25895419",
      "implementation_code_sha256": "7df00bea75e6c65c554bea8397e60bcbee1683c45f8b19792f532abf39f38e84",
      "start_block": "25895390"
    },
    "market": "0x02e0415e828a5f97309f93f001885b5db8a87d71",
    "wrapper": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  },
  {
    "attributed_logs": 1,
    "declared": true,
    "deployment": {
      "block_number": "25895400",
      "log_index": 9,
      "transaction_hash": "0x3d4589fc17fd2411112e6ca40cfa6075dbc7dca2984219ee41f51cc387207079",
      "transaction_index": 4
    },
    "epoch": {
      "end_block": "25895419",
      "implementation_code_sha256": "1f2212c33bc410b2d97c807952e733f608b35d1923d9695e5cb3c2db49eb6721",
      "start_block": "25895400"
    },
    "market": "0x20632bd54e16fcbcd35dcb2c8882a8a8802ad38d",
    "wrapper": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  }
]
```

## Refusals

For each case the script changes the specimen to carry it and runs the same
four commands, stopping at the first that exits non-zero. Each refusal exits 1
and names the wrapper and the block or market at fault:

1. Unknown market. Collect refuses: `usdc-interval: a preserved WrapperDeployed log at block 25895390 names market 0x1212121212121212121212121212121212121212, which is not one of the 80 markets the registry declares, for wrapper 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
2. Wrapper without code. Collect refuses and records failure receipt code `no-code-at-wrapper-deployment`: `usdc-interval: wrapper 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa has no runtime code at block 25895390, the block of the WrapperDeployed log that names it, so no epoch opens for it`
3. Wrapper log before its epoch, a constructed log from A at block 25895385. Collect and reconcile exit 0; build refuses and writes no release: `usdc-interval: wrapper 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa emitted a preserved log at block 25895385, before block 25895390, where the WrapperDeployed log that names it opens its epoch; no epoch owns that log`
4. Declared wrapper without deployment. Collect refuses: `usdc-interval: declared wrapper 0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb is named by no preserved WrapperDeployed log from the wrapper factory 0xea6de11f8f3f83c79bd9d8db5517fcfdf2bb148a inside the interval, blocks 25895340 to 25895419`

Collect records no failure receipt for cases 1, 3 and 4. Collect never hands
build a staging tree carrying cases 1, 2 or 4. Step 3's `WrapperRefusalTests`
prove that build refuses such a tree, admitting each case past collect with a
patch; this script does not repeat that.

The script then runs `check` over four copies of the specimen release, each
with one journal record edited to carry one case. Each copy is re-sealed with
its objects moved to the paths their new digests name, so `verify` accepts it.
`check` exits 1 on each copy:

| Case | Edited component | Message |
| --- | --- | --- |
| 1 | `logs`: market topic of A's `WrapperDeployed` set to `0x1212121212121212121212121212121212121212` | case 1's message above |
| 2 | `epoch-evidence`: A's `eth_getCode` answer set to `0x` | case 2's message above |
| 3 | `logs`: emitter of the constructed log at block 25895345 set to A | case 3's message with block 25895345 in place of 25895385 |
| 4 | `logs`: first topic of B's `WrapperDeployed` changed | case 4's message above |

## Portable payload

`PortableBudgetTests.test_run_adds_at_most_five_payload_files_and_100000_bytes`
measures the payload against run base
`50d71a2e8c1777f8eb26db32dd8adeadb34063bd`. The run adds 2 files and 51,527
bytes across the 11 shipped paths it changes, against limits of 5 files and
100,000 bytes. The two files are
`plugins/alexandria/scripts/alexandria_lib/wildcat_wrappers.py` and
`plugins/alexandria/schemas/wildcat-v2-wrapper-subjects-v1.schema.json`. The
rendered `.horos/boundary.json` is outside the comparison.

## Retained rebuild

The V1 and V2 staging trees were restored from internal custody into a private
directory outside every repository and named by
`ALEXANDRIA_WILDCAT_V1_STAGING` and `ALEXANDRIA_WILDCAT_V2_STAGING`:

```sh
python3 plugins/alexandria/tests/emit_wrapper_report.py --step 4 --retained --report .hexaemeron/steps/4/retained.json
```

- V2 release `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`: pass.
- V1 release `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`: pass.

No retained test skipped. One run of the command over this Step's sources took
84.9 seconds of wall-clock time. That is an observation, not a budget.

## What this establishes

On constructed data, a plan declaring two wrappers collects, reconciles, builds
and checks through the CLI, and `check` lists each wrapper with its market,
deployment position, epoch and attributed log count. Each of the four cases
refuses through the CLI, and `check` refuses each on an edited release that
`verify` accepts. The preserved V2 and V1 releases rebuild to their
identifiers with this Step's code.

It does not establish:

1. That any real wrapper can be captured. No real wrapper data was collected and no RPC was called.
2. Wrapper immutability. Each wrapper's code is treated as immutable over its epoch, and every wrapper release states this as a gap.
3. Single-factory provenance. Whether every wrapper comes from the factory `0xea6de11f8f3f83c79bd9d8db5517fcfdf2bb148a` stays unknown, and every wrapper release states this as a gap.
4. Anything about wrappers in the preserved releases. Their plans declare no `wildcat_v2_wrappers`, so the retained rebuild shows only that legacy identities hold.
5. Tabularium's wrapper contexts, which stay with the issue's `tabularium-wrapper-context` carryover.
