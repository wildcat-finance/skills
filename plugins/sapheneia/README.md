![Sapheneia](./assets/characters/sapheneia.png)

# Sapheneia

<!-- marketplace-context:start -->
## In one line

Sapheneia keeps actions, boundaries, state, evidence, unknowns, and next steps visible for an AuDHD reader, and shortens every record the agent writes down to the least prose its protected evidence allows.

**Current frontier.** Cross-model behaviour has not yet been held against a published AuDHD task corpus.

**Next Fiat job.** Use /hexaemeron:fiat to build and publish a held cross-model corpus covering debugging, explanation, destructive-action and long-running task turns, then reconcile the ten rules against its results. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Start here

Use Sapheneia when an AuDHD reader needs the action, boundary, current state,
evidence, unknowns, and next step kept visible throughout an agent session. A
separate bounded operation shapes every record the agent writes down, from an
audit record, issue, or issue comment to a pull request, a repository document,
or a commit message, cutting each to the shortest form its protected evidence
allows.

It does not diagnose the reader, change another skill's facts, or turn on
session shaping merely because one durable record was edited. The ten rules
have not yet been tested against a published held cross-model task corpus.

## Place in the collective

Sapheneia shapes the collective's interaction layer and every record its
agents write down, whether that is an audit record, a GitHub issue, an issue
comment, a pull request, a repository document, or a commit message. Warden
uses the durable-record operation before a Fiat audit receipt. Imprimatur and
Vulgate govern wording, while Brevitas governs engineering-prose structure.
Sapheneia changes none of their facts or gates and does not activate session
mode merely because it shaped one record.

A Synkrisis report may pass through these prose layers, but Sapheneia will not
change its evidence or conclusion. Synkrisis renders that report from fixed
templates and verifies that it recomputes from the original inputs, so any
reshaping happens after the verification, never inside it.

Sapheneia is the interaction contract for agents working with AuDHD engineers.
It keeps the next action, task boundary, done condition, current state, evidence
and unknowns on screen.

The session operation applies to the agent itself. Once active, it shapes commentary,
questions, progress reports, errors and final replies until the reader turns it
off. It does not diagnose anyone, and a reader's stated preference wins.

The separate durable-record operation shapes any prose the agent writes down:
an audit record, a GitHub issue title and body, a GitHub issue comment, a pull
request, a repository document, a commit message. It removes only claim-neutral
connective prose and aims at the shortest candidate that still carries every
protected item. Exact evidence, uncertainty, and the record's required
structure stay in place. Bytes another owner fixes by generator, digest, or
fixed template are outside it, as is any record already written. This bounded
operation does not activate the session contract.

The ten ranked rules and the complete activation contract live in
[`skills/sapheneia/SKILL.md`](skills/sapheneia/SKILL.md).

#### Day to day

**Developers.** A coding task spans several turns and the current step keeps
falling out of view. Sapheneia keeps one step active, states what changed and
what was verified, and ends with one next action.

**Security and audit.** A finding mixes observed behaviour, inference and an
untested assumption. Sapheneia labels each one and keeps the risk-bearing
qualification attached to the decision it changes.
## How it works

The session contract sits upstream of whatever the agent is producing. It applies to
commentary, progress updates, questions, errors and final replies for the rest
of the session once selected. It does not diagnose the reader, and it yields
as soon as the reader states a different preference.

For every record the agent writes down, the bounded operation starts from a
protected evidence inventory. It preserves exact identifiers, locations,
hashes, numbers, links, findings, verdicts, unknowns, and host structure, cuts
the prose around them as far as parity allows, and then hands the candidate to
later prose gates.

The ten rules are ranked. The first line carries the action or finished result;
asks are literal and labelled; multi-step work has one active step; facts,
assumptions and unknowns stay separate; and unfinished work ends with one next
action. Imprimatur remains the prose lint, and a voice mask remains responsible
for register.

## What it ships

- one canonical [`SKILL.md`](./skills/sapheneia/SKILL.md) shared by Codex, Claude Code and portable agents;
- an agent-facing runtime contract that makes the agent itself the subject;
- contract tests and labelled cases for session shaping, deactivation, and the bounded written-record pass.
