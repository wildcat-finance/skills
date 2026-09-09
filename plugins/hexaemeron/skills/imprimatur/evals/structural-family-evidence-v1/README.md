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
issues in `wildcat-finance/skills`. Prose from the 16 v1 source groups,
Imprimatur's own files and issue #1298 itself is excluded, so no specimen
shares a source group with the spent v1 holdout.

Candidates are discovered by the literal `discovery_phrases` recorded on each
family row, ordered by:

```text
sha256("imprimatur-structural-family-evidence-v1" || source_url || text)
```

and taken in that order until the family's tier minimum is met. Discovery by
phrase is a stated bias: it finds the forms the issue describes and cannot
find the forms the issue missed. Every rejected candidate is written to
`selection-rejections.jsonl` with its reason.

The annotator records the span, decision and rewrite before running any lint,
and `annotated_before_lint` records that protocol on every row. The current
lint has none of these families, so it could not fire on them; the field
exists so v2 can trust the order.

A source group is a repository plus a document, the unit v1 splits on. Two
positive specimens for one family are independent only when their
`source_group_id` values differ.

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

The `high-value` families are `causal_subject_has_no`,
`causal_fact_clause_wrapper`, `reason_is_because`, `empty_expletive_case`
and the narrow adversative form of `redundant_connective_pair`. The `signal`
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

1. Possessive versus "of" relationships are a style choice until a recurring grammatical move and reader cost are shown.
2. Rare object-fronting or inversion has no demonstrated recurrence.
3. "For the sake of" has no bounded family or rewrite in the catalogue and remains an observation to test.
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

Its exit codes are three:

- `0`: the fixture is clean.
- `1`: the checker found something. It prints every finding of the first
  class it meets, in the order `family-tier`, `family-schema`,
  `family-duplicate`, `family-minimum`, `specimen-annotation-order`,
  `specimen-schema`,
  `specimen-duplicate`, `specimen-unknown-family`,
  `specimen-family-mismatch`, `specimen-span`,
  `specimen-digest`, `specimen-group-id`, `specimen-independence`,
  `tier-minimum`, `source-mismatch`.
- `2`: the invocation or a read was refused, which covers a missing fixture
  directory, an unknown `--tier`, `--min-independent-positive` without
  `--tier`, a symlink, an oversized file, an
  unreadable JSONL row, a row carrying the same JSON key twice, and a
  `--verify-sources` row, citation or reply that cannot name one pinned
  object.

The flags are:

- `--report <path>` writes one JSON report holding `families`, `specimens`,
  `below_minimum` and `rejections_path`. `below_minimum` is the answer a
  later run needs: the family id, its tier, the counted independent
  positives and negatives, and the minimums its tier requires.
  `rejections_path` points at `selection-rejections.jsonl`.
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
`issue_body`, `pull_request_body`, `issue_comment` and
`pull_request_comment` kinds have no such reference on their endpoints, so
their replay compares the current body. A body edited after annotation changes that answer, which is
why `annotated_before_lint` and the recorded span carry the annotation order
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
as a clean one. A field read there is skipped when it is not a string, and reported by
the validation that follows, so an object or an array in `source_group_id` or
`evidence_tier` is a finding rather than a traceback.

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

## Files

- `README.md`: this record of the fixture location, row schemas, selection
  rule, tier minimums, family count and frozen digests.
- `schemas/family.schema.json`: the family row.
- `schemas/specimen.schema.json`: the specimen row.
- `issue-1298.md`: the exact body of issue #1298, checked in unedited so the
  wording test has something to compare the catalogue against.
- `families.jsonl`: the 42 family rows.
- `specimens.jsonl`: the specimen rows, filled by a later step of the
  committed runbook.
- `selection-rejections.jsonl`: every rejected candidate with its reason,
  written by the same later step.

The accepted study and runbook are committed at
`plugins/hexaemeron/docs/imprimatur-structural-family-evidence/`.
