# Remaining venue event validation

On 30 September 2026, Mason rebuilt all 816 pinned remaining-venue inputs twice: 1,632 successful corpus builds, 19,735 event declarations and 214,906 chunks. Every pair has identical JSONL, provenance bytes and build identifiers. The independent census and complete corpus reconstruction passed for every partition. This producer record precedes the independent Fiat audit and publication receipts.

## Coverage

Registry SHA-256: `fef8a08e9cbb421ed7a45fa8d56ebec15fcb6b8fecd0e2a2c5571d7b2136103d`. The complete join has 12 resolved rows, including two inherited Wildcat rows, and eight excluded rows. All 816 required original inputs match their recorded byte size, SHA-256 and Git blob identity where recorded. The recovered Euler input was taken from the saved capture; this run made no live source requests.

| Registry row | Disposition | Partitions | Events | Chunks |
| --- | --- | ---: | ---: | ---: |
| wildcat-v1-ethereum-mainnet | inherited | 0 | 0 | 0 |
| wildcat-v2-ethereum-mainnet | inherited | 0 | 0 | 0 |
| aave-v3 | complete | 135 | 5589 | 52775 |
| maple-v1 | complete | 49 | 690 | 8132 |
| maple-v2-fixed-term | complete | 95 | 989 | 11728 |
| maple-v2-open-term | complete | 84 | 765 | 9473 |
| euler-v1 | complete | 60 | 1971 | 7906 |
| euler-v2 | complete | 179 | 1189 | 29971 |
| centrifuge-v3 | complete | 130 | 5478 | 57362 |
| morpho-optimizers | complete | 70 | 2142 | 25303 |
| morpho-blue | complete | 77 | 1482 | 18374 |
| morpho-midnight | complete | 10 | 43 | 2064 |

Some rows share source sets. The aggregate counts each of the 816 partitions once; summing this table counts shared partitions again. Excluded registry rows remain: `aave-v4`, `centrifuge-tinlake`, `centrifuge-v2`, `clearpool-permissionless`, `compound-v2`, `compound-v3`, `wildcat-v2-plasma-mainnet`, `wildcat-v2.5-release-line`. Eight recorded subjects lack source and 19 source sets lack a chosen public commit. Neither group was silently removed or reported as a deployed-code match.

Selections retain all sources except the five preparation cases already declared in the checked study. Two explicit reference-library exclusions, one compiler-resolved target closure, one metadata-target extraction and one reversible citation mapping retain their complete private requests and source maps. The selection record was reviewed by Mason for this static conformance scope; #1359 still owns source-to-deployment and path acceptance. Full reconstruction also checked 9,118 retained non-event aliases. Events retain separate declarations and have 0 aliases.

## Reproduction and evidence

The private evidence stays under `.hexaemeron/evidence/step-4-mason/full-v3/`. Each partition retains its original-input pin, preparation request and manifest, compiler transcripts, independent census, two dedicated corpus directories, CLI arguments, exits and stdout/stderr. The producer record pins the exact code and source-bound runbook. The original failed campaign remains under `full-v1/` with all 816 outcomes and both capacity refusals. The complete `full-v2/` campaign is also retained; a later repository check exposed a process-cleanup race, so `full-v3/` repeats every build after that repair.

| Private artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `.hexaemeron/evidence/step-4-mason/full-v3/bundle.json` | 1982143 | `9e5123772da5a0eef51af9b0f7aa8926062e195c540e88693404716748169643` |
| `.hexaemeron/evidence/step-4-mason/full-v3/verification.json` | 152345 | `d55f6e0e7873a1293fad1a8dae923abb4504ef8adc3397546f753f98866cdbfe` |
| `.hexaemeron/evidence/step-4-mason/full-v3/selection-review.json` | 492507 | `3eb5a990875479d32ddb4591bb98ee859c0e3c962b3a144c6096b0aa0e8ffdbf` |
| `.hexaemeron/evidence/step-4-mason/full-v3/producer.json` | 1720 | `9d7a3991b6b2bbca78ccadc05201432e702a763249541be502ce6ddc7e3c6b5d` |
| `.hexaemeron/evidence/step-4-mason/full-v3/production-example-config.json` | 323 | `1928e398a6130e508cc148f53bfa916cfcf4b6864dcb7e8b9b28229874e0a5a9` |
| `.hexaemeron/evidence/step-4-mason/full-v3/full-conformance-config.json` | 307 | `f6ca7578ad17fa9d461f4334242fa941574ed125ceb9f14696f9c7e3fa32428b` |
| `.hexaemeron/evidence/step-4-mason/negative-bundle-v2/report.json` | 2777 | `636d1d256bd5336b08c3e732dc4f58f8a4f95e2598099b878a350473acdbb599` |
| `.hexaemeron/evidence/step-4-mason/step-4-guards-candidate-counterfactual.json` | 177 | `cb0725711204e85d5fa69d3ff66940c3209d4adc571b1355b442452f95c8df42` |
| `.hexaemeron/evidence/step-4-mason/step-4-guards-green.json` | 177 | `153c56f42e82108b94983006256b0af0719142a1fa1184e31bec6babe5d641ee` |

From the run root, replay the full evidence with:

```bash
python3 plugins/lemma/corpus_evidence.py \
  --bundle "$PWD/.hexaemeron/evidence/step-4-mason/full-v3/bundle.json" \
  --root / --complete --full
```

The design resolvers use `.hexaemeron/evidence/lemma-1366-conformance.json`. Restore the exact `full-conformance-config.json` bytes there for `venue-conformance`, or `production-example-config.json` for the earlier nine-example `production-conformance` gate. Keep their reports separate and choose a fresh output path when replaying; existing consumed reports are preserved. The complete-input-custody gate accepts either configuration because both bind all 816 originals. The venue gate command is:

```bash
python3 plugins/lemma/tests/emit_issue_1366_remaining_report.py \
  --case venue-conformance --candidate prepared-events \
  --report .hexaemeron/reports/venue-conformance-recheck.json
```

Six mutations of the full bundle were refused: omitted partitions, duplicate partition, stale corpus digest, forged census, changed indexed ABI metadata with rebound manifest digest, and forged aggregate. The 121-test event suite also corrupts indexed metadata under all 20 compilers and checks refusal with absent and existing output files. The repaired preparation/evidence suite passed 35 tests, and the complete compiler-backed Solidity suite reported zero failures.

## Compiler identities and capacity

| Exact compiler identity | Partitions | Artifact SHA-256 |
| --- | ---: | --- |
| `0.6.11+commit.5ef660b1` | 36 | `9778e4a7667d5fd7632caf3ef3791d390a7cc217f94f96e919a31e3be332386a` |
| `0.8.10+commit.fc410830` | 87 | `5eaee3240a06891abf5ac70c75caf9a0c33ebe9a2736abdaa22a337f86c22933` |
| `0.8.13+commit.abaa5c0e` | 62 | `387343bcf8f2b77fe4cdcddcaa84361fabf8e1c3508f874fbbcbb9c313542f56` |
| `0.8.15+commit.e14f2714` | 2 | `71135e459d691767ce3453bab4564ef4a640dd50182da36517cbc1f96c1d4c7c` |
| `0.8.17+commit.8df45f5f` | 3 | `617828e63be485c7cc2dbcbdd5a22b582b40fafaa41016ad595637b83c90656c` |
| `0.8.18+commit.87f61d96` | 7 | `d82bdcba2c386d60b33aca148a9cfdf097551f68c5e45d8ec01aebbafacf5075` |
| `0.8.19+commit.7dd6d404` | 37 | `e0b74e0a16e783a35169f74d1a615ecb48d07c30f97346b83cd587949268681e` |
| `0.8.20+commit.a1b79de6` | 15 | `5c509f760dc110a695c8b39bbc21e08c17dee431aa14d606f59e623d7c3cc657` |
| `0.8.21+commit.d9974bed` | 18 | `45bea352b41d04039e19439962ddef1d3e10cf2bc9526feba39f2cc79e3c5a17` |
| `0.8.22+commit.4fc1097e` | 12 | `92d283c545395b91a656fa1ec94d567a464bca55aebcdbb99debf42b43026845` |
| `0.8.23+commit.f704f362` | 6 | `9c681b165c8647867589c0a5ecdc8692637a935928a2b1bbea2ff4a1f4976985` |
| `0.8.24+commit.e11b9ed9` | 151 | `11b054b55273ec55f6ab3f445eb0eb2c83a23fed43d10079d34ac3eabe6ed8b1` |
| `0.8.25+commit.b61c2a91` | 17 | `f8c9554471ff2db3843167dffb7a503293b5dc728c8305b044ef9fd37d626ca7` |
| `0.8.26+commit.8a97fa7a` | 15 | `db85e5396f523cc1a53c4c4d742e204f6dcba1a05842623d73be946809e11cd6` |
| `0.8.27+commit.40a35a09` | 52 | `d91c08277f801321af4e80958015aea18b41c01d2c6a38310a23014485b0e51c` |
| `0.8.28+commit.7893614a` | 179 | `72ef580a6ec5943130028e5294313f24e9435520acc89f8c9dbfd0139d9ae146` |
| `0.8.30+commit.73712a01` | 4 | `81475c98b6d2094a821fd9d7b6278556d8095ccc23e0b8a1029b1c08a89cd4b2` |
| `0.8.32+commit.ebbd65e5` | 1 | `d9216e6d578f67e1afd54ecb931b9db6a053ff2522d2e21eca3b61b337a9199c` |
| `0.8.34+commit.80d5c536` | 11 | `c8649f8d57f81b3244c7d2dd662efc0620d1ae296f623b347a2c616a6cfd11d8` |
| `0.8.7+commit.e28d00a7` | 101 | `663ba99f7c7ee907f0f03227502d48a78256c3c292ace3b79a5d3eb510665306` |

Two healthy compiler outputs held 2,533,341 and 2,699,890 decoded JSON values. Their retained stdout was 27,405,458 and 29,335,528 bytes, with zero compiler errors. The original shared 1,000,000-value cap refused them. `MAX_JSON_VALUES=4,000,000` now bounds decoding separately; the AST/corpus limits stay at 1,000,000, depth stays 128 and every byte cap is unchanged. Four pure decoder tests passed on the repair. Against the unchanged parent decoder they produced three assertion failures, zero errors and zero skips. Both real outputs then decoded successfully, and both partitions passed complete double builds.

The first final repository run passed 14 of 15 selected checks. Its preparation test exposed a Darwin race: an overflowing child had exited, and signalling its zombie-only group raised EPERM before cleanup reaped it. Recovery now requires an observed terminal leader, reaping and a signal-zero probe proving group absence. Live or unknown groups still refuse. No delivering signal follows reaping. Eight combined decoder and cleanup guards passed; against the unchanged Step 3 product they produced six assertion failures, zero errors and zero skips. Native Darwin red/green records and the original failed repository report remain private.

The final campaign used six worker processes and took 414.125 seconds. It read 91,739,305 original-input bytes and retained 1,009,092,146 bytes in paired corpus/provenance files. These are observations from this machine and workload; they support no comparative speed or memory claim.

Required repository gates are `python3 scripts/run_checks.py --scope lemma --scope root` on the final code and `.githooks/greenlight` on the staged tree. Fiat's audit and publication records carry their completion and the independent review result.

## Inherited evidence and handoff limits

Wildcat V1/V2 remain inherited. The accepted archive was rechecked at 21,728,910 bytes with SHA-256 `c2933988f0619b2874c5880211ef0f6d3586f3a463515b317ff8a7f609785fe1`; all 149 pinned content members matched. The prior event-validation document was byte-identical to merge `d0349335f9949de5a4ae84fc2d718f676dcc582b`, SHA-256 `f5493ea54bf812936a2cb3e6a8d8719c240e8597ef849d0440fc47099d6325ef`. Its historical external report paths are absent locally, so this run claims neither fresh Wildcat execution nor revalidation of those missing external bytes.

The result establishes static compiler AST/ABI agreement, source-linked chunk reconstruction, declared selection coverage and repeatability for these pinned inputs. Recorded compiler transcripts are not authenticated execution evidence. Source-only results establish no source truth, deployed bytecode identity, runtime emissions or #1359 acceptance. Original deployment qualifications and gaps remain in the private registry join. Neither the #1872 capture controller nor the #1359 controller was changed.
