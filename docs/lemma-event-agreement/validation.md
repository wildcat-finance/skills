# Lemma event agreement: Wildcat successor validation

Step 3 of Fiat run 1366 rebuilt all 10 accepted Wildcat V1/V2 partitions twice with the successor event validator. In both builds, chunk bytes, chunk IDs, schema, event census and corpus build IDs equal the accepted baseline. Provenance changes in one field, the chunker version.

This delivery covers Wildcat V1/V2 only. On 2026-09-27 the operator decided to integrate it into `main` ahead of the other venues. That decision supersedes the clause in the [study](study.md) and [runbook](runbook.md) that kept base integration blocked on them; both otherwise still define the scope. Seven venue-generation results remain unavailable: Aave V3; Maple V1, V2 fixed-term and V2 open-term; Euler V1 and V2; and Centrifuge V3's hub and corresponding spokes. [#1366](https://github.com/wildcat-finance/skills/issues/1366) stays open for them, and [#1359](https://github.com/wildcat-finance/skills/issues/1359) tracks their obligations and corpus handoffs. This record holds no private source or corpus bytes.

## Inputs and bindings

- Accepted archive: `lemma-1359-wildcat-reviewed-2026-09-26.zip`, SHA-256 `c2933988f0619b2874c5880211ef0f6d3586f3a463515b317ff8a7f609785fe1`, 21,728,910 bytes, 150 members.
- Accepted build plan: `build-plan.json`, SHA-256 `363ba016b86abb899feff6855f7fc901f0e7d697c9a031d894757adbb86f2ddc`, with 10 partitions and 15 inputs. Baseline report: SHA-256 `49a2add79b21a21bcf3713d6491f95b00e6966de72424760c6c493d48da1d4ed`.
- Successor tool: commit `a801dd9381d62e46e6a0fbd4dae9fc95e820fc80`, `plugins/lemma` tree `95d7bcfd298591e61f6764fd67cd955d215536ee`, skill version 0.3.1. Control tool: commit `df56bfeec3f67bf689d0b083c4994fc329477905`, whose three tool sources equal the accepted plan's `tool_sources`.
- Compilers: 0.8.22+commit.4fc1097e, 0.8.25+commit.b61c2a91 and 0.8.28+commit.7893614a. Their wrapper and soljson digests equal [`compiler-evidence.json`](../../plugins/lemma/tests/fixtures/issue-1366/compiler-evidence.json).
- Runtimes: the CPython pin in [`.python-version`](../../.python-version); Node.js v26.6.0, SHA-256 `1ef99ea25fe70c9b67e7efe768ef8ee22148d3cabc703db6131b57aeb617d040`.

The successor binding pins the three runtime tool sources at `a801dd93`:

| Path | SHA-256 | Git blob |
| --- | --- | --- |
| `chunkers/solidity.py` | `3bef581a4bfb6bb46a5e726c3be47cee43cf0362e77ea04a96e0feb1acd873b8` | `2c7db3b9650502f8f5cd1aaf8b79b8791dfd51f5` |
| `schema.py` | `032a58e9586b98bc2d754b1f30558a00bac9f844e23a1c594a0629373826a775` | `214ae1ab51eb0725ee1aa75a8ce86a4f3ee31bbd` |
| `skills/lemma/SKILL.md` | `033c03b15ea411e64828bf5960d82c7e1a51a6f4409a2660671cc86cf53ebb18` | `17e3381334a0732cb91172ba3f37fcc37a3bd205` |

Both tools ran from read-only `git archive` snapshots whose every file matched the commit's `plugins/lemma` tree. The driver rechecked the bound bytes after each build. The accepted bundle and its old tool binding were not edited.

## Commands

The reporters ran from the clean step tree at `a801dd93`:

```sh
python3 plugins/lemma/tests/emit_issue_1366_report.py --case event-conformance --report .hexaemeron/steps/3/mason/conformance-2.json
python3 plugins/lemma/tests/emit_issue_1366_report.py --case event-tests --report .hexaemeron/steps/3/mason/event-tests.json
```

The evidence run of the private driver used `D=~/Downloads/lemma-1366-6bOLSX`, `B=~/Downloads/lemma-1359-wildcat-reviewed-2026-09-26` and `M` naming the run's `.hexaemeron/steps/3/mason` directory:

```sh
python3 "$D/step-3/driver/successor_verify.py" run \
  --archive "$B.zip" --archive-sha256 c2933988f0619b2874c5880211ef0f6d3586f3a463515b317ff8a7f609785fe1 --archive-members 150 \
  --bundle "$B" --baseline "$D/baseline" --baseline-verification "$D/baseline-verification.json" \
  --baseline-verification-sha256 49a2add79b21a21bcf3713d6491f95b00e6966de72424760c6c493d48da1d4ed \
  --baseline-timing "$D/baseline-timing.json" \
  --binding "$D/step-3/successor-tool-binding.json" --control-binding "$D/step-3/control-tool-binding.json" \
  --fixtures "$D/step-3/tools/lemma-a801dd93/plugins/lemma/tests/fixtures/issue-1366" \
  --conformance-report "$M/conformance-2.json" --event-tests-report "$M/event-tests.json" \
  --named-tests-log "$M/named-tests.log" --repo <run worktree> \
  --output "$D/step-3/evidence" --report "$D/step-3/successor-verification.json"
```

It built each partition with the accepted `build_wildcat.py` invocation, two partitions at a time: `python3 <tool>/chunkers/solidity.py --input <each plan input> --solc <bundle wrapper> --expect-solc <pin> --include 'src/**' --no-dedupe --source-ref <plan source_ref> --out <destination>/chunks.jsonl`. The order was two control builds, then two successor builds, each into a fresh directory.

## Results

| Generation | Partition | Chunks | Events | Interface events | Successor provenance SHA-256 |
| --- | --- | ---: | ---: | ---: | --- |
| V1 | `core-da74452a` | 692 | 70 | 53 | `43460988382257ec39d7e1e7d92024fad969efb2191e83d2d40e38f4276f6b8d` |
| V1 | `sentinel-6164ddd4` | 57 | 6 | 6 | `386134cc1c43cb2be917ba66723f4477daecb75435fd8b24f3cee279dae74b4c` |
| V1 | `lens-verified-mixed` | 756 | 70 | 53 | `7f839b9ce21cf307149f1fccfe62c660e39a6c88299a07bea25582a6cb2ef07a` |
| V2 | `core-a70f297f` | 989 | 84 | 51 | `ce1dafd406ec29665412bf2adf3b30b40b466343154ce59f53bc5467c24eda6f` |
| V2 | `lens-e1f77540` | 989 | 84 | 51 | `b496e47f2093e4aab3bb0385c5cb798f2aae46505a228b2269fd209889e59841` |
| V2 | `fixed-term-730-5838b2f3` | 276 | 15 | 0 | `c51eb4481e36450349d0c289c5801ca8c87b0e63a45207cda5ce3e0d4a794372` |
| V2 | `fee-recipient-ac73bda3` | 35 | 4 | 0 | `d20d32fb991d7946775b7405b556c8b2c0c8feb51d1df40fb978c026bad3e497` |
| V2 | `role-provider-5d7f8c88` | 8 | 0 | 0 | `77bf49795356448aefc127b162acce3c7c2030bf4c5062f0942a5ff7433d1bc6` |
| V2 | `collateral-46dba596` | 227 | 29 | 17 | `4ed2c4930c7906066b0994becec73d6810fcea1c768f80a263db4b67378f2333` |
| V2 | `wrapper-c7be4039` | 180 | 20 | 18 | `60bc11142756e8eed2888f4e96a4b4ae0ad5eb29d14a14ef1db495140e822565` |
| Total | | 4,209 | 382 | 249 | |

For every partition in both successor builds:

1. `chunks.jsonl` equals the baseline and the accepted `corpora/` copy byte for byte, 9,204,504 bytes per build. Chunk IDs match the baseline in order.
2. Chunks and provenance report zero schema faults. The corpus build ID equals the baseline and recomputes from the written chunks.
3. Provenance inputs, compiler block, source ref and source selection match the plan and a fresh compile.
4. The event census equals the baseline report: path, contract, kind, name, line, declaration SHA-256 and chunk ID. Each declaration matches exactly one Event chunk, and no Event chunk is unmatched.
5. The second build reproduces the first. Chunks, provenance and stderr are byte-identical; stdout is identical once the destination root is masked. All 15 compiler outputs are byte-identical across the two builds.
6. The successor validator, run in-process on each of the 15 compiler outputs, passes with 0 added compiler calls and at most 1,221 type expansions.

## Provenance change

Each successor `provenance.jsonl` differs from the baseline in `chunker_version` only: `0.2.1` becomes `0.3.1`, the governed version in `plugins/lemma/skills/lemma/SKILL.md` at `a801dd93`. So every provenance SHA-256 changes (the baseline report holds the old values), and stdout's `--producer-version` capture flag reads `0.3.1`. Provenance size stays 32,118 bytes per build. Chunk bytes and corpus build IDs are unchanged because chunk records do not carry the chunker version.

The two control builds, using the accepted tool at `df56bfee` through the same driver, reproduced every accepted chunk and provenance file byte for byte. The version change therefore comes from the tool, not from the driver.

## Refusals through the pinned compiler

The production CLI ran each case with the pinned wrapper behind a pass-through script. The script mutates the output of one named compiler call and logs each call.

| Case | Input | Result |
| --- | --- | --- |
| Synthetic control | `event-input.json` fixture, 0.8.25 | exit 0; corpus and provenance written; 1 compiler call |
| Indexed bit | same, first `indexed` flag flipped | exit 1: `event descriptors differ (Changed: inputs[0].indexed)`; no output |
| Unsupported AST shape | same, parameter type node set to `Mapping` | exit 1: `unsupported event AST type shape 'Mapping'`; no output |
| Missing membership | same, `usedEvents` removed | exit 1: `missing, malformed or oversized usedEvents membership`; no output |
| Pass-through count | V2 `core-a70f297f`, 5 inputs, no mutation | exit 0; 5 compiler calls; chunks equal the accepted bytes |
| Late unit | V1 `core-da74452a`, second of 2 units flipped | exit 1 after 2 calls; the accepted chunks and provenance placed in the destination keep their digests |
| Single unit | V1 `sentinel-6164ddd4`, flipped | exit 1; the accepted files placed in the destination keep their digests |

Every refusal names the mutated contract, and the event where one was mutated, and prints `corpus and provenance unchanged`.

## Conformance and tests

- Conformance resolver: exit 0, `value: true`, 13 tests. Report SHA-256 `df63a83465d537e7095589eba34d8e0651e61cdcb6fc2725b9aef16349a14e3a`.
- Event suite through the step's Elenchus reporter: 47 tests, 0 failures, 0 errors, 0 skipped.
- Named reruns: both indexed-bit guard tests, unsupported primitive and compound shapes, missing and malformed evidence, late-unit no output and preserved existing outputs. 6 tests, OK.
- The step:3 design gate, `design_evidence.py .hexaemeron/design-evidence.json --transition step:3`, exits 0 with no findings.

These tests use in-process compiler fixtures. The refusal table above is their counterpart through the real compiler.

## Integrity

Before the builds, after each of the four builds and at the end, the driver checked all 150 archive members against the extraction. It also checked the 149 `SHA256SUMS` entries, the 15 plan inputs, the 6 compiler files and the baseline digests. The combined state digest `a79d6a4799352406afafedba161f0827f7cdce802274693993f353e44e89f1ce` was identical at all six checks. The extraction also holds 85 files outside the archive; the driver read none of them.

## Duration and size

| Build | Tool | Wall seconds |
| --- | --- | ---: |
| Control 1 | `df56bfee` | 5.6939 |
| Control 2 | `df56bfee` | 5.4484 |
| Successor 1 | `a801dd93` | 5.5953 |
| Successor 2 | `a801dd93` | 5.4235 |

The preserved baseline took 5.4840 seconds, using the accepted `build_wildcat.py` at `df56bfee` with two jobs. Each build wrote 9,204,504 chunk bytes and 32,118 provenance bytes. Two samples per tool cannot establish variance, so this record claims no speed change.

## Not established

- Seven venue-generation results are unavailable, not passed: Aave V3; Maple V1, V2 fixed-term and V2 open-term; Euler V1 and V2; and Centrifuge V3's hub and corresponding spokes. Their obligations stay on [#1359](https://github.com/wildcat-finance/skills/issues/1359).
- Full closure of #1366, which stays blocked on those results. Integrating the Wildcat V1/V2 tranche establishes none of them.
- Deployed log fidelity, compiler honesty, chain reads and bytecode agreement.
- Review of the driver in Git. It is private; the external report binds its SHA-256, `3ab6becab84c5273f4603edf4d59d2bf52b62bd78cb9ced193ab23c507eec77a`.

## External evidence

The external report is `~/Downloads/lemma-1366-6bOLSX/step-3/successor-verification.json`, SHA-256 `c9b7dcc1dcc7f432b4e08928574c13f453afb9c27afd5c01ca413e59981fd930`, 290,418 bytes. It retains every command, digest, wall time and size above. An earlier trial of the driver, written to `step-3/dev-1`, also passed; it is not cited because the driver changed after it. The successor tool binding beside it is `successor-tool-binding.json`, SHA-256 `a5e2811cbaba1f4fd3603dc021671b83283ec212a3648e22f255dec11d4f6193`.
