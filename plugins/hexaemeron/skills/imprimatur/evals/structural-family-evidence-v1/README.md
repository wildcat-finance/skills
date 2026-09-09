# Structural family evidence v1

This fixture records every candidate structural prose family from issue
#1298 and binds shipped specimens to the families that advance. It is an
evaluation fixture for labelled-prose-v2 (issue #422), and it changes no lint
behaviour: `scripts/imprimatur.py`, the three lexicon files and
`evals/labelled-prose-v1/` stay byte-identical, no regex, score or threshold
is added, and `EVOLUTION.md` does not change because no lint generation
changes. The digests below fix that claim.

The catalogue answers one question for the Imprimatur maintainer: which
grammatical moves have two independent shipped examples and the negative
neighbours a regex would need to leave alone. It does not decide which family
earns a regex; that decision belongs to labelled-prose-v2.

## Fixture location and row schemas

The fixture lives at `evals/structural-family-evidence-v1/` beside
`labelled-prose-v1`. It has two row files, each one JSON object per line.

`families.jsonl` holds one row per family. Its fields are `family_id`,
`group`, `evidence_tier`, `form`, `reader_cost`, `direct_rewrite`,
`boundary`, `disposition`, `overlaps`, `discovery_phrases`,
`minimum_positive`, `minimum_negative` and `source_issue`. The wording of
`form`, `reader_cost`, `direct_rewrite`, `boundary` and `disposition` is
copied from the issue body. `group` is one of the issue's five section
headings.

`specimens.jsonl` holds one row per shipped paragraph. Its fields are
`specimen_id`, `family_id`, `tier` (always `structural`), `family`,
`polarity`, `decision` (`actionable`, `signal_only` or `negative`), `text`,
`text_sha256`, `start_byte`, `end_byte`, `reason`, `rewrite`, `repository`,
`source_url`, `source_commit`, `source_path`, `source_start_line`,
`source_end_line`, `source_object`, `source_group_id`, `origin`,
`annotated_before_lint`, `selection_seed` and
`selection_rank_within_group`. The span fields `tier`, `family`,
`start_byte`, `end_byte` and `text_sha256` carry the names the v1 label and
sample schemas already use, so a v2 evaluator reads them without translation.
Byte offsets are UTF-8 offsets into `text`.

`schemas/family.schema.json` and `schemas/specimen.schema.json` declare both
rows in the hand-written JSON Schema subset that v1's evaluator validates.
This layout was chosen over a Markdown reference, an extension of the sealed
v1 fixture, and regex-free entries in `lexicon/structural.json`; the
committed study records the probe that ruled each of those out.

## Selection rule, seed and universe

Candidate paragraphs come from the v1 universe: public `wildcat-finance`
repositories at a pinned default-branch head, plus merged pull requests and
issues in `wildcat-finance/skills`. The six source kinds the specimen schema
names are all read: Markdown paragraphs and commit messages reachable from
each pinned head, and the bodies, conversation comments and review comments
of the named repository's issues and merged pull requests. Prose from the 16
v1 source groups, Imprimatur's own files, vendored or generated trees
(`lib`, `build`, `vendor`, `node_modules`, `third_party`, `third-party`,
`.github`) and issue #1298 itself is excluded, so no specimen shares a source
group with the spent v1 holdout.

One further tree is excluded, and it is excluded on its own testimony.
`plugins/lemma/baseline/` in `skills` describes itself as "A small invented
corpus", says "Everything here is fabricated for the purpose" and that "None
of it corresponds to a deployed system, and the prose is written to be chunked
rather than to be read." A specimen taken there would be evidence of writing
nobody published, and two of its paragraphs had reached the candidate pool. It
is named by repository and path prefix rather than by a path segment, so an
unrelated directory called `baseline` is unaffected, and it is the only tree
in the universe that declares itself invented. Its eleven documents are
counted as `invented-corpus` in the rejection table below.

`scripts/collect_family_evidence.py` is the executable form of this rule.
It fetches only through `gh api` at the pinned commits, with a fixed argument
list and no shell, treats every fetched byte as data, writes every rejected
candidate with its reason to `selection-rejections.jsonl`, and writes
`specimens.jsonl` through a temporary file and a rename. Its `--head`
arguments are the pinned heads below; `--threads wildcat-finance/skills`
admits that repository's threads and comments; `--v1-samples` names the one
v1 file it may open, `samples.jsonl`, and it refuses any other v1 file by
name so the spent holdout labels are never read while specimens are chosen.

One pass over this universe is 11,702 documents and a little over four
thousand `gh` calls, which is most of an hour and most of a 5,000-call hourly
quota, so two things about the pass are recorded rather than left to be
rediscovered. A transient answer is retried a bounded number of times with a
fixed wait -- only HTTP 429, 500, 502, 503 and 504, read from GitHub's own
status line, and every other non-zero exit stays the refusal it was -- because
one HTTP 504 at document 900 of 1,370 used to end the pass and discard
everything already fetched. And `--corpus-out` records the fetched universe so
a rerun can read it back with `--corpus-in` against each row's stored digest;
this collection was ordered and annotated from such a record, and every
shipped row was still re-fetched from its own endpoint before it was written.

The universe is pinned on one side and not the other, which the fixture states
rather than implies. The Markdown and commit halves are reachable from the
pinned heads and cannot move. The thread half is enumerated from 1 to the
highest number GitHub answers for, so a later pass sees the issues and pull
requests opened since, and a body edited since is fetched as it now reads.
That is why `annotated_before_lint` and the recorded span carry the annotation
order rather than the replay.

Candidates are discovered by the literal `discovery_phrases` recorded on each
family row, ordered by:

```text
sha256("imprimatur-structural-family-evidence-v1" || source_url || text)
```

and taken in that order until the family's tier minimum is met. Discovery by
phrase is a stated bias: it finds the forms the phrases name and cannot find
the forms they miss. Every rejected candidate is written to
`selection-rejections.jsonl` with its reason.

How the phrases were chosen is part of that bias. Before collection, a
reconnaissance pass over the same universe counted each family's form with a
bounded pattern held in the run's scratch directory; no pattern was added to
the lint, the lexicon or this fixture. For the ten families whose form is a
closed phrase, `discovery_phrases` carries the issue's own forms plus one or
two near-neighbour literals that supply negatives (`the fact that`, `the case
that`, `potentially`, `Note that`, `There are`, `and also`). For the three
families whose form has an open slot between the connector and the verb
(`causal_subject_has_no`, `causal_negative_passive`,
`litotic_double_negative`) a literal cannot name the form, so the recorded
phrases are the exact strings the reconnaissance matched, and the collector
finds what the reconnaissance found and nothing else. The nearest generic
literal for those three (`because the`, `not un`) names 870 to 980 paragraphs
each, which nobody could annotate in digest order.

A second reconnaissance pass ran when six families ended the first collection
below their minimum, over the same pinned universe, by the same method, and
it changed one phrase set. `stacked_epistemic_modal` gained `could plausibly`
and `might plausibly`, two attested pairs of the closed class the issue names
four members of; nothing else was widened, because for the other five the
phrase set was already the widest literal their form admits. `the fact that`
and `the case that` name every occurrence of their families' forms; `is
because` and `There are` name the predicate and the opener of theirs. A
literal cannot find what the corpus does not contain, and the Collection
record below says what that search found for each of the four families still
short.

Widening the universe was considered in the same pass and refused. The seven
public `wildcat-finance` repositories outside `--head` stay outside for the
reasons recorded below, and the 18 to 180 word band stays as
labelled-prose-v1 set it.

The annotator is the agent running the step. It records, for each candidate
in digest order until the tier minimum is met, the polarity, the decision,
the actionable span as UTF-8 byte offsets, the reason and, for a positive, a
content-preserving rewrite; a family whose universe holds too few positives
is annotated to its last candidate. The record is keyed by family and
candidate, because one paragraph can carry two families' phrases and be a
positive for one move and a negative for the other. A candidate annotated on
a side of the minimum that is already met is not shipped; it stays in
`selection-rejections.jsonl` as `minimum-already-met` with its annotation
named in the detail. All of this happened before any lint ran, and
`annotated_before_lint` records that protocol on every row. The current lint
has none of these families, so it could not fire on them; the field exists so
v2 can trust the order.

A source group is a repository plus a document, the unit v1 splits on. Two
positive specimens for one family are independent only when their
`source_group_id` values differ.

## Collection record

Specimens were collected on 2026-09-09 from these pinned heads, with
`wildcat-finance/skills` also supplying its issues, merged pull requests and
their comments:

| Repository | Pinned head |
| --- | --- |
| `wildcat-finance/collateral-contract` | `6f8c1213b4ee339eaab4b34b5d73e7b12e2ee7fe` |
| `wildcat-finance/credit-default-swaps` | `f46a26129d5e985ae6618c01146fb46163182955` |
| `wildcat-finance/erc` | `1fd1fd36bd6126d6fd2464abe49b569b9b123c52` |
| `wildcat-finance/project-aleph` | `06cd4ea1f31b54bcd5bab48910002c1aedb9921c` |
| `wildcat-finance/project-null` | `fdba24d3ab4b79c71480d36023a3b170472799c2` |
| `wildcat-finance/ripcord` | `b3a2f403ff474b99864a3e3bb3a78d1a911836b8` |
| `wildcat-finance/shoggoth-wave-atlas` | `3f50cc5fa54147f56479b5a53a1cbe29fc5f631e` |
| `wildcat-finance/skills` | `592390722f10df53658906623b15428dbfb88d8f` |
| `wildcat-finance/subgraph` | `63f399e6ceff76a85c14ed26017a792e15513efd` |
| `wildcat-finance/v2-protocol` | `f5a26146987926f4811b72a795d662813dedfe85` |
| `wildcat-finance/wildcat-app` | `1368b013832407d6bc90fe2b9d57de16bd662623` |
| `wildcat-finance/wildcat-app-v2` | `564a189bb9cdc9394b3fd4f444531a261ada99b3` |
| `wildcat-finance/wildcat-docs` | `636b1dcba90c816e699c0d876c22d39be2c58b06` |
| `wildcat-finance/wildcat-fee-collector` | `ccb14d6d4f958b854505a23657c7a468b43902f7` |
| `wildcat-finance/wildcat-juris` | `8c20413ddc96fccebc71503b9b32ce8a001dae14` |
| `wildcat-finance/wildcat-landing` | `c7cb914c2fa462e80d910afb37599b991d218d53` |
| `wildcat-finance/wildcat-protocol` | `488b30d08c73a93be3e4bf99128c774997411d3a` |
| `wildcat-finance/wildcat-tranching` | `863bd053034572e7d95521d946b10438e9401fff` |
| `wildcat-finance/wildcat-whitepaper` | `51f2df6b7231dfbdedce391ee9896b24adfe3dfd` |
| `wildcat-finance/wildcat.ts` | `b12f36b1677c8c9989527c002d3ccceabd8997ab` |

Seven public `wildcat-finance` repositories were left out of `--head`, and
the reason is recorded per repository: `skills-runtime` and `lemma` mirror
skills prose byte for byte (390 of 391 and 12 of 13 Markdown files hash to
blobs already in `skills`), so either would supply a second "independent"
source group for one document; `chainalysis-subgraph`, `ethena_sats_adapters`
and `ethereum-access-token` are forks of other organisations' work, whose
prose this fixture would be attributing to Wildcat; `fiat-checkpoints` and
`wildcat-juris-debug` are empty, and `repos/<name>/commits` answers HTTP 409
`Git Repository is empty` for both, so neither has a commit to pin. Those
reasons were re-read when six families ended the first pass short, and none
of the seven was admitted: a mirror manufactures a second source group for
one document, a fork's prose is somebody else's writing, and an empty
repository has no head. The organisation's public listing holds 27
repositories, which is these seven and the twenty above.

The collector rejected 170 documents whole before any
phrase was tried, rejected 116 phrase-bearing paragraphs on the word band, the
table, code, digest and issue-quotation rules, ordered the 352 that remained as
candidate rows across the 13 target families, and shipped 38 specimens. A
paragraph carrying two families' phrases is one candidate row per family.
Per target family, where `Judged` counts the candidates whose annotation the
selection read: the walk stops where a family's minimum is met, and reaches
the last candidate where it is not, so `Judged` equals `Candidates` on each of
the four that fall short.

| Family | Tier | Candidates | Judged | Independent positives | Negatives | Minimum met |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `causal_subject_has_no` | `high-value` | 17 | 9 | 2 | 2 | yes |
| `causal_negative_passive` | `signal` | 30 | 3 | 2 | 1 | yes |
| `reason_is_because` | `high-value` | 18 | 18 | 1 | 2 | no |
| `causal_fact_clause_wrapper` | `high-value` | 14 | 14 | 0 | 2 | no |
| `backward_demonstrative_cause` | `signal` | 16 | 3 | 2 | 1 | yes |
| `agentless_choice_passive` | `signal` | 93 | 3 | 2 | 1 | yes |
| `purpose_periphrasis` | `signal` | 35 | 3 | 2 | 1 | yes |
| `stacked_epistemic_modal` | `signal` | 20 | 8 | 2 | 1 | yes |
| `redundant_connective_pair` | `high-value` | 13 | 4 | 2 | 2 | yes |
| `litotic_double_negative` | `signal` | 25 | 9 | 2 | 1 | yes |
| `attention_adverb_opener` | `signal` | 33 | 3 | 2 | 1 | yes |
| `empty_expletive_case` | `high-value` | 15 | 15 | 0 | 2 | no |
| `existential_relative_shell` | `signal` | 23 | 23 | 1 | 1 | no |

Shipped specimens by source kind: commit_message 8, issue_body 5, markdown_paragraph 22, pull_request_body 3. By
origin class: model_assisted 21, unknown 17. Every rejection reason and its count:

| Reason | Rejections |
| --- | ---: |
| `code-heavy` | 3 |
| `excluded-issue` | 2 |
| `generated-data` | 11 |
| `group-already-used` | 1 |
| `imprimatur-own-prose` | 10 |
| `invented-corpus` | 11 |
| `minimum-already-met` | 313 |
| `outside-word-band` | 102 |
| `path-carries-whitespace` | 6 |
| `unknown-thread` | 19 |
| `v1-source-group` | 32 |
| `vendored-or-mirrored-path` | 90 |

Four target families end the collection below their tier minimum, and the
shortfall is the evidence rather than a gap in the collection. Each was
searched over the whole pinned universe with a bounded pattern for its own
form, not only for its `discovery_phrases`, and this is what that search
found.

`reason_is_because` holds one independent positive. A reason noun followed by
a copula and `because` -- `reason`, `reasons`, `reasoning`, `rationale`,
`cause`, `explanation`, `motivation`, `purpose` or `point`, then `is`, `was`,
`are`, `were`, `being` or `be`, then `because`, with up to 120 characters
between -- occurs exactly once in the universe, and it is the specimen
shipped here. The second independent example does not exist to be found.

`causal_fact_clause_wrapper` holds none. `the fact that` occurs in 14 prose
paragraphs across 13 source groups, and in not one of them is it preceded by
a causal connector. The two nearest are `in reliance on the fact that` in the
master loan agreement, which the family's own boundary keeps outside as a
defined legal formulation, and `guarded by the fact that` in a Horos study,
where `by` makes the fact clause the agent of a passive verb. The other
twelve are fact clauses in object or subject position, which the issue's
`broad_fact_clause` row exists to keep out. Both nearest neighbours are
shipped as this family's negatives.

`empty_expletive_case` holds none. `the case that` and `be the case` occur in
15 prose paragraphs across 14 source groups, and none is the `it is/was the
case that` shell the boundary restricts the family to. Fourteen use `the
case` as a noun with a relative clause, almost always naming a test case. The
nearest is `it may be the case that` in the borrower documentation, which
carries modality the boundary keeps outside the shell, and it is shipped as a
negative.

`existential_relative_shell` holds one independent positive. A
sentence-opening existential with a quantified noun and a relative clause
occurs in exactly one prose paragraph source group,
`wildcat-docs:using-wildcat/day-to-day-usage/borrowers.md`, which carries two
of them: the shipped positive and a second at line 23 that is rejected as
`group-already-used` because independence is decided by source group. It
occurs twice more in the universe and neither is a prose paragraph: once
inside a table row of an audit round record, which the table rule excludes,
and once in that record's generated synopsis, where the whole 28,799-word
file is one paragraph.

The word band was tested rather than assumed. Every phrase-bearing paragraph
these four families lost to `outside-word-band` was re-read, and each is
either a generated audit synopsis of thousands of words with no blank line in
it or a line under eighteen words; none carries a form the band is hiding. The
band stays labelled-prose-v1's 18 to 180 words.

Under the issue's own packet a family that advances needs two independent
shipped examples, so these four do not advance from public Wildcat prose. The
checker exits 1 on this fixture without `--allow-below-minimum`, and the four
rows in `below_minimum` are what it reports.

Four annotation judgements are recorded so v2 can dispute them rather than
inherit them. `attention_adverb_opener` meets its minimum on two sentences
opening with the imperative `Note that`, read as the "similar attention
instruction" the issue's form admits; without that reading the family has no
positive. `reason_is_because` counts its one positive on "If your reasoning is
because you would like a slightly different phrasing", read as the scaffold
with `reasoning` in place of `the reason`; without that reading it has none.

`redundant_connective_pair` is the third and the largest. The issue's Form
names two shapes, the adversative `but, however` and the additive `the checker
validates and also records the digest`, and rates the first a strong candidate
and the second signal only. The adversative shape does not occur anywhere in
the universe: a pattern for `but`, `yet`, `however`, `nevertheless`,
`nonetheless` and `even so` in any pairing returns nothing but `but ... still`,
where `still` carries its own meaning. So the family's evidence is the additive
shape or nothing. An earlier pass rejected every additive candidate on the
categorical ground that the high-value form is the adversative one; this pass
judges them one at a time on the issue's own test, which is whether removing
`also` leaves the same emphasis and scope. Two pass that test and are shipped,
and two do not and are shipped as the negatives beside them. The consequence a
v2 reader has to see is that `decision` reads `actionable` on both positives,
because the collector derives the decision from the family's tier, while the
issue rates this shape signal only. The tier is this fixture's minimum
contract, not the issue's verdict.

`stacked_epistemic_modal` is the fourth. Its minimum is met on `might
plausibly` and `could plausibly`, two pairs of the same closed class as the
issue's `might possibly` but not named by it, added to `discovery_phrases`
after reconnaissance attested them. The issue's four named pairs, and every
pair built from `potentially`, `possibly` or `conceivably`, occur nowhere in
the universe; without the two attested pairs this family has no positive
either.

The annotator's record is kept outside the fixture, in the run's own
directory, and is not shipped. Every shipped row carries its annotation
fields, and every candidate the annotator read and did not ship is in
`selection-rejections.jsonl` with the reason.

## Tier minimums

| Evidence tier | Families | Minimum positive | Minimum negative |
| --- | ---: | ---: | ---: |
| `high-value` | 5 | 2 independent | 2 |
| `signal` | 8 | 2 | 1 |
| `boundary` | see families.jsonl | 0 | 0 |
| `existing-family` | see families.jsonl | 0 | 0 |
| `future` | see families.jsonl | 0 | 0 |

Each row carries this table's pair as its own `minimum_positive` and
`minimum_negative`, and the checker compares the two: the table above is what
it enforces, so a row declaring anything else is a finding rather than a
second answer.

That sentence was itself unjoined. The table above, the checker's
`TIER_MINIMUMS`, the test module's own literal and every catalogue row were
four copies of one contract, and only the last two were compared: editing the
`signal` row here to 1 and 0 while the checker enforced 2 and 1 left all 54
tests green. `test_the_readme_tier_table_states_the_enforced_minimums` reads
this table and compares it with `TIER_MINIMUMS`, and the test module imports
that table rather than restating it, so one source states the contract and the
other three are checked against it.

The `high-value` families are `causal_subject_has_no`,
`causal_fact_clause_wrapper`, `reason_is_because`, `empty_expletive_case`
and `redundant_connective_pair`, whose tier follows the strong candidate the
issue names for its adversative shape while its Form names the additive shape
as well; the Collection record says which shape the shipped specimens carry
and what that costs the `decision` field. The `signal`
families are `stacked_epistemic_modal`, `causal_negative_passive`,
`purpose_periphrasis`, `agentless_choice_passive`,
`litotic_double_negative`, `attention_adverb_opener`,
`backward_demonstrative_cause` and `existential_relative_shell`. These 13
are the issue's evidence targets. The remaining 29 rows carry the issue's
boundary, disposition and rewrite, with specimens optional.

## Family count

The issue body has 42 `###` family headings, each carrying `Form`, `Reader
cost`, `Direct rewrite`, `Boundary` and `Disposition` lines: 8 under
"Missing conditions and causal wrappers", 5 under "Hidden actors, authority,
and intent", 6 under "Verb, capability, and purpose shells", 12 under
"Stacked hedges, emphasis, and redundant markers" and 11 under "Existential,
reference, and scope constructions needing more evidence". The run brief
quoted 39; the catalogue keeps all 42.

Five observations under "Ideas that do not yet form a family" are recorded
here and are not rows, because the issue proposes no rule for any of them:

1. Possessive versus "of" relationships are a style choice until a
   recurring grammatical move and reader cost are shown.
2. Rare object-fronting or inversion has no demonstrated recurrence.
3. "For the sake of" has no bounded family or rewrite in the catalogue and
   remains an observation to test.
4. "I.e." and other explicit technical restatements can be precise.
5. A bare "due to" rule would turn grammar preference into policy.

## Checking the fixture

`scripts/check_family_evidence.py` is the checker. It reads only files below
`--fixture`, and it refuses a symlink, a file over 1,048,576 bytes, an
unreadable JSONL row and any path that resolves outside that directory.
Specimen text is handled as bytes, so it is never executed, evaluated or
passed to a shell. No socket opens unless `--verify-sources` is given.

```bash
python3 plugins/hexaemeron/skills/imprimatur/scripts/check_family_evidence.py \
  --fixture plugins/hexaemeron/skills/imprimatur/evals/structural-family-evidence-v1 \
  --report /tmp/family-evidence.json
```

It has three exit codes:

- `0`: the fixture is clean.
- `1`: the checker found something. It prints every finding of the first
  class it meets, in the order `schema-contract`, `family-tier`,
  `family-schema`, `family-duplicate`, `family-minimum`,
  `family-overlaps`, `specimen-annotation-order`, `specimen-schema`,
  `specimen-duplicate`, `specimen-unknown-family`,
  `specimen-family-mismatch`, `specimen-span`, `specimen-digest`,
  `specimen-group-id`, `specimen-independence`, `tier-minimum`,
  `source-mismatch`.

  `schema-contract` is first because it reports a schema whose own
  declarations this checker cannot account for, and every other class is
  measured against that schema. It covers three joins: each schema's
  `required` list against the checker's `FIELD_ENFORCEMENT` register, which
  names for every required field either the check that enforces it beyond its
  own schema clause or the runbook step that writes it; the family schema's
  `evidence_tier` enum against the enforced tier set; and the specimen
  schema's `selection_seed` const against the checker's `FIXTURE_SEED`. Each
  of the three was two unjoined copies of one contract, and each could be
  edited with the whole suite green: dropping `origin` from the specimen
  schema's `required` list, adding a sixth `evidence_tier` the checker would
  refuse on every row, and changing `FIXTURE_SEED` away from the const every
  specimen must declare. Adding a field to either schema now means adding its
  row to the register.

  `family-overlaps` resolves the `overlaps` link. A row could name a family
  that does not exist in this catalogue and exit 0, which is
  `specimen-unknown-family`'s check applied to the catalogue's own referential
  field.
- `2`: the invocation or a read was refused, which covers a missing fixture
  directory, an unknown `--tier`, `--min-independent-positive` without
  `--tier`, a symlink, an oversized file, an unreadable JSONL row, a row
  carrying the same JSON key twice, a schema document this checker's
  validator cannot read, and a `--verify-sources` row, citation or reply
  that cannot name one pinned object.

  A schema in `schemas/` is fixture data below `--fixture`, like the two
  JSONL files, so it is gated when it is read rather than trusted where it
  is used: the document is an object, a `type` names one of the seven
  predicates the validator checks, `required` and `enum` are lists of names,
  a `pattern` compiles, `minLength`, `minItems`, `minimum` and `maximum` are
  numbers, and `properties` and `items` values are objects, all the way
  down. A document that is valid JSON and unusable is refused with exit 2
  rather than reaching a field access, where it printed a traceback and
  exited 1.

  A readable schema is not yet a schema the checker can rely on, so a second
  gate reads it before any row: the clause each keyed field's safety stands
  on has to be declared. `family_id` on a family row, and `specimen_id`,
  `family_id` and `source_group_id` on a specimen row, are declared as
  strings, because this checker hashes, iterates and normalises them;
  `polarity` and `source_object` declare their enums, because those decide
  whether a row counts at all and which endpoint replays it. Dropping one of
  those six clauses is a schema this checker cannot use, refused with exit 2.
  Five of them left a row the weakened schema admitted raising an uncaught
  `TypeError` or `AttributeError`, printing a traceback and exiting 1; the
  `polarity` enum was quieter and worse, because a positive specimen then
  counted as neither polarity, reached no independence count, and the fixture
  exited 0.

The flags are:

- `--report <path>` writes one JSON report holding `families`, `specimens`,
  `below_minimum`, `unenforced_fields` and `rejections_path`.
  `below_minimum` is the answer a later run needs: the family id, its tier,
  the counted independent positives and negatives, and the minimums its
  tier requires. `unenforced_fields` is the second: the eight required
  fields this step declares and does not enforce, each with the row file it
  belongs to and the step that writes it. Those eight were found one at a
  time by four audit rounds reading `grep` output, so they are a report key
  rather than a source comment. `rejections_path` points at
  `selection-rejections.jsonl`.
- `--allow-below-minimum` records a tier-minimum shortfall in the report
  rather than reporting it as a finding. **This flag exists for the build
  phase only**, while specimens are still being collected. A released
  fixture must exit 0 without it.
- `--min-independent-positive <n>` and `--tier <tier>` restrict the
  tier-minimum check to one evidence tier and override its
  independent-positive minimum. The design record's
  `two-independent-specimens` gate is resolved with
  `--min-independent-positive 2 --tier high-value`. The override applies to
  every tier the run measures, so it needs `--tier` to name the one it is
  overriding and is refused with exit 2 on its own; `boundary`,
  `existing-family` and `future` require nothing, and the flag alone put all
  42 families below a minimum no tier declares.
- `--verify-sources` replays each specimen against the GitHub object it cites
  through `gh`, at the pinned host, and checks that the specimen's `text` is
  present in what comes back. This is the only path that opens a socket. The
  flag's own `--help` text says the same thing: it described the replay as
  reaching an immutable object for a round after that claim was corrected
  here, and `--help` is the copy an operator reads. Only a row that cleared
  every local check is replayed, and `text_sha256` is compared against the
  row's own `text` before the replay rather than after it.

The replay is bounded in three places, and one of those bounds does not reach
every kind.

The host is pinned in the argv. Every endpoint below is a relative API path,
and `gh` resolves a relative path against `--hostname`, then `GH_HOST`, then
the working directory's own remote, so a path alone named an object only once
somebody else's environment had chosen a host. `gh api --hostname github.com`
is what the checker runs, and `GH_HOST` and `GH_REPO` are removed from the
child so neither can name a host or a repository the specimen never cited.

The endpoint is bounded by shape. The schema is not that boundary: it
validates with `re.search`, its `^wildcat-finance/` pattern admits
`wildcat-finance/../other-org/repo`, its `^[0-9a-f]{40}$` admits a trailing
newline, and `source_path` carries no pattern at all. Every value that
becomes part of an endpoint therefore passes one gate, `endpoint_segment`,
which fullmatches the pattern pinned for that field in `ENDPOINT_SEGMENTS`
and refuses anything else with exit 2. A field with no row there cannot reach
`gh`, so adding a field to an endpoint means naming its pattern first.

The endpoint is also bounded by identity, because shape alone says only that
it is one `wildcat-finance` object and not that it is the one this specimen
cites. The endpoint is built from `repository`, `source_commit` and
`source_path`, so `source_url` has to agree with them: it must begin
`https://github.com/<repository>/`, and its path must be `blob/<commit>/<path>`
or `raw/<commit>/<path>` for `markdown_paragraph`, `commit/<sha>` or
`commits/<sha>` for `commit_message`, `issues/<n>` for `issue_body` and
`pull/<n>` or `pulls/<n>` for `pull_request_body`. A citation naming any other
object is refused with exit 2. A query string is dropped with the fragment,
because neither is part of the path and GitHub's own permalink for a Markdown
file carries `?plain=1`.

For the two comment kinds the id is read from the `#issuecomment-<id>` or
`#discussion_r<id>` fragment of that same URL, because the number before it is
the issue or pull request the comment sits under; the fragment rather than
`source_object` decides the collection, since a pull request's conversation
comment is an issue comment on GitHub. The path before the fragment still has
to cite that thread, `issues/<n>`, `pull/<n>` or `pulls/<n>`: a fragment on a
blob, a commit or a release named a comment the citation leads no reader to,
and `#discussion_r` under an issue thread names a review comment an issue does
not have. Which thread the comment belongs to is not established, because
GitHub keys a comment by id alone and a citation naming another thread cannot
be told apart from here.

Only two of the six kinds replay an object GitHub cannot change under the
reference sent: a file read at `?ref=<sha>`, and a commit read by its sha. The
`issue_body`, `pull_request_body`, `issue_comment` and `pull_request_comment`
kinds have no such reference on their endpoints, so their replay compares the
current body. A body edited after annotation changes that answer, which is why
`annotated_before_lint` and the recorded span carry the annotation order
rather than the replay. The reply is data from outside too, and is refused
with exit 2 unless it carries the string field its kind expects.

Five values could decide something while reading as something else, so each
carries its own check. Rows split on the newline and on nothing else:
`str.splitlines` also splits on U+000B, U+000C, U+0085, U+2028 and U+2029,
each of which is legal inside a JSON string, so a file `wc -l` and a diff
show as 42 rows could otherwise carry a further row the checker counted, and
a specimen whose `text` carried one of them raw was split into fragments and
refused as unreadable JSON. `family` is compared with `family_id`, because
the two hold one family name in the spellings v1 and v2 use and nothing else
tied them together. A `source_group_id` carrying whitespace or a non-printing
character is refused, and so is one that is not in Unicode normal form NFC,
because independence is decided by comparing that value between two
positives, and two ids differing by a space or by a combining mark read as
one group on screen and as two here. A `specimen_id` carried by a second row
is refused the way a duplicate `family_id` is, because two byte-identical
negative rows otherwise counted as two negatives and carried a high-value
family's whole negative minimum out of one document; independence itself stays
the positives-only rule the study's register asks for. And `source_url` is
compared with the fields the endpoint is built from, above.

A sixth value sits on the family row rather than the specimen. Each row
declares `minimum_positive` and `minimum_negative`, and the tier table above
is what the checker enforces; nothing joined the two, so the declared pair
could read as one answer while the checked pair was another, with the report
printing the enforced number beside a row declaring a different one and the
suite green either way. The two are compared now.

Two of those measurements read raw fields, before anything is validated:
`--report`'s `below_minimum` counts have to exist on a broken fixture as well
as a clean one. A field read there is skipped when it is not a string, and
reported by the validation that follows, so an object or an array in
`source_group_id` or `evidence_tier` is a finding rather than a traceback.

`plugins/hexaemeron/tests/test_imprimatur_family_evidence.py` guards each
refusal, the clean-fixture exit, the copied issue wording and the frozen
digests below. It builds every fixture it checks in a temporary directory, so
the shipped fixture is never mutated.

## Frozen digests

The fixture was built against `wildcat-finance/skills` at
`7d12d63e13fe193fcc1f8827b393f8aa51161731`. These SHA-256 digests must hold
at every step of the delivery and afterwards:

| Path | SHA-256 |
| --- | --- |
| `scripts/imprimatur.py` | `7522d57632d5ceee515f37355744718853ee82d26c5e549b68571a2dce9ad50a` |
| `lexicon/hard.json` | `a6ad7adbc6c8e06512032cf460c92749a49a6c139b4f2aee101de8bdc95df844` |
| `lexicon/gated.json` | `e554ab6f9661d88095f285c6651983c980bd672b854287f74daa288b1dabc34c` |
| `lexicon/structural.json` | `908e20c6319b587e95fa21de5949a10c0088ed698d546b0a1048686211826240` |
| `EVOLUTION.md` | `19d88c8bbf1548c99509a964fd0828cc047e6319c4682292ea79973c42a1a606` |

Paths are relative to `plugins/hexaemeron/skills/imprimatur/`. Check them
from the repository root with:

```bash
sha256sum plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py \
  plugins/hexaemeron/skills/imprimatur/lexicon/hard.json \
  plugins/hexaemeron/skills/imprimatur/lexicon/gated.json \
  plugins/hexaemeron/skills/imprimatur/lexicon/structural.json \
  plugins/hexaemeron/skills/imprimatur/EVOLUTION.md
```

### Fixture inputs

The five rows above are the lint and lexicon files this delivery does not
touch, and they do not cover the fixture's own inputs. `issue-1298.md` in
particular is the oracle the wording test compares the catalogue against, and
it was unpinned: an edit made consistently to the oracle and to the catalogue
left every test green, because nothing held the oracle's bytes.

| Fixture path | SHA-256 |
| --- | --- |
| `families.jsonl` | `3e5585ba0ee86754d37085f181817471b5abfb34aa2b9bed05cffab215937a4c` |
| `issue-1298.md` | `ccff01a9db78693b183a3193b5cd76edbd908f75f3d48b4e25c46fda907f1e46` |
| `schemas/family.schema.json` | `46244a6a6a9386b903aa16731f4b4f30df07945b2e3221320544b243aafa8185` |
| `schemas/specimen.schema.json` | `ed8de25920f263308ed22928b603dcbd351230595b521af471d1f144dd1700c9` |
| `selection-rejections.jsonl` | `85a8c1ecccbfbcd97717da94aaa88d586434e550bdd2caca25d8aa6ee6d47df9` |
| `specimens.jsonl` | `406ed81594b9691a20b0c7c5c25e6839d6ba873c4bb616d427ecd2e07d5dcc0a` |
Paths are relative to this directory.
`test_the_fixture_digest_table_covers_every_fixture_file` walks the fixture
and requires every file to appear above or to be named in the test's own
exclusion set, so a file cannot arrive unpinned by being left out. One is
excluded: this `README.md`, which carries the table and cannot hold its own
digest. Step 3 wrote `specimens.jsonl` and `selection-rejections.jsonl` and
refilled `discovery_phrases` in `families.jsonl`, so all three carry the
digests of that step's bytes.

Pinning the oracle does not settle whether it is the issue's current body.
It raises a consistent edit from two files to three, and closing it needs a
network read.

## Files

- `README.md`: this record of the fixture location, row schemas, selection
  rule, tier minimums, family count and frozen digests.
- `schemas/family.schema.json`: the family row.
- `schemas/specimen.schema.json`: the specimen row.
- `issue-1298.md`: the exact body of issue #1298, checked in unedited so the
  wording test has something to compare the catalogue against.
- `families.jsonl`: the 42 family rows.
- `specimens.jsonl`: the specimen rows, written by step 3 of the committed
  runbook.
- `selection-rejections.jsonl`: every rejected candidate with its reason,
  written by the same step.
- `../../scripts/collect_family_evidence.py`: the collector that wrote both,
  outside this directory beside the checker.

The accepted study and runbook are committed at
`plugins/hexaemeron/docs/imprimatur-structural-family-evidence/`.
