# Bound integration revalidation separately from commit ranges and prose diffs

Issue: [skills#774](https://github.com/wildcat-finance/skills/issues/774).
Run branch: `fiat/774-bound-integration-revalidation-separately-fr`.
Starting ref: `main` at `00786ccd`, the merge of
[#776](https://github.com/wildcat-finance/skills/pull/776).

## Assumptions

Proceeding on these unless corrected:

1. CPython 3.14.6, the interpreter named in `.python-version`, with stdlib
   `unittest`. No third-party runtime dependency is added.
2. The change is confined to the Fiat controller and its tests. No other
   skill's behaviour moves.
3. `fiat-integration-revalidation/v2` keeps its aggregate contract exactly as
   [#710](https://github.com/wildcat-finance/skills/issues/710) shipped it.
   This run changes a count limit, not a schema.
4. The run ships no Solidity, so the bundled Pashov suite is waived rather
   than run. That waiver is already receipted.
5. The generation label and the ADR number are resolved at integrate against
   whatever `main` then holds, not pinned here.

## 1. Problem statement

One constant, `GIT_PATHS_MAX = 500`, serves five unrelated bounds in
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`. Two of them bound
integration revalidation. Three do not. Because integration surfaces grow with
the base and the other three do not, the shared constant now refuses runs that
have nothing wrong with them.

The concrete stop is [#556](https://github.com/wildcat-finance/skills/issues/556).
Its stack merged, its ledger is intact, and its integration pull request
[#773](https://github.com/wildcat-finance/skills/pull/773) cannot receipt
`done sync-run`: the composition delta against `main` is 1,660 unique paths, of
which the single registered generator aggregate absorbs 958, leaving 702 that
require exact individual coverage against a limit of 500.

The surface only grows. `done sync-run` pins the sync commit's first parent to
the final recorded step merge, so `product_head` never advances past it and the
composition always spans the base's entire advance since that merge. Waiting
does not shrink it and rebuilding against a newer base enlarges it.

A working prototype here means: the same evidence #556 already prepared is
accepted, and every bound this change does not concern still refuses at 500.

**Demo path.** `python3 -m unittest discover -s plugins/hexaemeron/tests -p
'test_hexctl_integration_path_bounds.py' -t plugins/hexaemeron/tests` passes,
and `python3 plugins/hexaemeron/tests/run_tests.py` shows no new failure
against the baseline recorded in section 3.

## 2. Prior art

**This exact change has already shipped once, green.**
[#679](https://github.com/wildcat-finance/skills/pull/679), merge `cb502e55`,
added `INTEGRATION_PATHS_MAX = 4096` and applied it at exactly the two
integration sites, left `GIT_PATHS_MAX = 500` and the non-integration sites
alone, kept the 2 MiB byte ceilings, added
`plugins/hexaemeron/tests/test_hexctl_integration_path_bounds.py` with a
907-path fixture, and still refused 4,097. It recorded `fiat-v5.31.1`.

**It was reverted for an unrelated reason.**
[#680](https://github.com/wildcat-finance/skills/pull/680), merge `a6ac1bcf`,
reverted #679 wholesale to its first parent because the Imprimatur continuation
it was unblocking had been cancelled. The revert records no defect in the change
and states no objection to its shape. The freed `fiat-v5.31.1` label was later
taken by #710.

**#710 declined the bound on scope, not on merit.** The generator-aggregate
transition said it did not authorise raising `GIT_PATHS_MAX`, calling that a
maintainer decision. Reading #680 and #710 without #679 leads to the wrong
conclusion, that this change was considered and rejected. It was neither.

**What #710 did deliver, and why it is not enough.**
`fiat-integration-revalidation/v2` classifies a generator-owned tree by prefix,
file count and tree digest, and is already absorbing 958 of #556's 1,660 paths
inside its 1,024-file and 32 MiB ceilings. It cannot absorb hand-authored
breadth: #556's residual 702 paths are source across twelve plugins plus docs,
audit records and tests, and no generator owns them. The generated-payload case
and the wide-hand-authored-base case are different failures that meet at the
same constant.

**Audit records read.** The whole-set currency check
(`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`)
exits zero, so synopses are the current reading view; the #710 round source was
read directly because it is the immediate predecessor in this area.
`audit/rounds/fiat-710-give-sync-run-one-checked-transition-across.md` records
six rounds over three steps, every one closed. Findings S1-R1-01, S2-R1-01 and
S3-R1-01 are closed by named signed commits. Its risk id
`general-cap-regression` was reviewed, which is why v2 left the individual bound
alone rather than widening it. No lead in that record is left open against this
area. `plugins/hexaemeron/audit/AUDIT.md` and the root `audit/AUDIT.md` carry
nothing against these five call sites.

**Carried forward from the last runs to change this file.** #710's integration
body records no unfinished work bearing on the bound. #608's records none
either. #556's own unfinished work is the thing this run unblocks and is stated
in section 3 as a non-goal.

## 3. Constraints and non-goals

**Starting ref.** `main` at `00786ccd`, the merge of #776. The run branch was
cut from that commit and carries no commits of its own yet. `main` has since
advanced two commits to `8c4073ed`, the merge of
[#778](https://github.com/wildcat-finance/skills/pull/778), an eight-path
delta of which the registered runtime aggregate owns two. The run therefore
already owes an integration sync, and that surface grows for as long as the run
stays open. Section 5 carries it as an enumerable concern rather than an
assumption that the base will stay still.

**Identifiers, resolved at integrate.** `main` holds `fiat-v5.35.1` with 40
history rows, hexaemeron package `1.6.10`, and `ADR-048` as its highest
decision record. This run therefore expects `fiat-v5.36.1`, package `1.6.11`
and `ADR-049`. No branch anywhere claims any of the three today. They are
stated as the next free value above the integration base rather than pinned,
because a literal picked now goes stale if another run lands first, and the
mechanism that would let a runbook declare the relation formally is #556, which
this run cannot use.

**Baseline, measured on `00786ccd` under CPython 3.14.6 on macOS.** Four
pre-existing failures. Two are environmental and two are real; none is caused
by this run and none is in scope to fix except where section 4 says otherwise.

| Failure | Cause | Disposition |
| --- | --- | --- |
| 92 failures across `test_hexctl_checkpoint` and `test_phylax_model_proxy` | the default macOS `TMPDIR` sits under `/var/folders`, a symlink, and the receipt path refuses it with `MP407 receipt.path` | environmental; a `TMPDIR` on a real path reduces the suite to three failures |
| `test_hexctl_generator_aggregates.IncidentAggregateTests` `setUpClass` | its fixture names sync commit `f0a84ca3`, which is not reachable in a fresh clone | environmental; `git fetch origin f0a84ca3` restores it and the module then passes 15 of 15 |
| `test_hexctl_checkpoint.test_resource_limits_refuse_before_publish` | constructs a 1,206-character path; the macOS limit is 1,024 | cannot pass on macOS at any `TMPDIR` |
| `test_hexctl_checkpoint.test_duplicate_state_and_ledger_keys_refuse` | expects `SystemExit` from 50,000-deep JSON nesting; CPython 3.14 parses it without recursion failure | real, on the pinned interpreter; out of scope, recorded here and carried forward |
| `tests/test_child_or_golden_retriever_primer` | `docs/a-child-or-a-golden-retriever-study.md` names `1.6.9` while the plugin is `1.6.10` | real; in scope, because step 2 moves that version and the document has to name the new one |

The last one deserves its own sentence, because it explains why the repository
believes it is green. `.github/workflows/repo.yml` runs the root suite on
ubuntu without Pillow, pypdf or ReportLab. `find_builder_python()` then returns
`None`, `setUpClass` returns early, and the version check never executes. CI
passed on `d8f99526` and on `00786ccd` with that check skipped. A version
propagation gap of this shape is structurally invisible to the gate that exists
to catch it.

**Non-goals.**

- Raising `GIT_PATHS_MAX` itself. That would loosen the commit-range and
  prose-diff bounds as a side effect, and this change has no argument about
  either.
- Changing `fiat-integration-revalidation/v2`'s aggregate rules, ceilings or
  registry.
- Making the outside-path count aggregate-aware.
- Editing #556's controller state, resuming it, or merging #773. This run
  delivers the transition; #556 is restarted separately afterwards.
- Repairing the CPython 3.14 nesting-refusal failure or the macOS path-length
  failure.
- Widening any byte ceiling. `SOURCE_BYTES_MAX` stays at 2 MiB and remains the
  real protection: #556's prepared artefact is 82,849 bytes for 688 paths, so
  4,096 paths stay an order of magnitude inside it.

## 4. Design options

**Option A: raise `GIT_PATHS_MAX` to 4,096.** One-line change, one constant to
keep straight. Rejected: it loosens a commit-range bound measured in commits and
a general prose-diff reader, neither of which this change has evidence about,
and neither of which grows with the base.

**Option B: a bound specific to integration revalidation, at 4,096, applied
only at the two integration sites.** This is #679's shape. Trade accepted: two
constants instead of one, in exchange for not widening bounds the change cannot
justify. Chosen. It is the construction cheapest to comprehend that still meets
the problem statement, and it has already been proven green once on this
codebase.

**Option C: make the outside-path count aggregate-aware, so paths absorbed by a
registered aggregate stop counting against the individual limit.** Rejected for
this run. It is a larger change to v2's contract, and it does not help the case
that motivates the work: #556's residual 702 paths are hand-authored, so no
aggregate forms over them however the counting is arranged.

**A correction to the issue's own analysis.** The issue names four call sites.
There are five. `_checkpoint_ref_names` at `hexctl.py:7902` also reads
`GIT_PATHS_MAX`, bounding the checkpoint export's Git *ref* set rather than a
path set. It is not an integration surface and must keep the 500 limit. The
chosen option leaves it alone, and the regression suite pins it so a later
reader cannot mistake it for a sixth integration site.

The scoping is clean because the two sites that change are reached only from
integration revalidation. `git_diff_paths` is called only from
`integration_revalidation_record`. `_manifest_paths` is called only from
`integration_revalidation_record`, `_integration_checks_v2` and
`_integration_revalidation_record_v2`. Nothing else in the controller reaches
either. `git_diff_paths_for_aggregates`, v2's own reader, carries no count bound
by design, so `_manifest_paths` is the binding constraint for the v2 route and
the one that matters for #556.

## 5. Risk register seed

```risk-register
shared-constant-widening | the four non-integration GIT_PATHS_MAX call sites | commit-range, prose-diff and checkpoint-ref bounds still refuse at 500 after the change
integration-site-scope | git_diff_paths and _manifest_paths callers | no caller outside integration revalidation reaches a widened bound
byte-ceiling-bypass | SOURCE_BYTES_MAX against a larger path count | an artefact over 2 MiB still refuses regardless of how few paths it names
upper-bound-absent | the new INTEGRATION_PATHS_MAX ceiling | 4,097 integration paths still refuse, before any state mutation
v2-aggregate-regression | the fiat-integration-revalidation/v2 route | aggregate prefix, count and tree-digest rules are unchanged and existing v2 fixtures still receipt
v1-compatibility | the fiat-integration-revalidation/v1 route | existing valid sync fixtures under 500 paths receipt exactly as before
refusal-order | done sync-run refusal paths | a refused artefact leaves state.json and ledger.jsonl byte-identical
version-propagation | the generation surface in step 2 | every file naming the plugin or skill version agrees, including the primer study CI cannot check
generated-copy-drift | .agents/skills/promise-machine/runtime/ | the portable copy of hexctl.py matches its canonical source byte for byte
boundary-currency | .horos/boundary.json | regenerated last, after every other file is final
base-advance-sync | diff(00786ccd, main at integrate) | the integration sync surface is measured at integrate and its outside-path count is stated, not assumed to be small
```

## 6. Glossary seeds

Integration revalidation: the bounded record `done sync-run` writes, proving
which paths a base-sync merge touched and which checks covered them.

Composition delta: `diff(product_head, sync_head)`, the paths a sync merge
changes relative to the run's final step merge.

Outside path: a path in the required set that no registered generator aggregate
owns, and which therefore needs exact individual coverage.

Registered aggregate: a generator-owned tree that v2 may cover by prefix, file
count and tree digest instead of listing every file.

Product head: the final recorded step merge, pinned as the sync commit's first
parent and never advanced by a completed sync.

## 7. Sources

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at `00786ccd`, lines 217,
  3958-3994, 4039-4062, 7114-7130, 7750-7762, 7876-7904.
- `plugins/hexaemeron/tests/test_hexctl_integration_path_bounds.py` as it stood
  at `cb502e55`, recoverable with `git show`.
- `audit/rounds/fiat-710-give-sync-run-one-checked-transition-across.md`.
- `docs/decisions/ADR-044-bind-sync-run-generator-aggregates.md`.
- `plugins/hexaemeron/skills/VERSIONING.md`.
- Issues [#556](https://github.com/wildcat-finance/skills/issues/556),
  [#679](https://github.com/wildcat-finance/skills/pull/679),
  [#680](https://github.com/wildcat-finance/skills/pull/680),
  [#710](https://github.com/wildcat-finance/skills/issues/710),
  [#774](https://github.com/wildcat-finance/skills/issues/774).

## 8. Signals, and the questions behind them

Two questions someone asks when a sync refuses at three in the morning, both
answered by diagnostic text rather than by telemetry, because this controller
is invoked from a terminal and emits no stream.

1. *Which limit refused me, and is it the one I think?* The two integration
   sites must name a different number from the three that keep 500, so the
   message alone distinguishes them. Step 1 owns this.
2. *Did the refusal change anything?* `done sync-run` refuses before mutation,
   and the existing suite already pins state and ledger byte-identity across a
   refusal. Step 1 keeps that property rather than adding to it.

No metric, trace or alert is added. A controller run by a person at a prompt
has no on-call question that a bounded exit code and a named diagnostic do not
already answer.

## 9. Boundaries, per capability

The change opens no new boundary. It moves a number at two existing ones.

- **The Git subprocess boundary** at `git_diff_paths`. Already controlled:
  argv is fixed, no shell, `GIT_OUTPUT_MAX` caps the output at 2 MiB and
  `GIT_TIMEOUT` caps the wall clock at 30 seconds. A larger path count reaches
  the same reader through the same cap.
- **The untrusted-artefact boundary** at `_manifest_paths`, which parses an
  operator-supplied JSON file. Already controlled: `SOURCE_BYTES_MAX` caps it
  at 2 MiB before parsing, every path is checked for absoluteness, traversal,
  control characters and a 4,096-byte encoded length, and the `allowed` set
  confines it to the computed delta. Raising the count limit widens none of
  those.

The control that closes the widened count is the byte ceiling, which is why
section 5 makes an over-2 MiB artefact an enumerable check rather than an
assumption.

## 10. The budget, or its absence

None. The change removes no work and adds none: it compares one integer against
a different integer. The largest artefact the new bound admits is bounded by
`SOURCE_BYTES_MAX` at 2 MiB, which the existing reader already handles. No
before-and-after measurement is owed, because nothing is being changed in the
name of speed.

## 11. The fail-closed posture

The run stops if any of these holds:

- an integration path bound admits more than 4,096 paths;
- any non-integration site admits more than 500;
- an existing v1 or v2 fixture that receipted before stops receipting;
- a refusal mutates `state.json` or `ledger.jsonl`;
- the baseline in section 3 gains a failure that is not already listed there.

A failure surfaced mid-step is worked to its cause under `elenchus` rather than
patched at the symptom, and the guard convention is the one this suite already
uses: a test that fails with the fix reverted and passes with it applied, named
for the property rather than the defect.

## 12. Decisions and their homes

One decision here is expensive to reverse, and #710 already declined it once on
scope, so the reasoning has to outlive this run rather than sit in a pull
request body.

Splitting the bound rather than raising the shared one, with #679's prior art,
#680's unrelated revert, and the five call sites and why three keep 500. Its
home is `docs/decisions/ADR-049-...`, with the number resolved at integrate.

The generation row, recording what changed and that the held issue 363 frontier
job is untouched. Its home is
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`.

Everything else is ordinary implementation and needs no standing record.
