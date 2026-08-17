# hexaemeron

<!-- marketplace-context:start -->
## In one line

Hexaemeron runs an explicit, receipted delivery loop and also exposes its fuzzing, audit-readiness, security-review and prose skills on their own.

**Try something else when.** Use Hermes for measured gas work, Pandects for reviewed credit laws, and Lemma when the output needed is source-linked retrieval chunks.

**Current frontier.** The bundled Solidity audit suite has not yet been exercised in a published end-to-end Fiat delivery.

**Next Fiat job.** Use /hexaemeron:fiat to run and publish the first Solidity delivery that exercises the bundled x-ray, solidity-auditor and fizz loop end to end, recording every round and closing state. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

Let there be light.

One command that takes a topic from nothing to a working prototype:
study, runbook, then for each runbook step the simplest implementation that
satisfies it, a security loop that runs until clean or
reasoned out, a prose pass in the house voice, and a merged PR. Every phase
leaves a receipt in a hash-chained ledger, so the run survives context
resets, crashes, and week-long pauses -- resume is the same command.

Named for the six days of ordered creation from a void to finished work,
then rest. The entry skill is `fiat`, so the invocation is
`/hexaemeron:fiat` and a fresh run's first words are the line above.

## The shape of a run

| Day | Phase | What happens |
| --- | --- | --- |
| 1 | `study` | Study the topic; write `.hexaemeron/study.md`, linted |
| 2 | `runbook` | Divide the work into discrete, self-contained steps |
| 3-4 | `implement` | Build the step, least mental load that satisfies the runbook |
| 5 | `audit` | The vendored Pashov suite in rounds until clean or reasoned out; fixes on a stacked branch |
| 6 | `prose` | The `imprimatur` lint, then the `vulgate` voice mask, on every document and the PR text |
| rest | `push` | Stage and commit the final diff, push, merge the PR, clean up the branch, and close the task issue |

Days 3 through the rest repeat per step. The sixth day makes the prose in
a human image, which is roughly the joke the name is carrying.

## Usage

```text
/hexaemeron:fiat "borrowing-base covenant hook for V2.5"   # start
/hexaemeron:fiat --base release/v2.5 "..."                  # start from a ref
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

## The controller

`skills/fiat/scripts/hexctl.py` sequences the run. The model does the work;
the controller decides what comes next and refuses to advance without a
receipt. State sits in `.hexaemeron/` (self-gitignored) beside an
append-only ledger where every entry hashes over the one before it.

```text
hexctl next                 # the single next action, as JSON
hexctl status [--json]      # where the run is
hexctl done <phase> ...     # receipt a phase; validation lives here
hexctl audit-round ...      # record one security round
hexctl record <key> <val>   # named receipts (resolved suite, run context)
hexctl halt / resume        # put a stop itself on the ledger
hexctl reset                # archive a completed run and clear active state
hexctl verify               # prove the chain and state were not edited
```

Mutating commands hold a kernel lock for their whole run. A second writer is
refused with the first process's details and a worktree command; `next`,
`status`, and `verify` still answer. The operating system releases the lock if
the holder crashes, so a stale metadata file never needs manual cleanup.

The receipts are opinionated where the process is: the audit phase will not
open without a resolved (or explicitly waived) security suite; it will not
close with findings open unless a reasoned no-further-leads verdict is
recorded; a prose receipt missing either configured skill is rejected; and a
push receipt requires the final head, a merged PR, and closure of any recorded
task issue. Fiat creates no GitHub issue unless the user or target repository
requires one.

## Skill versions and the stopping rule

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

## Configuration

Per-run, via `hexctl config set <path> <value>`:

| Path | Default | Meaning |
| --- | --- | --- |
| `skills.prose_lint` | `hexaemeron:imprimatur` | Bundled lint the prose receipt demands |
| `skills.voice` | `hexaemeron:vulgate` | Bundled voice mask the prose receipt demands |
| `skills.security` | the vendored Pashov ids | Intent only; the ids the `security_suite` receipt records at preflight |
| `audit.max_rounds` | `8` | Rounds before the controller forces a verdict |
| `audit.stacked_suffix` | `--audit` | Fix branch: `<step-branch>--audit` |
| `audit.fold` | `false` | Merge the stacked branch into the step branch on close |
| `audit.log_path` | `audit/AUDIT.md` | Where rounds append |
| `git.base` | `main` | Starting ref |
| `git.step_base` | `chain` | Steps branch from the prior step (`base` for independent) |

The Pashov suite -- `x-ray`, `solidity-auditor`, and `fizz` -- is based on
https://github.com/pashov/skills tag `v28062026` under the MIT licence. Each
`NOTICE.md` records the local distribution changes. The copies keep their
upstream instructional register; Wildcat's house prose lint does not rewrite
third-party source solely for style. Credit: Pashov Audit Group,
https://www.pashov.com/. Preflight records the bundled ids in the
`security_suite` receipt; the controller gates on the receipt, not the config,
so a stale config cannot fake a suite. Prose-free or Solidity-free runs record
a waiver instead.

## The prose masks

Everything the loop needs ships in the plugin; it stands alone. The two
prose masks are vendored, not referenced: `imprimatur` (a three-tier lint
over the tells that mark prose as machine-written) and `vulgate` (a voice
mask that renders text into a plain human register) live under `skills/`
and can be invoked on their own, outside the loop, whenever a draft needs
the treatment. Edit the lexicon in place when a term needs adding.
Upstream attribution for the absorbed lint material sits in
`skills/imprimatur/NOTICE.md`. Fiat never bypasses a gate, but once the gates
pass it merges its own PR and closes its own task issue rather than leaving
routine publication work behind.

## Agents

Four subagents for context isolation on long runs: `surveyor` (the study),
`mason` (a step's implementation), `warden` (one audit round), `scribe`
(the prose pass). The old caveat about skills not
resolving inside subagents is gone on both fronts: the prose masks and the
security suite are files inside the plugin, reachable from any context by
path, so the warden and scribe always have their tools.

## Tests

```text
python3 tests/run_tests.py
```

The tests cover the controller and Fiat contract: phase ordering, completed
run archival and reset, audit gating and round caps, fixes evidence, prose
skill enforcement, halt/resume, ledger tamper detection, concurrent writer
exclusion, crash recovery, and the Wildcat marketplace boundary.
