![Hexaemeron](./assets/characters/hexaemeron.png)

# HEXAEMERON

<!-- marketplace-context:start -->
## In one line

Hexaemeron carries an explicit, receipted delivery from study to one merged change while keeping every controller, worker, phase discipline, prose mask, and security tool inside its own authority.

**Current frontier.** load_state validates the version-1 state container spine in deterministic order before any command traverses it, with path-and-kind diagnostics shared by verify and mutations; delegated task identities can still expose an earlier issue when a collaboration handle is reused.

**Next Fiat job.** Use /hexaemeron:fiat to complete skills#363 by binding every Fiat delegation task identity to the current issue or topic, step number and role, refusing or replacing a stale reused handle; accept it only when issue N cannot retain issue M in its visible name, all four workers expose current deterministic identities, resume and post-compaction reconstruction preserve them, and an executable regression rejects stale reuse. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

Let there be light.

## START HERE

Use Hexaemeron when you want one repository issue carried through the complete
controlled delivery, not merely edited. Its Fiat controller orders study,
runbook, implementation, audit, prose, push, and integration, and records each
accepted transition in durable state.

Fiat is explicit-only. It does not start because a task sounds like delivery.
Its checkpoints survive local context loss at completed boundaries; they are
not arbitrary mid-step snapshots or a distributed cross-machine service.

## PLACE IN THE COLLECTIVE

Hexaemeron is the delivery system, not a general replacement for the other
plugins. Fiat controls the run. Surveyor, Mason, Warden, and Scribe execute
source-bound packets. Protasis, Phylax, Ephoros, Metron, Elenchus, and
Hypomnema state the disciplines the phases must meet. Imprimatur and Vulgate
shape prose. Kronos may rank held frontier jobs and dispatch one into Fiat.

The Pashov X-Ray, Solidity Auditor, Fizz, Fizz Convert, and Fizz Sync skills
remain upstream-owned security siblings. Warden reads the applicable upstream
contracts by path; Hexaemeron does not rewrite or absorb them. Domain work such
as gas optimisation, credit laws, evidence preservation, or source chunking
stays with Hermes, Pandects, Lazarus or Alexandria, and Lemma respectively.

Synkrisis sits outside the delivery controller. Its four operations compare
validated observations from several runs, emit bounded findings and a fixed
report, and verify the path from the original inputs. It cannot select work,
steer a worker, file an issue, or dispatch Fiat.

One explicit Fiat request takes a topic through a study and runbook, then
implements, audits, documents, pushes, and integrates each runbook step. The
steps stack and the complete stack lands on the base in one merge. Every phase
leaves a receipt in a hash-chained ledger inside a dedicated worktree, so the
same local run can be verified and resumed after context loss.

Named for the six days of ordered creation from a void to finished work,
then rest. The entry skill is `fiat`, so the invocation is
`/hexaemeron:fiat` and a fresh run's first words are the line above.

## HOW IT WORKS

Let there be light. A deterministic controller (`hexctl`) decides what comes next and refuses to advance without a receipt; state and a hash-chained ledger survive context resets, so resume is the same command.

1. Study the topic and write a linted study file.
2. Derive a runbook of discrete, self-contained steps.
3. Implement the checked candidate bound into the runbook, one step at a time.
4. Run the vendored Pashov suite (`x-ray`, `solidity-auditor`, `fizz`) in rounds until a round comes back clean or the remaining leads are judged not worth another pass, shape each audit record through Sapheneia, and put fixes on a stacked branch.
5. Rewrite every shipped document and the PR text through the bundled `imprimatur` lint and `vulgate` voice mask.
6. Push the step branch, open its pull request against the step below it, and move to the next step.
7. Once every step is pushed, merge the stack into the run branch in order, receipt one signed base sync if concurrent work created an integration conflict, then merge the run branch into the base once.

A run works on one integration branch cut from the base. An issue-free run uses
`fiat/<run slug>`. When a known task issue is supplied during initialization,
the branch uses `fiat/<issue>-<run slug>` and every step branch keeps that
prefix. Each step's pull request targets the step below it, step 1 targets the
run branch, and nothing merges until the whole stack is ready. The base sees
exactly one merge per run.

## WHAT IT SHIPS

- the executable [`hexctl.py`](./skills/fiat/scripts/hexctl.py) controller with a tamper-evident ledger (`verify` proves both chain and state);
- the [`imprimatur`](./skills/imprimatur) three-tier prose lint and the [`vulgate`](./skills/vulgate) voice mask, invokable on their own;
- [`kronos`](./skills/kronos), which ranks eligible held frontier jobs and loops complete Fiat runs until none remain;
- the phase disciplines, of which six ship an executable check: [`protasis`](./skills/protasis) on what a study and runbook must answer and whether the evidence due for their chosen design is present, [`elenchus`](./skills/elenchus) on the root cause of a failure that already happened, [`phylax`](./skills/phylax) on the off-chain surface, [`ephoros`](./skills/ephoros) on what a step emits once it runs unattended, [`metron`](./skills/metron) on every measurement except gas, and [`hypomnema`](./skills/hypomnema) on what gets recorded and where;
- the Pashov Audit Group suite vendored verbatim (MIT; `LICENSE` and `NOTICE.md` in each skill directory);
- Codex metadata for explicit or automatic invocation; and
- the controller, contract, practice-check and lint test suite, plus a fuzz-audit log ([`audit/AUDIT.md`](./audit/AUDIT.md)) covering the controller's own surfaces.

## DAY TO DAY

**Developers.** A half-formed idea and a week to find out whether it holds. Hexaemeron turns it into a study, a runbook of discrete steps, and one pull request per step. Each directive carries a source-bound agent packet; each Fiat-created commit is verified locally, and pushed ranges and merge SHAs must carry GitHub's valid verification before their receipts advance.

**Security and audit.** You want the Pashov suite over a contract and nothing else. `x-ray`, `solidity-auditor` and `fizz` are vendored whole and run on their own, without taking on the loop around them.

**Marketing.** A launch post reads like a machine wrote it. `imprimatur` says what is wrong with it across three tiers and `vulgate` rewrites it in house voice. Neither needs the controller, and neither needs installing separately.

**Business development.** An integration document has to be accurate about what the protocol does and readable by someone who is not an engineer. The study phase produces the first and the prose masks produce the second.

## THE SHAPE OF A RUN

| Day | Phase | What happens |
| --- | --- | --- |
| 1 | `study` | Study the topic; write `.hexaemeron/study.md` to `protasis`'s contract, linted |
| 2 | `runbook` | Divide the work into steps that meet `protasis`'s schema: discrete, self-contained, provable exits |
| 3-4 | `implement` | Build the step, least mental load that satisfies the runbook |
| 5 | `audit` | The vendored Pashov suite in rounds until clean or reasoned out; every round requires `--audit-filter sapheneia:sapheneia`; non-Solidity rounds run the `phylax`, `ephoros` and `hypomnema` lints; fixes on a stacked branch |
| 6 | `prose` | `hypomnema` decides what gets recorded, then the `imprimatur` lint and the `vulgate` mask, on every document and the PR text; a bound task issue also gets its closing-comment draft |
| rest | `push` | Stage and commit the final diff, push the step branch, and open its stacked pull request |
| -- | `integrate` | Merge the stack into the run branch in step order, then the run branch into the base once, and close the task issue |

Days 3 through the rest repeat per step. The sixth day makes the prose in
a human image, which is roughly the joke the name is carrying.

## USAGE

```text
/hexaemeron:fiat "borrowing-base covenant hook for V2.5"   # start
/hexaemeron:fiat --base release/v2.5 "..."                  # start from a ref
/hexaemeron:fiat --task-issue https://example.test/issues/438 "..." # bind a known issue
/hexaemeron:fiat                                            # resume
/hexaemeron:fiat status                                     # report
/hexaemeron:kronos                                          # rank and run frontier jobs until none remain
```

Kronos is the small loop around Fiat. It scores every eligible held frontier
out of 100, sends the best one through a complete Fiat run, then ranks again.
The name carries the old Kronos/Chronos knot: sickle for the ripest job, clock
for keeping the sequence moving.

> Highest first, then Fiat runs.
>
> Kronos cuts till work is done.

The run stops on its own only for a decision that belongs to a human: the
audit loop hit its round cap with findings still open, a push was
refused, or a Solidity repo is missing its security-suite receipt.
Everything else proceeds.

## THE CONTROLLER

`skills/fiat/scripts/hexctl.py` sequences the run. The model does the work;
the controller decides what comes next and refuses to advance without a
receipt. State sits in `.hexaemeron/` (self-gitignored) beside an
append-only ledger where every entry hashes over the one before it. Before any
state-backed command reads further, the controller checks the required
version-1 container spine in deterministic order and refuses a missing or
wrong-kind container with a value-free path-and-kind diagnosis.

```text
hexctl init --topic <topic> [--task-issue <url>]  # start; bind a known issue before branch creation
hexctl next                 # the single next action, as JSON
hexctl status [--json]      # where the run is
hexctl done <phase> ...     # receipt a phase; validation lives here
hexctl audit-round --audit-filter sapheneia:sapheneia ... # record one shaped security round
hexctl record <key> <val>   # named receipts (resolved suite, run context)
hexctl halt / resume        # put a stop itself on the ledger
hexctl reset                # archive a completed run and clear active state
hexctl verify               # check state shape, then prove chain and state integrity
```

`init --task-issue <url>` stores the exact issue URL in the initial transition
and puts its positive issue number first in the automatic run branch. The
complete issue-bearing slug keeps the existing 48-character limit. An exact
override must start with `fiat/<issue>-`. A late first issue receipt is refused
rather than renaming a stored branch; issue-free and legacy names stay
unchanged.

`init` creates a dedicated git worktree for the run, under `tmp/fiat/`, and the
run works there for its whole length. The checkout it was started from is never
checked out, never branched, and never left on a branch the run created, so a
run can start against a tree somebody is standing in with uncommitted work. That
checkout keeps one breadcrumb line per live run, and `status` or `next` there
name the tree and the exact `--dir` to use. A target that is not a repository, an
occupied or escaping path, a branch already checked out, or a failing
`git worktree add` each refuse by name before anything is written; there is no
in-place fallback. `reset` archives a completed run into the origin checkout and
removes the tree when git can do it without force, keeping any tree that holds
work.

Mutating commands hold a kernel lock for their whole run. Separate runs get
separate trees and separate state, so the lock only bites when a second agent
enters one run's tree; a second writer is refused with the first process's details, and
`next`, `status`, and `verify` still answer. The operating system releases the
lock if the holder crashes, so a stale metadata file never needs manual cleanup.

The receipts are opinionated where the process is: the audit phase will not
open without a resolved (or explicitly waived) security suite; it will not
close with findings open unless a reasoned no-further-leads verdict is
recorded; every round records the exact checked operator declaration
`--audit-filter sapheneia:sapheneia`, which is not semantic proof of the pass;
a prose receipt missing either configured skill is rejected; and a push receipt
requires the final head and a pull request aimed at the step below it in the
stack, and refuses a merge commit outright. It does adopt one it observes: a
pull request already merged into that base is receipted when the recorded head
still matches and the merge is reachable from the base, and the step is then
completed from that record instead of merging again, provided the run branch
carries the work. Merges the run performs are the integrate phase's
business: the controller hands them out one step at a time, in order, and the
run is not done until the run branch has landed on the base and any recorded
task issue is closed. Its closing comment follows Sapheneia, Imprimatur,
Vulgate, and an Imprimatur re-lint, then is posted verbatim and read back. Fiat
creates no GitHub issue unless the user or target repository requires one.

## SKILL VERSIONS AND THE STOPPING RULE

The first-party Fiat, Imprimatur, Vulgate, and Kronos skills keep an
`EVOLUTION.md` ledger beside `SKILL.md`. Labels use
`{skill}-v{evolution}.{generation}.{epoch}`: evolution counts completed
frontier advances, generation counts meaningful behavioural changes, and
epoch marks a rare compatibility or provenance boundary. These are governed
by `skills/VERSIONING.md`; they are not SemVer and do not change invocation
names.

A held Next Fiat job changes only after that exact frontier job completes.
Once a capable review finds that another pass has no concrete chance of
material improvement, the ledger becomes `mature`, its next job becomes
`None -- mature`, and Fiat refuses further frontier runs. A different rewrite
or another model's curiosity is not grounds to keep seasoning it.

## AUDIT SYNOPSES

Fiat keeps each audit source authoritative and commits a bounded deterministic
read view beside it. A legacy `**/audit/AUDIT.md` uses
`AUDIT_SYNOPSIS.md`. A direct `audit/rounds/<run>.md` source uses
`<run>.synopsis.md`, so several runs can share the directory without replacing
one another. Synopsis files are excluded from source discovery, and duplicate
destinations refuse the whole plan before a write. Refresh or check every
discovered pair from the repository root:

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --write .
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
```

`fiat-audit-synopsis/v1` has one metadata line and one physical line per raw
H2. An unescaped `<br>` separates retained source lines; `%b` encodes a literal
`<br>` and `%%` encodes a literal `%`. The renderer's
`decode_synopsis_record()` reverses that framing exactly. The metadata binds
source path, source SHA-256 and H2 count; records retain strict fields,
canonical findings, recognised legacy risk tables, and every physical
`Leads not pursued` occurrence with its remaining section. Missing legacy
values stay missing. Explicit `fiat-audit-round/v1` records keep their
topic-bearing heading; new per-run records use `fiat-audit-round/v2` and a
path-bound `Step` heading. Discovery excludes nested Git
repositories and worktrees, including active Fiat trees below `tmp/fiat/`.
The CLI refuses symlinks, escape, invalid UTF-8, non-LF line endings, sources
or rendered views over 16 MiB, more than 10,000 H2s, source lines over 1 MiB,
and views that fail the strict 15% integer line budget. `--write` uses a
flushed same-directory temporary, atomic replacement, cleanup and exact
post-write read. It has no network, shell, dependency, or generation clock.

## CONFIGURATION

`hexctl config get <path>` reads every path. After `init`, `config set` may
change only the exact `audit.log_path` leaf, the `git` section, or a path below
`git`. Every other write is refused before value parsing or a ledger append.

| Path | Default | Mutable after `init` | Meaning |
| --- | --- | --- | --- |
| `skills.prose_lint` | `hexaemeron:imprimatur` | no | Bundled lint the prose receipt demands |
| `skills.voice` | `hexaemeron:vulgate` | no | Bundled voice mask the prose receipt demands |
| `skills.security` | the vendored Pashov ids | no | Intent only; the ids the `security_suite` receipt records at preflight |
| `audit.max_rounds` | `8` | no | Rounds before the controller forces a verdict |
| `audit.stacked_suffix` | `--audit` | no | Fix branch: `<step-branch>--audit` |
| `audit.fold` | `false` | no | Whether a legacy run folds the stacked audit branch on close |
| `audit.log_path` | `audit/rounds/<flattened run branch>.md` | yes | Where this run's rounds append; `init` derives it, and an override may move the directory but must keep the file name, so no two runs share a record |
| `git.base` | `main` | yes | Starting ref, and the only branch a run merges into |
| `git.run_branch_prefix` | `fiat/` | yes | Run branch is this plus the topic slug, or `<issue>-<topic slug>` when `init --task-issue` binds a known issue; an exact override must keep that issue prefix |
| `git.draft_pr` | `false` | yes | Whether a run asks for draft pull requests |
| `solidity` | `auto` | no | Classify the round from the `security_suite` receipt; older recorded boolean overrides remain readable |

The Pashov suite -- `x-ray`, `solidity-auditor`, and `fizz` -- is based on
https://github.com/pashov/skills tag `v28062026` under the MIT licence. Each
`NOTICE.md` records the local distribution changes. The copies keep their
upstream instructional register; Wildcat's house prose lint does not rewrite
third-party source solely for style. Credit: Pashov Audit Group,
https://www.pashov.com/. Preflight records the bundled ids in the
`security_suite` receipt; the controller gates on the receipt, not the config,
so a stale config cannot fake a suite. Prose-free or Solidity-free runs record
a waiver instead.

## THE SKILLS EACH PHASE IS HELD TO

The standards each phase is held to are carried by their own skills, and each
runs on its own outside the loop. `protasis` says what a study and a runbook must answer.
`elenchus` works an observed failure down to its cause and guards it.
`phylax` holds the off-chain surface: input, subprocesses, fetched hosts,
secrets, dependencies and model output. It also ships the synthetic
job-scoped model proxy component and its digest-bound fourteen-row conformance
command. That proof leaves the JobSpec acceptance receipt, launch receipt,
live provider, public pilot and #702 Fiat integration/end-to-end digest join
open. `ephoros` chooses
what a step emits once it runs unattended. `metron` refuses a performance
change without a recorded before and after. `hypomnema` decides which
decisions earn a written reason and where each record lives. Each carries its
own `EVOLUTION.md`, so Kronos ranks their frontiers alongside the rest.

## THE PROSE MASKS

Everything the loop needs ships in the plugin; it stands alone. The two
prose masks are vendored, not referenced: `imprimatur` (a three-tier lint
over the tells that mark prose as machine-written) and `vulgate` (a voice
mask that renders text into a plain human register) live under `skills/`
and can be invoked on their own, outside the loop, whenever a draft needs
the treatment. Edit the lexicon in place when a term needs adding.
Upstream attribution for the absorbed lint material sits in
`skills/imprimatur/NOTICE.md`. Fiat never bypasses a gate, but once the gates
pass it merges its own PR and closes its own task issue rather than leaving
routine publication work behind. It reads the task-issue comment and closed
state back from GitHub; the closure receipt does not attest the prose passes.

## AGENTS

The four workers isolate bulky phases without inheriting controller authority:

- **Surveyor** receives one brief naming the topic, target, base, and output.
  It researches and writes the study, then reports the path and summary.
- **Mason** receives one exact runbook step plus `branch` and `branch_from`.
  It builds and tests that step on those refs, signs its commits, and stops
  before push or receipt.
- **Warden** receives one audit round, the exact risk register and runbook step,
  the step branches, audit path, and tool paths. It runs the applicable suite,
  records findings, fixes them, and returns the exact Elenchus verdict.
- **Scribe** receives the sorted prose diff, PR base and draft path. It runs
  Imprimatur, applies Vulgate with content held fixed, reruns Imprimatur, and
  returns the file count and skill identities.

Fiat can do the same packet inline when isolated workers are unavailable. It
alone receipts their results and chooses the next directive. The current open
frontier is the visible identity of a reused worker handle: callers must reject
one that still names an older issue, step, or role.

## TESTS

```text
python3 tests/run_tests.py
```

The tests cover the controller and Fiat contract: phase ordering, ordered
state-container validation, completed run archival and reset, audit-filter
gating and round caps, fixes evidence, task-issue comment publication, prose
skill enforcement, halt/resume, ledger
tamper detection, concurrent writer exclusion, crash recovery, and the
Wildcat marketplace boundary.
