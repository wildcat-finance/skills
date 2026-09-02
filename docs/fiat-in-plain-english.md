# Fiat in plain English

Fiat is the controller for taking one repository issue from “we should fix
this” to an inspectable delivery. It keeps the work in order, records what each
phase returned, and refuses to let a worker approve or advance its own output.

Fiat runs only when a user explicitly asks to start, run, resume, recover, or
continue Fiat or Hexaemeron. A general request to implement something does not
activate it.

## The short version

```text
understand the problem
        |
write a buildable plan
        |
implement one checked step
        |
audit that exact step
        |
explain what shipped
        |
push and integrate in order
```

Fiat owns the state between those phases. A worker returns an artefact; Fiat
checks the receipt and decides whether the next dependent action may begin.
Chat history is never the controller ledger.

## One run from beginning to end

| Phase | Work produced | Who may advance the run |
| --- | --- | --- |
| Study | The problem, sources, options, chosen design, risks, and open questions | Fiat |
| Runbook | Small implementation steps, tests, boundaries, and acceptance conditions | Fiat |
| Implementation | Code, tests, one step commit, and visible deferrals | Fiat |
| Audit | Raw tool output, findings, fixes, and the failure-to-guard record | Fiat |
| Prose | Checked documentation and pull-request text that match the shipped change | Fiat |
| Push | The verified branch and its stacked pull request | Fiat |
| Integration | Ordered step merges and one verified result on the base | Fiat |

The route can include an amended study, a revised runbook, several
implementation steps, and several audit rounds. A failed check keeps its
dependent action closed while inspection, repair, rerun, rollback, or safe exit
remains available.

“The code looks done” is not a controller state.

## The four worker roles

These workers are deliberately less powerful than Fiat. Each receives one
source-bound packet and returns named evidence.

### Surveyor

Surveyor studies one problem. Its packet names the target, base revision,
sources, and output path. It returns a buildable account of the problem, the
reasonable design options, the selected design, the risks, and any questions
that still need a person.

Surveyor cannot record its own receipt, change the issue, publish, or move Fiat
into the runbook.

### Mason

Mason implements exactly one runbook step from the exact starting revision and
branch pair Fiat supplies. It writes the code and tests, commits the step, and
returns the commit, test command, result, and any deliberate deferral.

Mason cannot push, open a pull request, merge, widen the step, or alter Fiat's
state.

### Warden

Warden performs one audit round over one step. It runs the security work the
study and change require, preserves every finding and raw audit artefact, fixes
bounded findings, and returns an Elenchus verdict that relates the failure to a
guard.

Warden cannot call missing evidence clean, accept its own round, or move the
run forward.

### Scribe

Scribe handles one bounded prose pass after the code and evidence exist. It
checks the complete changed prose with Imprimatur, applies Vulgate to the
surface without changing protected content, reruns Imprimatur, and reports the
files and skills used.

Scribe cannot invent a claim, issue reference, caveat, test result, or
publication authority. It cannot receipt its own phase.

Fiat may execute any of these packets in its own context when an isolated
worker is unavailable. The packet, artefact, and receipt stay the same.

## The disciplines inside a run

The following are skills Fiat may apply during a phase. They are not extra
controllers.

| Skill | Used when | Question it owns |
| --- | --- | --- |
| Protasis | Before and during implementation | Are the study and runbook buildable, and is the evidence due for the chosen design present now? |
| Phylax | Off-chain software is in scope | Are inputs, commands, fetches, secrets, dependencies, paths, and model output controlled? |
| Ephoros | A step may run unattended | What must it emit so an operator can explain it later? |
| Metron | A non-gas performance claim exists | Was the change measured before and after in the same way? |
| Elenchus | A failure has been observed | Was it reduced to its cause and guarded by a parent-red, fixed-green test? |
| Hypomnema | A durable explanation may be needed | What must be recorded, and where? |
| Imprimatur | Prose is about to ship | Does it contain banned writing habits or unsupported technical language? |
| Vulgate | Checked content reads like machine prose | Can the wording become plain and human without changing the content? |

Hermes owns Solidity gas measurements. Warden may also use the unchanged
Pashov security skills for audit preparation, Solidity review, and stateful
fuzzing. Those tools can use their own internal specialist roles; none of them
controls Fiat.

## Durable state and checkpoints

Fiat stores its run in a dedicated worktree with a hash-chained state record.
After an accepted step it writes a verified archive into a fixed local
checkpoint store before continuing. A replacement local agent can restore that
checkpoint only after verifying the archive, Git boundary, signatures, and
controller capsule.

This survives context loss on one machine. It does not make arbitrary
mid-step state portable and it is not a distributed cross-machine service.

When handing off a completed step, pass the checkpoint's absolute path and
digests directly. Do not infer progress from chat, choose an informal archive
destination, or reuse a worker handle whose visible issue, step, or role comes
from an older run.

## Git and publication

Fiat owns branch creation, step commits, pushes, stacked pull requests, ordered
merges, and the final controller report within the authority the user and
repository supplied. It never gains publication authority merely because the
implementation passed.

An external human contributor keeps their own Git author, signing identity,
and GitHub account. Required Shoggoth provenance supplements that authorship;
it does not replace it or permit the human to use a private Shoggoth key or
account. Runtime hosts and model names are not co-authors or generated-by
bylines for governed work.

If the required signer, repository access, or controller evidence is absent,
Fiat stops before the dependent commit, push, pull request, or merge and leaves
a precise hand-off.

## What completion means

A complete Fiat run has satisfied the controller's required receipts and
reached its authorised integration endpoint. The final report identifies the
issue, run, branches, commits, checks, remaining boundaries, and current state.

Completion does not mean:

- every possible test was run;
- a security review found every defect;
- a maintainer must accept the contribution;
- GitHub has already credited every author; or
- a local checkpoint can be resumed anywhere.

It means the next person can inspect what changed, why it changed, which checks
ran on which bytes, what remains uncertain, and which authority accepted each
transition.

The canonical controller rules are in
[`plugins/hexaemeron/skills/fiat/SKILL.md`](../plugins/hexaemeron/skills/fiat/SKILL.md).
This guide explains them; it does not replace them.
