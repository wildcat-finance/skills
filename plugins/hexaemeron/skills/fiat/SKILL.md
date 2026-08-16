---
name: fiat
description: >
  Run the one-shot delivery loop: study, runbook, then per-step
  implement/audit/prose/push until a working prototype exists.
  Use only when a Wildcat contributor explicitly asks to start, run, resume,
  or report a Hexaemeron or Fiat delivery, including /hexaemeron:fiat forms.
  Do not infer activation from a similar task.
metadata:
  version: "1.0.0"
---

# Fiat

Let there be light.

Drive the whole loop from durable controller state, never from conversation
history. The controller emits one directive at a time; do the work it names,
receipt it, ask for the next one. A phase without a receipt did not happen.

`$SKILL_DIR` = the directory containing this SKILL.md file; resolve it from
the path you loaded this skill from. `$PLUGIN_ROOT` = two directories above
`$SKILL_DIR`; sibling skills live at `$PLUGIN_ROOT/skills/<name>/`. Both
hold on any host that can read this file.

Controller:

```text
python3 "$SKILL_DIR/scripts/hexctl.py" --dir "$PWD" <cmd>
```

Alias it as `hexctl` mentally; every command below means that invocation.
State lives in `.hexaemeron/` beside a hash-chained ledger. The directory
ships its own `.gitignore`, so git never sees it.

Mutating commands hold a kernel lock for their whole run. If another writer is
active, `hexctl` names it and prints a worktree command. Use another worktree;
do not retry against the same state. `next`, `status`, and `verify` remain
available while the writer runs, and a crashed process releases the lock
without manual cleanup.

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
2. If `.hexaemeron/state.json` exists, run `hexctl verify`, then
   `hexctl status --json`. If its phase is `done`, run `hexctl reset` to
   archive the completed run, then continue immediately as a new run at step
   3. Do not ask the user to remove, rename, or approve resetting completed
   state. If the phase is not `done`, this is a resume: enter the loop and
   treat the state file as canonical.
3. Otherwise: say exactly `Let there be light.` and nothing else before it,
   then run preflight (below), then `hexctl init --topic "<topic>"
   --base <ref>` and enter the loop. `--base` defaults to `main`; honour any
   branch, repo, or commit the user named as the starting point.

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
   because its name looks related.
3. The prose masks ship inside this plugin: the `imprimatur` lint (a script
   at `$PLUGIN_ROOT/skills/imprimatur/scripts/imprimatur.py`) and the
   `vulgate` voice mask (rules at `$PLUGIN_ROOT/skills/vulgate/SKILL.md`).
   Nothing to resolve.
4. The security suite is vendored in this plugin: the Pashov `x-ray`,
   `solidity-auditor`, and `fizz` skills sit under `$PLUGIN_ROOT/skills/`.
   After init, record the bundled ids:
   `hexctl record security_suite
   '["hexaemeron:x-ray","hexaemeron:solidity-auditor","hexaemeron:fizz"]'`.
   If the run will produce no Solidity and no suite applies, record a waiver
   instead: `hexctl record security_suite '"waived: <reason>"'` -- and say so
   out loud. Never claim a tool ran when it did not.
5. Nothing else. Fiat has no issue phase. Ignore ambient issue-first
   conventions for this workflow: do not create, search for, register,
   reconcile, or close GitHub issues. Only an explicit higher-priority policy
   in the target repository can override this rule.

## The loop

Repeat until `next` returns `done`, `halted`, or `audit-verdict`:

```text
hexctl next
```

Act on the single directive it prints, then receipt it. The directory:

| `do` | Action | Reference | Receipt |
| --- | --- | --- | --- |
| `study` | Research the topic; write the study | [study.md](references/study.md) | `done study --artifact <path> --skills <csv>` |
| `runbook` | Derive discrete steps from the study | [runbook-format.md](references/runbook-format.md) | `done runbook --artifact <path> --steps-file <path>` |
| `implement` | Build the step, simplest construction that satisfies the runbook | [runbook-format.md](references/runbook-format.md) | `done implement --branch <name> --commit <sha> [--tests <summary>]` |
| `audit-round` | One security round: run the suite, log, fix on the stacked branch | [audit-loop.md](references/audit-loop.md) | `audit-round --findings <n> [--log <path>] [--fixes-commit <sha>]` |
| `close-audit` | Last round was clean; close the phase | [audit-loop.md](references/audit-loop.md) | `done audit [--fixes-ref <ref>]` |
| `resolve-security-suite` | Suite receipt missing; resolve or waive | preflight step 4 | `record security_suite ...` |
| `prose` | Rewrite every prose artefact and draft the PR text | [prose-pass.md](references/prose-pass.md) | `done prose --files <n> --skills <csv>` |
| `push` | Push and open the PR | [push-discipline.md](references/push-discipline.md) | `done push --pr-url <url>` |
| `audit-verdict` | Max rounds hit with findings open | ask the user | `done audit --no-further-leads --reason ...` or `halt --reason ...` |
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

**Implementation.** Pick the construction that takes the least effort to
comprehend, then stop. The runbook step is the yardstick: reread it before
declaring the step complete, and do not add anything it does not ask for.
Branch as `step-<n>-<slug>` from the base named by `config git.step_base`
(`chain` means branch from the previous step's branch; `base` means branch
from `config git.base`).

**Audit.** The longest phase by design. One round is the full suite: `x-ray`
first, then `solidity-auditor`; when the step ships Solidity under Foundry or
Hardhat, `fizz` builds or refreshes the invariant fuzz suite and its campaign
results count as part of the round. Read each skill's SKILL.md from
`$PLUGIN_ROOT/skills/<name>/` and follow it. Every finding is logged
to the audit file, fixes committed to the stacked branch. Record the round even when it finds nothing.
Zero findings closes the loop; a genuine judgement that the remaining leads
are not worth another round closes it with `--no-further-leads --reason`.
Never report a round that did not run.

**Prose.** Every prose artefact in scope plus the PR title and body, through
the `imprimatur` lint first and the `vulgate` mask second, content held
constant. Both are bundled: run the lint script by path, read the mask's
SKILL.md by path and apply it. The receipt refuses a skills list missing
either configured id.

**Push.** Push the branch and open a PR using the prepared prose. Do not add
an issue reference unless the user independently supplied one. Receipt the PR
URL. Pushing opens a PR; it never merges one. Merge review belongs to humans
and to whatever gate the repo runs.

## Delegation and context

For long runs, hand research and implementation bulk to the bundled agents
(`surveyor`, `mason`) through the runtime's subagent mechanism, passing the
controller path, the state directory, and the current directive verbatim. If
the runtime has no subagent mechanism, perform the work in the main session
and keep the controller receipt as the boundary. Keep the audit and prose
phases in the main session when a delegated context cannot load the bundled
skills. After each `done push`, compact if the runtime supports it: the
receipts carry everything a fresh context needs.

## Stop conditions

Stop and ask the user when: `next` says `audit-verdict`; a push is rejected;
the security suite cannot be resolved for a Solidity repo; or `verify` fails.
Use `hexctl halt --reason ...` so the stop itself is on the ledger.

## Hard rules

- Never advance past a phase whose receipt command failed.
- Never reconstruct progress from chat; `status` and `next` are the truth.
- Never claim a lint, audit round, or test run happened when it did not.
- Never merge a PR or force-push over someone else's work.
- Never create a GitHub issue merely to satisfy this workflow.
- Never disclose a failed, unavailable, or inconclusive contributor check.
- Never install a wider-marketplace plugin before the study receipt exists.

## Final report

When `next` returns `done`, run `hexctl status` and `hexctl verify`, then
hand over: topic, step list with PR URLs, audit rounds per step with the
closing state of each, and where the study and runbook live.
