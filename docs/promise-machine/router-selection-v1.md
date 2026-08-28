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

`pairs` is an array of the sibling boundaries the corpus grades. Each pair
carries an `id`, the `skills` it separates, and the `deciding_sentence` that
separates them.

`runs` is an array of recorded grading runs, empty until one is recorded. Each
run carries `model`, `date`, `prompt_template_sha256`, `corpus_sha256`,
`cases`, `passed`, `failed` and `failures`.

## Quoting

A case quotes the clause naming its own skill. A pair quotes the whole sentence
that separates its members, because the separation is what the pair is about.

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
sentence still occurs in the section of the file the entry names. And that any
recorded run block carries the eight fields above with a `corpus_sha256` that
recomputes from the cases on disk.

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

## Authorises

Reporting the corpus's coverage and the latest recorded run through
`tests/emit_router_selection_report.py`, and citing a recorded run with the
model, date and corpus digest it names attached. Nothing else.

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
does not name, whose digest disagrees with the cases on disk, or whose case,
pass and fail counts cannot all be true: every case the run covered was passed
or failed, and a run records every failing case id.

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
