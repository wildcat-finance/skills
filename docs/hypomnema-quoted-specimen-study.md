# H003 must tell a quoted specimen from a live runbook pointer

Assuming, unless corrected:

1. Python 3.11 and stdlib `unittest`, matching every other checker in this
   plugin. No new dependency.
2. The run starts from `main` at `5d6fc67bb6c861f2be631eef2d7bef3c01c73e84`
   and ships one generation row on the Hypomnema ledger, not a frontier
   advance. The held `design-bridge-check` target stays exactly as written.
3. `audit/AUDIT.md` is append-only. The two lines that fail today cannot be
   edited, pragma'd, or rewrapped, so the fix has to be on the checker side.
4. Ephoros keeps E004 and its YAML annotation ownership. Nothing in this run
   changes what Ephoros reads or reports.

Proceeding on those unless corrected.

## 1. Problem statement

Hypomnema's Markdown H003 pass reads a `runbook:` pointer out of prose and
reports the target when it does not exist. It skips fenced blocks. It does not
skip inline code spans, so a round narrative that quotes a specimen pointer
inside backticks is read as though the narrative were itself an alert.

Two lines of `audit/AUDIT.md` fail this way today:

```text
audit/AUDIT.md:6041: H003 alert names runbook `runbooks/missing`, which is not there
audit/AUDIT.md:6186: H003 alert names runbook `runbooks/present.md`, which is not there
```

Both sit inside a single inline code span in a historical round record, where
the pointer is the specimen the round was about. Neither is a promise that a
file exists. The file is append-only, so no pragma can be added to either
line and no rewrap can move them.

A working prototype means the checker tells the two cases apart on the
evidence in the text. The demo path is the checker over the ledger it cannot
read today:

```bash
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py audit/AUDIT.md
```

Exit 0, with the documented tree command still exit 0 and the two guard tests
red against the current tree and green against the fixed one.

## 2. Prior art

**In this repository.** `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`
already carries the same distinction under the name `mask_quoted`: a banned
term inside quotation marks is being mentioned, not used, so the lexicon pass
blanks quoted spans with spaces and keeps line and column correct. Its
`RE_QUOTED` reads inline code as one of the quoted forms. That function is the
shape to follow, and the reason it exists is the reason this finding exists.

`plugins/lemma/chunkers/markdown.py` implements CommonMark backtick runs
properly, including escaped runs and multi-line spans. It lives in another
plugin and is not importable from here, so its rules are prior art rather
than a dependency.

`hypomnema.py` itself already skips fenced blocks for H001, H002 and H003, and
`_record_findings` and `_runbook_findings` both read headings outside fences
"so a record quoting the template in an example neither gains nor loses a
section". The mention-versus-use boundary is therefore established in this
file; only the inline case is missing.

**The last two merged changes to this skill.** `4983ed9` folded plain YAML
`runbook` values so a first-line decoy could not stand in for the real
scalar, and `6934de9` preserved blank folds inside that same value. Both were
audit fixes inside the YAML pass. Neither touched the Markdown pass, and
neither left work behind that this run inherits: the ledger row for that work,
`hypomnema-v4.3.0`, records the YAML pointer pass as complete and the held
frontier as unchanged.

**The audit record.** `audit/AUDIT.md` has judged this exact question three
times and never fixed it:

- `SCG-S1-R1-02` recorded the two findings and closed with "applying the
  pointer gate to the changed documentation scope named by the audit
  contract; no checker or shipped-document defect existed, so no code guard
  was added".
- The Phylax unsafe-deserialization round recorded them as "quoted prior
  findings outside the step paths, so neither enters this round's required
  lint exits".
- The issue 434 step-1 round recorded them as "two old H003 specimens" whose
  scope "excludes `audit/AUDIT.md`".

Each round reached the same reading of the text and each declined to act,
because the required lint scope in `AGENTS.md` does not name `audit`. The
reading is consistent across all three; what none of them had was a mechanical
rule. The three records also cite the failing lines as 6119 and 6269, while
the current tree reports 6041 and 6186. The ledger is appended by concurrent
runs and merged, so its line numbers are not stable and nothing in the fix may
depend on them.

**Outside.** CommonMark section 6.1 defines a code span as a backtick run
matched by a run of equal length, with an unmatched run left as literal text.
That rule is what makes the fix bounded, because an odd backtick cannot open a
span that swallows the rest of a line.

## 3. Constraints and non-goals

Starting ref: `main` at `5d6fc67bb6c861f2be631eef2d7bef3c01c73e84`.
Toolchain: Python 3.11, stdlib only, `unittest`. No new dependency and no new
file outside `docs/`.

Constraints:

- H000 to H007 keep their codes, and H001, H002 and H004 to H007 keep their
  present firing conditions unchanged.
- The YAML H003 pass is untouched. Backticks are not YAML syntax and the two
  passes share no code path.
- Ephoros keeps E004 and alert classification.
- The ledger row is a generation row: `hypomnema-v4.4.0`, with the frontier
  revision, digest, status and next job byte-identical to `v4.3.0`.
- The scan stays per line, matching the existing loop.

Non-goals:

- **Widening the required lint scope.** Adding `audit` to the `AGENTS.md`
  command would make the ledger a permanent gate: one future round that pastes
  an unbackticked missing pointer breaks every later step's lint exit, and the
  append-only contract forbids repairing it. The issue asks for the checker
  side. The scope decision is separate and is recorded as the successor lead.
- **H001 and H002.** A backticked link or superseding reference has the same
  mention-versus-use question, and no instance exists in the repository today.
  Changing three codes' scope in one run means three fixture sets and one
  audit loop covering all of them. H003 is what issue 500 names.
- **Multi-line code spans.** CommonMark allows a span to open on one line and
  close on the next. The existing scan is per line and stays that way; an
  unmatched run is literal, so a pointer on such a line stays checked. That is
  the fail-closed direction and it is documented rather than fixed.
- **A CommonMark parser.** Escapes, HTML blocks and link-reference definitions
  are Lemma's job, not a record lint's.

## 4. Design options

**A. Blank every inline code span before the H003 scan.** One call mirroring
`mask_quoted`, spaces preserving offsets. Trade: it also blanks a backticked
path after a bare `runbook:` key. The existing pattern carries an optional
quote character around the path precisely so `runbook: ` with a backticked
target still resolves, so option A retires a supported form without saying so.

**B. Skip a match whose `runbook:` keyword starts inside an inline code span.**
The keyword's position is the discriminator: a specimen quotes the whole
key-and-value pair, a live pointer writes the key in prose and may format the
path. Trade: a Markdown line that backticks a real annotation whole stops
being checked. No such line exists in the repository, and real annotations live
in YAML files, where the separate pass owns them.

**C. Skip the match unless the whole match sits outside every span, and drop
the pattern's optional quote characters.** Trade: the simplest rule to state,
but it narrows H003 twice in one change and removes a form neither the tests
nor the documents cover, so the second narrowing would ship unmeasured.

**D. Suppress by document convention: skip lines under a round heading in an
append-only ledger.** Trade: it couples a general record lint to Fiat's audit
format, and a specimen quoted in a study or a README stays broken.

**Chosen: B.** It is the option that states one rule, keeps every form the
current pattern supports, and needs no knowledge of which document it is
reading. A is cheaper by a line and pays for it with a silent narrowing; C
bundles a second change; D fixes one file rather than the rule.

The pairing is one linear pass keyed by run length. A naive pair-search is
quadratic in the unmatched runs on a line, and the plugin's own round-1
adversarial sweep used 60k-character lines and 30k backticks, so the linear
form is the one that survives that input rather than an optimisation.

## 5. Risk register seed

The audit loop should look hardest at the new span scan, because it decides
whether a finding is reported at all: a wrong span silently retires a check,
and a check that reports nothing looks exactly like a clean document.

```risk-register
backtick-run-blowup | the per-line span scan over adversarial Markdown | pairing is one linear pass keyed by run length, and a line of 30k runs stays inside the stated budget
span-hides-live-pointer | the boundary between a quoted specimen and a live pointer | a bare runbook keyword still fires H003 when the path after it is backticked
unmatched-run-drift | a line carrying an odd backtick run | an unpaired run stays literal text and opens no span, so it cannot swallow a later live pointer
multiline-span-boundary | a span opened on one line and closed on the next | the scan stays per line, so such a pointer stays checked rather than silently skipped
code-scope-creep | H001, H002 and H004 to H007 reading the same documents | only the H003 loop consults the spans, and every other code keeps its present cases
yaml-pass-isolation | the block-YAML H003 pass | backticks carry no YAML meaning and the two passes share no helper, so the YAML cases stay byte-identical
pragma-interaction | the existing allow pragma, which is an HTML comment holding backticks in some records | span state is computed per line before suppression runs, and suppression keeps its current behaviour
```

## 6. Glossary seeds

A code span is an inline backtick run matched by a run of equal length on the
same line, with the text between them read as code rather than prose.

A quoted specimen is a pointer written inside a code span to show what
something looked like. It is a mention, not a promise that the target exists.

A live pointer is a `runbook:` key written in prose, whose target the document
asserts can be found.

An unmatched run is a backtick run with no equal-length partner on its line.
CommonMark leaves it as literal text, and it opens no span here.

A generation row is a Hypomnema ledger row that records behaviour without
moving the held frontier revision or its digest.

## 7. Sources

- `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`, the `RUNBOOK`
  pattern and the Markdown loop that consumes it.
- `plugins/hexaemeron/skills/hypomnema/SKILL.md`, the mechanical-subset
  section that states what H003 reports.
- `plugins/hexaemeron/skills/hypomnema/EVOLUTION.md`, `hypomnema-v4.3.0` and
  the ledger boundary paragraph.
- `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`, `mask_quoted`
  and `RE_QUOTED`.
- `plugins/hexaemeron/tests/test_hypomnema_checker.py`, the `codes` helper and
  the `Runbooks` case class.
- `audit/AUDIT.md`, records `SCG-S1-R1-02`, the Phylax unsafe-deserialization
  leads paragraph and the issue 434 step-1 leads paragraph.
- `AGENTS.md`, the Lints section and the required Hypomnema command.
- `plugins/hexaemeron/skills/VERSIONING.md`, the generation axis and frontier
  discipline.
- [Issue 500](https://github.com/wildcat-finance/skills/issues/500).
- CommonMark 0.31.2, section 6.1, code spans.

## 8. Signals, and the questions behind them

None, and here is why: this is a lint a person or an audit round invokes from
a terminal and reads immediately. It runs to completion in under a second, it
holds no state between runs, and nothing schedules it unattended, so there is
no three-in-the-morning question about a past invocation. Its exit code and
its finding lines are the whole record, and the round that ran it writes what
it saw into `audit/AUDIT.md`. Adding a log or a metric here would produce
output nobody reads and a second place for the count to disagree with itself.

## 9. Boundaries, per capability

One boundary, and it is not new: the checker reads document bytes it does not
control, from a repository walk. This change adds a second pass over the same
untrusted text.

- **Untrusted document text, per line.** Worth taking: nothing, beyond the
  read the checker already performs. Control: the span scan is a bounded
  linear pass over one already-read line, with no recursion, no catastrophic
  pattern and no filesystem or subprocess access. It computes offsets and
  nothing else.
- **The decision to report.** Worth taking: a false clean, which is the
  boundary that matters here. A crafted line that opens a span and hides a
  real pointer is the attack, and the control is that only an equal-length
  matched run opens a span while an unmatched run stays literal. The register
  carries this as `span-hides-live-pointer` and `unmatched-run-drift`, and both
  get a guard test.

No new dependency, no new file read, no new write, no credential and no
network. Phylax's list is otherwise unchanged by this step.

## 10. The budget, or its absence

There is a budget, because the checker walks 1,376 files on every audit round
and a per-line scan is the kind of change that quietly doubles that.

Measured before and after with the documented command:

```bash
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
```

Recorded baseline on the starting ref: 0.26s, 0.27s, 0.28s over three runs.
The change holds if the same command stays at or under 0.35s. A second bound
covers the adversarial case: one line carrying 30,000 backtick runs completes
in under one second.

## 11. The fail-closed posture

What stops the run: a guard test that does not fail against the current tree,
because a guard that was green before the fix proves nothing; the documented
tree command reporting a finding it did not report before; either budget
above missed; or a change in any code other than H003.

A failure found mid-step follows Elenchus: reproduce it as a `codes` case in
`plugins/hexaemeron/tests/test_hypomnema_checker.py` first, run that case
against the unfixed tree to see it red, then fix the cause and leave the case
behind. The guard convention here is one test method per register id it
covers, named for the behaviour rather than the bug, in the existing
`Runbooks` class.

The direction of failure is fixed: when the span scan cannot tell, the pointer
is treated as live and H003 fires. A false finding is visible and arguable; a
false clean is neither.

## 12. Decisions and their homes

Two decisions expected to be expensive to reverse, and one that is not.

- **The discriminator: the keyword's position, not the whole match.** Once
  shipped, every document in the marketplace is written against it and a later
  reversal reclassifies text nobody will re-read. Home: the
  `hypomnema-v4.4.0` row of
  `plugins/hexaemeron/skills/hypomnema/EVOLUTION.md`. This is a governed
  skill's own behaviour, so the point-or-write bridge puts it in that ledger
  row and not in an ADR, and not in both.
- **Leaving `audit` out of the required lint scope.** Home: the same ledger
  row, named as the successor lead, because it is a consequence of this
  change rather than a separate cross-cutting choice.
- **The linear pairing.** Not expensive to reverse and not a decision record:
  it is an implementation detail with a measurement, and the comment beside it
  carries the reason.

No ADR. `docs/decisions/` holds cross-cutting choices, and a single skill's
finding boundary is what its ledger exists to record.

### Amendment -- 2026-08-24

**What changed.** Item 11 said every guard must fail against the unfixed tree.
The guards split into two kinds and only one kind can. Three change-guards are
red on the parent: a wholly quoted pointer earns no finding, an escaped
backslash still opens a span, and both recorded ledger specimens go clean.
Eight invariance pins are green on the parent and on the fixed tree by
construction, because each one asserts behaviour the change must not move: a
live pointer with a backticked path still fires, an unmatched run still fires,
an escaped pair still fires, H001 and H002 keep their scope inside a span, the
pragma still suppresses, the YAML pass is untouched, and the adversarial line
still resolves its pointer. A pin that went red on the parent would mean the
change had broken something, so demanding red from it inverts its purpose.

**Why.** The rule was written before the guard set existed and generalised
from the change-guards. Leaving it as written would force either a false claim
in the round or the deletion of the pins that prove nothing else moved.

**Steps touched.** Step 2's Tests field, which repeats the same rule. Its
guards, exit commands and both budgets are otherwise unchanged; only the
evidence claim about the guards narrows to the three that can carry it.

**Still holding.** Step 2: entry holds; exit holds.
