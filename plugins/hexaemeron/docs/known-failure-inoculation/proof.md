# Proof: the inoculation contract, driven end to end

`proof.py` beside this file builds one disposable signed Git repository,
runs the checked-in Fiat controller through three lanes inside it, writes
these bytes, and then checks them against the run it just finished. Every
number, command, exit status, path and digest below came out of that run.
The question, case, class and result labels are `proof.py`'s own, and so is
every `verdict=` value; the refusal matrix below says what that column
rests on.

## What this run of the contract used

The delivery that built this contract ran on the pinned plugin-cache
controller, which predates the gates the contract adds. Its runbook receipt
carries no known-failure capture, so every reader in that run took the
legacy branch, and its guard and final-green evidence came from running
Elenchus and the green commands by hand. That is the manual bootstrap
procedure, and it is the only procedure that delivery used.

So the claim here is narrow and it is the only one these bytes support: the
controller checked into this tree enforces the contract on the disposable
repository `proof.py` just drove. It does not claim that the controller
which produced this run's receipts enforced anything.

## What the lanes establish

The guarded lane carries one assigned known failure. It shows the receipted
runbook opening its step in `inoculate` rather than `implement`, the
controller refusing implementation before a valid inoculation receipt, every
non-guard verdict and both runner faults refused at retention, one admitted
guard binding exact report bytes and exact Git objects, a repeated retention
resuming the published pair rather than sampling a second run, a halt and
resume preserving the assigned and completed ids, the inoculation receipt,
the fixed-tree green run with both declared suites, one audit round, and a
final verification.

The no-known lane carries no assigned finding. It shows the same step
opening in `inoculate`, the controller refusing the phase while the explicit
claim is absent, and the receipt binding that claim's study, inventory and
source-view digests once it exists. An empty array is not what closed it.

The unguarded lane declares a guard path that is not a test file, which the
inventory contract permits and the guard runner cannot classify. Its step can
never finish, so the lane stops at the refusal it exists for.

## What the refusal matrix covers

Six report shapes reach the classifier and come back as something other than
`guarded`: a passing guard, a run that executed nothing, a run carrying an
infrastructure error, and three whose single case was skipped, expected to
fail, or unexpectedly succeeded. Three shapes never reach it at all: a report
the runner declared incomplete, which the parser rejects first; no report
written; and guard blobs holding no test file, which answer `unguarded`
instead of a classification.

The controller refuses all nine. The last three share one refusal text,
because a result missing a verdict's own members is what Fiat sees in each
case, so that text cannot tell an unguarded commit from a broken runner. The
verdict column below is therefore inferred from the bound counters under
Elenchus's published classification, not read out of the refusal, and the
rows that never reached classification say so instead of naming a verdict.

## What this does not establish

These bytes say nothing about the controller in the plugin cache, about any
repository other than the one the proof created and destroyed, or about
timing. The proof measures correctness only and makes no latency or
throughput claim. The disposable guard, product, suite and audit source are
fixtures, not the real ones. A lane stops at its own verification: nothing
here pushes, opens a pull request, merges, or completes a step.

## The bound record

The block below is what the checker reads. Each line is one record: fields
are separated by ` | `, the first field names the kind, and a value written
`@name` is a token whose actual run-local value is resolved through the
`bind` records. Changing any command, exit status, count, commit token, path
or digest in it makes the check refuse.

```proof-record
source | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | 941813 | cf9c31d92aaf8b996c1f6d04114e888d1b6257ea0316ec7d2d6902698b4895a0
source | plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py | 46847 | 34e639a4f14856b16c27c382117b25191e357b249e5e3373f975c939d3c41c1b
source | plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py | 58800 | 58d21ef473e2a8c4bf7557fbd7f885faef4dfa44c55ef0a52e5e3ace2b866243
source | plugins/hexaemeron/skills/protasis/scripts/design_evidence.py | 30436 | 4f38e555d1d704aff250c9b1ffe00a956db44f9d139d8f127ae8e445deafd096
source | plugins/hexaemeron/skills/elenchus/scripts/elenchus.py | 77643 | e8c4b3bff7d87bc16e065f9c86cea405a996f2b4573c7845f7c32f905db7990e
lane | guarded | proof guarded lane | fiat/proof-guarded | fiat/proof-guarded-step-1-guard-the-answer-then-fix-it
lane | no-known | proof no known lane | fiat/proof-no-known | fiat/proof-no-known-step-1-release-with-no-assigned-finding
lane | unguarded | proof unguarded lane | fiat/proof-unguarded | fiat/proof-unguarded-step-1-declare-a-guard-that-is-not-a-te
phase | guarded | 1 | study | was the study receipted with its design lock | hexctl done study --artifact .hexaemeron/study.md | 0 | receipted | source_views=1;findings=1 | design_candidate=receipted-inoculation
phase | guarded | 2 | runbook | does the receipted runbook open the step in inoculate | hexctl done runbook --artifact .hexaemeron/runbook.md --steps-file .hexaemeron/steps.json | 0 | step 1 -> inoculate | steps=1 | -
phase | guarded | 3 | inoculate | what does the controller direct before any product edit | hexctl next | 0 | do=inoculate | assigned=1;remaining=1 | step_parent=@step-parent;agent=mason;then=hexctl done inoculate
phase | guarded | 4 | inoculate | which exact report bytes and Git objects does the guard bind | hexctl retain-guard --finding-id kf-proof-01 --guard-commit <object-id> | 0 | disposition=created | report_bytes=159;complete=true;executed=1;assertion_failures=1;errors=0;skipped=0;verdict=guarded | guard_commit=@guard-commit;step_parent=@step-parent;report_sha256=a3e8d6a24c60d1c0d9c817f8b92e1e94d64402daf2c598c17e2547e279559cbe;manifest=@guard-manifest;retained_report=.hexaemeron/steps/1/inoculation/reports/kf-proof-01.report
phase | guarded | 5 | inoculate | does a repeated retention resume the published evidence | hexctl retain-guard --finding-id kf-proof-01 --guard-commit <object-id> | 0 | disposition=already-retained | published_pairs=1 | manifest=@guard-manifest
phase | guarded | 6 | inoculate | does a halt and resume preserve the assigned and completed ids | hexctl resume --note resumed for the proof | 0 | do=inoculate | completed=1;remaining=0 | step_parent=@step-parent
phase | guarded | 7 | inoculate | what does the inoculation receipt bind before implementation | hexctl done inoculate | 0 | phase -> implement | assigned=1;guard_manifests=1 | step_parent=@step-parent;manifest=@guard-manifest;no_known_findings=null
phase | guarded | 8 | implement | is the guard green on the fixed tree and both suites clean | hexctl done implement --branch <step-branch> --commit <object-id> --tests python3 tests/suite.py | 0 | phase -> audit | verified_commits=2;green_manifests=1;suite_rows=2;green_report_bytes=159;complete=true;executed=1;assertion_failures=0;errors=0;skipped=0 | final_commit=@final-commit;suites=hexaemeron-suite+root-suite;green_report_sha256=fc26652c99ed7e19ca1ccbcc13a328867602f55e0b0b36f6d67094d9e895de99
phase | guarded | 9 | audit | does the audit round record its own log boundary and lints | hexctl audit-round --findings 0 --audit-filter sapheneia:sapheneia --phylax-exit 0 --ephoros-exit 0 --hypomnema-exit 0 | 0 | round 1 recorded | rounds=1;findings=0;phylax=0;ephoros=0;hypomnema=0 | log=audit/rounds/fiat-proof-guarded.md;audit_filter=sapheneia:sapheneia
phase | guarded | 10 | verify | does the finished lane verify its own chain and state | hexctl verify | 0 | chain intact, state consistent | ledger_entries=9 | state=@guarded-state-6;ledger=@guarded-ledger-7
phase | no-known | 11 | study | was a study with no assigned finding receipted | hexctl done study --artifact .hexaemeron/study.md | 0 | receipted | source_views=1;findings=0 | -
phase | no-known | 12 | runbook | does a zero-assignment step still open in inoculate | hexctl done runbook --artifact .hexaemeron/runbook.md --steps-file .hexaemeron/steps.json | 0 | do=inoculate | assigned=0 | -
phase | no-known | 13 | inoculate | what does the explicit no-known-findings receipt bind | hexctl done inoculate | 0 | phase -> implement | assigned=0;source_views=1;consuming_step=1 | assertion=no-known-findings-for-step;study=@no-known-study;inventory=@no-known-inventory
phase | no-known | 14 | verify | does the no-known lane verify its own chain and state | hexctl verify | 0 | chain intact, state consistent | ledger_entries=4 | state=@no-known-state-12;ledger=@no-known-ledger-13
phase | unguarded | 15 | study | was a study whose declared guard is not a test receipted | hexctl done study --artifact .hexaemeron/study.md | 0 | receipted | source_views=1;findings=1 | -
phase | unguarded | 16 | runbook | does the step still open in inoculate with that guard declared | hexctl done runbook --artifact .hexaemeron/runbook.md --steps-file .hexaemeron/steps.json | 0 | do=inoculate | assigned=1 | -
phase | unguarded | 17 | verify | does the refused lane still verify its own chain and state | hexctl verify | 0 | chain intact, state consistent | ledger_entries=3 | state=@unguarded-state-14;ledger=@unguarded-ledger-15
refuse | guarded | implement-before-inoculate | early-product | hexctl done implement | 2 | step 1 cannot implement before a valid inoculation receipt | @guarded-state-1/@guarded-state-1 | @guarded-ledger-2/@guarded-ledger-2 | -
refuse | guarded | passed | non-guard-verdict | hexctl retain-guard --finding-id kf-proof-01 --guard-commit <object-id> | 2 | guard evidence was not admitted: Elenchus did not return guarded | @guarded-state-1/@guarded-state-1 | @guarded-ledger-2/@guarded-ledger-2 | complete=true;executed=1;assertion_failures=0;errors=0;skipped=0;verdict=passed
refuse | guarded | zero-executed | non-guard-verdict | hexctl retain-guard --finding-id kf-proof-01 --guard-commit <object-id> | 2 | guard evidence was not admitted: Elenchus did not return guarded | @guarded-state-1/@guarded-state-1 | @guarded-ledger-2/@guarded-ledger-2 | complete=true;executed=0;assertion_failures=0;errors=0;skipped=0;verdict=inconclusive
refuse | guarded | infrastructure-error | non-guard-verdict | hexctl retain-guard --finding-id kf-proof-01 --guard-commit <object-id> | 2 | guard evidence was not admitted: Elenchus did not return guarded | @guarded-state-1/@guarded-state-1 | @guarded-ledger-2/@guarded-ledger-2 | complete=true;executed=1;assertion_failures=0;errors=1;skipped=0;verdict=inconclusive
refuse | guarded | skipped-case | non-guard-verdict | hexctl retain-guard --finding-id kf-proof-01 --guard-commit <object-id> | 2 | guard evidence was not admitted: Elenchus did not return guarded | @guarded-state-1/@guarded-state-1 | @guarded-ledger-2/@guarded-ledger-2 | complete=true;executed=0;assertion_failures=0;errors=0;skipped=1;verdict=inconclusive
refuse | guarded | expected-failure | non-guard-verdict | hexctl retain-guard --finding-id kf-proof-01 --guard-commit <object-id> | 2 | guard evidence was not admitted: Elenchus did not return guarded | @guarded-state-1/@guarded-state-1 | @guarded-ledger-2/@guarded-ledger-2 | complete=true;executed=0;assertion_failures=0;errors=0;skipped=1;verdict=inconclusive
refuse | guarded | unexpected-success | non-guard-verdict | hexctl retain-guard --finding-id kf-proof-01 --guard-commit <object-id> | 2 | guard evidence was not admitted: Elenchus did not return guarded | @guarded-state-1/@guarded-state-1 | @guarded-ledger-2/@guarded-ledger-2 | complete=true;executed=1;assertion_failures=0;errors=1;skipped=0;verdict=inconclusive
```

```proof-record
refuse | guarded | incomplete-report | runner-fault | hexctl retain-guard --finding-id kf-proof-01 --guard-commit <object-id> | 2 | Elenchus returned an unsupported parent-guard result | @guarded-state-1/@guarded-state-1 | @guarded-ledger-2/@guarded-ledger-2 | complete=false;executed=1;assertion_failures=1;errors=0;skipped=0;verdict=not-reached
refuse | guarded | absent-report | runner-fault | hexctl retain-guard --finding-id kf-proof-01 --guard-commit <object-id> | 2 | Elenchus returned an unsupported parent-guard result | @guarded-state-1/@guarded-state-1 | @guarded-ledger-2/@guarded-ledger-2 | complete=absent;executed=absent;verdict=not-reached
refuse | guarded | undeclared-product-path | early-product | hexctl retain-guard --finding-id kf-proof-01 --guard-commit <object-id> | 2 | undeclared guard path | @guarded-state-1/@guarded-state-1 | @guarded-ledger-2/@guarded-ledger-2 | changed_paths=2;declared_guard_paths=1
refuse | no-known | absent-no-known-claim | absent-claim | hexctl done inoculate | 2 | no-known-findings record is not one stable bounded regular file | @no-known-state-8/@no-known-state-8 | @no-known-ledger-9/@no-known-ledger-9 | claims=0
refuse | unguarded | no-test-blob | non-guard-verdict | hexctl retain-guard --finding-id kf-proof-02 --guard-commit <object-id> | 2 | Elenchus returned an unsupported parent-guard result | @unguarded-state-14/@unguarded-state-14 | @unguarded-ledger-15/@unguarded-ledger-15 | complete=not-reached;executed=not-reached;verdict=unguarded
bind | @final-commit | commit descends-from=@guard-commit
bind | @guard-commit | commit sole-parent=@step-parent
bind | @guard-manifest | manifest-digest
bind | @guarded-ledger-2 | ledger-digest
bind | @guarded-ledger-7 | ledger-digest
bind | @guarded-state-1 | state-digest
bind | @guarded-state-6 | state-digest
bind | @no-known-inventory | inventory-digest
bind | @no-known-ledger-13 | ledger-digest
bind | @no-known-ledger-9 | ledger-digest
bind | @no-known-state-12 | state-digest
bind | @no-known-state-8 | state-digest
bind | @no-known-study | study-digest
bind | @step-parent | commit
bind | @unguarded-ledger-15 | ledger-digest
bind | @unguarded-state-14 | state-digest
```
