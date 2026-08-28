# Issue 556: resolve runbook target versions at integrate time

Rounds for the run on branch
`fiat/556-resolve-runbook-target-versions-at-integrate`, off `main` at
`8e6480230a5f43c57aef4f9a6c52f4c602d86790`. The run's audit record is this
file; `audit/AUDIT.md` is unchanged.

## Step 1, round 1 -- 2026-08-24

Non-Solidity round over Mason commit
`77458260d3fb0386a2d60b062a91e6c2c636ece4`. Two findings, both fixed on the
named audit branch in this round.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | `plugins/hexaemeron/skills/protasis/scripts/protasis.py` | The relation row and path checks rejected C0 controls and DEL but accepted C1 and Unicode format controls. An otherwise valid path containing U+0080 or U+202E returned no P006 finding, despite the closed contract refusing control characters. | fixed in this round: one printable-boundary check now covers the complete row and the path helper; both code points are regression cases in `test_unsafe_paths_refuse` |
| S1-R1-02 | medium | `plugins/hexaemeron/skills/protasis/scripts/protasis.py` | Five P006 messages interpolated a runbook-controlled target id, ledger path, or relation value. A row can occupy almost the 2 MiB document cap; a refusal then copies source content into output instead of naming only the failed field and check. | fixed in this round: P006 diagnostics are value-free, and `test_relation_findings_do_not_echo_runbook_controlled_values` covers the invalid-id, duplicate-path, unknown-relation, and concrete-token paths |

### Evidence

The Warden red report is
`.elenchus/fiat-556-step-1-warden-round1-red.json`, SHA-256
`4f5d633f93444d39e5f86c1036cfbbedf84ef4d9da8b5cb071c22915c7a4dd9f`.
It records `elenchus.unittest.v1`, 1,057 tests, six assertion failures, zero
errors, and zero skips while the worktree diff contained the guards and no
product fix. The fixed-tree report is
`tmp/elenchus/fiat-556-step-1.json`, SHA-256
`2a6d37d37d479e94097a3a283db04b0c59881cfce198755572b78846ee5f3405`.
It records 1,057 tests, zero failures, zero errors, and zero skips.

Mason's earlier evidence remains intact. The first parser red is
`.elenchus/fiat-556-step-1-mason-red.json` with 1,055 tests and 22 assertion
failures. The link-placement red is
`.elenchus/fiat-556-step-1-link-conflict-red.json` with 1,056 tests and two
assertion failures. Both have zero errors and zero skips. Mason's signed commit
has parent `8e6480230a5f43c57aef4f9a6c52f4c602d86790`, a good local Shoggoth
signature, and exactly one co-author trailer and one origin trailer.

The fixed tree passes 89 focused Protasis tests, 350 root tests, all 71 Promise
Machine coverage rows, and the 1,057-test Hexaemeron report above. Phylax,
Ephoros, and Hypomnema exit 0 over the changed product paths. Both Promise
Machine commands are clean. Protasis accepts the receipted study and amended
runbook, and Horos reports that the boundary matches the tree.

The bounded Sapheneia record pass preserves every finding, qualification,
identifier, path, hash, count, verdict, and status. Imprimatur scores this file
100.0 with zero defects. Brevitas reports B011 only: the required findings
table has two data rows. It stays one row per actual finding; adding a third
would change the round's finding count.

The tracked study is byte-identical to the receipted study at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`.
Its five relative skill links resolve from `docs/fiat-version-relations-study.md`.
The tracked runbook is byte-identical to the amended receipt at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
The misplaced plugin-local study path is absent. The changed product paths are
six paths, all authorised by the amended Step 1 Files field; no other product
file changed.

### Risk register

Four risk-register concerns are reachable in this step. `relation-block-shape`
surfaced S1-R1-01; every other malformed, duplicate, misplaced, oversized,
blank, decoy, and lexical path case is green. `literal-compatibility` is green
for a missing block, a partial target list, and every concrete-token position.
`diagnostic-leak` surfaced S1-R1-02. `promise-overclaim` is green: the Protasis
Promise names a lexical structure verdict and disclaims suitability, version
selection, and integration-base knowledge.

The other 19 concerns are not reachable in Step 1 and are not claimed as
reviewed here: `anchor-substitution`, `generation-arithmetic`, `frontier-drift`,
`ledger-history-rewrite`, `metadata-mismatch`, `multi-target-partial`,
`base-ref-race`, `run-ref-race`, `post-check-race`,
`remote-evidence-failure`, `git-object-shape`, `sync-carriage`,
`revalidation-coverage`, `resolution-staleness`, `state-history-growth`,
`self-hosted-collision`, `legacy-state`, `receipt-replay`, and
`interrupted-resolution` belong to later steps.

Leads not pursued: none.

## Step 1, round 2 -- 2026-08-25

Zero findings over signed audit-tip commit
`4278196365a8d288e1224be3e864cd505a4f7697`. Its parent is Mason commit
`77458260d3fb0386a2d60b062a91e6c2c636ece4`; both local signatures verify.
Round 1 remains the unchanged 79-line prefix of this record.

### Evidence

Independent hostile probes refused all 33 C0 controls, 32 C1 controls, 12
bidi controls, 170 Unicode format controls, 19 other sampled nonprinting code
points, and 13 unsafe path forms. Five concrete-token positives refused; five
near tokens and the legacy no-block case stayed accepted. Six controlled-value
cases produced seven value-free P006 messages, at most 80 characters. A
maximum-size 2 MiB row produced one 75-character P006 message without echoing
its contents.

The fixed tree passes 89 focused Protasis tests, 350 root tests, and the full
1,057-test Hexaemeron report with zero failures, errors, or skips. The report
is `tmp/elenchus/fiat-556-step-1.json`, SHA-256
`2a6d37d37d479e94097a3a283db04b0c59881cfce198755572b78846ee5f3405`.
The identical Round 1 green report remains preserved at
`.elenchus/fiat-556-step-1-warden-round1-green.json`; every earlier red report
also remains present.

Promise Machine reports 14 clean plugin copies and 71 of 71 covered promises.
The Protasis Promise still limits P006 to lexical structure and disclaims
relation suitability, version selection, and integration-base knowledge.
Phylax, Ephoros, and Hypomnema exit 0 over their complete repository paths and
this record. Horos reports that the boundary matches the tree.

The tracked study remains byte-identical to its receipt at SHA-256
`4f379dac26ed32af4310bcd55ebaef7ca91774da7ca53f69f2d3a6401e8942c7`;
all five relative skill links resolve. The tracked runbook remains
byte-identical to its amended receipt at SHA-256
`593ce6e4faa9598c475475e931f66c28e6d2ecaff116232299a7085e47ee89d2`.
The misplaced plugin-local study path is absent. All six product paths remain
inside the amended Step 1 Files field, and `audit/AUDIT.md` remains unchanged.

The bounded Sapheneia pass preserves the full Round 1 prefix and every Round 2
hash, count, qualification, path, and status. Imprimatur scores this record
100.0 with zero defects. Brevitas reports B011 only, from the required two-row
Round 1 findings table; this zero-finding round adds no finding row.

### Risk register

The four Step 1 concerns are green. `relation-block-shape` covers malformed,
duplicate, decoy, nonprinting, and unsafe path inputs. `literal-compatibility`
covers near tokens, partial declarations, and no-block runbooks.
`diagnostic-leak` covers the maximum-size and controlled-value probes.
`promise-overclaim` remains bounded by the Promise text. The other 19 study
concerns belong to later steps and receive no claim in this round.

Leads not pursued: none.
