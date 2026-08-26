# issue 429 audit-record proof

this record covers the checked-in `v5.13.1` controller and synopsis generator at
step 3 parent `4b78dfa8b35efe4da794a200096682eb7495c3b3`. the replay ran on
2026-08-24 UTC in a fresh temporary Git repository with Python 3.12.13. the
driver read and copied the receipted study and runbook bytes as fixed inputs.
it never called the live v5.12.1 controller, used a network or credential, or
printed signature material. the disposable controller never opened or mutated
live `.hexaemeron` state.

generated worktree paths, controller clocks, state hashes, ledger hashes, and
signed commit ids make the replay hashes run-local. source-file, audit-entry,
prefix, and synopsis hashes below are hashes of stated bytes and do not depend
on those generated values.

## fixed inputs and commands

| input | SHA-256 | use |
| --- | --- | --- |
| `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `7d2eb3ada9cd349bc478266a2921cd08eb533fc13a5e947741be936181530dd0` | the only controller process |
| `plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py` | `fba96f11812c33e18a406d3724ae4aa18c4b0527577c6021c4e5dc31729cc1dc` | every disposable and release render |
| `study.md` | `65b804081a676a42f0ee52af72bf149776d0e54bebc8f258792ba67ba2c25fd3` | the exact 13-id risk register |
| accepted replay runbook, `.hexaemeron/runbook.md` | `457cdd395b37dcfe89e1b36ae89ff04b584cd81a56b6d7c21407a94f85acc2e5` | the exact three-step plan used by the replay |
| release runbook, `plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/runbook.md` | `07003da0855c317d78d00f3287d6fa38eefa1b49dfe6f3037dcda60fc2236998` | the same plan with its Elenchus runner pinned to Node 26.6.0 and `{report}` exposed as one argument |

the driver used `subprocess.run` with argument lists and `pathlib` writes. its
controller command sequence was:

```text
hexctl --dir $DEMO_ORIGIN init --topic "issue 429 proof" --base main
hexctl --dir $DEMO_RUN done study --artifact $DEMO_STUDY --skills hexaemeron:protasis,hexaemeron:imprimatur
hexctl --dir $DEMO_RUN done runbook --artifact $DEMO_RUNBOOK --steps-file $DEMO_STEPS
hexctl --dir $DEMO_RUN next
hexctl --dir $DEMO_RUN done implement --branch $STEP_BRANCH --commit $IMPLEMENTATION --tests "disposable v5.13.1 proof fixture"
hexctl --dir $DEMO_RUN record security_suite '"waived: issue 429 disposable proof has no Solidity target"'
hexctl --dir $DEMO_RUN status
hexctl --dir $DEMO_RUN next
hexctl --dir $DEMO_RUN verify
hexctl --dir $DEMO_RUN audit-round --findings N --log audit/AUDIT.md --phylax-exit 0 --ephoros-exit 0 --hypomnema-exit 0
audit_synopsis.py --write $DEMO_RUN
audit_synopsis.py --check $DEMO_RUN
hexctl --dir $DEMO_RUN audit-round --findings N --log audit/AUDIT.md --fixes-commit SHA --elenchus-verdict VALUE --phylax-exit 0 --ephoros-exit 0 --hypomnema-exit 0
hexctl --dir $DEMO_RUN done audit --log audit/AUDIT.md
hexctl --dir $DEMO_RUN verify
hexctl --dir $DEMO_RUN status
hexctl --dir $DEMO_RUN next
```

the implementation commit was
`210e03713736f24c9fdfee4cf58a7266c64999d4`. its tree contained a
1,168-byte legacy `audit/AUDIT.md` and its freshly rendered sibling. the
controller verified its local signature and the two exact trailers before
entering audit.

## legacy fixture and refusal boundary

the committed legacy source has 52 physical lines, SHA-256
`68e26c9d5844faf8044be6fd452bd449ba2a05433610e995e83d9532128395c3`.
its two-line synopsis has SHA-256
`db78c654530d3a789c14c0a6fd27fa5b182dec95a246bc855a7b7c81d72939e9`.
the writer and checker both exited 0 and reported the strict line budget as
`2 * 100 < 52 * 15`.

one v5.12.1-shaped round was then appended to disposable state and ledger as a
legacy fixture. it retained `round`, `findings`, `log`, `fixes_commit`,
`elenchus_verdict: null`, `verified_commits`, three zero lint exits, and `ts`.
it omitted all five issue-429 receipt leaves: `schema`, `record_timestamp`,
`entry_sha256`, `log_end_offset`, and `synopsis_sha256`. the ledger tail was
recomputed over that exact state; no live state was edited.

`status`, `next`, and `verify` each exited 0 without changing either file.
`next` returned audit round 2. before and after those readers, `state.json`
had SHA-256
`48a5133f6e938310bc98bb23ca41bdbb46069850d75c4ddb07b87e399405f284`
and `ledger.jsonl` had SHA-256
`8857d84101e624f8681b359a24007524440b1827ed3cf64a0261a6823d1e534a`.

each refusal started from those same bytes, wrote one candidate source, ran
the exact no-fix `audit-round` command above, and restored the committed
legacy source and synopsis before the next case. all 30 commands exited 2;
every before and after state and ledger hash was the full value stated above.

| class | exact candidates | observed refusal |
| --- | --- | --- |
| required blocks | omit `Audit schema`, `Covered`, `Not checked`, `Elenchus verdict`, the findings table, or `Leads not pursued` | field-specific schema refusal; no mutation |
| separators | remove each of the seven required empty or terminal LF lines in turn | named blank, row-boundary, or EOF refusal; no mutation |
| identity and time | schema `v2`, another topic, date-only timestamp, or `2026-02-30T00:00:02Z` | schema, heading, timestamp-shape, or calendar refusal; no mutation |
| coverage and negative space | one missing, duplicate, unknown, or `accepted` risk disposition; empty `Not checked`; empty leads | coverage or non-empty-field refusal; no mutation |
| count and verdict | one clean row beside `--findings 1`, one finding row beside `--findings 0`, or `guarded` beside the no-fix command | row-count, clean-row, or verdict refusal; no mutation |
| synopsis and path | absent synopsis, stale synopsis, `--log other/AUDIT.md`, or a symlinked configured source | missing, stale, configured-path, or symlink refusal; no mutation |

the stale-synopsis diagnostic bound the valid candidate without quoting it:
68 source lines, 3 synopsis lines, source SHA-256
`280e77af9d54058fabb1c2b58cacda0317c44b0139468305e41de44df9958815`,
fresh SHA-256
`c74a06bd2d1dffb546de2fcce9338d1683981ef4d32f9228dc73943c0bdf5476`,
and committed SHA-256
`db78c654530d3a789c14c0a6fd27fa5b182dec95a246bc855a7b7c81d72939e9`.

## accepted rounds and close

four single-commit fixes followed the legacy baseline. `git verify-commit`
exited 0 for the implementation and all four fixes. every message ended with
one exact `Co-authored-by: Shoggoth <shoggoth@wildcat.finance>` line followed
by one exact `Wildcat-Origin: shoggoth` line. no raw verifier output entered
this record.

| round | findings / verdict | signed commit / parent | entry SHA-256 | log end / source lines | synopsis SHA-256 / lines |
| ---: | --- | --- | --- | --- | --- |
| 1 | 1 / explicit `null` | legacy fixture / implementation baseline | missing by design | 1,168 bytes / 52 | `db78c654530d3a789c14c0a6fd27fa5b182dec95a246bc855a7b7c81d72939e9` / 2 |
| 2 | 1 / `guarded` | `f34d47dcf860e63339c9ef33b1cfeea11bc595b1` / `210e03713736f24c9fdfee4cf58a7266c64999d4` | `39d718df22e8b2296f979d44f485ee926fd300d868aae66e69d3e70f6187309f` | 1,828 / 68 | `a49a1aab8956f6b96b17396d5c35ecf28f1f04c41def4fe6fadbf7621a3c69b6` / 3 |
| 3 | 1 / `unguarded` | `81058c90d3902c6800a66330e795d0c07dcb7bac` / `f34d47dcf860e63339c9ef33b1cfeea11bc595b1` | `c3bec01d6d5e5b103a2360402f31e322d805086432bb74bd622199fee1e7aa40` | 2,490 / 84 | `25123a233c696b8677ae45d2266eda2e1527b7c0c582d3df2bd53a7be6deba2c` / 4 |
| 4 | 1 / `passed` | `035416cd9a81cda34fd56d53b13cb97cf6f31a6b` / `81058c90d3902c6800a66330e795d0c07dcb7bac` | `5bac5d1377222ee4d15ce956ee752ca3e3953bd766fb076411e6253fd2c44a62` | 3,149 / 100 | `20eb7479b0821857a1c31dd80867976fc9392c8251f47bb1e4e80108a0196804` / 5 |
| 5 | 0 / `inconclusive` | `a9ab5e2d0a8c0aeb430f8dc9fb83300261ea5445` / `035416cd9a81cda34fd56d53b13cb97cf6f31a6b` | `ce797c3661d71c3db711e672ac55a7bf66a7d9775fd28a079cd5b36d16887b04` | 3,788 / 116 | `857524b1148baa81d02d7654c3e033b8a3c3964546a95492da9edbb1d2248970` / 6 |

every writer, checker, and accepted controller call exited 0. every round's
stored `verified_commits` list contained only its named fix. the strict budget
passed at 3/68, 4/84, 5/100, and 6/116 lines. the final source SHA-256 was
`510a270f0c1bec60783bfca5c7643aa85c6aa35daf070b93d6252f43fda8367d`.
its first 1,168 bytes still hashed to
`68e26c9d5844faf8044be6fd452bd449ba2a05433610e995e83d9532128395c3`.

`next` returned `close-audit`; `done audit --log audit/AUDIT.md`, `verify`,
`status`, and the following `next` each exited 0. the state remained version 1,
the step moved to `prose`, and the final packet named that phase. final
state SHA-256 was
`1eaefdb29dad0d3149670cbf1307f1b9c8947b5253f279d314b8ca86e39bd8a5`;
final ledger SHA-256 was
`de69dd1486c4cdcf0ea66da965488895514ef75f3576865694449238599ca216`.

## release snapshot at the step 3 parent

the six-prefix fixture has SHA-256
`b0326cdd5c3c807a6e5bb5791773f523d8e7c7a440f5b16ab65bc9dda01aa5c9`.
each live source still begins with these exact bytes from
`ced4e6f439021b7509833ed5da66348c86d22f01`:

| source | prefix bytes / lines | prefix SHA-256 |
| --- | --- | --- |
| `audit/AUDIT.md` | 580,893 / 9,392 | `96583f59dea6da5363bf83feadc6686d8c4897adc282f4d33de7b4aa0a5d52e9` |
| `plugins/ariadne/audit/AUDIT.md` | 32,253 / 466 | `d8d13eb238b6e270fb9f89ec11fea797b4a3aa27025b5a62a7f36ac2642617af` |
| `plugins/hexaemeron/audit/AUDIT.md` | 5,621 / 71 | `8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f` |
| `plugins/pandects/audit/AUDIT.md` | 45,906 / 696 | `66908cb68630f3c3cbea432aec6cf6efc305bcab85ccf5fadb278c535635edf9` |
| `plugins/probitas/audit/AUDIT.md` | 52,540 / 842 | `ba532815ae3abe13be3494b96044bf5d874cfb23842249d8e1cd867186e486c9` |
| `plugins/tabularium/audit/AUDIT.md` | 14,400 / 262 | `1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7` |

the round 1 correction extends that metadata with a self-contained Git
membership witness. its 14 exact commit and tree objects occupy 5,070 decoded
bytes and bind all six paths to the named commit without carrying the audit
blobs. the extended fixture has SHA-256
`bff474effb5917fce29da78b908a1986ba0c3e8e8c3e76b878d76a3e7aada7b0`.

the checked-in generator then rendered all six in memory. each committed view
matched its fresh bytes and stayed below the integer budget:

| source | source lines | synopsis lines | source SHA-256 | synopsis SHA-256 |
| --- | ---: | ---: | --- | --- |
| `audit/AUDIT.md` | 9,932 | 371 | `eb29dd4dcec8550908feff5213de81f61660b972ef01fa0bd5d341102811f817` | `e4bfdf451203f1946710b65494a89d03f68316f24bac5de4d4dcec800cac13b1` |
| `plugins/ariadne/audit/AUDIT.md` | 466 | 22 | `d8d13eb238b6e270fb9f89ec11fea797b4a3aa27025b5a62a7f36ac2642617af` | `53aacbb59bc9bc1455ce580ce484cbcb16802f7faa41b2b12f65c3ce614d1b4a` |
| `plugins/hexaemeron/audit/AUDIT.md` | 71 | 3 | `8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f` | `2e919d920cd952a837bee6069251b710a9543df37514d7248a996d61766138cd` |
| `plugins/pandects/audit/AUDIT.md` | 696 | 18 | `66908cb68630f3c3cbea432aec6cf6efc305bcab85ccf5fadb278c535635edf9` | `ecde800e07ed8b1bc94b5a55714e3b01fbe0dfb1283bdafc88be170357dd32f1` |
| `plugins/probitas/audit/AUDIT.md` | 842 | 25 | `ba532815ae3abe13be3494b96044bf5d874cfb23842249d8e1cd867186e486c9` | `5eab3774f4d66147e8a4fc18a1014b181f7b1f2309003a93a1dfffb0ff4891a1` |
| `plugins/tabularium/audit/AUDIT.md` | 262 | 14 | `1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7` | `2432d6fd11be15a838d62ab067a190314a1a63011a67e106682f700cc3447e6c` |

the live currency test also compared every H2 heading, every physical leads
occurrence with duplicates, and each present issue-327 verdict field after
decoding. the exact command
`python3.12 plugins/horos/skills/horos/scripts/horos.py scan . --json | shasum -a 256`
exited 0 and returned SHA-256
`3d8555abebc5ced63a6ff034813456295f35f7735602a66ad7ec3c98c5656b99`.
the scan had 99 hard entries and no synopsis path among them.
the committed boundary check exited 0; its four synopsis notices were advisory
candidate drift, not hard entries.

## cold release read

the release surfaces agree on Fiat `5.13.1`, Fiat ledger
`fiat-v5.13.1`, and Hexaemeron package `1.5.6`. both plugin manifests and both
marketplaces carry `1.5.6`. all three Fiat Promise runtime bindings name
controller SHA-256
`7d2eb3ada9cd349bc478266a2921cd08eb533fc13a5e947741be936181530dd0`.
the frontier remains `state-shape-validation` at
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`,
with issue 363's held job unchanged.

the Warden contract, audit loop, Fiat contract, README, generation row,
controller, generator, version tests, and Promise binding agree on the checked
source, derived sibling, five new leaves, and legacy omission. the 15 root-log
appends after the generator's introduction each changed
`audit/AUDIT_SYNOPSIS.md` in the same commit. the Protasis and Elenchus skill
trees are byte-identical to the step entry, so this release does not implement
issues 369 or 453; the Fiat frontier text does not implement issue 363. issue
state itself was not refreshed because this replay was required to stay
offline.

the cold read found that commit
`60697037cfa9c3929797301616c86f8c7f6fbe80` added `fetch-depth: 0` to the
Janus, Lazarus, and Pandects workflows so their root-test jobs can resolve the
pinned prefix commit. that conflicts with study assumption A10 and the study's
stated ask-first CI boundary; no later study amendment records the change.
round 1 removes those checkout options. the prefix test now recomputes the
object ids in the checked-in witness, walks each committed tree path, and
matches the protected bytes to the resulting blob id. this keeps the permanent
guard authoritative under a default shallow checkout without expanding CI
scope.

the required Brevitas report pass found a second pre-existing discrepancy.
the runbook, proof, Fiat contract and ledger, README, Warden contract, and
audit-loop reference each exited 0. the accepted study exited 1 with `B011`
at lines 303, 347, and 431 because each named table has two real-data columns.
the fenced release suite does not make that report a zero-exit gate. rewriting
the accepted study here would repin its bytes after implementation, so step 3
records the result and does not call the study Brevitas-clean.

the Elenchus report runner exposed a stale runbook command. its direct
`python3.12` form inherited host Node v22.22.3 and exited 1 after 925 of 926
tests passed; `test_fixture_exercised_the_declared_node_version` required
v26.6.0. the first pinned replacement hid `{report}` inside the `--call`
string, so Elenchus refused it as `inconclusive` when a later fix carried a
test. round 1 replaces all four occurrences with the direct `npx` executable
form, where `{report}` is one exact argument and the child still sees Node
v26.6.0. the accepted `.hexaemeron/runbook.md` remains at its receipted digest
above; no controller state was rewritten.

## release gates

each command below ran from the step-3 worktree against these proof bytes. the
Node package runner was forced to its local offline cache. a zero exit
establishes only the named check.

| command | observed result | exit |
| --- | --- | ---: |
| `python3.12 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` | six committed views matched fresh bytes and passed budget | 0 |
| `python3.12 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill tests.test_audit_prefix_integrity tests.test_audit_synopsis_currency -q` | 403 tests passed in 223.733s | 0 |
| `python3.12 -m unittest discover -s tests` | 160 tests passed in 8.782s | 0 |
| `npm_config_offline=true npx --yes --package=node@26.6.0 --call 'python3.12 plugins/hexaemeron/tests/run_tests.py'` | 926 tests passed in 233.979s | 0 |
| `python3.12 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py` | 62 of 62 passed | 0 |
| `python3.12 scripts/promise_machine.py check` | 14 plugins and 14 copies clean | 0 |
| `python3.12 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/study.md` | clean | 0 |
| `python3.12 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/runbook.md` | clean | 0 |
| `python3.12 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests` | clean | 0 |
| `python3.12 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests` | clean | 0 |
| `python3.12 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs` | clean | 0 |
| `python3.12 plugins/horos/skills/horos/scripts/horos.py check .` | boundary matched; four synopsis notices remained advisory candidate drift | 0 |
| `python3.12 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/proof.md` | score 100.0, no defects | 0 |
| `python3.12 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/docs/audit-record-schema-timestamp-synopsis/proof.md --mode report` | no diagnostics | 0 |
| `python3.12 plugins/hexaemeron/tests/run_tests.py --elenchus-report .elenchus/hexaemeron-unittest.json` | host Node v22.22.3 contradicted the declared v26.6.0; 925 of 926 passed | 1 |
| `npm_config_offline=true npx --yes --package=node@26.6.0 --call 'python3.12 plugins/hexaemeron/tests/run_tests.py --elenchus-report .elenchus/hexaemeron-unittest.json'` | 926 tests passed in 229.638s; report schema `elenchus.unittest.v1`, 926 run, zero failures, errors, skips, or unexpected outcomes | 0 |
| `python3.12 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref HEAD --test-command "npx --yes --package=node@26.6.0 --call 'python3.12 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}'" --report-format unittest-json-v1 --report-file .elenchus/hexaemeron-unittest.json --format json` | historical invocation returned `unguarded` before validating the command because the proof commit changed no test files | 0 |
| `python3.12 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref e9ca4ecb74f8b5de2a312c9296723c3c4eed5b00 --test-command "npx --yes --package=node@26.6.0 -- python3.12 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}" --report-format unittest-json-v1 --report-file .elenchus/hexaemeron-unittest.json --format json` | `guarded`: 928 tests executed; one parent assertion failure, zero errors, and zero skips | 0 |
| `git diff --check` | clean | 0 |

the successful `unittest-json-v1` report was 161 bytes on one line with
SHA-256
`931c77441655305c6bb8fa0ddf26f3e4657ffecbfe11c94962da7314d8291ef7`.
