---
name: fiat
description: >
  Run the one-shot delivery loop: study, runbook, then per-step
  implement/audit/prose/push until a working prototype exists.
  Use only when a Wildcat contributor explicitly asks to start, run, resume,
  or report a Hexaemeron or Fiat delivery, including /hexaemeron:fiat forms.
  Do not infer activation from a similar task.
metadata:
  version: "5.31.1"
---

# Fiat

## Where this sits

Fiat owns the delivery controller, not Hexaemeron's bundled audit or prose
skills. Its version, held frontier, next job, and maturity state live in
[EVOLUTION.md](EVOLUTION.md). Read that ledger before suggesting, starting, or
resuming work intended to advance Fiat itself.

**Current frontier.** The ledger above is authoritative. Never substitute
Hexaemeron's plugin-wide Solidity frontier for Fiat's own held target.

## Phase skills

Six sibling skills carry the loop's content contracts; Fiat runs the loop and
defers to them rather than restating their rules. Each slots in as follows:

| Skill | Slots into | Carries |
| --- | --- | --- |
| [protasis](../protasis/SKILL.md) | study and runbook phases | what a study must answer, what a runbook step must contain, when a topic decomposes first |
| [phylax](../phylax/SKILL.md) | implement phase | the boundaries a step introduces and the control each needs |
| [ephoros](../ephoros/SKILL.md) | implement phase | what the step must emit once it runs unattended |
| [metron](../metron/SKILL.md) | implement phase | refusal of any speed-motivated change without a recorded before and after |
| [elenchus](../elenchus/SKILL.md) | implement phase and audit rounds | any failure surfaced mid-step or mid-round, worked to its cause |
| [hypomnema](../hypomnema/SKILL.md) | prose phase | what the step records and where it lives, before the masks run |

Their lints run in every audit round, so meeting them during the step is
cheaper than meeting them in the round. The phase notes below say how each one
is applied.

Let there be light.

Drive the whole loop from durable controller state, never from conversation
history. The controller emits one directive at a time; do the work it names,
receipt it, ask for the next one. A phase without a receipt did not happen.
Every state-backed command first validates the required version-1 container
spine in deterministic order. A missing or wrong-kind container stops with one
value-free path-and-kind diagnosis before a reader or writer can traverse it.

Resolve paths from the exact `SKILL.md` file that activated Fiat. Do not
resolve them from the target repository, the shell's current directory, the
GitHub URL, or a guessed plugin-cache version.

Before the first controller call:

```text
FIAT_SKILL_FILE=<exact path of the active fiat/SKILL.md>
FIAT_SKILL_DIR=<real parent directory of FIAT_SKILL_FILE>
PLUGIN_ROOT=<real directory two levels above FIAT_SKILL_DIR>
PROJECT_ROOT=<real root of the user's target repository>
```

Fail closed if `FIAT_SKILL_DIR/scripts/hexctl.py` is not a file. Sibling
skills live at `PLUGIN_ROOT/skills/<name>/`, which is where `protasis`,
`elenchus`, `phylax`, `ephoros`, `metron` and `hypomnema` resolve from.

Controller:

```text
python3 "$FIAT_SKILL_DIR/scripts/hexctl.py" --dir "$PROJECT_ROOT" <cmd>
```

Alias it as `hexctl` mentally; every command below means that invocation.

## The run's worktree

`init` creates a dedicated git worktree for the run and works in it for the
whole run. Point `--dir` at the target repository once, at `init`, and at the
worktree it prints for everything after that. The operator's checkout is never
checked out, never branched, and never left on a branch the run created, so a
run can start against a checkout somebody is standing in with uncommitted work
of their own.

- **Where it lives.** `tmp/fiat/<run branch with separators flattened>` under
  the repository root. One run maps to one directory. The home ignores itself,
  so it never shows in the checkout's `git status`.
- **Where state lives.** `.hexaemeron/` inside the worktree, beside a
  hash-chained ledger, with its own `.gitignore` so git never sees it. The
  checkout keeps one breadcrumb line per live run at `.hexaemeron/worktree`, so
  `status` and `next` run there name the tree and the exact `--dir` to use.
- **Fail closed.** A target that is not a git repository, a derived path that is
  occupied or escapes the repository, a run branch already checked out
  somewhere, or a failing `git worktree add`, each refuse by name before any
  state, ledger or breadcrumb is written. There is no in-place fallback.
- **Cleanup.** `reset` archives a completed run into the checkout it was started
  from, then removes the tree when git can remove it without force. A tree
  holding work is kept and named instead. Nothing is ever forced. Retirement is
  not at `integrate`, because `status` and `verify` still have to read the run
  after it reports done.

Mutating commands hold a kernel lock for their whole run. Separate runs get
separate worktrees and separate state, so the lock only bites when two agents
share one run's tree; if that happens, `hexctl` names the holder and either wait
or start a separate run. `next`, `status`, and `verify` remain available while
the writer runs, and a crashed process releases the lock without manual cleanup.

## Day to day

**Developers.** A half-formed idea and a week to find out whether it
holds. Hexaemeron turns it into a study, a runbook of discrete steps,
and one pull request per step, with the audit suite run against each
before it is pushed.

**Security and audit.** You want the Pashov suite over a contract and
nothing else. `x-ray`, `solidity-auditor` and `fizz` are vendored whole
and run on their own, without taking on the loop around them.

**Marketing.** A launch post reads like a machine wrote it. `imprimatur`
says what is wrong with it across three tiers and `vulgate` rewrites it
in house voice. Neither needs the controller, and neither needs
installing separately.

**Business development.** An integration document has to be accurate
about what the protocol does and readable by someone who is not an
engineer. The study phase produces the first and the prose masks produce
the second.

## Start or resume

1. If the user passed `status`, run `hexctl status` and report. Stop.
2. Apply the frontier maturity gate below. This happens before `init` and
   before resuming an existing frontier run.
3. If `.hexaemeron/state.json` exists, run `hexctl verify`, then
   `hexctl status --json`. If its phase is `done`, run `hexctl reset` to
   archive the completed run, then continue immediately as a new run at step
   4. Do not ask the user to remove, rename, or approve resetting completed
   state. If the phase is not `done`, this is a resume: enter the loop and
   treat the validated state file as canonical. A run arriving as a
   checkpoint zip verifies first, per the `Step checkpoint` section of
   [push-discipline.md](references/push-discipline.md).
4. Otherwise: say exactly `Let there be light.` and nothing else before it,
   run the read-only preflight checks below, then bring the base up to date
   before anything is cut from it, then `hexctl init --topic "<topic>" --base
   <ref>`, record the post-init receipts, and enter the loop. If a task issue is
   already known, use `hexctl init --task-issue <url> --topic "<topic>" --base
   <ref>` so the issue is bound before branch creation.
   `--base` defaults to `main`; honour any branch, repo, or commit the user
   named as the starting point. `init` also names the run branch, printed and
   held in state: one integration branch for the whole run, cut from the base.
   `init` cuts it, in the run's own worktree, so nothing needs creating by hand;
   push it before the first step. An issue-free automatic name remains
   `fiat/<topic slug>`. A known
   issue produces `fiat/<issue>-<topic slug>`, with the complete issue-bearing
   slug limited to 48 characters so the leading number survives truncation.
   Pass `--run-branch <name>` only when the user wants an exact override. With
   `--task-issue`, that override must start with `fiat/<issue>-`.

**Sync the base first.** A run inherits every mistake in the ref it was cut
from, and a local checkout that has been sitting is the normal case rather than
the exception:

```text
git fetch origin
git status --short                     # must be clean
git checkout <base> && git merge --ff-only origin/<base>
git rev-parse HEAD                     # record this; it is the run's real start
```

Fast-forward only. If the base will not fast-forward, the local branch has
commits the remote does not, and that is a question for the user rather than
something to merge or rebase past on the way to starting work. If the tree is
dirty, stop: uncommitted work belongs to whoever left it there, and it would
otherwise ride into the first step's commit under this run's provenance. Cut the
run branch from the synced base, and state the starting SHA in the study's
constraints so the spec and the branch agree about where the run began. Skipping
this is how a study cites a starting ref that is a hundred commits behind the
work it is about to build on.

## Frontier maturity gate

Apply this gate only when the requested run is meant to advance a skill's
declared frontier. Ordinary product or repository delivery still uses Fiat
without pretending that it changes Fiat or another skill.

1. Read the target skill's `EVOLUTION.md` and the shared
   [versioning contract](../VERSIONING.md).
2. If its frontier status is `mature`, refuse to start or resume. Do not
   suggest another Fiat run. A new run is allowed only after the ledger
   records an epoch reopening backed by a new failure, requirement,
   dependency change, or equivalent external evidence.
3. If the status is `open`, compare the held next job with current evidence.
   If its acceptance condition is already met or another pass would only
   produce stylistic, speculative, or interchangeable changes, do not start
   the controller. Report that the frontier should close; do not overseason
   the skill to manufacture work.
4. At the end of a completed frontier job, update the ledger exactly once:
   increment evolution, retain generation and epoch, and either record one
   evidenced next job or set `Frontier status` to `mature` and `Next Fiat
   job` to `None -- mature`. A normal Fiat delivery does not touch skill
   versions or frontier text. The contract also states what every frontier run
   owes before it is recorded as done, whichever plugin the skill sits in; read
   it there rather than expecting the held job to spell it out.

**Make step 4 mechanical.** Name the ledger at `init` and the controller holds
the run to it:

```text
hexctl init --topic "<topic>" --base <ref> \
  --frontier plugins/<plugin>/skills/<skill>/EVOLUTION.md
```

`init` records that file's digest and row count, and `done integrate` refuses
until it carries exactly one new row valid under the versioning contract: the
axis arithmetic, the digest recomputed over the frontier line the row describes,
the header and the row naming the same version, a generation holding the prior
revision and digest, and a mature status carrying no next job. Each refusal names
which of those failed.

Pass it whenever the run is meant to advance a frontier. Leave it off for
ordinary delivery, where there is no ledger row to owe. If the job turns out not
to close after all, `hexctl halt --reason ...` puts that on the ledger; the gate
refuses a silent finish, not a recorded stop.

If that frontier run also has a known task issue, add `--task-issue <url>` to
the same `init` command. The issue and frontier receipts then share the initial
state transition.

## Preflight (new runs only)

1. Run the fail-silent contributor and marketplace check in
   [wildcat-marketplace.md](references/wildcat-marketplace.md). Do not announce
   the check. Use an already-authenticated local GitHub account when available;
   a GitHub connector is optional and must not be treated as the only access
   path. A failed or unavailable check changes nothing and must not be
   mentioned. A successful check records only the non-identifying
   `labs_marketplace` receipt, acknowledges the contributor, and names the
   other marketplace plugins one by one with their likely fit. Do not install
   a plugin at this point.
2. Confirm `git` and `gh auth status` work in the target directory. Resolve
   the repository from the current directory and the user's named target;
   never substitute an organisation or clone a different repository merely
   because its name looks related. Every receipt reads GitHub over REST, so a
   proxy or environment that serves the REST API without GraphQL can still
   receipt a run. A read that never arrived says so in its own words, and it
   is not a statement about whether the commits are verified.
3. `init` observes this controller's own currency and refuses a proven-behind
   pin by name, before any run state exists. On that refusal, re-pin through
   the host's own installer, refresh, and re-resolve the paths, per
   [plugin-currency.md](references/plugin-currency.md); where that cannot
   happen, rerun init with `--controller-currency-waiver '<reason>'`, which
   records the verdict and reason in the init receipt. Treat an `unknown`
   currency warning, or the warning that this controller is older than a Fiat
   checked into the target repository, the same way. Do not run the loop
   under a controller you have noticed is behind and said nothing more about:
   the rules it does not enforce leave no trace, because a flag it rejects is
   indistinguishable from a rule nobody wrote.
4. The prose masks ship inside this plugin: the `imprimatur` lint (a script
   at `$PLUGIN_ROOT/skills/imprimatur/scripts/imprimatur.py`) and the
   `vulgate` voice mask (rules at `$PLUGIN_ROOT/skills/vulgate/SKILL.md`).
   Nothing to resolve.
5. The security suite is vendored in this plugin: the Pashov `x-ray`,
   `solidity-auditor`, and `fizz` skills sit under `$PLUGIN_ROOT/skills/`.
   After init, record the bundled ids:
   `hexctl record security_suite
   '["hexaemeron:x-ray","hexaemeron:solidity-auditor","hexaemeron:fizz"]'`.
   If the run will produce no Solidity and no suite applies, record a waiver
   instead: `hexctl record security_suite '"waived: <reason>"'` -- and say so
   out loud. Never claim a tool ran when it did not.
6. If the user supplied a task issue or a higher-priority target-repository
   rule required one, pass its exact URL to `init --task-issue <url>`. Do not
   invent an issue. A first `task_issue` record after initialization is refused
   because the stored branch might already be published; an exact repeat of the
   initial receipt is a no-op.
7. Nothing else.

## Branches, stacks, and the one merge

A run is one integration branch off the base and a stack of step branches on
top of it. An issue-free run uses `fiat/<topic slug>`. An issue-backed run uses
`fiat/<issue>-<topic slug>`, and an explicit override must keep the exact
`fiat/<issue>-` prefix. The controller stores that run branch once and prefixes
every derived step branch with it; it never reparses the issue or renames a
stored branch. Take every branch and pull request base from the directive rather
than inventing a name.

```text
main ─── <run branch>                                     the run branch
          └── <run branch>-step-1-<slug>                  PR -> run branch
               └── <run branch>-step-2-<slug>             PR -> step 1
                    └── <run branch>-step-3-<slug>        PR -> step 2
```

Each step branches from the step below it and its pull request targets that
same branch, so a reviewer sees one step's diff and nothing else. Step branches
are siblings of the run branch, never nested under it: git cannot hold
`fiat/x` and `fiat/x/step-1` as refs at once.

Nothing merges while the steps run. The stack stays open, each pull request
reviewable on its own, until every step is pushed. Then the `integrate` phase
merges the stack into the run branch in step order and merges the run branch
into the base exactly once. One merge into `main` per run, at the end, carrying
the whole delivery.

## The loop

Repeat until `next` returns `done`, `halted`, `blocked`, or `audit-verdict`:

```text
hexctl next
```

Act on the single directive it prints, then receipt it. The directory:

| `do` | Action | Reference | Receipt |
| --- | --- | --- | --- |
| `study` | Research the topic; write the study | [protasis](../protasis/SKILL.md) | `done study --artifact <path> --skills <csv>` |
| `runbook` | Derive discrete steps from the study | [protasis](../protasis/SKILL.md) | `done runbook --artifact <path> --steps-file <path>` |
| `implement` | Build the step, simplest construction that satisfies the runbook | [protasis](../protasis/SKILL.md) | `done implement --branch <name> --commit <sha> [--tests <summary>]` |
| `audit-round` | One security round: run the suite, shape and log its record, fix on the stacked branch | [audit-loop.md](references/audit-loop.md) | `audit-round --findings <n> --audit-filter sapheneia:sapheneia [--log <path>] [--fixes-commit <sha> --elenchus-verdict <value>]`, plus `--phylax-exit`, `--ephoros-exit` and `--hypomnema-exit` on a non-Solidity round |
| `close-audit` | Last round was clean; close the phase | [audit-loop.md](references/audit-loop.md) | `done audit [--fixes-ref <ref>]` |
| `resolve-security-suite` | Suite receipt missing; resolve or waive | preflight step 4 | `record security_suite ...` |
| `prose` | Rewrite every prose artefact and draft the PR text | [prose-pass.md](references/prose-pass.md) | `done prose --files <n> --skills <csv>` |
| `push` | Stage and commit final changes, push the step branch, open its stacked PR against `pr_base`, and leave it open | [push-discipline.md](references/push-discipline.md) | `done push --pr-url <url> --head-commit <sha> --pr-base <ref>` |
| `merge-step` | Merge the named step's PR into the run branch, bottom of the stack first | [push-discipline.md](references/push-discipline.md) | `done merge-step --step <n> --merge-commit <sha>` |
| `sync-run` | When the base advanced and the integration PR conflicts, preserve the completed product evidence and receipt a signed two-parent merge plus bounded integration revalidation; supersede a failed composition receipt only with the exact active SHA, a reason and fresh evidence | [push-discipline.md](references/push-discipline.md) | `done sync-run --commit <sha> --base-commit <sha> --revalidation .hexaemeron/integration-revalidation.json [--supersede-sync <sha> --reason <text>]` |
| `integrate` | Open and merge one PR from the run branch into the base, name what the run leaves unfinished in `.hexaemeron/run-pr.md`, then clean up and close any recorded task issue | [push-discipline.md](references/push-discipline.md) | `done integrate --pr-url <url> --merge-commit <sha> [--closed-issue-url <url>]` |
| `audit-verdict` | Max rounds hit with findings open | ask the user | `done audit --no-further-leads --reason ...` or `halt --reason ...` |
| `blocked` | A receipted study or runbook amendment broke the current step; inspect it, halt, or use the runbook repair below | below | -- |
| `halted` | Report the reason; wait for the user | -- | `resume --note ...` when cleared |
| `done` | Final report | below | -- |

Read the named reference before working a phase for the first time in a run.
The receipt command is the boundary: if it exits non-zero, the phase is not
done -- fix what it complained about rather than arguing with it.

After a successful `done study` receipt, the study is the completed spec. If
the `labs_marketplace` receipt exists, perform the post-spec reassessment in
[wildcat-marketplace.md](references/wildcat-marketplace.md) before asking the
controller for the runbook directive. This is the first point at which a
missing marketplace plugin may be installed. Refresh skills only after all
selected installs finish; resume in a new chat when the host requires one.

## Phase notes

**Study and runbook.** `protasis` is the content authority: what a study must
answer, what a runbook step must contain, and when one topic needs decomposing
first. Fiat keeps the mechanics. The study goes to `.hexaemeron/study.md` and
the runbook to `.hexaemeron/runbook.md` beside `.hexaemeron/steps.json`, a JSON
list with one entry per step in order, as strings or `{"title": ...}` objects.
Run the `imprimatur` lint on each artefact before receipting it, and pass the
skills that ran to the receipt. Repo copies are committed later, in step 1 of
the runbook, after the prose pass.

**Amending receipted specifications.** After the study and runbook receipts exist,
and only while build steps are active, append one final dated Protasis
amendment to the receipted study and run:

```text
hexctl amend study --artifact <candidate>
```

The candidate keeps the currently receipted study bytes as its exact prefix.
Its suffix is one `### Amendment -- YYYY-MM-DD` block with `What changed`,
`Why`, `Steps touched`, and `Still holding` fields, in that order. The last
field contains one exact verdict for every current or pending step:
`Step N: entry holds|broken; exit holds|broken.` The command checks the whole
candidate with the bundled Protasis checker, copies captured candidate bytes
to the canonical study path through a recoverable write-ahead transaction,
records the prior, new, and amendment digests with bounded step verdicts in
state and the ledger, and re-pins the study receipt. A pending transaction
blocks every other controller command; rerun `amend study` against the
canonical study to finish or roll back the labelled transition. The command
does not establish that the amendment is true or that a holding verdict is
correct.

Arbitrary drift, an edited prefix, a malformed block, incomplete or ambiguous
step verdicts, a checker failure, an unsafe or oversized path, and an attempt
outside the steps phase leave the current receipt unchanged. A broken entry or
exit verdict for the current step is recorded, then `next` returns a durable
blocked directive and step receipts refuse to advance. Inspect the amendment,
halt the run, or use a separately specified runbook-repair transition; do not
resume dependent work by editing state or repeating `done study`.

A runbook correction uses the same dated four-field suffix and runs:

```text
hexctl amend runbook --artifact <candidate>
```

The candidate keeps the currently receipted runbook bytes as its exact prefix.
`What changed` consists only of one or more complete replacement clauses in
the form `Complete replacement Exit: <full value>`, using one of the six
runbook field names. A changed Exit includes its replacement command, and a
changed Tests field includes its complete runner contract. The suffix may not
add, remove, duplicate, reorder, renumber or rename a step. It may touch only
current or pending steps and carries one exact entry-and-exit verdict for every
unbuilt step.

The receipt records the prior, new and amendment digests, exact amendment byte
offsets, date, touched steps, ordered verdicts, replacement field names and the
current study digest under `amend:runbook`. `verify`, `status` and delegated
packet construction recompute both receipted artefacts and the amendment
history. This establishes byte continuity, shape and carriage. It does not
establish that a replacement is semantically complete, correct, or likely to
pass.

Each write-ahead marker names either `study` or `runbook`. One pending subject
blocks every other command until its exact amend command finishes or rolls it
back. If both markers exist, recovery refuses without removing either. Study
markers written before the subject field existed remain readable as study
transactions.

Mason and Warden receive the same effective step source: one numbered and
titled baseline block, its digest, and every current-study-bound amendment
that names the step, in receipt order with exact bytes and digests. The last
baseline step ends before the first real amendment heading. Fenced decoys,
unrelated or stale amendments, mismatched history and later unreceipted bytes
do not enter the packet.

A broken runbook verdict blocks the current step. A holding runbook amendment
clears a broken study verdict only when it names the current step, carries at
least one complete replacement field and records the current study digest. A
later study amendment changes that digest, so an older repair no longer
applies. Recovery remains another checked amendment or an explicit halt; state
and ledger history are not edited to manufacture a holding result.

**Implementation.** Pick the construction that takes the least effort to
comprehend, then stop. The step runs under the phase skills: `phylax` names
the boundaries the step introduces and the control each needs, `ephoros` names
what it must emit once it runs unattended, `metron` refuses any change made in
the name of speed without a recorded before and after, and a failure worked
mid-step follows `elenchus` rather than a guess. Their lints run in every
audit round, so meeting them here is cheaper than meeting them there. The runbook step is the yardstick: reread it before
declaring the step complete, and do not add anything it does not ask for.
The `implement` directive carries `branch` and `branch_from`: cut that exact
branch from that exact ref. Step 1 branches from the run branch, every later
step from the step below it, so each step builds on the reviewed tree of the
one before without waiting for a merge.

**Audit.** `elenchus` works any failure a round surfaces down to its cause.
The longest phase by design. One round is the full suite: `x-ray`
first, then `solidity-auditor`; when the step ships Solidity under Foundry or
Hardhat, `fizz` builds or refreshes the invariant fuzz suite and its campaign
results count as part of the round. Read each skill's SKILL.md from
`$PLUGIN_ROOT/skills/<name>/` and follow it. Every finding is logged
to the audit file, fixes committed to the stacked branch. Warden receives the
exact source-bound runbook step and uses its test command, report format, and
report file for any fix. A round supplying `--fixes-commit` also supplies one
exact `--elenchus-verdict`: `guarded`, `unguarded`, `passed`, or
`inconclusive`. Fiat checks and records that declaration; it does not attest
the report bytes, and this generation does not block a non-`guarded` value.
Record the round even when it finds nothing. Before append, apply Sapheneia's
bounded audit-record operation, retain the protected evidence and host shape,
and give `audit-round` the exact checked operator declaration
`--audit-filter sapheneia:sapheneia`. The controller records the declaration;
it does not prove the semantic pass. Zero findings closes the loop; a genuine
judgement that the remaining leads are not worth another round closes it with
`--no-further-leads --reason`. Never report a round that did not run.

**Prose.** `hypomnema` decides what this step needs recorded and where it
goes, before the masks run. Every prose artefact in scope plus the PR title and
body, through
the `imprimatur` lint first and the `vulgate` mask second, content held
constant. Both are bundled: run the lint script by path, read the mask's
SKILL.md by path and apply it. When the run has a task issue, draft its closing
comment here under the repository's Sapheneia, Imprimatur, Vulgate, Imprimatur
publication order; fill the exact integration URL and status, then rerun that
whole order immediately before posting. The receipt refuses a skills list
missing either configured id.

**Push.** Stage and commit every intended final change with a valid local
signature and the two exact provenance trailers. Authorship follows the
contributing actor. A human contributor keeps their own Git author and valid
signer and publishes through their own GitHub account; never ask for or use the
Shoggoth private signing key or account for that contribution. Work contributed
by Shoggoth uses the Shoggoth identity. If a cloud runtime cannot publish that
Shoggoth work through the Shoggoth signer and account, stop before the commit or
pull request and hand the exact branch or patch to an environment that can.
Claude, Codex, another runtime host, or its generated-by footer is not
authorship for either case. Then push the step branch,
and open its pull request against the `pr_base` the directive names, using the
prepared prose. Once `gh pr create` returns, read the body back over REST before
receipting, as the `Read the body back` section of
[push-discipline.md](references/push-discipline.md) says, because a host can
append its attribution line or session link after creation. Wait for its gates
but leave it open: a step's work lands in the
integrate phase, not here. Do not add an issue reference unless one was
independently supplied or required by higher-priority repository policy. Receipt
the head SHA, PR URL, and PR base. Then, before acting on the next directive,
upload the step checkpoint the `Step checkpoint` section of
[push-discipline.md](references/push-discipline.md) requires.

**Integrate.** Once every step is pushed, the stack comes down in order.
Before the run is recorded as integrated, every identity its push receipts
recorded has to remain attributable from the recorded merge, and the receipt
records which mechanism carried it.
Retarget the next step's pull request onto the run branch, then merge this
step's, and delete no branch here; receipt each merge before starting the next.
Deleting a merged step's branch closes the pull request stacked on it, and a
closed pull request whose base ref is gone can be neither reopened nor
retargeted, so the order is not a preference. With the stack landed, open one
pull request from the run branch into the recorded base. When a run was pinned
to an exact starting commit, that commit remains the starting-base evidence and
`config.git.base` names the branch the run integrates into; the directive,
sync receipt and final receipt keep both identities. If concurrent work
advanced the base and that pull request conflicts, merge the exact remote base
tip into the run branch once with a signed two-parent commit whose first parent
is the final recorded step merge, push it, require GitHub valid verification,
and receipt it with `done sync-run`; never rebase or rewrite the signed stack.
Base advancement does not invalidate the signed implementation or completed
audit. The sync receipt keeps their exact-tree digests and adds a bounded
integration-revalidation record over the computed upstream, product and overlap
path sets. Reopen only evidence whose declared dependency changed or whose
revalidation failed. A base advance by itself does not authorise a carryover,
another study, or another product audit. If a pushed sync exposes a failed
composition check, repair only that surface, reconstruct the two-parent merge
from the same signed product head, and supersede the active sync by its exact
SHA with a bounded reason and fresh revalidation. Publish the sibling merge
only with a force-with-lease pinned to that active SHA; bare force and any
other rewritten ref remain forbidden. Fiat retains the failed sync and permits
only the replacement to integrate.
Then name everything the run
left unfinished in its body under `## Carried forward`, wait for its gates,
merge it without bypassing them, require GitHub to report `verified: true` and
`reason: valid` for every pushed commit and merge SHA, delete the run branch and the step branches
where policy allows, and close any recorded task issue. That merge is the only
one into the base for the whole run. A routine publish or closure action is not
a handoff to a human. Before closing a task issue, post its exact checked
closing-comment bytes, read the comment and issue state back from GitHub, and
report only that remote evidence. The controller's closure receipt does not
attest the comment's semantic passes or bytes.

## Delegation and context

Every `next` envelope carries `state_sha256`, an explicit `agent`, and a
source-bound `brief`. Delegate the exact packet to `surveyor`, `mason`,
`warden`, or `scribe` when the runtime supports isolated agents. An inline
directive carries explicit null packet fields. Refuse an artefact whose digest
has drifted; do not reconstruct its study block, runbook step, risk register,
or sorted prose diff from chat. If delegation is unavailable, execute the same
packet in the main session. After compaction, rerun `next`: the receipted
artefacts and state digest deterministically reconstruct the packet.

## Stop conditions

Stop and ask the user when: `next` says `audit-verdict` or `blocked`; a push is rejected;
the security suite cannot be resolved for a Solidity repo; or `verify` fails.
Use `hexctl halt --reason ...` so the stop itself is on the ledger.

## Hard rules

- Never advance past a phase whose receipt command failed.
- Never reconstruct progress from chat; `status` and `next` are the truth.
- Never claim a lint, audit round, or test run happened when it did not.
- Never receipt a Fiat-created commit without a valid local signature and one
  exact copy of each provenance trailer. Never receipt a pushed commit or
  GitHub merge SHA unless GitHub reports `verified: true` and `reason: valid`.
- Never force-push over someone else's work or bypass a merge gate.
- Never target the base or the repository default branch with a step pull
  request, and never merge one during the steps; the stack lands in
  `integrate`.
- Never merge into the base more than once in a run, and never open a step
  branch straight off the base once a run branch exists.
- Never invent a branch name the controller did not give, and never name a
  branch after its number alone.
- Never attach the first task issue after `init` or rename a stored run branch.
- Never call a plan or implementation complete while its own final changes,
  PR, task branch, or recorded issue still need routine stage, push, merge,
  deletion, or closure work.
- Never create a GitHub issue merely to satisfy this workflow.
- Never disclose a failed, unavailable, or inconclusive contributor check.
- Never install a wider-marketplace plugin before the study receipt exists.
- Never run or recommend a frontier Fiat job for a skill whose ledger is
  mature, or when a capable review finds no concrete material improvement.
- Never change a held `Next Fiat job` during a generation update; only clarify
  its context without changing its target or acceptance condition. An epoch
  may replace it only with the reopening evidence required by the ledger.

## Optional companion observation receipt

Observation is never a phase gate. When a selected controller receipt needs a
companion record, obtain `observation_run_id` from `hexctl status --json`, emit
the stream beneath `.hexaemeron/observations/`, and run the root
`scripts/run_observation.py check-prefix` command. Immediately after the
receipt being described, bind the accepted prefix:

```text
hexctl observe --artifact .hexaemeron/observations/run.jsonl \
  --capture-status accepted --redaction-status passed
```

Record a gap, refusal, unknown, or unavailable observer without an artefact and
with a bounded `--reason-code`. Ordinary `hexctl verify` remains the controller
integrity check. Only `hexctl verify --observations` asks the dependent prefix
claim. Later selected boundaries extend the same file byte for byte; appended
bytes remain unbound until then. The complete interface and `FOB` recoveries
are in [the run-observation binding guide](../../../../docs/fiat-run-observation-binding-v1.md).

## Final report

When `next` returns `done`, run `hexctl status` and `hexctl verify`, then
hand over: topic, the run branch and the base it landed on, the step list with
each stacked PR URL and the order the stack merged in, the integration PR and
its merge SHA, audit rounds per step with the closing state of each, and where
the study and runbook live.

## Promise Machine contract

### fiat-study-amendment

- Promise: A successful `hexctl amend study` establishes that the captured candidate preserved the currently receipted study bytes as its exact prefix, carried one structurally accepted final amendment, passed the bundled Protasis check, and recorded bounded digest and unbuilt-step verdict evidence.
- Evidence: Scoped bounded reads of the receipted study and candidate, exact prefix SHA-256, deterministic amendment and field parsing, complete unbuilt-step verdict coverage, the bundled checker exit, the write-ahead transaction, canonical artefact digest, state receipt and `amend:study` ledger event.
- Evidence classes: checked, recorded
- Boundary: The receipt establishes candidate structure, byte continuity, checker acceptance and recorded operator verdicts; it does not establish that the correction is true, that a holding verdict is correct, or that a broken runbook has been repaired.
- Authorises: Recoverably replacing the canonical study with the exact checked candidate, re-pinning its receipt, and either continuing to the existing next directive when the current step holds or emitting a durable blocked directive when it does not.
- Consequence: 2
- Refuses: An edited prefix, ambiguous or malformed amendment, incomplete verdict coverage, unsafe or oversized path, failed checker, unlabelled interrupted mutation, or dependent work after a broken current-step verdict.
- Recovery: Inspect the pending record and study, rerun `hexctl amend study --artifact <canonical-study>` to finish or roll back an interrupted transaction, halt safely, or use a separately specified runbook-repair transition after a recorded broken verdict.
- Exceptions: none

### fiat-runbook-amendment

- Promise: A successful `hexctl amend runbook` establishes that the captured candidate preserved the currently receipted runbook bytes as its exact prefix, carried one structurally accepted final amendment with complete replacement clauses, passed the bundled Protasis runbook check, and recorded bounded digest, current-study binding and unbuilt-step verdict evidence.
- Evidence: Scoped bounded reads of the receipted runbook and candidate, exact prefix SHA-256, deterministic field, replacement, topology and verdict parsing, complete unbuilt-step verdict coverage, current study digest, bundled checker exit, subject-labelled write-ahead record, canonical artefact digest, receipt history, `amend:runbook` ledger event and recomputed effective packet source.
- Evidence classes: checked, recorded
- Boundary: The receipt establishes candidate continuity, structure, recorded operator verdicts and exact source carriage. It does not establish that the free-form replacement is semantically complete or correct, that its command passes, or that a holding verdict is true.
- Authorises: Recoverably replacing the canonical runbook with the exact checked candidate, re-pinning its receipt, carrying current digest-matched replacement bytes to Mason and Warden, and clearing a study block only through the recorded current-study join and complete-replacement rule.
- Consequence: 2
- Refuses: An edited prefix, ambiguous or malformed final block, changed step topology, completed or unknown touched steps, incomplete verdict coverage, partial or duplicate replacement clauses, unsafe or oversized input, failed checker, stale study binding, mismatched receipt history, unlabelled interrupted mutation, pending-subject collision, unreceipted drift or dependent work after an unrepaired broken verdict.
- Recovery: Inspect the named pending subject and canonical artefact, rerun `hexctl amend runbook --artifact <canonical-runbook>` to finish or roll back exactly once, submit another valid current-study-bound amendment, or halt without editing receipt history.
- Exceptions: none

### fiat-run-observation-binding

- Promise: A successful `hexctl observe` followed by `hexctl verify --observations` establishes that one bounded `promise-machine-run-observation/v1` prefix passed the structural validator and redaction gate, names this controller run, extends any earlier selected prefix byte for byte, and is digest-bound to the immediately preceding Fiat ledger receipt.
- Evidence: The derived controller run identity, no-follow run-local path walk, bounded stable rereads, `check-prefix` result, event interval and count, byte count and SHA-256, capture, validation and redaction statuses, exact preceding receipt hash, `record:run-observation` ledger row, recomputation result, unbound-tail count, hostile fixture manifest and focused tests.
- Evidence classes: checked, recorded
- Boundary: The binding establishes only the named prefix bytes, structural and gate results, and receipt association. It does not establish that events are true or complete, that capture saw every event, that an unbound tail conforms, or that the preceding receipt or delivery claim is correct.
- Authorises: Recording the bounded binding without advancing Fiat, and reporting that exact prefix as attached to the named receipt when explicit observation verification succeeds.
- Consequence: 2
- Refuses: A missing binding, unsafe or unstable path, wrong contract or controller run, non-contiguous or open prefix, changed earlier bytes, non-increasing selection, mismatched receipt, interval or count, replaced, reordered or truncated bound bytes, or capture, validation or redaction that is not accepted and passed.
- Recovery: Keep ordinary controller verification available, inspect the stable `FOB` code, restore or append to the exact run-local stream, record one new selected receipt boundary when needed, and rerun `check-prefix`, `observe`, then `verify --observations`.
- Exceptions: none

### fiat-receipted-delivery

- Promise: A successful `hexctl verify` establishes that the controller state has the required version-1 container shape, the state and append-only ledger agree, and every recorded phase transition occurred in the required order with the required receipt shape.
- Evidence: The ordered state-container check, exact study and runbook receipts, step branches and locally verified commit ranges, GitHub-verified pushed commits and merge SHAs, preserved product-receipt digests and the bounded integration-revalidation receipt when a completed run syncs with an advanced base, audit rounds, prose and push receipts, hash-chained ledger, controller version and zero-exit verification result.
- Evidence classes: checked, recorded
- Boundary: Controller verification proves the required container shape, receipt order, integrity, checked audit-entry structure, the recorded receipt-time synopsis check, and the recorded local and GitHub signature checks; it does not establish current working-tree currency, establish that audit prose or coverage judgements are true, make the lossy synopsis authoritative, validate other heterogeneous leaf values, prove a test summary, implementation claim, signer authority beyond those checks, or user authority merely written into a receipt.
- Authorises: Advancing only to the single next controller directive and reporting the recorded workflow state without strengthening any underlying receipt.
- Consequence: 2
- Refuses: Skipping a phase, reconstructing progress from chat, accepting a malformed or missing receipt, or describing an unrun check as complete.
- Recovery: Inspect `hexctl status`, repair the current phase's real evidence without editing ledger history, submit the required receipt and rerun `hexctl verify`.
- Exceptions: none

### fiat-final-integration

- Promise: A successful integration receipt establishes that every stacked step was merged in controller order, the run branch passed its required gates, any completed product evidence remained bound to its exact product head across the active signed base-sync merge, every superseded failed composition remained recorded and unavailable for integration, the computed product/base overlap and declared affected paths received bounded green composition checks, every identity the push receipts recorded remains attributable from the recorded merge, and exactly one recorded merge landed the run on the named base under the user's delivery authority.
- Evidence: The user's explicit Fiat request, green step checks, exact product receipt digests, the active signed sync merge with the final product head as first parent and exact remote base as second parent when the base advanced, any superseded sync identities and bounded reasons, computed product, upstream, overlap and product-to-sync composition paths, a digest-bound integration-revalidation artefact whose affected paths equal the composition surface plus every overlap and whose green checks cover all of them, stacked PR URLs, exact GitHub-verified pushed ranges, GitHub-verified merge-step and integration SHAs, the recorded attribution mechanism for each identity, final controller state and verified ledger.
- Evidence classes: checked, recorded
- Boundary: Exact-tree implementation and audit evidence remains evidence about the recorded product head when the base advances; it does not automatically apply to bytes changed while composing that head with the new base. The revalidation receipt establishes only the named checks over the computed and declared integration surface. Integration establishes the recorded repository transition; it does not prove the software defect-free, make audit judgements independent or authorise a deployment, financial action or another repository. The attribution result establishes that the base carries each recorded identity by ancestry or by a recorded merge's author or trailer; it does not establish that GitHub will resolve that identity to an account or list it as a contributor.
- Authorises: Publication of the complete run to the named base and a final report limited to the merged artefacts and recorded evidence.
- Consequence: 3
- Refuses: Direct step merges to the base, bypassed gates, a second base merge, deletion that closes a stacked PR prematurely, treating base advancement alone as product-evidence invalidation or authority for a carryover, a sync whose first parent is not the recorded product head, silent replacement of a sync receipt, an affected-path manifest that differs from the computed composition surface plus overlap, a failed or uncovered integration check, a merge that leaves a recorded identity carried by nothing, or integration without explicit delivery authority.
- Recovery: Leave the stack open; if only the base advanced, merge the exact remote base into the completed run with the recorded product head as first parent, determine the affected surface, rerun its integration-sensitive checks, and receipt that revalidation without rebuilding or re-auditing unchanged product bytes. If that composition later fails a required check, repair the affected surface, reproduce the signed two-parent merge, rerun bounded revalidation and supersede the exact active sync with a reason; the old receipt remains in the ledger. Restore another required branch or check, retarget and merge in controller order, or halt with the exact blocker before any base mutation.
- Exceptions: none
