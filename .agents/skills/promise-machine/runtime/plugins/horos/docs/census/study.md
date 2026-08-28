# The filetype census, the study

This run executes Horos's held frontier job: teach scan to record a
per-filetype breakdown of the tree under `.horos`, so two recurring
decisions stop being guesses. Is this repository worth walking at all, and
when its weight sits in a filetype Horos cannot yet map, which extractor is
worth building next.

## Assumptions

Proceeding on these unless corrected:

1. The census is a mode of scan (`scan --census`), not a new verb: the held
   job says "add a filetype census to scan", and the census must use
   exactly the walk the boundary uses (same skips, same symlink refusal) or
   its numbers describe a different tree.
2. A filetype is the name's last suffix, lowercased; a name without a dot
   is bucketed as `(no suffix)`. Compound suffixes like `.d.ts` are not
   distinguished in this run; if the evidence ever shows that mattering,
   it is a one-rule change.
3. The census counts the whole tree, including the contents of vendored and
   generated directories the boundary aggregates: walk-worthiness is a
   question about everything an unguided agent might read, not only about
   what survives the boundary. Each row therefore carries both its total
   bytes and the part already inside the boundary, so readable weight per
   filetype is the difference.
4. The recorded artefact is `.horos/census.json`, deterministic and
   schema-tagged like the boundary, written atomically by the same
   machinery, beside the boundary rather than inside it: the boundary
   schema is frozen at 1 and this run does not touch it.
5. The completed job increments evolution: `horos-v3.2.0` becomes
   `horos-v4.2.0`, generation and epoch retained.

## 1. Problem statement

Whether a repository deserves a boundary, and which extractor Horos should
grow next, are currently decided by ad-hoc shell arithmetic; this session
alone ran `find`-and-`awk` three times to learn what the tree was made of.
The census makes that a recorded, checkable artefact.

What it does, stated so a test can refuse it:

- `scan <root> --census` prints one row per filetype: files, bytes, share
  of total bytes to one decimal, and the bytes already inside the boundary,
  sorted by bytes descending then suffix. With `--write` it also commits
  `.horos/census.json` atomically. Without `--census` nothing changes,
  byte for byte: the boundary document and the adoption stanza are frozen
  contracts.
- The census walks exactly what scan walks: `.git`, `.horos` and
  `__pycache__` never counted, symlinks never followed, unreadable files
  counted as skipped. Files inside boundary-aggregated directories are
  counted per filetype, with their bytes also attributed to the boundary
  column.
- Shares are computed from exact byte counts and rounded only for display;
  the JSON carries the exact integers.

A working prototype means: the census of the shipped example fixture is
committed and reproduced byte for byte; a recorded census of the
wildcat-app-v2 clone is the evidence bundle, and its biggest
readable-but-unmappable filetypes are named in the ledger's next-job
decision; both suites and the lints are green.

## 2. Prior art

The two scan captures fix the evidence-bundle shape and the determinism
rules. The boundary's atomic writer is reused as-is. Outside: tokei, cloc
and GitHub Linguist's language statistics are the census's ancestors; none
records the result in-repo for an agent to consult, and none subtracts an
evidence-backed exclusion set, which is the column that makes this one
worth having.

## 3. Constraints and non-goals

- Stdlib only, as always. No content sniffing in the census: it buckets by
  name, and content judgements stay the classifier's job.
- The boundary document, the check verb, the map verb and the adoption
  stanza do not change.
- Non-goals: language detection beyond the suffix, per-directory
  breakdowns, line counts, any automatic decision made from the census (it
  informs the human and the ledger; it triggers nothing), and any change to
  the shipped example beyond adding its committed census.

## 4. Design options

**A. A scan mode sharing the boundary's walk, two-column rows, a sibling
artefact.** Chosen. Trade: scanning with `--census` stats the aggregated
directories' files it would otherwise only sum, which costs milliseconds on
real trees and nothing in reading budget.

**B. A separate census verb with its own walk.** Rejected: two walks drift,
and the census's exclusion column must mean exactly what the boundary
means.

**C. Fold census rows into boundary.json.** Rejected: the boundary schema
is frozen at 1, its consumers (check, the committed captures, the adoption
stanza's contract) expect entries and counts only, and a census refresh
should not force a boundary diff.

## 5. Risk register seed

- Determinism: same tree, same census bytes; sorted rows, sorted keys,
  exact integers in JSON, rounding only at print time.
- The two walks must not diverge: the census reuses the scan's skip and
  symlink rules by construction, not by parallel implementation, and a test
  pins that a symlinked file and a `.horos` directory appear in neither.
- Attribution: a file inside an aggregated vendored directory must land in
  its own suffix row with its bytes in the boundary column; the fixture has
  exactly this shape already.
- Share arithmetic: rows must sum to the total, and the boundary column
  must never exceed the row's bytes; both asserted by test.
- The frozen surfaces: a byte-for-byte test that scan without `--census`
  still reproduces the committed fixture boundary.

## 6. Glossary seeds

- Census: the per-filetype breakdown of one tree, recorded under `.horos`.
- Row: one filetype's files, bytes, share, and boundary-attributed bytes.
- Walk-worthiness: whether a tree's readable weight justifies an agent
  walking it at all; the census is the number that question reads.

## 7. Boundaries

- **Always.** Both suites and the three tree lints before a commit;
  imprimatur on every shipped document; digests by script; the frozen
  boundary reproduced byte for byte.
- **Ask first.** Any change to the boundary schema; compound-suffix rules;
  content sniffing in the census; a new verb.
- **Never.** A second walk implementation; census output that varies
  between identical runs; touching the recorded captures.

## 8. Success criteria

1. `python3 -m unittest discover -s tests` passes.
2. `python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
   passes, including the census tests and the frozen-boundary check.
3. `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`
   and the ephoros equivalent exit clean.
4. Demo path: `python3 plugins/horos/skills/horos/scripts/horos.py scan
   plugins/horos/examples/fixture --census --json` reproduces the committed
   fixture census byte for byte, and the recorded wildcat-app-v2 census at
   `plugins/horos/docs/evidence/wildcat-app-v2-census.md` is machine-checked
   by the suite like the other bundles.

## 9. Sources

The v3.2.0 ledger row holding this job in the maintainer's words. The three
recorded wildcat-app-v2 bundles and the clone at
`9b8b6d5d6db06428c5b539f267623277b65315cd`. tokei, cloc and GitHub Linguist
as the census's outside ancestors. The boundary writer and walk in
`plugins/horos/skills/horos/scripts/horos.py`.
