# Issue 923 step-branch extension proof

This record covers Step 2 of
[issue 923](https://github.com/wildcat-finance/skills/issues/923). It tests the
four observable relations between a waiting step's push receipt and its live
branch tip. It also records the three issue-904 branch extensions that exposed
the old equality rule.

## Evidence boundary

The ancestry checks establish local Git topology only. They do not establish
signatures, provenance trailers, GitHub verification, author or committer
identity, the publisher, or why a branch moved. A descendant becomes eligible
to continue, then `done merge-step` rechecks the complete live range and stores
that evidence in `effective_push`. The original push receipt remains unchanged.

The focused fixture uses a real local `P -> E` graph and an unrelated commit.
Its subprocess call uses fixed arguments, disables replacement objects, scrubs
inherited `GIT_*` state, disables lazy fetch and prompts, and keeps startup,
time, and output failures inside the unknown result. No performance claim is
made. Equality makes no relation call; each unequal waiting tip gets at most
one bounded native relation call.

## Parent and implementation results

The new focused file was overlaid onto Step 2's entry commit and run through
the source-bound unittest reporter. The raw parent run produced 10 failed test
outcomes comprising 11 assertion-failure records, with 0 infrastructure errors
and no skips. This is the preserved red result: the entry controller still
rejected every unequal tip.

At the implementation head, the same focused file passed all 10 tests:

```text
python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_step_branch_extensions.py' -v
Ran 10 tests
OK
```

The adjacent receipt and legacy guards also remained green:

```text
python3 plugins/hexaemeron/tests/test_push_receipt_identity.py -v
Ran 6 tests
OK

python3 -m unittest plugins.hexaemeron.tests.test_hexctl.RewrittenStackRefusal -v
Ran 6 tests
OK
```

The focused issue-429 integrity guard first failed with one assertion and no
errors because the changed controller digest was
`a9a28e3e22cb99ddb0f25a90aff0b8b3286d7734f590a281c498ee8b2e2bf4a1`
while its unscoped literal still held
`310dac029bca484532900068257fd8c6e9836e31e5f87b55aab9c8d4c0261115`.
The final runbook amendment permits only that literal to move. Its passing
result is checked alongside the generated Promise Machine bindings.

## Observable outcomes

| Recorded head and observed tip | Result | Evidence retained |
| --- | --- | --- |
| Equal | Admit without a relation call | Existing push receipt; later merge gate unchanged |
| Strict descendant | Admit topology only | Complete live range rechecked later under `effective_push` |
| Non-ancestor | Refuse before state or ledger mutation | Branch and both exact commits; no cause claim |
| Unknown relation | Refuse before state or ledger mutation | Branch and both exact commits; unavailable answer named |

The descendant end-to-end fixture also checks that the merge receipt records
the new live head, local and GitHub verification, and both author and committer
attribution while byte-preserving the original push receipt.

## Issue 904 ancestry checks

All three checks used `git --no-replace-objects merge-base --is-ancestor` in
the repository holding the incident commits. Each returned status 0.

| Step | Receipted head | Observed tip | Result |
| --- | --- | --- | --- |
| 1 | `bf54296d96a7cc937757e2afaf467aeef8ff1f2b` | `a8af2b0fa87e3e964157f7d3c9f3d39439d3bc31` | ancestor; one later boundary-rescan commit |
| 2 | `f01f476e15e0b9a33332d644c35413d47a9fbe8b` | `e13aaaa65e5cdd7dca052cfd7edd9cbc6f43a9d6` | ancestor; the repair plus one forward merge |
| 3 | `c1171d9a5305b3e363a6a725139ceb54bff64422` | `133b39e467d087f22c6eee2c78fd20816a75cce1` | ancestor; both lower repairs plus one forward merge |

These results show that equality alone misclassified honest forward history.
They do not settle issue #904's separate router work or establish that every
future extension is valid. The controller admits only native ancestry here and
defers all current-range delivery evidence to the existing merge receipt.
