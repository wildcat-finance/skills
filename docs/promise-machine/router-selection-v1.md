# Router selection corpus, v1

The contract for schema `promise-machine-router-selection/v1`, the corpus at
`tests/fixtures/router-selection/cases.json` and the checker at
`tests/test_router_selection.py`. It states what a passing check establishes,
what it does not, and what makes it refuse.

## Subject

A corpus of request phrasings, each paired with the canonical skill the
Promise Machine router should select for it and with the sentence that decides
that selection, quoted from the file that holds it. Selection is the thing
being graded: choosing one of the router's rows, as distinct from resolution,
which is a link or a name pointing at a file that exists.

## Shape

The corpus is one JSON object with four keys.

`schema` is the exact string `promise-machine-router-selection/v1`.

`cases` is a non-empty array. Each case carries exactly seven fields:

- `id`, unique across the corpus.
- `family`, the kind of case this is.
- `request`, the phrasing presented to a graded agent.
- `expect`, either `{"outcome": "select", "canonical": <skill name>}` or
  `{"outcome": "refuse", "reason": "ambiguous" | "uncovered"}`.
- `contested`, the canonical skills whose boundary the request sits near.
  Empty for a case that only one row matches.
- `deciding_sentence`, an object of `path`, `section` and `text`.
- `not_established`, the nearest overclaim this selection does not support.

`pairs` is a non-empty array of the sibling boundaries the corpus grades. Each
pair carries an `id`, the `skills` it separates, and the `deciding_sentence`
that separates them.

`runs` is an array of recorded grading runs, empty until one is recorded. Each
run carries `model`, `date`, `prompt_template_sha256`, `corpus_sha256`,
`cases`, `passed`, `failed` and `failures`. A failure entry carries exactly
`case` and `selected`, the failing case id and what the graded context actually
answered.

`selected` admits every answer a graded context can give, and nothing else. A
canonical skill name records a selection, whether the corpus expected a
different skill or expected a refusal. `refuse:ambiguous` and `refuse:uncovered`
record a refusal of a case the corpus expects to be selected, and separate a
refusal for the wrong reason from a refusal for the right one. Both sides stay
closed sets the checker resolves, which is what keeps model prose out of a
committed file. A field admitting only canonical names would leave a refusal
with nothing to name, and a procedure that cannot record every answer its
subject can give is one that reports the answers it likes.

## Quoting

A case quotes the clause naming its own skill. A pair quotes the whole sentence
that separates its members, because the separation is what the pair is about.
Where the two quotable files hold no such sentence, the pair is one the corpus
declares in order to record that gap, and it quotes the router rule that
disposes of it instead. `elenchus-metron` is the one such pair: neither name
occurs anywhere in `AGENTS.md`, and in the router each occurs only in its own
table row, so nothing separates them and `RS-33` expects a refusal. The checker
holds every quotation to its occurrence in the named section and does not read
which of the two a pair carries.

Two files may be quoted: `AGENTS.md` and
`.agents/skills/promise-machine/SKILL.md`. That set is closed in the checker,
so a case naming any other path is refused before anything is opened.

The search collapses runs of whitespace on both sides before comparing. Both
files are hard-wrapped, so a sentence spans lines and a byte comparison would
fail on rewrapping. Rewrapping a paragraph therefore passes and rewording one
fails, which is the distinction the check is for.

## What a passing check establishes

That the corpus declares this schema. That every case has exactly the fields
above, with a unique id and an expectation the checker recognises. That every
canonical name a case expects or contests, and every name a pair separates, is
the frontmatter name of a real `SKILL.md` under `plugins/`. That every quoted
sentence still occurs in the section of the file the entry names. That every row
of the router's two selection tables is named by at least one case. That every
pair the corpus declares is contested by at least one case, whose `contested`
list holds all of the skills that pair separates. And that any recorded run
block carries the eight fields above with a `corpus_sha256` that recomputes from
the cases on disk, names the model, date and prompt-template digest a reader
needs to recount it, carries a prompt-template digest equal to the digest of the
template committed beside the corpus, and names each of its failures by a case
id this corpus holds and a canonical skill that resolves.

## Evidence classes

`checked` for the shape, the id uniqueness, the canonical names and the quoted
sentences. `recomputed` for the corpus digest, which is derived again from the
cases on disk rather than read from the file that carries it. `recorded` for a
run block: the model, the date and the failures it names are preserved from the
run that produced them. `measured` for that block's counts, which are observed
by running one model against one corpus digest under one prompt template.

The last two classes name a surface this contract covers, not one it asserts is
populated. While `runs` is empty the reporter prints `not-run`, there is no
score to cite, and nothing here is `proved` at any point.

## Boundary

A passing check establishes nothing about how any agent routes. It does not
establish that the corpus is representative of real requests, that a case the
corpus expects is the selection a reader would agree with, or that a recorded
run would repeat. A recorded score is evidence about one model, one prompt
template, one corpus digest and one date. It is never called proved and it is
never a gate: making it one would invite tuning the corpus until the model
passed it.

The prompt-template digest reaches the prompt the grading supplied and stops
there. A graded context also receives a harness system prompt, whatever
repository instruction files that harness loads, and the definitions of the
tools it may call, and no digest in this contract covers any of them. The
template is the part a later reader can retrieve and reissue; the rest is the
condition the run was performed under, and it is recorded nowhere.

Nor does a contested case establish that the boundary it declares is what
decided it. `contested` records the canonical skills whose boundary the request
sits near, and nothing more. A request carrying a word that occurs under one
plugin's runtime contract and under no other is answerable from that word, with
the separating sentence unread, and the corpus holds no field that tells such a
case apart from one that needs the sentence. A perfect score across the
contested cases is therefore consistent with the boundaries separating the
siblings and consistent with the requests being easy, and the run does not
distinguish them.

## Authorises

Reporting the corpus's coverage and the latest recorded run through
`tests/emit_router_selection_report.py`, and citing a recorded run with the
model, date, prompt-template digest and corpus digest it names attached.
Nothing else.

The `router_selection` capability entry pins that reporter's bytes beside the
corpus, the prompt template, the guard fixtures, the checker and this document.
Without the pin the authorised surface was the one surface nothing held: the
reporter could be rewritten to echo a request or a deciding sentence, which is
the contamination the report exists to avoid, and no digest would move.

## Refuses

A corpus that is absent, unreadable, not UTF-8 or not JSON. A corpus declaring a
schema other than `promise-machine-router-selection/v1`. A top-level value
that is not an object, or one whose `cases`, `pairs` or `runs` key is missing
or the wrong type. An empty case list, which is refused by name rather than
allowed to pass every later check over nothing. A case whose field set differs
from the seven above, whose id repeats, whose expectation names neither a
select nor a recognised refusal reason, whose required field is present but
empty, whose `contested` is not a list of canonical names, or whose quotation
is not the three keys the schema names. A quoted path outside the closed set. A
canonical name no `SKILL.md` declares. A sentence the named section no longer
contains. An empty or whitespace-only quotation, which would otherwise occur in
every section and pass while establishing nothing. A pair whose field set, id,
separated skills or quotation the schema does not name, held to a case's shape
because it quotes prose the same way, its id required to be present and
non-empty exactly as a case's is. A run block whose field set the schema
does not name, whose digest disagrees with the cases on disk, whose `failures`
is present but is not a list, or whose case, pass and fail counts cannot all be
true: every case the run covered was passed or failed, and a run records every
failing case id.

On coverage, which the two checks over the router's tables and the corpus's
pairs block add. A router row whose canonical selection no case expects. Two
rows selecting the same canonical skill, because a named row is matched by its
skill rather than by its predicate, so one case would stand in for both and the
second row would arrive graded by nothing. The one row that names no canonical
skill, the vendored Pashov suite's, quoted by no case that selects; a case that
refuses does not cover it. A selection cell that is neither a canonical name in
backticks nor that row's known phrase, because a row the check cannot read is a
row it would pass unexamined. A router carrying no `## Select one runtime
contract` section, or that section carrying no selection table. A section whose
parsed rows and table lines disagree, which is what a parser that skipped a row
looks like. A corpus declaring no pairs at all, refused for the reason an empty
case list is. A declared pair no case contests in full, since a case holding
only some of its members leaves the rest ungraded. And a pair carrying no list
of separated skills to contest.

On completeness, which the run-block check adds. A run block that is not an
object. A `model` that is absent, empty or not a string, a `date` that is not a
`YYYY-MM-DD` date, or a `prompt_template_sha256` that is not a lowercase sha256
digest: a score whose model, date or prompt nobody can recover is not evidence
about any of them. An absent or unreadable prompt template, or a
`prompt_template_sha256` that is not the digest of the template committed beside
the corpus: a digest naming bytes the repository does not hold is evidence about
no prompt at all, which is the defect this corpus exists to argue against, one
level up. Holding the two equal makes a regrade under a different prompt commit
that prompt, and it holds every recorded block against the one committed
template, so the corpus carries one prompt template at a time and a regrade
under a different prompt replaces the earlier block rather than joining it. A run covering no cases at all, whose counts agree with each other
while measuring nothing. A failure entry whose field set is not exactly `case`
and `selected`, since the entries are model output written into a committed file
and the shape is closed rather than free text. A failure naming a case id this
corpus does not hold. The same case id named by two failures, which would make
the failing cases uncountable. And a failure recording an answer that is neither
a canonical name a `SKILL.md` declares nor one of the two refusal forms, since
a field that took anything else would be taking model prose.

## Recovery

The failure names the case or pair, the file and the sentence it looked for.
Requote the current sentence or retire the case; do not reword the source to
match the corpus, because the source is the thing being graded. For a name that
no longer resolves, correct the case or add the skill. For a run block whose
digest has moved, regrade against the current cases rather than editing the
digest to agree.

## Digest scope

`corpus_sha256` covers the `cases` array alone, serialised with sorted keys and
no whitespace. A run block is recorded into the file it pins, so a digest over
the whole document would move the moment a run was recorded and could never
match.
