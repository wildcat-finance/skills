# Study: gate durable agent prose before publication

Assuming, unless corrected: the new rule governs agent-authored audit records,
GitHub issue titles and bodies, and GitHub issue comments written after this
change. Existing audit entries, issue text, and comments remain untouched.
`AUDIT.md` records require Sapheneia. Issue submissions and comments require
Sapheneia, Vulgate, and Imprimatur. A GitHub issue submission includes its title
and body.

## 1. Problem statement

Sapheneia currently shapes the agent's session replies and explicitly yields an
artefact's substance and format to the skill that owns it. That leaves three
durable agent-authored surfaces outside its promise: Fiat audit records, GitHub
issue submissions, and comments on those issues. Those surfaces are read after
the working session has gone away, so hidden state, process narration, or a
dropped qualification costs more there than in chat.

Fiat's `audit-round` command checks a findings count, lint exits, and a
conditional Elenchus verdict. It does not require the record to have crossed a
Sapheneia pass. Root `AGENTS.md` specifies four issue queues and their title
prefixes, but it does not state a pre-publication prose path for an issue or
comment. Fiat's integration instructions also allow a short task-issue closing
comment after the prose phase without naming any prose pass.

Done means all of the following are true:

1. Sapheneia has a bounded durable-record operation for the three named
   surfaces. Invoking that operation alone does not activate session-wide
   response shaping.
2. The operation removes connective and process prose only. Exact identifiers,
   paths, `file:line` locations, hashes, addresses, selectors, numbers, dates,
   links, quotations, severities, findings, verdicts, status, uncertainty,
   negative evidence, and required host structure survive.
3. `hexctl next` names an exact Sapheneia obligation for every audit round,
   `audit-round` refuses a missing or different declaration, and the accepted
   identifier is recorded in state and the hash-chained ledger.
4. Root instructions require agent-authored issue titles, bodies, and comments
   to follow Sapheneia, Imprimatur, Vulgate, then an Imprimatur re-lint of the
   exact publishable bytes. Required queue prefixes and body rules are frozen
   before those passes.
5. Fiat's one existing issue-comment path, the closing comment for a recorded
   task issue, names and follows the same sequence before publication.
6. Tests hold the Sapheneia promise, routing language, issue/comment rule,
   audit-round refusal, next-action disclosure, and receipt field together.
7. The Sapheneia and Fiat generation rows advance without moving either held
   frontier revision, digest, status, or Next Fiat job. Delivery-package
   versions agree across both host manifests and both marketplaces.
8. No existing durable record is rewritten, no generic issue-publishing wrapper
   is introduced, and no result claims that GitHub itself rejects a bypass.

## 2. Prior art

The target is current `main` at
`dd23413ef6e9021bd80b930ad57e1766bf166f0b`. Targeted reads covered the current
Sapheneia skill, runtime, fixtures, tests, manifests, and evolution ledger; the
Fiat skill, controller, Warden contract, audit loop, prose pass, push discipline,
tests, and evolution ledger; root routing and issue-queue instructions; and the
relevant Fiat and Sapheneia records in `audit/AUDIT.md`.

The last two merged Fiat changes were PR #511, which made governed authorship
checkable, and PR #493, which added the checked-and-recorded Elenchus declaration
to audit fixes. The latter is the closest controller pattern: Fiat accepts an
exact operator declaration, records it, and states that it does not attest the
underlying report bytes. The last two merged Sapheneia changes were PR #293,
which bound its Promise Machine contracts, and PR #80, which adopted its
evolution ledger. Neither gives Sapheneia a durable-record operation.

Open issue #429 and open PR #509 own a different audit change: the raw record
schema, timestamp, bounded suffix parser, and synopsis. PR #509 is green and
mergeable but is not on `main`. This study neither copies that parser nor
changes its fields. The new declaration must compose with that branch when one
side is rebased.

The live queue also fixes four ownership boundaries:

- #421 owns an executable generic Sapheneia pre-send checker.
- #501 owns Vulgate's code-adjacent register and protected-span rule.
- #427 owns the unresolved tree-wide Brevitas scope and document modes.
- #372 and #373 own missing Brevitas evidence-token coverage and JSON
  diagnostics.

This change does not close or silently implement those issues. The repository
contains no `gh issue create`, `gh issue comment`, issue-comment API call, or
other central publication command to put behind a server-side gate.

## 3. Constraints and non-goals

- Promise Machine results authorise only the transition in their canonical
  skill. Sapheneia shapes information, Vulgate changes register without changing
  content, and Imprimatur checks the exact bytes passed to its checker.
- The existing Fiat prose order is lint, Vulgate, then re-lint. Sapheneia runs
  before that sequence for the named GitHub surfaces so the final Imprimatur run
  still covers the exact published bytes.
- Queue titles keep their required `{skill}-next`, `{skill}-N`, `{skill}-wish`,
  or `framework-N` prefix and issue bodies keep the queue-specific opening.
- `AUDIT.md` stays append-only. The new rule applies to each candidate record
  before append and does not edit earlier bytes.
- The controller may prove that an exact declaration was supplied. Until #421
  ships, it cannot prove that a model performed Sapheneia's semantic work.
- Root instructions can govern agents working in this repository. They cannot
  make GitHub reject a human or tool that ignores those instructions.
- Brevitas runs only where its current contract already selects it, after the
  word-choice and register passes. This change does not create a universal
  issue or audit-log Brevitas gate.
- No Solidity, dependency, credential, network client, GitHub App, webhook, or
  new subprocess wrapper is in scope.
- The held Sapheneia, Imprimatur, Vulgate, Brevitas, and Fiat frontier jobs stay
  unchanged.

## 4. Design options

### Option A: instructions only

Extend root and Fiat prose instructions, with no controller or Sapheneia promise
change. This is small, but an audit round can still be receipted without any
Sapheneia evidence and the canonical skill still says it governs replies rather
than the durable record. Rejected.

### Option B: bounded Sapheneia operation plus layered gates

Add `sapheneia-durable-record-shape` to the canonical Sapheneia skill. It accepts
only audit records, GitHub issue titles and bodies, and GitHub issue comments.
It preserves the owning format and the protected evidence inventory, compresses
only prose that does not change the claim, and returns a checked declaration.
Using it for one artefact does not silently turn on session-wide Sapheneia.

For audit rounds, make `--audit-filter sapheneia:sapheneia` mandatory. Expose
the exact flag and value through `next`, pass them in the Warden packet, and
record the value in the round receipt and ledger event. This is a declaration
gate, with the same honesty boundary as the Elenchus verdict.

For issue titles, bodies, and comments, add a root publication rule with this
order:

1. freeze the queue format and the complete evidence inventory;
2. apply the bounded Sapheneia operation;
3. run Imprimatur and clear its reported defects without losing qualifiers;
4. apply Vulgate in the fitting register with content parity;
5. re-run Imprimatur on the exact publishable bytes.

Fiat's task-issue closing comment follows the same rule in its push discipline.
Its instructions require a byte-for-byte protected-token comparison and remote
readback before the issue is treated as closed. The controller does not claim
semantic or remote-byte proof it does not possess.

This option is chosen. It gives the audit path a refusal and durable receipt,
gives every repository agent one publication rule, keeps the final lint bound
to the bytes sent, and leaves the generic executable checker to #421.

### Option C: wrap or replace every GitHub publication command

Build a command or GitHub App that accepts drafts, runs all checks, publishes,
and reads the result back. This would add network, credential, subprocess,
authentication, and bypass surfaces. It would also consume most of #421 before
that issue's corpus and diagnostic dependencies land. Rejected for this run.

### Option D: rewrite records into one terse template

Force audit, issue, and comment prose into one shared template, and compact old
records. This conflicts with the audit schema owner, the four issue queues,
Vulgate's content-parity rule, and append-only history. Rejected.

The trade is explicit: Option B can mechanically establish the audit
declaration and final Imprimatur exit. Sapheneia and Vulgate remain
model-checked operations, and generic GitHub publication remains governed by
repository policy rather than a server hook.

## 5. Risk register seed

```risk-register
evidence-loss | Sapheneia compression across audit and GitHub prose | protected facts, unknowns, negative evidence, identifiers, numbers, links, severities, verdicts and host structure survive byte-for-byte where exactness matters
false-semantic-proof | the audit filter declaration accepted by hexctl | state and docs call it a checked operator declaration and never claim the controller assessed the prose
final-byte-drift | Vulgate output after an Imprimatur check | a second Imprimatur run gates the exact title, body or comment bytes sent
queue-format-drift | issue title prefixes and queue-specific body openings | the publication rule freezes them before any prose pass and tests name all four queues
github-bypass | issue and comment publication outside repository instructions | docs state that GitHub does not enforce this rule and no server-side claim is emitted
history-rewrite | existing audit entries, issues and comments | no migration or edit path exists and tests compare only new contract text and new receipts
session-leak | one durable-record pass activating persistent Sapheneia | the new promise is bounded to the named artefact and session activation remains a separate promise
open-issue-collision | wishes 421, 501, 427, 372 and 373 | the implementation adds no generic checker, protected-span feature, universal Brevitas gate or JSON diagnostic mode
pr-509-overlap | both branches change Fiat audit-round files | keep the change to one independent flag, receipt field and instruction block; rebase and rerun both suites if main advances
frontier-drift | generation work on Sapheneia and Fiat ledgers | retain each frontier revision, digest, status and Next Fiat job exactly while incrementing only the generation axis
task-comment-mismatch | Fiat's prepared closing comment and the remote issue | push discipline requires verbatim publication and a GitHub readback, while the controller disclaims remote-byte attestation
```

Look hardest at `evidence-loss`, `false-semantic-proof`, `final-byte-drift`, and
`pr-509-overlap`.

## 6. Glossary seeds

**Durable record:** Agent-authored prose that remains after the session: one
Fiat audit record, one GitHub issue title and body, or one GitHub issue comment.

**Sapheneia declaration:** The exact `sapheneia:sapheneia` value asserting that
the bounded durable-record checklist was applied. It is evidence of the
operator's declaration, not a semantic proof by `hexctl`.

**Protected evidence inventory:** The claims, qualifications, unknowns,
negative evidence, identifiers, paths, locations, hashes, addresses, selectors,
numbers, dates, links, quotations, severities, verdicts, status, and required
host structure that a prose pass may not drop or change.

**Publishable bytes:** The exact UTF-8 title, body, or comment submitted to
GitHub after the final Imprimatur run.

**Bounded operation:** Applying Sapheneia to one durable record without changing
the session activation state.

## 7. Sources

| Source | Evidence used | Boundary |
| --- | --- | --- |
| `dd23413ef6e9021bd80b930ad57e1766bf166f0b` | Exact base for the study and replacement Fiat run | Later main changes require a rebase and fresh proof |
| `plugins/sapheneia/skills/sapheneia/SKILL.md` and `plugins/sapheneia/AGENTS.md` | Current session-only activation, ranked rules, pre-send check, and Promise boundaries | No executable semantic checker exists |
| `plugins/sapheneia/tests/**` and `plugins/sapheneia/skills/sapheneia/EVOLUTION.md` | Current promises, host description checks, version, frontier revision, digest, and held job | Tests cover contract text, not cross-model behaviour |
| `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | Current audit receipt, lint exits, Elenchus declaration, ledger event, and next directive | Main lacks PR #509's raw suffix parser |
| `plugins/hexaemeron/skills/fiat/references/{audit-loop,prose-pass,push-discipline}.md` | Audit append path, lint-voice-re-lint order, and task-issue closing comment | Instructions do not prove remote GitHub bytes |
| `AGENTS.md` and ADR-009 | Four issue queues, title prefixes, and body ownership | No pre-publication prose sequence is stated |
| `audit/AUDIT.md` | Relevant Fiat and Sapheneia record shapes and append-only use | Historical entries are evidence and remain unchanged |
| merged PRs #511, #493, #293, and #80 | Closest Fiat declaration gate, current authorship rule, Promise binding, and evolution baseline | Prior merges do not authorise this new operation |
| open issue #429 and PR #509 | Separate owner and live implementation for audit schema, timestamp, raw suffix, and synopsis | This study adds no schema parser or synopsis |
| open issues #421, #501, #427, #372, and #373 | Existing owners for executable Sapheneia checks, Vulgate protected spans, and Brevitas gaps | Those issues remain open and their acceptance is not claimed |
| live repository search for issue publication calls | No central `gh issue create/comment/edit` or equivalent API path was found | Absence in the tracked tree does not prevent an external caller |

## 8. Signals, and the questions behind them

The audit gate emits no metrics. Its on-call questions are local and bounded:
what durable-record skill was declared, which round accepted it, and why was a
round refused? `next` answers the first before work starts. The round entry and
ledger event retain the exact identifier. Refusal names a missing or wrong
`--audit-filter` without printing audit prose.

Issue and comment publication has no repository runtime to observe. The useful
signal is the final Imprimatur exit plus the agent's content-parity and
Sapheneia checks. Instructions must not turn those into a claim that GitHub ran
them. Fiat's task-issue path adds a remote readback of the posted comment so an
operator can catch a copy or quoting error before closure is reported.

## 9. Boundaries, per capability

Sapheneia receives a draft and its protected evidence inventory. It may reorder
or shorten connective prose, expose state and negative evidence, and remove
process narration. It may not change the owning audit schema, issue queue,
finding, severity, status, verdict, qualification, fact, or required structure.

Vulgate receives the Sapheneia-shaped candidate and changes register only. The
inventory comparison supplies the evidence for content parity. Imprimatur
receives the exact candidate bytes before and after Vulgate and reports only its
known lexicon and structural patterns. None establishes factual truth.

Fiat receives the exact Sapheneia skill identifier. It checks equality, records
the declaration, and refuses absence or disagreement. It does not interpret the
audit text. GitHub remains outside the controller boundary.

## 10. The budget, or its absence

No latency or throughput budget applies. The controller adds one constant-size
argument comparison and one receipt field. The prose passes already run over
bounded drafts. The chosen design adds no tree scan, network request, model
call, or parser. A performance claim would therefore be unsupported and is not
part of acceptance.

## 11. The fail-closed posture

Red tests first show that `audit-round` accepts no Sapheneia declaration, that
`next` does not name one, that no receipt retains one, and that root instructions
omit the issue/comment path. After the change:

- missing and different audit-filter values exit non-zero before state or ledger
  mutation;
- the accepted value is exactly `sapheneia:sapheneia`;
- issue and comment prose is not published by a compliant agent after a failed
  Imprimatur run, failed content-parity check, changed queue prefix, or dropped
  protected token;
- any failed repository, plugin, Promise Machine, version, prose, tree, or
  boundary check stops publication; and
- a main advance or overlap with PR #509 triggers rebase, combined tests, and a
  fresh signed commit rather than an inferred clean merge.

The recovery is to restore the protected content or missing declaration, rerun
the exact gate, and publish only the checked bytes. Existing history is never a
recovery target.

## 12. Decisions and their homes

The reversible-at-cost decision to give Sapheneia a separate bounded
durable-record promise belongs in the canonical Sapheneia `SKILL.md`, runtime,
fixtures, tests, README, router text, marketplace prose, and a root ADR. Its
generation row records the behaviour change while retaining the held corpus
frontier.

The audit declaration belongs in Fiat's `hexctl.py`, Warden packet, audit-loop
reference, canonical skill, tests, and evolution ledger. The controller and
ledger own mechanical receipt; Sapheneia owns what the declaration means.

The issue and comment sequence belongs in root `AGENTS.md` because it governs
every agent writing to this repository. Fiat's push discipline repeats the
task-issue closing-comment case because the plugin must remain usable outside
this checkout. Imprimatur and Vulgate keep their current canonical contracts;
this run selects them for a new host surface but does not change their promise.

The study and runbook ship under `docs/durable-agent-prose-gates/`. The ADR
records why a repository policy plus one controller declaration was chosen over
a GitHub wrapper. Open issues #421, #501, #427, #372, and #373 remain the homes
for the work this design refuses.

### Amendment -- 2026-08-24

**What changed.** Step 2's runbook entry says Fiat's frontier revision is `receipted-lint-rounds`; the pinned base records `state-shape-validation`, which is the revision the implementation must retain. The former token is a documentary error and is superseded by this amendment.
**Why.** A direct read of `plugins/hexaemeron/skills/fiat/EVOLUTION.md` at `dd23413ef6e9021bd80b930ad57e1766bf166f0b` disproved the runbook token during the pre-commit Step 2 review.
**Steps touched.** Step 2.
**Still holding.** Step 2: entry holds; exit holds.

### Amendment -- 2026-08-24

**What changed.** Step 2's runbook says to rebase if `main` advances first. Fiat's canonical push discipline forbids rebasing or rewriting the signed stack and instead requires one signed `sync-run` merge after the final step merge when the integration pull request conflicts. The canonical transition supersedes the runbook's rebase wording; the final combined tree must be regenerated and checked before integration.
**Why.** PR #518 advanced `origin/main` to `191f2ce1d60abb8068887095a8c39fb4341f0be6`, and a combined-tree probe found a real `.horos/boundary.json` conflict. The live condition now requires Fiat's recorded integration recovery rather than a history rewrite during Step 2.
**Steps touched.** Step 2.
**Still holding.** Step 2: entry holds; exit holds.
