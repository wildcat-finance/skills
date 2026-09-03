# Study: reinstate the Wave Delta distributed checkpoint programme

Assuming, unless corrected:

1. This delivery is paperwork only. Call it Tier 0. It writes decision records,
   a fresh programme study and a fresh programme runbook. It does not implement
   [#860](https://github.com/wildcat-finance/skills/issues/860) through
   [#867](https://github.com/wildcat-finance/skills/issues/867), does not create
   `wildcat-finance/fiat-checkpoints`, touches no cloud account, key, region or
   spend, and changes nothing in `wildcat-finance/shoggoth-wave-atlas`. Each of
   those remains a later, separately authorised delivery.
2. No executable checkpoint behaviour changes here. `hexctl checkpoint export`
   and `hexctl checkpoint restore` keep the bytes they have.
3. The target repository is `wildcat-finance/skills` and nothing else. The
   starting ref is `main` at `ff47f3070c8dce05c767b6c0dad65234c56870de`.
4. The interpreter is the one pinned in `.python-version`, 3.14, with the
   standard-library `unittest`. No dependency is added.
5. The maintainer has reinstated the programme. Every document in the tree
   currently says the opposite, and resolving that contradiction is the work.
6. ADR-028 does not have to be overturned to do it. Its own text calls the local
   checkpoint store an interim transport rule and says adopting a distributed
   transport requires another accepted change. That sentence is the hook the
   reinstatement hangs from.
7. Milestone 64 also carries two live controller defects,
   [#899](https://github.com/wildcat-finance/skills/issues/899) and
   [#901](https://github.com/wildcat-finance/skills/issues/901). Both are
   `hexctl` controller code. Assumption 2 puts them outside this delivery. The
   maintainer decided on 2026-09-02 that both are re-filed against the Fiat
   frontier rather than the programme. This delivery edits neither issue; the
   fresh programme documents record that the two are controller defects leaving
   milestone 64, so the estate does not read as though the programme owns them.
   The re-filing itself is work this run does not finish, so it earns a
   `## Carried forward` entry in `.hexaemeron/run-pr.md` at integration.
8. Rewriting the `wave-atlas-review` block on the nine estate issues is inside
   this delivery. The maintainer authorised it on 2026-09-02 for all of #859
   through #867. Section 3 states the reason and section 9 states the control.
9. [#508](https://github.com/wildcat-finance/skills/issues/508) no longer gates
   [#860](https://github.com/wildcat-finance/skills/issues/860). This is a
   maintainer decision recorded on 2026-09-02, not a reading derived from the
   issue text: the 26 August review's blocker is treated as lapsed because its
   co-blocker #547 does not resolve, and #508's own lane is exhausted-audit
   carryover and delegated writes rather than checkpoint identity. #860 is
   startable once the reinstatement records land. #508 stays open in its own
   lane inside milestone 64. The fresh programme runbook carries both halves of
   that sentence forward. Since that decision was recorded, #860's controller
   half has landed on the default branch: commit `482172e7` reapplies pull
   request #1069, so init resolves one immutable starting commit, an init-owned
   `fiat-run-anchor/v1` receipt joins the run identity to that commit, and
   `hexctl checkpoint identity` derives one semantic checkpoint identity. The
   issue stays open, and the fresh programme documents take #860's remaining
   scope from that commit rather than from its title.
10. Five records, as designed: ADR-069 states the reinstatement route and
    ADR-070 through ADR-073 carry ADR-029 through ADR-032 forward one for one.
11. This run reports its results in the pull-request body. Where a step would
    otherwise report something as an issue comment, it goes in the PR body
    instead. The single exception is the closing comment `done integrate`
    requires on #859 before it closes it, which stays a short pointer at the run
    pull request and carries nothing that is not already in the PR body.

I will proceed on these assumptions unless corrected.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | additive-successors
record | docs/decisions/ADR-069-reinstate-the-distributed-checkpoint-layer-above-the-local-store.md
```

The bridge names a record this delivery creates. It resolves from Step 1's exit
and not before, which is why ADR-069 lands in Step 1 beside the committed study
rather than later with its four siblings.

## 1. Problem statement

Milestone 64 has been reinstated by the maintainer and the repository does not
know it. Four decision records that describe the distributed layer are marked
Retired. The record that retired them is Accepted. The programme study and the
programme runbook both open with a banner saying they no longer govern. The
`wave-atlas-review` block on all nine estate issues reads defer or blocked.

An engineer who is handed "build #861" today reads a retired protocol decision,
a study that disclaims itself, and an issue whose current review says do not
start. Nothing in the tree tells that engineer the position changed. The build
would either stop or proceed against records that contradict it.

What is being built is the paperwork that makes the reinstatement legible: a
standing decision record for the reinstatement route, one standing successor for
each retired decision, and a programme study and runbook that govern rather than
disclaim. The user is the engineer who picks up #860 through #867 next, and the
maintainer who has to review what those engineers build against.

A working prototype here means the contradiction is gone and no gate broke
proving it. The demo path is one command from the run worktree:

```bash
python3 docs/wave-delta-reinstatement-demo.py --repo .
```

It reads the tree and exits non-zero unless all five hold: ADR-029 through
ADR-032 each name exactly one standing successor record; ADR-028 is still
Accepted and still carries its mandatory-local-hand-off amendment verbatim; no
document under `docs/` that governs the programme carries a "no longer governs"
banner; the current `wave-atlas-review` verdict on each of the nine estate
issues names the reinstatement; and `python3 -m unittest tests.test_decision_records
tests.test_fiat_checkpoint_decision_record` exits zero.

## 2. Prior art

**In this repository, the shipped half.** Fiat is at `fiat-v5.49.1`. At this
run's base commit `ff47f3070c8dce05c767b6c0dad65234c56870de`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` defines exactly two
checkpoint subcommands, `cmd_checkpoint_export` and `cmd_checkpoint_restore`,
with no intake, publication, acceptance, revocation or lineage-resolution
command and no service client. The default branch has moved since. Commit
`482172e7` adds `cmd_checkpoint_identity`, a third subcommand that prints one
verified semantic checkpoint identity, and amends ADR-028 with `Immutable run
anchors and checkpoint identity (2026-08-29)`, which derives that identity from
the verified run anchor and separates it from exact capsule and archive bytes.
Semantic checkpoint identity is therefore accepted and shipped, and the
reopened layer consumes it rather than defining one.
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md` holds the
capsule contract: schema `fiat-controller-checkpoint/v1`, the two accepted
export boundaries, a closed manifest, hostile-input read ceilings, an atomic
no-replace publish, and a restore transaction that appends one
`checkpoint:restore` entry to the same ledger. That reference states its own
limit in one sentence: the manifest digest identifies exact controller bytes and
is not the semantic checkpoint identity, service acceptance or outer archive
identity. `docs/fiat-controller-checkpoint-study.md` is the study behind it.

Three EVOLUTION rows carry the history. `fiat-v5.35.1` added capsule export and
restore. `fiat-v5.43.1` moved study and runbook receipts to portable relative
paths on restore. `fiat-v5.44.1` retired the Google Drive transport and made
every accepted boundary write to the fixed local store under the origin
checkout.

So the distributed programme still needs, on top of the capsule and the
semantic identity `hexctl checkpoint identity` now prints: the outer archive
and Git bundle assembly that ADR-028 leaves to a manual procedure; an intake,
validation and publication state machine; an independent signer and locked
storage; a publication fence on external runs; and a lineage graph with
explicit resolution. It does not need controller-state capture, ref binding,
ledger prefix verification, relocation or a semantic identity of its own. Those
exist and work.

**In this repository, the retired half.** `docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`
is Accepted, dated 2026-08-27, and its Status says it retires ADR-029 through
ADR-032. ADR-029 (protocol and authority separation), ADR-030 (locked storage
behind replaceable compute), ADR-031 (signed acceptance fence) and ADR-032
(lineage DAG) are each Retired on the same date with their bodies preserved as
historical rationale. Each also records that PR #569 first published it under a
number between ADR-024 and ADR-027, and that the collision was resolved by
moving the five records to ADR-028 through ADR-032. #569 does not resolve, so
that attribution is carried from the retired record bodies rather than from the
pull request. That is why ADR-026 and ADR-027 do not exist on disk; the gap is a
scar from the renumber, not a free slot. The highest record present is ADR-068. Confirmed by listing
`docs/decisions/`: 66 files, numbered to 068, missing only 026 and 027.

`docs/hexaemeron-checkpoint-programme-study.md` and
`docs/hexaemeron-checkpoint-programme-runbook.md` both open with a "Historical
proposal" banner and a dated issue-renumbering note. The runbook decomposes the
programme into ten steps whose titles remain a usable skeleton for the fresh
runbook: land the decisions, fix identities, export and restore, intake and
publication, deploy the authority, enforce the fence, preserve siblings, break
and recover, Atlas routing, demonstrate and close.

**The last two merged pull requests that changed the subject.** Read before
anything else was written.

- PR [#1072](https://github.com/wildcat-finance/skills/pull/1072), merged
  2026-08-31, repointed the two programme documents at the successor issue
  numbers. It carried three things forward. First: `docs/fiat-controller-checkpoint-study.md`
  still holds dead links to #558, #560 and #561 and was left alone because
  `tests/test_fiat_checkpoint_decision_record.py` pins its digest, so a hand
  edit breaks the binding to the bytes the run produced. Carried forward here as
  a stated non-goal in section 3; this delivery does not amend that file.
  Second: no test resolves documentation links against GitHub, so the rot is
  unguarded and will recur. Carried forward as risk `dead-issue-links` in
  section 5 and answered by the demo script, which checks the five in-tree
  conditions rather than every link. Third: the same two files in
  `wildcat-finance/skills-marketplace` still carry the old numbers. Refused by
  name: that repository is outside assumption 3.
- PR [#997](https://github.com/wildcat-finance/skills/pull/997), merged
  2026-08-30, made the local checkpoint store mandatory and removed the Drive
  transport, the issue-note trust anchor and the waiver. It carried nothing
  forward; its body records only summary and verification. Its verification
  block is the shape this delivery's steps should match: root suite count,
  Hexaemeron suite count, and the named lint set.

**Audit records.** `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py
--check .` was run from the target root and exited zero, with `committed=match`
on every pair, so the verified synopsis is the normal reading view. In-scope
sources and what was read:

| Source | Read | Evidence for the choice |
| --- | --- | --- |
| `audit/AUDIT.md` | `audit/AUDIT_SYNOPSIS.md` | whole-set check exit 0, `committed=match`, `source_sha256=d0be89aa…` |
| `plugins/hexaemeron/audit/AUDIT.md` | `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` | whole-set check exit 0, `committed=match`, `source_sha256=8acff29e…` |
| `audit/rounds/fiat-557-portable-run-state-recovery-r2.md` | its `.synopsis.md` | whole-set check exit 0, `committed=match` |
| `audit/rounds/fiat-909-compact-lossless-agent-instruction-language.md` | its `.synopsis.md` | whole-set check exit 0, `committed=match` |
| `audit/rounds/fiat-1021-adopt-an-early-step-merge.md` | its `.synopsis.md` | whole-set check exit 0, `committed=match` |

No source was read directly, because no view was missing, stale or unsupported.
Every finding id and status in those synopses is retained by the renderer,
including `Covered`, `Not checked`, `Elenchus verdict` and `Leads not pursued`;
the legacy rounds carry `[missing legacy field: ...]` and those stay unknown.
None of the retained findings is about decision-record numbering, retirement or
programme documents, so none is carried forward as content. The relevant
negative result is that the checkpoint rounds found nothing that argues against
reopening the distributed layer.

**Outside this repository.** The retired bodies name the outside art they rested
on: S3 Object Lock in governance mode with versioned object retention, AWS KMS
asymmetric P-256 signing, cross-account and cross-region replication,
DigitalOcean Droplets and Managed PostgreSQL in `LON1`, and Git bundles as a
transport format. None of that is re-evaluated here. Section 3 defers it to the
delivery that actually deploys anything.

## 3. Constraints and non-goals

**Starting ref and toolchain.** `main` at
`ff47f3070c8dce05c767b6c0dad65234c56870de`. Python 3.14 from `.python-version`,
standard-library `unittest`, no new dependency, no change to any workflow under
`.github/`.

**Programme checks, run from the run worktree, all four green at both ends of
every step.**

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
```

`plugins/hexaemeron/tests/run_tests.py` is the parallel runner and is the one
that counts. Plain `unittest discover` over that tree swallows ImportErrors and
reads as a clean suite, so a green `discover` there proves nothing.

**Hard gates that already exist and constrain the design.**

- `tests/test_decision_records.py`: one number per record, filename
  `ADR-NNN-kebab-case.md`, the H1 stating the number its filename claims, and no
  collision with a number already on the default branch. New numbers must be
  free on `origin/main` at the moment the branch lands, not only in the worktree.
- `tests/test_fiat_checkpoint_decision_record.py`: pins the SHA-256 of
  `docs/fiat-controller-checkpoint-study.md` and
  `docs/fiat-controller-checkpoint-runbook.md`, and asserts a fixed list of
  literals inside ADR-028, including the whole mandatory-local-hand-off
  amendment. Any candidate that rewrites ADR-028's operative clauses has to edit
  this test to land.

  Checked, because the answer decides whether a step owes a digest update: the
  test's `EXPECTED_DIGESTS` covers those two files and nothing else. ADR-028 is
  held by literal presence, not by digest. The historical programme pair is not
  pinned by any test. Neither file this delivery writes to,
  `docs/decisions/ADR-028-…` in Step 1 nor
  `docs/hexaemeron-checkpoint-programme-{study,runbook}.md` in Step 4, is a
  digest-pinned file, so **no step updates a pinned digest and no step exit owes
  that clause**. The other pin the repository holds over ADR-028 is
  `tests/test_evolution_contract.py` line 222, which asserts the string
  `ADR-028` appears in the `fiat-v5.35.1` row's evidence column; this delivery
  does not touch `EVOLUTION.md`.

  One placement constraint follows from the same test.
  `test_adr_supersedes_remote_transport_with_mandatory_local_handoff` slices
  ADR-028 from the mandatory-local heading to the next `## ` heading and
  requires seven literals inside that slice. The new amendment is appended after
  `## Consequences`, at the end of the file, which leaves that slice
  byte-identical. Both that placement and inserting before `## Alternatives`
  were run against the test's own slicing logic and both keep all seven
  literals; end-of-file is specified because it changes the least.
- `tests/test_shipped_prose_lints.py` excludes `docs/**` from the shipped-prose
  lint by design, because editing a delivered spec to satisfy a later lexicon
  rewrites history. That exclusion means the suite will not catch a lint defect
  in a new ADR. Fiat's own prose phase is the only enforcement, so imprimatur
  then vulgate runs on every changed prose file whether or not a test would
  notice.

**Prose gates.** Imprimatur lint, then vulgate, on every changed prose file.
Hypomnema decides what is recorded and where. The study's `design-bridge` block
binds the selected candidate to exactly one ADR home.

**Ruled out by the user.**

- Implementing #860 through #867.
- Creating `wildcat-finance/fiat-checkpoints`.
- Touching any cloud account, key, region or spend.
- Changing `wildcat-finance/shoggoth-wave-atlas`.
- Changing executable checkpoint behaviour.

**Non-goals this study adds.**

- Amending `docs/fiat-controller-checkpoint-study.md` or its runbook. PR #1072
  established that both are digest-pinned run artefacts; their dead links stay
  dead until the controller's amendment path is used, which is a separate job.
- Re-evaluating the infrastructure choices in the ADR-030 body. The carried-forward
  record states them as the shape to test, not as a standing authorisation, and
  says so in its own Status.
- Fixing #899 or #901, and editing either issue. Both are controller code and
  assumption 2 excludes code. Assumption 7 sends them to the Fiat frontier.
- Re-opening the #508 question. Assumption 9 settles it by maintainer decision.
  The supporting fact is that `gh issue view 547` returns "Could not resolve to
  an issue or pull request", but the decision is the maintainer's, not that
  fact's.

**Reporting convention.** Assumption 11 governs where every step's result goes.
A step exit that would name an issue comment names the pull-request body
instead. The one comment this run writes is the closing pointer `done integrate`
puts on #859.

**In scope, and why.** Rewriting the `wave-atlas-review` block on #859, #860,
#861, #862, #863, #864, #865, #866 and #867 belongs to this delivery. The block
is the operative verdict a reader sees first, it currently says defer or
blocked, and leaving it is the same contradiction this delivery exists to
remove, relocated from disk to GitHub. Excluding it would produce a repository
that reinstates the programme and an issue estate that still refuses it, with
nothing saying which one is current. The block is rewritten by appending a new
dated review, in the same additive shape the records use, and the mapping is
recorded on disk in `docs/wave-delta-issue-estate-2026-09-02.md` so the change
is reviewable without GitHub. The maintainer authorised this on 2026-09-02 for
all nine issues, on the shape stated here and controlled in section 9.

## 4. Design options

Four constructions were weighed. The record in `.hexaemeron/design-evidence.json`
selects between them; the prose below explains what each is.

**`additive-successors`.** ADR-069 records the reinstatement route itself: the
distributed layer is reopened above the local store, ADR-028 stays Accepted, and
the reopening is done by addition. ADR-070 through ADR-073 then carry the four
retired bodies forward one for one, rebased on `fiat-v5.49.1` so each says what
the shipped capsule already supplies and what its own decision still owes.
ADR-028 gains one dated amendment naming the layer above it; its Status line is
untouched. *The trade:* five records to write, five numbers to hold free against
a moving default branch, and the largest reviewed surface of the four. In
exchange every retired decision gets a named successor a reader can follow,
every reopened decision stays independently supersedable, and no durable record
is rewritten.

**`reopen-in-place`.** Flip the Status line of ADR-029 through ADR-032 from
Retired back to Accepted and rewrite the ADR-028 Status paragraph that says it
retires them. *The trade:* the smallest number of new files, none, against
rewriting five durable records. It erases the retirement event rather than
recording that it was undone, which is the thing Hypomnema's placement rule
refuses: a record that stops being true earns a new record, not an edit. A
reader six months out would find no evidence the decisions were ever retired.

**`composite-record`.** One ADR-069 reinstates the whole programme, referencing
the four retired bodies without carrying any forward. *The trade:* cheapest to
write and review, and one clear home for the reinstatement, against collapsing
four independent decisions into one record. The protocol and authority split,
the storage substrate, the publication fence and the lineage model can then only
be superseded together, and each retired record still ends with no successor to
follow.

**`overturn-028`.** Mark ADR-028 Superseded and write ADR-069 as its
replacement, covering both the local store and the distributed layer. *The
trade:* one coherent record for the whole checkpoint story, against leaving
every shipped checkpoint behaviour governed by a superseded record. `hexctl
checkpoint export`, `hexctl checkpoint restore`, the mandatory local store and
the capsule contract are all live in `fiat-v5.49.1` and all rest on ADR-028
alone.

### Design evidence

The record is `.hexaemeron/design-evidence.json`, schema
`protasis-design-evidence/v1`, digest
`6a171b6f72d1a651ebd9b7dd32af331ba6a9aaff600f02100c328907d1b9d755`. Five
selection criteria cover correctness, recovery, compatibility, time and space;
one conformance gate blocks `integration`.

Every selection value was computed by `.hexaemeron/design_eval.py` from two
sources and nothing else: the candidate's declared change plan under
`.hexaemeron/plans/`, and the bytes of this repository. Where a plan names a
repository path, the evaluator opens it; a plan naming a path the repository
does not hold refuses rather than scoring zero. The twenty reports live under
`.hexaemeron/reports/` and each binds its exact command and exit 0.

| Criterion | additive | reopen | composite | overturn |
| --- | ---: | ---: | ---: | ---: |
| `retired-decision-successors` (gate, at least 4) | 4 | 0 | 0 | 0 |
| `durable-records-rewritten` (gate, at most 0) | 0 | 5 | 0 | 1 |
| `shipped-behaviour-left-ungoverned` (gate, at most 0) | 0 | 0 | 0 | 4 |
| `prose-gate-passes` (minimise) | 11 | 10 | 7 | 7 |
| `carried-prose-bytes` (minimise) | 24,550 | 0 | 0 | 0 |

`additive-successors` is the only candidate that clears all three hard gates, so
it is the only eligible candidate and the only member of the non-dominated
frontier. Selection rule `unique-frontier`. It loses both comparative metrics,
which is the honest reading of its cost: it is the most expensive route to
review, and the gates say the cheaper ones are not admissible. `python3
design_evidence.py .hexaemeron/design-evidence.json --transition design-lock`
exits 0.

The conformance gate `programme-checks-green` is pending for all four
candidates, resolver `python3 plugins/hexaemeron/tests/run_tests.py && python3 -m
unittest discover -s tests && python3 scripts/promise_machine.py check && python3
scripts/promise_machine.py coverage --check`, blocking `integration`.

## 5. Risk register seed

The exposure here is not memory safety or arithmetic. This delivery goes wrong
by leaving a record set that reads as authoritative and is not, and by writing to
one publication surface no repository test can reach.

```risk-register
adr-number-collision | the ADR numbers 069 to 073 against a concurrently landing delivery | tests/test_decision_records.py compares against the fetched default branch, and every step re-runs it after a base sync rather than trusting the number chosen at study time
adr-028-clause-drift | the literals tests/test_fiat_checkpoint_decision_record.py pins inside ADR-028 | the amendment is appended after Consequences so the mandatory-local slice the test reads stays byte-identical; the test runs unmodified at every step exit and its required-literal list is not edited
pinned-artefact-digest | the SHA-256 pins on docs/fiat-controller-checkpoint-study.md and its runbook | checked: neither is in this delivery's write set, so no step owes a digest update; neither file is opened for writing in any step and the pinned-digest test runs at every step exit
retired-body-drift | the four ADR-029 to ADR-032 bodies carried into ADR-070 to ADR-073 | each successor states which clauses it carries verbatim, which it rebases on fiat-v5.49.1, and which it drops, so a reader can diff successor against source
capsule-overclaim | prose describing what the distributed layer still needs | no new record or study section describes as absent anything controller-checkpoint.md already specifies; the capsule contract is cited rather than restated
issue-body-publication | the nine wave-atlas-review blocks on GitHub | the new block is drafted on disk in docs/wave-delta-issue-estate-2026-09-02.md, passes the prose gates there, and is published verbatim with a remote readback; the original filing under wave-atlas-original is never touched
dead-issue-links | every issue and pull-request number cited by the new records and study | each number is resolved with gh before the step that cites it lands, and one that does not resolve is named as unresolved in the text rather than linked
scope-creep-to-code | the boundary between this Tier 0 delivery and issues 860 to 867, 899 and 901 | no step opens plugins/hexaemeron/skills/fiat/scripts/hexctl.py or any file under plugins/, and the step exit fails if git diff --name-only names one
banner-inversion | the two historical programme documents once the fresh pair exists | the historical banner stays and gains a forward pointer; the fresh documents carry no banner, and the demo script fails if a governing document carries a no-longer-governs banner
```

## 6. Glossary seeds

- **Capsule.** The `fiat-controller-checkpoint/v1` directory `hexctl checkpoint
  export` writes: exact `.hexaemeron` bytes plus a closed manifest. Exact-byte
  evidence, not a semantic identity.
- **Outer archive.** The zip, Git bundle, signature proof and sidecar ADR-028
  keeps in a manual procedure around the capsule. Not built by `hexctl`.
- **Local checkpoint store.** The fixed path
  `<origin>/.hexaemeron/checkpoints/<run-worktree-name>/` that ADR-028 makes the
  only current transport.
- **Distributed layer.** Everything the reinstated programme adds above that
  store: intake, signed acceptance, the external-run fence, and lineage
  resolution, over the semantic identity the controller already prints.
- **Semantic checkpoint identity.** A `snapshot_id` that survives harmless
  repacking, as distinct from an archive byte digest. Printed by `hexctl
  checkpoint identity` on the default branch since `482172e7`.
- **Standing successor.** A new record that carries a retired record's decision
  forward and names it, leaving the retired record in place as history.
- **Estate.** The nine issues #859 through #867 plus the review blocks on them.
- **Tier 0.** This delivery: records and documents, no code, no infrastructure.

## 7. Sources

- `docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`, Accepted 2026-08-27, with amendments dated 2026-08-29 and 2026-08-30.
- `docs/decisions/ADR-029-…`, `ADR-030-…`, `ADR-031-…`, `ADR-032-…`, each Retired 2026-08-27.
- `docs/hexaemeron-checkpoint-programme-study.md` and `docs/hexaemeron-checkpoint-programme-runbook.md`.
- `docs/fiat-controller-checkpoint-study.md` and `docs/fiat-controller-checkpoint-runbook.md`, digest-pinned by `tests/test_fiat_checkpoint_decision_record.py`.
- `plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `cmd_checkpoint_export`, `cmd_checkpoint_restore` and the `checkpoint` subparser block, read at the run's base commit `ff47f3070c8dce05c767b6c0dad65234c56870de`. The file has changed on the default branch since, so it is cited by symbol rather than by line.
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, rows `fiat-v5.35.1`, `fiat-v5.43.1`, `fiat-v5.44.1`, current `fiat-v5.49.1`.
- `tests/test_decision_records.py`, `tests/test_fiat_checkpoint_decision_record.py`, `tests/test_shipped_prose_lints.py`.
- Issues #859, #860, #861, #862, #863, #864, #865, #866, #867, #508, #899, #901 in `wildcat-finance/skills`, each read on 2026-09-02. #547 does not resolve.
- Pull requests #1072 merged 2026-08-31 and #997 merged 2026-08-30.
- `audit/AUDIT_SYNOPSIS.md`, `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` and three round synopses, admitted by `audit_synopsis.py --check .` exit 0.
- `plugins/hexaemeron/skills/hypomnema/SKILL.md` for the ADR shape and the placement rule.

## 8. Signals, and the questions behind them

None for a running system, and here is why: this delivery ships no process. It
adds Markdown files to a repository and edits nine issue bodies. Nothing runs
unattended, so there is no three-in-the-morning question about it and nothing to
instrument. Ephoros owns what a signal must carry, and there is no signal here.

The two questions that do get asked, and where each is answered, both belong to
a reader rather than to a monitor:

1. *Is the distributed programme on or off right now?* Answered by
   `docs/decisions/ADR-069-…`, and mechanically by the demo script in section 1.
2. *Which record governs the checkpoint behaviour my controller just ran?*
   Answered by ADR-028 remaining Accepted with its amendment intact, checked at
   every step exit by `tests/test_fiat_checkpoint_decision_record.py`.

Neither is a runtime signal. If the programme's later deliveries build the
service, the on-call questions arrive with #862 and #863 and are that delivery's
to answer.

## 9. Boundaries, per capability

Three boundaries open here. Phylax owns the boundary list and the controls;
these are the instances.

1. **The GitHub issue-body write on nine issues.** What is worth taking at it:
   the ability to make the estate say something a reader will act on, under the
   run's identity. The control: the block is drafted on disk, passes Sapheneia's
   bounded durable-record pass and then imprimatur and vulgate there, and is
   published verbatim with a remote readback comparing the published bytes to
   the drafted bytes. The `wave-atlas-original` section is never edited, so the
   historical filing survives whatever the new block says. This is an ask-first
   boundary and the maintainer granted it on 2026-09-02 for these nine issues
   and this shape. The grant does not extend to any other issue, to #899 or
   #901, or to a comment: the only comment this run writes is the closing
   pointer on #859 that `done integrate` requires.
2. **The `gh` reads that resolve every cited issue number.** What is worth
   taking at it: a wrong or absent number becomes a plausible link. The control:
   fixed-argument `gh issue view` per number with the repository named
   explicitly, a number that does not resolve written as unresolved prose rather
   than as a link, and no shell interpolation of anything read back.
3. **The demo script this delivery adds under `docs/`.** What is worth taking at
   it: it is executable Python in a documents delivery. The control: it takes
   `--repo` and nothing else, opens files read-only, starts no subprocess other
   than the two named `unittest` modules with fixed argv and no shell, and
   writes nothing.

No credential is read, no network write happens other than the nine issue edits
named above, and no dependency is added.

## 10. The budget, or its absence

No performance budget, and here is why: the delivery adds roughly 40 kilobytes
of Markdown and one small script to a repository whose test suites already run
in the tens of seconds. Nothing measurable gets slower, and Metron's rule is
that a performance change needs a recorded measurement first. There is no
performance change to record.

One number is worth watching rather than budgeting, because it is a review cost
rather than a machine cost: `carried-prose-bytes` for the selected candidate is
24,550 bytes of retired body carried into four successors, and
`prose-gate-passes` is 11 files. Both are recorded in the design evidence so a
later reader can see what the chosen route cost in reading, and neither gates
anything.

## 11. The fail-closed posture

What stops the run:

- Any of the four programme checks failing at either end of a step.
- `tests/test_decision_records.py` reporting a number collision against the
  fetched default branch, or reporting that the comparison could not run. That
  test says so rather than passing quietly, and a comparison that could not run
  is treated as a stop, not a pass.
- `tests/test_fiat_checkpoint_decision_record.py` failing on a pinned digest or
  a missing ADR-028 literal. That means a step touched a file this delivery
  promised not to touch.
- `protasis.py --study` or `protasis.py` on the fresh programme documents
  exiting non-zero.
- `hypomnema.py --study` reporting H008 once ADR-069 exists.
- An imprimatur defect on any changed prose file, before vulgate rather than
  after.
- A published issue body whose remote readback does not match the drafted bytes.

The guard convention follows Elenchus: a fix lands with a test that fails
without it. For this delivery that mostly means the demo script grows an
assertion. If a step breaks a record-set property, the repair adds the check for
that property to `docs/wave-delta-reinstatement-demo.py` and the check is shown
failing against the broken tree before the repair lands. Where the property
belongs to an existing suite instead, the assertion goes there;
`tests/test_decision_records.py` is the home for anything about numbering.

## 12. Decisions and their homes

Expensive to reverse, and where each record lives. Hypomnema owns which
decisions earn a record and where; these are the ones this delivery makes.

1. **The reinstatement route: reopen by addition above ADR-028 rather than
   overturning it.** Home:
   `docs/decisions/ADR-069-reinstate-the-distributed-checkpoint-layer-above-the-local-store.md`.
   This is the record the `design-bridge` block binds. Reversing it later means
   unpicking four successor records and their references.
2. **One standing successor per retired decision.** Homes: ADR-070 (from
   ADR-029), ADR-071 (from ADR-030), ADR-072 (from ADR-031), ADR-073 (from
   ADR-032). Each names its source and states what it carries verbatim, what it
   rebases on `fiat-v5.49.1`, and what it drops.
3. **ADR-028 stays Accepted and gains one dated amendment.** Home: an appended
   `## Amendment: distributed layer reinstated (2026-09-02)` section inside
   ADR-028 itself, placed after `## Consequences` at the end of the file. Its
   Status line and every literal the pinned test names are left alone, and the
   slice that test reads stays byte-identical.
4. **The fresh programme documents supersede the historical pair by addition.**
   Homes: `docs/wave-delta-checkpoint-programme-study.md` and
   `docs/wave-delta-checkpoint-programme-runbook.md`. The historical pair keeps
   its banner and gains a forward pointer.
5. **The estate's operative verdict.** Home:
   `docs/wave-delta-issue-estate-2026-09-02.md` on disk, published as a new
   dated `wave-atlas-review` block on each of the nine issues.

No Fiat `EVOLUTION.md` row is earned here. This delivery changes no governed
skill's behaviour, and VERSIONING.md's axis arithmetic has nothing to record. If
the maintainer wants the reinstatement visible on the Fiat ledger, that is a
separate decision and section 12 of the fresh programme study is where it would
be argued.

Five questions were put to the maintainer before this study was receipted and
all five came back answered on 2026-09-02. Each answer is a settled assumption
above, not an open item: #508 no longer gates #860 and stays open in its own
lane (assumption 9); five records rather than four (assumption 10); the
nine-issue review rewrite is authorised on the stated shape (assumption 8);
#899 and #901 stay out and are re-filed against the Fiat frontier, earning a
carryover entry (assumption 7); ADR-028 gains the appended dated amendment
(decision 3 above). Nothing in this study now rests on an unanswered question.

Two of those answers are the maintainer's judgement rather than a reading of
the evidence, and are recorded that way so a later reader does not mistake them
for derivations. The #508 lapse is a decision about a blocker, not a conclusion
drawn from #508's text. The re-filing of #899 and #901 is a decision about which
frontier owns them, not a finding about their content.

One item is carried rather than closed. Re-filing #899 and #901 against the Fiat
frontier is work this delivery does not do, so `.hexaemeron/run-pr.md` carries it
under `## Carried forward` at integration, where `done integrate` requires that
section to be non-empty. The fresh programme documents state that both are
`hexctl` controller defects leaving milestone 64, so the estate does not read as
though the programme owns them.
