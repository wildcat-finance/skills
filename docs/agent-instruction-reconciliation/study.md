# Reconcile reviewed corpus spans after law edits

Assuming, unless corrected: this delivery owns issue #1513 on `main` at
`b9f8e36b8b6210bcd023a68059ecb46da3e35769`, tree
`5f48caffde9c41846e13dfdda5c5f10165d3e274`. It preserves the version-1 corpus,
all three fixtures and 15 reviewed bindings. A source edit may move reviewed
bytes but may not change them. Issue #1192 retains the relative-offset schema;
#1467 is already delivered and closed through PR #1554. No new dependency,
paid endpoint, profile capability or semantic re-review is authorised here.

## 1. Problem statement

Give contributors a reusable, fail-closed repair for a bound instruction source
whose unchanged reviewed spans moved. Today `reconcile` selects only
`fiat-study-runbook-phase`; a law edit is rejected as unrelated drift. Merely
re-pinning the law digest can then return `nothing-to-reconcile` while deeper
bindings remain stale. The exact source, selected fixture set, baseline bytes
and remaining evidence dependencies must be visible before any live write.

A working prototype prepares the complete derived fixture set in a confined
stage, preserves reviewed meanings and evidence classes, and publishes only a
fully checked candidate with recoverable writes. The proving demonstration
uses a disposable checkout: append and prepend outside each of the three
reviewed spans; refuse changed or ambiguous reviewed bytes; complete one
before-span law repair using fresh complete owner-generated measurement and
parity cohorts; apply, check, and exercise interruption recovery. Three
before-span structural probes may report `needs-evidence`; that is not a
completed repair. The completed law case must pass the existing full checker.

The future focused runner is
`python tests/emit_agent_instruction_reconciliation_report.py REPORT`.
The future recorded demonstration is verified by
`python scripts/prove_agent_instruction_reconciliation.py demonstrate --root . --verify docs/agent-instruction-reconciliation/demonstration.json`.
Both are implementation deliverables, not commands reported as already run.
The verifier rechecks every declared input/dependency hash and the acquired
reports against their staged corpus and profiles. Its closed summary uses
`agent-instruction-reconciliation-verification/v1`, `outcome: accepted`, the
record SHA-256, six structural placements, one completed law repair, 15
unchanged reviewed bindings and a positive verified-dependency count. A
boolean assertion without those source-bound checks is insufficient.

## 2. Prior art

Read PR #1550, merged 2026-09-12, and PR #1416, merged 2026-09-06: these are
the last two merged PRs returned for the latest commits touching the actual
corpus/prover scope. Read their enclosing integration PR #1554 as well.
#1550 repaired four law bindings displaced by 4,412 bytes, reviewed profiles
and acquired 10 measurement calls plus 36 parity calls. #1416 re-pinned an
unchanged Fiat span after its reset change and carried its counts without a
new model observation. Their exact bodies and identities are saved under
`.hexaemeron/prior-art/`.

The current `Reconciliation.rederive_offsets` already locates each anchor and
node by unchanged bytes, checks its digest and refuses duplicate occurrences.
`LiveReconciliation` takes no baseline source, fixes one subject and performs
six individually atomic passes without a transaction. ADR-076 preserves
whole-file bindings while projecting bound digests from the measured streams;
absolute offsets still affect both corpus identity and measured model/compact
bytes. Fresh evidence is therefore required after relocation. The #1538 repair
in `docs/main-root-suite-recovery/` demonstrates that owner acquisition can
complete this case, but its bespoke repair is not a reusable API.

The whole-set audit-synopsis currency check exited 0. The exact source/view
hashes and complete scoped round records are retained in
`.hexaemeron/study-evidence/audit-read-inventory.json`: #1098 Step 5 round 1
and Step 6 rounds 1 and 2; #909 Step 4 rounds 3 and 6 and Step 5 round 3;
#1538 both rounds; and both legacy Hexaemeron plugin rounds. These were read
as verified synopsis records, not as full historical source files. Every
selected record retains its finding ids/statuses, Covered, Not checked,
Elenchus verdict and Leads not pursued. Missing legacy fields remain unknown.
Earlier rounds remain authoritative; no full-history read is claimed. The root
legacy synopsis has no exact corpus/prover subject match and is outside this
repair's technical audit scope.

#1098 S6-R1-01 is fixed as a diagnostic but leaves interrupted multi-file
writes unresolved. S6-R1-02 and S6-R1-03 remain open historical study defects:
the real writer includes the coverage register outside the fixture root, and
four digests moved in that example rather than the register's stated six.
This study names repository confinement and derives the changed target set.
It does not rewrite the earlier record. #909 S4-R3-01 was fixed by anchoring
profile bytes before any launch; that control stays intact.

Carryovers remain separate: #1192 relative offsets; #1198 guard attribution;
#1199 acquisition-output identity and independent token-count assurance;
#1200 design-report/placement scope; and #1267 ADR/provenance format. #1513
addresses reusable reconciliation and its recovery only. PR #1548 for #1192
is open at `c3a6f92933cb818fee763b06972a8c7a7201bbd7`, based before #1538,
and reported `DIRTY`. Its model/compact changes still owe fresh evidence;
it supplies no green dependency and is not adopted.

Outside this repository, Git's `show` reads a named object, and Python's
`os.replace` supplies one successful rename's atomicity. Neither is a
multi-file transaction. This design infers a need for checked baseline reads
and a recovery journal from those boundaries. Sources:
[git-show](https://git-scm.com/docs/git-show) and
[os.replace](https://docs.python.org/3.14/library/os.html#os.replace).
No other organisation repository provides a required dependency.

## 3. Constraints and non-goals

Use Python 3.14.6 through `uv run --no-project --python 3.14.6 python` and
stdlib tooling. The exact worktree fingerprint is
`issue/16777233-521985670`; it resolved through `/.vol` before inspection.
The source-bound Fiat controller remains the parent's owner. This study may
write only untracked `.hexaemeron` artefacts and issues no receipt.

Always: preserve source bytes and reviewed metadata; check every unchanged
sibling fixture; validate exact generated targets; run the active root and
applicable suites, generated/prose checks and staged greenlight before a signed
commit. Then run all 35 declared checks with `--full --jobs 12` on the clean
signed HEAD before the implementation receipt. The complete package must keep
at least 5,242,880 bytes below its fixed 26,214,400-byte cap.

Ask first only for a new dependency, a changed public/storage schema, a new
trust boundary, CI changes or a rewrite of released evidence outside this
packet. The authorised additive v1 repair and disposable demonstration need
no repeated permission. Never change counts, answers, review assertions,
profile anchors or thresholds to make a result pass; never publish a partial
set, silently rebind sibling drift, bypass the commit gate or alter old audits.

Excluded: #1192 schema migration, model quality, independent truth of token
counts, arbitrary English, new profile authorisation and hardware power-loss
atomicity. A killed process must leave a detectable journal and a checked
recovery route; this does not claim an instantaneous cross-file swap visible
to every unrelated reader.

## 4. Design options and selection

The complete matrix is `.hexaemeron/design-evidence.json`. Its selected
candidate is `staged-general-v1` under `unique-frontier`; the design-lock
checker exited 0. All 15 selection cells are resolved; nine conformance cells
are pending, three per candidate. At integration, only the selected candidate's
due gates authorise continuation.

| Candidate | Correctly classified fixture placements | Restored injected publication faults | Preparation p95 | Extra old/new stage bytes |
| --- | ---: | --- | ---: | ---: |
| `fixed-live-v1` | 1/6 | no checked recovery primitive | 226 ms | 0 |
| `sequential-general-v1` | 6/6 | 1/4 | 263 ms | 0 |
| `staged-general-v1` | 6/6 | 4/4 | 227 ms | 24,092 |

A correctly classified placement means unchanged reviewed bytes at their
re-derived offsets and the existing checker result: accepted after-span, or
`WAI-E-DIGEST.CORPUS` at `$.evidence.measurement_record` before-span.
It is a count of correct repair/dependency classifications, not six green
corpora. All six changed/duplicated-span probes refused for each general
candidate. Live source digests remained unchanged. The p95 is the nearest rank
of six actual preparation samples, rounded up; workload, host, raw samples and
limits are preserved in `study-evidence/`. No performance improvement is
claimed. The space measure covers four law targets' old/new bytes only.

The fixed candidate loses the six-placement gate. The general sequential
candidate loses the preimage-recovery gate. Staging pays 24,092 measured bytes
for this four-target prototype and passes those selection gates. The fault
probe handles injected `OSError` between writes; it has no durable on-disk
journal, killed-process recovery or coverage publication. Those remain named
conformance obligations and are not inferred from the probe.

Implement the selected design through additive prepare/apply/recover verbs in
`scripts/prove_agent_instruction_reconciliation.py`, with a focused helper
module if needed and `tests/test_agent_instruction_reconciliation.py`.
Preserve the existing proof verbs and their defaults.

Preparation takes one explicit source path, an immutable baseline commit and
a stage path. Resolve the baseline without inherited Git repointing, replace
objects or lazy fetch; read its source blob and require the manifest's recorded
whole-file digest. Verify the accepted baseline manifest and its complete
bound closure before comparing the edited source. Select every fixture that
binds that source; refuse an absent source and any unrelated sibling drift.
Locate each unchanged reviewed span once, then each node once within that span.
Recompute every digest and v1 absolute offset. Never guess a shift or accept a
changed review because it looks similar.

Create the candidate's complete fixture/evidence inputs below a new confined
stage and record exact old/new identities plus the derived publication target
set. Prepare performs no live writes or model calls. Report corpus, measured
streams, profiles, measurement and parity as separate dependency states.
Unchanged projected inputs may retain exact old evidence. Moved offsets require
complete new owner records; print the exact `agent_instruction.py measure`,
`parity` and `check` commands against the stage. Failed or changed profile
identity refuses; it is never re-pinned automatically. Preserve every refused
acquisition attempt. The ordinary checker must accept the complete staged
manifest before apply can start.

Apply rechecks stage and target identities, the selected edited source and all
sibling bindings. It stages every candidate and backup before publishing, with
a closed journal under the declared state directory. Persist intent before the
first write. A handled fault restores exact old generated bytes. An unfinished
journal blocks another application; recover verifies each target is its old
or planned new bytes and restores the preserved old set, refusing any third
version. Recovery is idempotent and never alters the contributor's edited
source. Manifest and coverage publish after their inputs; success appears only
after all writes and their readback pass. Concurrent conflicting writers,
symlinks, path escapes, duplicate keys, special files and changed baselines
refuse with a bounded code and the recovery command.

A coverage rebind may also stale whole-coverage evaluation bindings, generated
copies and demonstrations. Report that owner closure explicitly. Reuse the
owner replay only after it proves its historical prompts unchanged; otherwise
refuse that dependent transition. The repair is complete only after the root
checks accept the resulting composition. It grants no ownership over unrelated
coverage rows or historical observations.

## 5. Risk register

```risk-register
baseline-authority | Git object to reviewed source | exact immutable baseline source digest and complete accepted closure; no inherited repointing or replacement objects
reviewed-byte-change | selected source to anchor and nodes | unique exact digest-checked relocation; changed, missing or ambiguous bytes refuse
sibling-drift | source selection to complete corpus | enumerate all affected fixtures and refuse every unexplained sibling or artifact mismatch
measured-byte-drift | offsets to model and compact streams | preserve v1 and require fresh complete measurement and parity when their inputs move
profile-authority | staged profile to adapter launch | preserve source-owned anchors; no profile self-authorisation or automatic re-pin
stage-escape | source, stage and report paths | bounded closed records and regular confined paths; reject links, traversal, aliases and special files
partial-publication | candidate set to live generated files | complete preflight, journal before writes, readback, injected faults and killed-process recovery
concurrent-change | preparation to apply or recover | compare exact baseline, target and candidate identities and refuse a third version
coverage-owner | repaired artifacts to dependent records | derive actual rebound set and retain historical prompt and evidence limits
signal-honesty | dependency report to operator | stable states separate needs-evidence, refused, ready, applied and recovered
historical-evidence | audit and acquisition records | preserve ids, statuses, unknowns and refused attempts without claiming fresh observations
package-reserve | generated package to fixed cap | verify complete package and runtime keep at least 5242880 bytes of reserve
```

## 6. Glossary seeds

Reviewed span: exact source bytes whose declared meaning was reviewed.
Baseline: the immutable pre-edit source and accepted fixture closure.
Stage: confined candidate files and their explicit unresolved dependencies.
Apply: publication only after the complete staged checker accepts.
Recovery: checked restoration of old generated bytes, retaining the source edit.

## 7. Sources and evidence

Local sources: `scripts/prove_agent_instruction_reconciliation.py:326` and
`:795`; `scripts/agent_instruction.py:2902`, `:2917`, `:3587` and its profile
identity checks; the manifest and its three fixture directories;
`docs/decisions/ADR-062-encode-a-closed-agent-instruction-model.md` and
`ADR-076-digest-neutral-measured-corpus.md`; and
`docs/main-root-suite-recovery/README.md`. PR and scoped audit sources are
identified in section 2 and the retained inventory.

The parent supplied fresh baseline evidence in
`.hexaemeron/baseline/proof.json`: corpus check exit 0 and both focused modules
exit 0, with 352 tests. This is checked evidence for the starting tree; the
prior 35-check report remains historical evidence for that same tree.
Selection commands, stdout, report digests and environment are retained beside
the design record. No model or profile identity command ran in this study.

## 8. Signals and their questions

Apply `plugins/hexaemeron/skills/ephoros/SKILL.md`. Which source and baseline
were compared? Emit their identities and affected fixture ids. Why is apply
blocked? Emit the exact corpus/profile/record dependency and its owner command.
Did publication complete or stop midway? Emit the journal id, stable phase,
planned/completed targets and one recovery action. This is a bounded CLI;
no new service, metric backend or alert is needed. Sample both successful and
refusing output in the focused suite.

## 9. Boundaries per capability

Apply `plugins/hexaemeron/skills/phylax/SKILL.md`. Git returns untrusted bytes;
source digest and accepted baseline validation decide their use. Paths and
JSON are untrusted; confine and cap reads/writes before traversal. Subprocesses
use fixed argument lists, checked executables, timeouts and bounded output.
No credential enters a stage or report. Profile records remain untrusted data
behind source-owned anchors. A model result retains measured/recorded evidence
classes and creates no instruction or publication authority.

## 10. Budget

Apply `plugins/hexaemeron/skills/metron/SKILL.md`. This is a correctness repair,
with no speed target or optimisation claim. Selection timing/space are narrow
observations, not production bounds. Retain the existing 600-second checker
subprocess limit and 1 MiB output cap; bound every new stage/journal file at 1 MiB, at most 256 targets and
32 MiB total staged content. Reuse the checker's lower per-input limits where
they apply. The
package reserve is checked by `python -m unittest tests.test_skills_sh_package`
and `python scripts/portable_promise_machine.py check`.

## 11. Failure and guards

Apply `plugins/hexaemeron/skills/elenchus/SKILL.md`. The six source-placement
reproductions are preserved before a fix. Add assertion guards that fail on the
unfixed behavior for law/horos selection and moved exact spans. Exercise
partial writes, process termination, retry, stage/target races, hostile paths,
stale profiles and stale records. A coverage-only failure is not attributed
as the behavior guard. The exact future runner above writes
`elenchus.unittest.v1`; the runbook supplies one `{report}` argument and
`.elenchus/agent-instruction-reconciliation.json` for Warden.

The three selected conformance resolvers are recorded exactly in the design
matrix and implemented in `.hexaemeron/scripts/resolve_reconciliation_conformance.py`.
They require the future focused report, the future demonstration verifier and
current corpus/package checks. Each blocks `integration`; none has run or is
reported passed. Their raw proof binds the observed HEAD/tree, relevant source
and demonstration hashes and resolver bytes before and after execution; any
change refuses. The currency resolver covers its three named commands only,
not the separate 35-check run. The parent additionally requires the complete clean-HEAD
checked run and normal audit/prose/receipt gates.

## 12. Decisions and their homes

Apply `plugins/hexaemeron/skills/hypomnema/SKILL.md`. The repository-wide
choice earns one numberless draft at
`docs/decisions/drafts/stage-reviewed-corpus-reconciliation.md`, bound through
the shipped study's design bridge to `staged-general-v1`. Extend ADR-076's
operational boundary through this successor while preserving its old text.
The parent assigns a number only during final integration. Step 1 commits the
study, design record/reports, runner plan and draft; the final step records the
disposable demonstration at `docs/agent-instruction-reconciliation/`.

Study readiness establishes 12/12 answered sections and a checked selection.
It authorises deriving the runbook. Implementation, durable crash recovery,
fresh demonstration acquisitions and final composition remain unestablished.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | staged-general-v1
record | docs/decisions/drafts/stage-reviewed-corpus-reconciliation.md
```
