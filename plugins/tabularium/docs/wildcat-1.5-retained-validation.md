# Retained Wildcat adapter 1.5.0 validation

Issue [#2148](https://github.com/wildcat-finance/skills/issues/2148) promotes the existing adapter `1.5.0` after a retained V2 build and offline verification. The operator authorised raising the generated-file budget. Its limit is now 1 GiB (1073741824 bytes), four times the former 256 MiB (268435456 bytes). Builder output checks, Wildcat verification and the coverage-manifest entrypoint share that limit. Raw component, aggregate-input and record-count limits remain unchanged.

## Retained result

The input was the previously R2-recovered, locally retained Ethereum mainnet V2 interval from block 21866550 to block 26022093, Alexandria release `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`. No new RPC collection ran. Two prior unmodified adapter-1.5.0 builds at Skills commit `2bbdd5d94653cdf19a3256f16d495c947ca0f2a9` refused with `Wildcat release artefact exceeds the output byte budget`. The measured `source.json` size was 297518776 bytes. Those refused builds supplied no accepted release.

With the larger limit, the explicit `--adapter-version 1.5.0` build and its separate offline verification both exited 0. After default promotion, an invocation omitting that option and its separate verification also exited 0. Both builds used release identifier `miskatonic-mr03-wildcat-v2` in distinct fresh private directories. Every generated file matched between the two builds. Each command ran under OS network denial with closed stdin; source-file hashes were checked before and after each command. Full captures and generated releases remain private.

The release contains 73219 canonical records and 8837 `recorded-hook-call-input` observations across 63 distinct recorded markets:

| Hook | Observations | Recorded hook gaps |
| --- | ---: | ---: |
| `onDeposit` | 5125 | 0 |
| `onQueueWithdrawal` | 3319 | 0 |
| `onTransfer` | 393 | 0 |
| `onExecuteWithdrawal` | 0 | 0 |
| `onRepay` | 0 | 0 |

The hook-gap collection is empty: zero `caller-not-registered-market`, `failed-call` and `failed-ancestor` entries. Every observation's recorded caller and target match its market and hooks-instance fields. The separate CLI verification rebuilds the observations from the copied raw release, including deployment-context target checks and native calldata decoding. No malformed-frame refusal occurred after the budget repair. Zero observations for a hook establish only its absence from this bounded mapped output.

| Generated file | Bytes | SHA-256 |
| --- | ---: | --- |
| `source.json` | 297518776 | `474b0eb101de4e09872e0d7b41c1218c036ba01bb59f1c63f9738da217e8f20e` |
| `capture.json` | 187339 | `04a0abe0146b4287200c1ce322aeb5997a4746b2c830e2ec94279fc4638bc493` |
| `events.jsonl` | 185634904 | `dbe64fe49d1517de046b6e057f8cd2cef2d644ef06c934fc842ae316f34faf82` |
| `coverage.json` | 191758 | `03ca57a86dc52443d1c8e12012549af02f02699f411d76ea1aca8508b5f191b8` |

## Compatibility and reproduction

A current-source adapter-1.4.0 control previously built and verified on the same retained input. Its four generated files matched the pinned 1.4.0 control byte for byte. The new 1.5.0 source, after removing `state_observations`, equals that 1.4.0 source. All 73219 canonical rows equal their 1.4.0 counterparts after removing only `provenance.adapter_version`; coverage counts are equal. Earlier version selectors and published example bytes remain unchanged.

The constructed default-selection regression failed against the former default: its source omitted the hook observations. It passed after promotion, comparing all four files with an explicit 1.5.0 build. The focused hook suite passed 18 tests. A separate negative test lowers the shared cap and checks that build and verification refuse, with no published output after the refused build.

Use the interpreter pinned by [`.python-version`](../../../.python-version) and fresh output directories. These commands read a preserved local input; they do not fetch one:

```sh
python3 plugins/tabularium/scripts/tabularium.py wildcat-canonical \
  --alexandria-release INPUT --adapter-version 1.5.0 \
  --release miskatonic-mr03-wildcat-v2 --out EXPLICIT_OUTPUT
python3 plugins/tabularium/scripts/tabularium.py verify EXPLICIT_OUTPUT/coverage.json
python3 plugins/tabularium/scripts/tabularium.py wildcat-canonical \
  --alexandria-release INPUT \
  --release miskatonic-mr03-wildcat-v2 --out DEFAULT_OUTPUT
python3 plugins/tabularium/scripts/tabularium.py verify DEFAULT_OUTPUT/coverage.json
```

## Size and evidence limits

The 297518776-byte source includes 239569813 bytes of mapping records (74088 entries), 36789117 bytes of hook observations, 19837117 bytes of dispositions (74088 entries) and 1112808 bytes of shared contract contexts (137 entries). These sizes measure canonical JSON values; object keys and separators account for the remaining bytes. Mapping records repeat native logs, ABI definitions, decoded fields, context, source references and limitations. Their ABI definitions alone occupy 47247667 bytes. Full native logs also appear in the canonical event file and the copied raw release.

The larger finite budget admits this retained Wildcat release. It establishes no Aave V3 or Morpho scale result. The current builder materialises its JSON in memory. [Miskatonic epic #129](https://github.com/wildcat-finance/miskatonic/issues/129) owns the future format work: preserve evidence once, reference shared definitions and source objects, and stream bounded shards. That format is not implemented here.

Hook input states remain recorded intermediate call inputs, not independently proved final stored market state. Gaps and limits inherited from the preserved capture remain visible. Offline verification establishes implemented mapping and local byte consistency; it establishes neither provider completeness, chain finality, publisher authenticity, counterparty identity nor accounting acceptance. This promotion changes no sealed Miskatonic mapping-3 or ledger-r2 record and supplies no #109 accounting review.
