---
name: hypomnema
description: >-
  Decide what gets written down and where it lives: the decision record behind
  a choice that would be expensive to reverse, the comment that explains why
  rather than what, the runbook an alert points at, and the README somebody
  starts from. Use when a decision is made, an interface changes, an alert
  needs somewhere to point, or the same explanation has been given twice. Do
  not use it to lint or rewrite prose, which belong to imprimatur and vulgate,
  and do not use it to decide what a study must contain, which belongs to
  protasis.
metadata:
  version: "5.6.0"
---

<p align="center">
  <img src="../../assets/characters/hypomnema.png" width="1200">
</p>

# Hypomnema

From *hypomnema*, the note written so the reason survives the person who had
it. Code records what was built. This records why, and what was turned down.

## Where this sits

Hypomnema owns what gets recorded and where it goes.

Protasis decides what a study must answer before the build. Hypomnema takes the
later question: which expensive-to-reverse decision, interface reason, runbook,
README, or alert pointer must survive and which existing home owns it. During
Fiat's prose phase it runs before Scribe applies Imprimatur and Vulgate. Fiat
keeps the mask order, pull-request text, and receipt.

A Synkrisis finding may give a maintainer a reason to write or point to a
record. It does not choose the durable home; Hypomnema's ordinary placement
judgement still owns that decision.

Its version, held frontier, next job, and maturity state live in
[EVOLUTION.md](EVOLUTION.md).

**Current state.** The ordinary walk checks recognised record and runbook
pointers and shapes. An explicit study mode now binds one selected Protasis
candidate to exactly one ADR or governed-skill ledger through a closed design
bridge. No evidenced unchecked mechanical frontier remains.

## Match what is already there

Look before writing. An existing convention beats every default below, and a
second scheme alongside the first helps nobody.

Check for decision records already in the tree, the numbering and naming they
use, the headings they carry, and any tooling that generates them. Where the
evidence conflicts, say so rather than quietly picking one.

Three conventions already run in this marketplace and its applications. Each
governed skill records its own decisions in an `EVOLUTION.md` ledger, so a
decision about one skill belongs there and not in a second document. The
marketplace's cross-cutting decisions live under `docs/decisions/` as numbered
records in the shape below, ADR-001 onward. The application generates its
changelog from conventional commits through release-please, so the commit
message is the changelog entry, and hand-editing the generated file loses at
the next release.

## Write the record when reversing gets expensive

A decision earns a record when undoing it later would cost real work: a
framework or a dependency that spreads, a data model, a trust boundary, an
interface others build against, a storage format that outlives its writer.

Where no convention exists, put them in `docs/decisions/` numbered in sequence,
and keep this shape.

```markdown
# ADR-001: <the decision, stated as a decision>
## Status
Accepted, 2026-08-18. Superseded by ADR-00N once it stops being true.
## Context
What forced a choice, and what was already true.
## Decision
What was chosen, in one sentence.
## Alternatives
Each one considered, what it offered, and why it lost.
## Consequences
What this makes easy, what it makes hard, and what it commits us to.
```

The alternatives section is the part that pays. A record saying only what was
chosen tells a reader nothing they cannot get from the code; the value is in
the options that lost and the reason they lost.

Records are not deleted when they stop being true. Write a new one, mark the
old superseded, and leave the history where somebody can follow it.

A shipped study is a ready-made source: it names a chosen design and the
alternatives that lost, which is exactly the material above. Before the step
that ships a study is receipted, that choice becomes a standing record or
points at one -- an ADR under `docs/decisions/` when the choice cuts across
the repository, the skill's `EVOLUTION.md` row when it belongs to one
governed skill. The study itself is a run artefact, not a record: the next
reader finds the code and the ledgers, and the option that lost survives only
where a record holds it. Pointing is enough; writing the same decision into
two homes is the drift the conventions above refuse.

## Comment the reason, never the mechanism

A comment restating the line above it goes stale and was never worth reading.
A comment carrying the reason stays true for as long as the reason does.

```python
# Nothing: the next line says this
counter += 1

# Something: the window resets at the boundary rather than on a timer,
# so a burst at the edge cannot buy a second allowance
if now - window_start > WINDOW:
    counter, window_start = 0, now
```

Write down a trap where somebody will hit it: an ordering that matters, a call
that must happen before another, an argument that looks optional and is not.
Point at the decision record when one exists.

Leave no commented-out code, since history already has it, and no note
promising work you could do now.

## Where each thing lives

- **A decision that shapes the code.** A record under `docs/decisions/`.
- **A decision about a governed skill.** That skill's `EVOLUTION.md`, which is
  the ledger the versioning contract already checks.
- **What an alert means and what to check first.** `docs/runbooks/`, one file
  per alert, named for the alert so the link in the alert can find it. Three
  answers make a runbook: `## What fired`, `## First check` and
  `## Who to wake`, each with a non-empty answer.
- **How to start the project.** The README: what it is, how to run it, the
  commands, and a pointer onward.
- **What shipped.** The commit message, in the convention the repository
  enforces, where the release tool can reach it.
- **What an agent needs.** The instructions file the runtime reads, kept
  current, because a stale one is followed exactly as confidently as a fresh
  one.

## Interfaces carry their own documentation

Something others call says what it takes, what it returns, and what it raises,
next to the signature rather than in a separate document that drifts. One
example beats a paragraph. Where an interface crosses a process boundary, the
schema is the documentation and prose describes only what the schema cannot.

## The mechanical subset

Five rules here are settled by a parser: whether the things a record points at
exist, whether a decision record carries the template's shape, whether a
source comment's record reference resolves, and whether each Markdown file
below a `runbooks` directory carries the three runbook answers. The fifth binds
one caller-named study's declared decision to the selected candidate in an
already checked Protasis design-evidence record and to one established standing
record. Run the ordinary walk over the documents a step touched, and require
exit 0.

```bash
python3 "$PLUGIN_ROOT/skills/hypomnema/scripts/hypomnema.py" docs plugins
```

For a step that ships a study, run the explicit bridge check as well:

```bash
python3 "$PLUGIN_ROOT/skills/hypomnema/scripts/hypomnema.py" \
  --study <repository-relative-study> \
  --design-evidence <repository-relative-design-evidence.json> \
  --repo-root <repository-root>
```

It reports a relative link that resolves to nothing, a superseding pointer
naming a record that is absent, a Markdown or block-YAML `runbook:` pointer
naming a local target that is not there,
a decision record under a decisions directory missing its dated status or
one of the template's five sections, and a source comment citing a record
that does not exist. H007 also reports each absent or empty `What fired`,
`First check` or `Who to wake` answer in a Markdown file below a directory
named `runbooks`; headings and bodies inside fenced examples do not count. A
record pointing at something absent is worse than no record, because it reads
as though the reason exists and was checked. The walk reads `#` comments in
Python and shell and `//` comments with `/* */` blocks in Solidity, JavaScript
and TypeScript, leaving string literals and URLs alone; in source files the
pragma is the bare `hypomnema: allow <why>` after a comment marker. Test
fixtures are skipped on a directory walk, since a specimen documenting a
fault is not a record.

Study mode reports H008 unless exactly one closed `design-bridge` fence carries
the three ordered rows `schema`, `decision` and `record`. The schema is
`hypomnema-design-bridge/v1`; the decision equals the selected candidate in the
strictly decoded `protasis-design-evidence/v1` selection envelope; and the
record is one portable repository-relative path. Protasis remains the only
owner of the complete candidate, criterion and result-matrix semantics, so a
valid checked record may retain pending conformance cells after design lock.
Hypomnema bounds those arrays and consumes only the schema, closed candidate
set and selected-candidate membership needed for this join.

The target is an ordinary non-symlink file read stably below the supplied root.
It is either an ADR-numbered Markdown file below a `decisions` directory or an
`EVOLUTION.md` beside a `SKILL.md` whose governed name matches its directory
under a plugin skills tree. H008 also refuses absent, repeated, malformed or
unclosed blocks, a selection mismatch, absolute, escaping, backslash or
control-bearing paths, a wrong or dangling home, oversized inputs, duplicate
JSON keys, excessive JSON depth, special files and a file that changes while
it is read. The ordinary walk never infers a bridge, so historical studies and
H000 through H007 retain their existing scope.

The YAML H003 pass reads generic `runbook:` keys outside comments and block
scalars, resolves relative Markdown targets from the YAML file's directory and
does not classify alerts or require annotations.

In Markdown, a `runbook:` keyword inside an inline code span is a quoted
specimen and H003 passes over it. A record that shows what a pointer looked
like is not promising that the target exists, and an append-only document
cannot be given a pragma after the fact. The keyword's own position settles
it, so a bare `runbook:` followed by a backticked path is still read and still
resolved. Spans pair per line by backtick-run length; an unmatched run stays
literal text, a backtick escaped by an odd number of backslashes opens
nothing, and a span that opens on one line and closes on the next is not read
as a span, so a pointer on that line stays checked.

The Markdown keyword begins at the start of a line or after a character other
than a word character or hyphen. List items, dotted `annotations.runbook:`
forms and sentence-initial keywords stay live. Word suffixes such as
`myrunbook:` and hyphenated tokens such as `sub-runbook:` are not pointers.

H001 gives a relative link inside an inline code span the same reading: a
quoted link is a mention and earns no finding, while a link outside a span,
after an unmatched backtick run or across a line break is still resolved.

The bundled third-party skills are skipped, since they document files they
generate in the target repository rather than files that live here. Pass
`--include-vendored` to check them anyway.

Deliberate walk exceptions state a reason: `<!-- hypomnema: allow <why> -->`, on the
line or the one above it. For H007, only a reasoned pragma on the file's first
line or the relevant heading suppresses the finding. Deciding what deserves a
record stays judgement. A pragma cannot manufacture or suppress an H008 bridge.

## Rationalisations

- "The code documents itself." It shows what. It cannot show what was
  rejected, or the constraint that made the choice.
- "Docs come once the interface settles." Interfaces settle sooner when
  written down, because the writing is the first test of the design.
- "Nobody reads documentation." Agents read it every session, and so does
  whoever is on call at three in the morning.
- "A decision record is overhead." Ten minutes now against the same argument
  had again in six months, with nobody able to recall the reason.
- "Comments go stale." Comments about mechanism go stale, which is why this
  skill only asks for the ones about reason.

## Red flags

- A choice that would be expensive to reverse, with no written reason.
- A second decision-record scheme beside an existing one.
- A hand-edited changelog in a repository that generates it.
- A skill decision written somewhere other than its ledger.
- An alert whose runbook link goes nowhere.
- A README that does not say how to run the project.
- Commented-out code kept instead of deleted.
- A note promising work that could be done now.
- An agent instructions file describing a layout that has since moved.

## Before the prose phase is receipted

Report the count, then name every item that failed.

- [ ] Every expensive-to-reverse decision in this step has a record.
- [ ] If this step ships a study, its chosen design and the alternatives that
      lost are in a standing record, or point at the one that holds them.
- [ ] Each record names the alternatives and why they lost.
- [ ] Superseded records are marked, not deleted.
- [ ] Records follow the convention already in the tree.
- [ ] A skill decision went to its ledger rather than to a second document.
- [ ] New alerts have a runbook file their link resolves to.
- [ ] Changed interfaces document arguments, returns and failures.
- [ ] Non-obvious traps are commented where somebody meets them.
- [ ] No commented-out code and no deferred note remain.
- [ ] The agent instructions file still matches the tree.

## Hand back

Lead with what was recorded and where it went. Name each decision this step
made and the file that now holds its reason.

Separate the decided from the still open. A choice made with its alternatives
written down is settled. One made because nobody objected is open, whatever the
diff suggests, and saying which is which is the whole point of the record.

End with one action: the decision still needing a record, the convention
conflict somebody has to resolve, or the runbook an alert is waiting on.

## Promise Machine contract

### hypomnema-pointer-gate

- Promise: A zero-exit Hypomnema lint establishes that the bounded checker found no unresolved relative links, absent superseding records, missing recognised Markdown or block-YAML runbook targets, absent and empty required runbook answers in the selected first-party documents, or invalid explicit design bridge in a named study-mode run.
- Evidence: The exact lint version, mode, arguments, selected paths, design-evidence and repository-root identities where supplied, structured findings and zero exit status.
- Evidence classes: checked
- Boundary: A clean ordinary walk proves only that recognised pointers resolve and recognised alert runbooks carry the three required answers at check time; it does not infer or require a design bridge. A clean study-mode run proves only the strict selection-envelope join and one declared established home; Protasis owns full design-record validity, ADR shape and the versioning contract own record content, and no semantic duplicate outside the closed declaration is discovered. The YAML pass does not classify alerts or establish annotation presence, a Markdown `runbook:` keyword or relative link inside an inline code span is not a recognised pointer so a clean result says nothing about a target quoted as a specimen, word-suffix and hyphenated `runbook:` tokens are not recognised keywords, and the lint does not prove that records or operational answers are correct, complete or current.
- Authorises: Passing the mechanical record and runbook-shape gate for the exact paths and checker version recorded.
- Consequence: 1
- Refuses: Unsafe, unreadable, unstable or oversized paths, unresolved recognised pointers, a missing or empty required runbook answer, an unexplained suppression, a malformed or mismatched explicit design bridge, or a claim about documents excluded from the run.
- Recovery: Restore or correct the target, mark supersession accurately, add the missing runbook or answer, repair the one closed bridge or its selected record, and rerun the same bounded lint mode.
- Exceptions: none

### hypomnema-record-placement

- Promise: A completed record-placement review establishes that each expensive-to-reverse decision introduced by the step has a reasoned record in the repository's established location, with rejected alternatives and resolvable pointers.
- Evidence: The step diff, decision inventory, authored or superseded records, alternatives and reasons, pointer-gate result and unresolved-decision list.
- Evidence classes: checked, inferred, recorded
- Boundary: The review covers the decisions identified in the named step; it does not prove that every future reader agrees with them or that an unidentified decision was documented.
- Authorises: Treating the recorded choices as the current project decisions until superseded through the same convention.
- Consequence: 2
- Refuses: A costly choice with no reason, a second record scheme, deletion of superseded history, an absent target or a decision placed where the repository's readers will not find it.
- Recovery: Identify the missing choice, write the reason and rejected alternatives in the established location, repair its pointers and repeat the review.
- Exceptions: none
