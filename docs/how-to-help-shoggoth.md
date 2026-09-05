# How to help build the Shoggoth

![One external contributor carries a bounded issue packet towards the Shoggoth.](assets/shoggoth-contributor-cover.png)

You do not need to learn all 25 members, run a long controller session, or wait
for someone to assign you a grand project. The useful starting point is one
real gap you can make smaller and prove.

This guide offers two routes:

- choose a small contribution yourself; or
- let the Wave Atlas allocate an unblocked issue and take it through Fiat.

Both routes produce ordinary repository contributions under your human
identity. Neither gives an agent extra authority.

## Ways to contribute

### Try one operation on real work

Pick the skill closest to a problem you already have. Run its documented
operation against a repository, dataset, historical block, or draft you are
allowed to use. Report the first reproducible failure, missing precondition, or
confusing instruction with the exact command and evidence.

Real use is especially valuable where the project currently has only
constructed examples: Synkrisis cohorts, a Berean reference release, a second
Janus host, or held tasks for the prose and interaction skills.

### Add one missing specimen or adapter

A small specimen can be more valuable than a broad feature. Examples include:

- a deliberately divergent on-chain and off-chain calculation for Homologia;
- an empty-block receipt fixture for Lazarus;
- a real callback host for Janus;
- structured Echidna or Medusa campaign evidence for Pandects;
- a missing ABI shape for Lemma;
- a source capture and mapping specimen shared by Alexandria and Tabularium.

Read the member's README, `AGENTS.md`, canonical `SKILL.md`, and current
`EVOLUTION.md` before choosing the exact shape. Historical studies and audits
explain earlier decisions but are not the current contract.

### Improve the front door

Documentation, examples, diagrams, error messages, and contribution paths are
part of the product. A good prose change makes a real operation easier to
select or run without changing its promise. Preserve commands, facts, caveats,
identifiers, and refusal conditions; run the repository's prose checks on the
complete candidate.

### Implement one recorded frontier

Every governed skill has an evolution ledger with its current frontier and one
accepted next job. A strong frontier contribution includes the implementation,
a specimen that fails before the change, tests that establish the bounded
claim, updated public orientation, and any generated installation copies the
repository owns.

Do not widen the skill because a neighbouring need appeared. Record the
handoff to the sibling that owns it.

### Review promises and recovery paths

You can help without writing code by checking whether a proposed operation
answers these questions:

1. What exactly does success establish?
2. Which evidence supports that result?
3. What nearby claim remains unsupported?
4. Which next action does success permit?
5. What stops when evidence is absent or stale?
6. Can a person inspect, repair, rerun, roll back, or exit safely?

Ambiguity at these boundaries becomes much more expensive after a capability
ships.

## Before editing

1. Read the root `AGENTS.md` and the `AGENTS.md` inside the plugin you will
   change.
2. Confirm the exact checkout, base revision, issue or task, and current Git
   status.
3. Check whether another branch or pull request already owns the same work.
4. Read the canonical skill and only the linked references needed for the job.
5. Keep generated files, vendored upstream skills, historical audits, fixtures,
   and content-addressed evidence out of a prose sweep unless the task
   specifically requires them.
6. Use the exact Python interpreter recorded in `.python-version` for the
   repository checks.

For a normal focused contribution, follow the plugin's checks and the root
checked runner. You do not have to use Fiat unless the task or issue requires
the controlled delivery loop.

## The Atlas and Fiat route

Use this route when you want the project to choose an unblocked issue and guide
the whole delivery.

The [Shoggoth Wave Atlas](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/)
draws one random open issue whose recorded hard dependencies are closed. It
returns the issue number, exact URL, and a filled-in prompt for a local Fiat
run.

Use one allocation route once. Each button or API request performs a fresh
random selection, so opening several routes can allocate several different
jobs.

### Checked bootstrap routes

[![OpenAI - ChatGPT web bootstrap](https://img.shields.io/badge/OpenAI-ChatGPT_web_bootstrap-10A37F?style=for-the-badge)](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/go/chatgpt)
[![Anthropic - Claude web bootstrap](https://img.shields.io/badge/Anthropic-Claude_web_bootstrap-D97757?style=for-the-badge)](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/go/claude)
[![Atlas - manual prompt](https://img.shields.io/badge/Atlas-Manual_prompt-3E68FF?style=for-the-badge)](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/api/job)

The ChatGPT and Claude routes are covered by the Atlas launcher tests. They
allocate one job and open a web chat with its prompt filled in. That is a
bootstrap, not evidence that the browser chat can edit a local checkout, sign
commits, restore a checkpoint, or publish through your GitHub account.

Before `hexctl init`, move the exact prompt to the local coding harness you will
keep open for the run. Confirm that it can work in the repository, use your
signing identity, and publish through your account.

### Local harnesses

Codex and Claude Code have native Wildcat marketplace packages. Open the
repository in either one, install from [`INSTALL.md`](../INSTALL.md), and start
the run by hand with the exact Atlas prompt. Neither has a one-click Atlas
launcher, and neither is part of the probed roster below.

The rest of the roster is generated from `docs/harness-classification.json`,
which a probe writes by looking at the host it runs on. Every route below is
manual: read `AGENTS.md`, then send the exact `job.prompt`.

<!-- harness-roster:begin -->
<!-- Generated by scripts/render_harness_roster.py from docs/harness-classification.json, recorded on darwin-arm64 on 2026-09-04 against c0524f0cd1288cc35316ae9acec6c7d2a6bd4272. Change the roster in scripts/probe_harnesses.py, re-run the probe, then re-run the renderer. Nothing between these markers is edited by hand, and the guide carries no harness name outside them. -->

| Harness | Class | Client found here | Version | Authenticated here |
| --- | --- | --- | --- | --- |
| GitHub Copilot | manual route | no | not read | no |
| Cursor | manual route | no | not read | no |
| Gemini CLI | manual route | no | not read | no |
| Windsurf | manual route | no | not read | no |
| Cline | manual route | no | not read | no |
| Roo Code | unsupported | no | not read | no |

Recorded on darwin-arm64 on 2026-09-04, against `c0524f0cd1288cc35316ae9acec6c7d2a6bd4272`. A row cannot reach `Atlas launcher` or `tested local route` without a client run somebody got an answer from, so every row below carries the exact reason it stopped where it did:

- **GitHub Copilot** -- Absent: copilot did not resolve on PATH, so the command was not run. No declared authentication signal was observed on this host. No Copilot seat is held on the active account and the organisation's Copilot CLI policy is unconfigured. Seat entitlement is a network fact this probe does not read, and clearing the blocker needs either an organisation policy change or a new personal plan.
- **Cursor** -- Absent: cursor-agent did not resolve on PATH, so the command was not run. No declared authentication signal was observed on this host. The client is absent and its authentication is an interactive account sign-in this environment has no Cursor account for.
- **Gemini CLI** -- Absent: gemini did not resolve on PATH, so the command was not run. No declared authentication signal was observed on this host. The client is absent and no authentication method is configured on this host.
- **Windsurf** -- Absent: windsurf did not resolve on PATH, so the command was not run. No declared authentication signal was observed on this host. The client is absent, and the product the issue names is now published as Cascade inside Devin Desktop. Which product a Windsurf row should describe is a naming question a maintainer has to settle before any run.
- **Cline** -- Absent: cline did not resolve on PATH, so the command was not run. No declared authentication signal was observed on this host. The client is absent and unauthenticated. Its positional-prompt form still defaults to act mode with auto-approval on, so the recorded hazard is unchanged.
- **Roo Code** -- No client binary is declared for this harness, so no client run was attempted. No declared authentication signal was observed on this host. The product is sunset and its repository archived. No active successor was named, so there is nothing to test.
<!-- harness-roster:end -->

Before Fiat starts, confirm that the issue is still open and does not already
have an active owner, issue-number branch, pull request, or merged delivery. An
open issue alone is not proof that the work remains outstanding.

### The hand-off in thirty seconds

1. Ask the Atlas for one job.
2. Read the issue number, URL, and complete prompt from that response.
3. Open the repository in the local harness you will keep for the run.
4. Read the repository instructions and install or update Hexaemeron if your
   harness supports it.
5. Send the exact prompt and let Fiat establish the study and runbook before
   implementation.
6. Answer genuine design or authority questions. Do not waive failed gates or
   widen the issue.
7. Continue until the controller reaches completion or a verified
   completed-step checkpoint.
8. Send the result through the normal GitHub pull-request and maintainer-review
   path.

## What Fiat does

Fiat keeps the delivery in this order:

```text
study -> runbook -> implementation -> audit -> prose -> push -> integration
```

The study defines the problem, sources, options, chosen design, and risks. The
runbook divides it into checkable steps. Each step is implemented, tested,
audited, and explained before the controller permits its next dependent
action. Durable state and receipts, not chat, determine progress.

The four worker roles are deliberately bounded:

- Surveyor writes one study.
- Mason implements and tests one runbook step.
- Warden performs one audit round and preserves every finding.
- Scribe checks one prose surface without inventing facts.

Only Fiat accepts their results and advances the controller. Read
[`fiat-in-plain-english.md`](./fiat-in-plain-english.md) for the full walkthrough.

## Identity and authorship

You are the external contributor, not Shoggoth. Keep your own Git author,
valid signing identity, and GitHub account. Fiat adds required Shoggoth
provenance without replacing you. Never copy, upload, request, or configure a
private Shoggoth signing key or GitHub account for your contribution.

Runtime hosts and models are not co-authors or generated-by bylines for
governed work. Remove:

- a `Co-Authored-By` trailer naming Claude, Claude Code, Codex, ChatGPT,
  Copilot, Gemini, or another runtime host;
- a `Generated with` or `Generated by` line naming Claude, Claude Code, Codex,
  ChatGPT, Copilot or Gemini, refused as a runtime-host byline; and
- a cloud-session link added as a host byline to a pull-request description.

The current expression is bounded: a line naming any other host passes the
gate and still has to go. It is not an approved list of model bylines.

Claude Code sessions opened in this repository read
`.claude/settings.json`, which disables its three known attribution defaults.
The cloud-link behaviour has not been observed as proved, so Fiat still reads
the pull-request body back and refuses forbidden lines. Other harnesses may
need the lines removed before the receipt.

## Checkpoints and interruption

After each accepted step, Fiat writes a verified archive to its fixed local
checkpoint store before continuing. A later local agent can resume from that
completed boundary only after verifying the archive, Git state, signatures,
and controller capsule.

Keep the harness open through an active step. Arbitrary mid-step state is not a
portable checkpoint. If you must interrupt, preserve only what Fiat identifies
as safe and mark the run incomplete.

When another local agent takes over a completed step, pass the checkpoint's
absolute path and digests directly. Do not ask the user to choose a destination,
infer progress from chat, upload the checkpoint to an unapproved service, or
reuse a worker handle whose visible issue, step, or role belongs to an older
run.

The current transport is the local filesystem. It is not a remote continuation
service and it does not support casual movement between machines.

## Completion and maintainer review

A complete run has reached the controller's stated endpoint. The required
implementation and checks are complete, the changes have been committed and
pushed as authorised, and the contribution is ready for the ordinary pull
request and maintainer-review path.

Completion does not promise acceptance or merge. It gives a maintainer an
inspectable issue, diff, test record, audit record, prose account, and list of
remaining limits.

A contributor working from a fork may not have authority to close the issue.
Name it in the pull-request body and leave closure to the maintainer who merges
the delivery. Otherwise an open but already delivered issue can return to the
Atlas pool.

## When something goes wrong

- If Atlas returns no job, stop. Do not invent an issue or choose a Wave.
- If the issue is already owned or delivered, request one new allocation before
  Fiat starts.
- If installation, signer, or access is missing, state the missing condition
  before changing or publishing anything.
- If a check fails, preserve the state and output, follow the named recovery,
  and rerun the same check.
- If a required audit tool did not run, the round is not clean.
- If the run stopped mid-step, mark it incomplete. Do not present it as a
  resumable checkpoint.
- When handing over a completed checkpoint, pass its path and digests. The new
  local agent verifies it before continuing.

## The manual Atlas route

Use this only when a checked bootstrap is unavailable:

1. Open [`GET /api/job`](https://shoggoth-wave-atlas.functi0nzer0.chatgpt.site/api/job).
2. Read `job.number`, `job.url`, and `job.prompt` from that one response.
3. Clone or open `wildcat-finance/skills` in the local harness you will keep for
   the run.
4. Read `AGENTS.md`, install or update Hexaemeron where supported, and send the
   exact `job.prompt`.
5. Finish the same local Fiat run and use the pull request it produces.

This does not turn a file-reading agent into a tested one-click launcher or
change the checkpoint boundary.

## Credit for merged work

Fiat records whether your human authorship reached the base. For every commit
it pushes, it records the GitHub account matched to the commit and a digest of
the author address, never the address itself. At integration it refuses to
claim success if the base no longer carries those identities, either in the
commits or in the merge that replaced them.

Your commit author address must be one GitHub can match to your account. Fiat
records an unmatched address as unresolved instead of guessing. GitHub's own
contributor view is computed and published by GitHub on its schedule; no local
receipt can force an entry to appear.

A daily repository job generates [`CONTRIBUTORS.md`](../CONTRIBUTORS.md) and the
thanks section in the root README from public history. It ranks resolved Skills
commits, using merged pull requests across Wildcat Skills and Shoggoth Wave
Atlas as the tie-break. It excludes runtime hosts, the Shoggoth account, and
the repository owner with recorded reasons.

That list is a narrow record of merged work, not a ranking of people. It does
not measure judgement, identify who wrote every line, or credit every reviewer
and collaborator. The full boundary is recorded in
[`ADR-019`](decisions/ADR-019-rank-contributors-by-resolved-identity.md).
