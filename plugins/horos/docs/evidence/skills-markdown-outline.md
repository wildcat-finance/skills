# Evidence bundle: the Markdown outliner against markdown-it-py

The differential corpus run the Markdown extractor's acceptance demanded:
every tracked `.md` file of this repository at a named commit, outlined by
Horos and independently parsed by markdown-it-py in its CommonMark preset,
with the two readings compared per file at declared altitudes.

## The run

- Corpus: this repository (`wildcat-finance/skills`) at
  `0696638c2a00a88387ae2441851193d4bb23030a`, all 900 tracked `.md` files,
  15,896,939 bytes, listed by `git ls-files '*.md'` at that commit
- Captured: 2026-09-05
- Outliner: `languages/markdown/markdown.py` as shipped in this delivery
- Oracle: markdown-it-py 4.2.0 with mdurl 0.1.2 in the `commonmark` preset
  (CommonMark 0.31.2 reference behaviour), installed in a scratchpad
  virtualenv and driven by the committed dev-time tool
  [../../dev/md_oracle.py](../../dev/md_oracle.py); absent from every
  runtime and test path, and imported by nothing the plugin ships
- Declared altitudes: headings by `(level, line)` at every container depth,
  ATX and setext alike; fenced code blocks by `(first line, last line)`.
  Heading text and fence info strings are not compared, because the
  outliner slices the verbatim line while markdown-it reports parsed inline
  content. Everything else either side sees is outside the comparison:
  inline structure, link reference definitions, indented code, thematic
  breaks, paragraphs, lists and tables.
- Excluded by declaration on both sides, the two exclusions this corpus
  needs. First, front matter: a `---` line at line 1 through the next `---`
  or `...` line is stripped before markdown-it parses and the remaining
  line numbers are shifted back, because CommonMark has no front matter and
  would read `title: x` under `---` as a setext heading in the corpus files
  that carry one. The outliner names the same block by line range and
  outlines nothing inside it, so the block is outlined on one side and
  compared on neither. Second, an unterminated fence: markdown-it reads a
  fence that never closes as a fence running to the end of the file, and
  the outliner refuses to invent the closing line, confesses the remainder
  as an unparsed region and exits 1. Such a fence is recorded as
  `fence_missed_confessed`, never as a match and never as a miss. This
  corpus holds none.
- A miss whose line falls inside a confessed region is `missed_confessed`
  and counted separately: the outliner said it had not read there. A miss
  outside every confessed region is a silent miss and fails the acceptance.
- Per-file results:
  [skills-markdown-outline.results.json](./skills-markdown-outline.results.json)

## The result

The oracle sees 9,527 headings and 1,130 fenced code blocks at the declared
altitudes. The outliner names all 9,527 headings and all 1,130 fences,
misses none, names nothing extra, and crashes on none of the 900 files. 190
files carry confessed regions, 576 regions in all, and no region hid a
heading or a fence the oracle could see, so the confessed count is zero on
both sides.

The corpus is the run's own repository, so the reading is over the widest
prose the extractor will meet in service: agent instruction files, audit
records with pipe tables and fenced blocks, plugin skill files with YAML
front matter, generated inventories, and vendored documentation trees.

## The corpus outline time, re-measured

Outlining all 900 corpus files in one process takes 170 ms, the median of
three runs (167, 173, 170), against the study's budget of 1,000 ms in
section 10. The measurement is the method of
`.hexaemeron/design-reports/resolve.py corpus-outline-ms` copied exactly:
every corpus file read and decoded once up front, then three passes calling
`declarations()` on each decoded source in process, the median of the three
wall times taken with `time.perf_counter`. It could not be run through
`resolve.py` unchanged, because that script imports the candidate modules
under `.hexaemeron/design-reports/candidates/`, and this figure has to come
from the shipped module; the copy substitutes
`languages/markdown/markdown.py` for the candidate and changes nothing
else. The study measured 319 ms on the candidate over the 895-file corpus
of the starting ref; the shipped module is the same construction with the
bounded scanning step 2 added.

## The refused candidates

The three candidates the design record refused, with the values measured
over the study's 895-file corpus (`.hexaemeron/design-reports/`, one closed
report per candidate and criterion):

| candidate | unconfessed misses | extras | foreign source lines | corpus ms | peak heap bytes | hostile crashes | unterminated fence confessed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `line-scanner` (selected) | 0 | 0 | 0 | 319 | 1,654,625 | 0 | true |
| `heading-only` | 1,128 | 135 | 0 | 91 | 1,623,773 | 0 | false |
| `vendor-parser` | 0 | 0 | 7,877 | 2,135 | 18,359,390 | 1 | true |
| `lemma-reuse` | 1,165 | 0 | 2,120 | 4,065 | 3,922,303 | 1 | false |

`heading-only` is the cheapest construction in both time and space and is
refused on correctness and recovery, not on cost: it reads `#`-led lines
inside `bash` fences as headings and sees no fence at all. `vendor-parser`
matches the oracle exactly, being the oracle, and is refused for the 7,877
lines of third-party Python the skill would have to carry and the 2 MiB
single-line input it times out on. `lemma-reuse` is refused for a
cross-plugin import of 2,120 lines and for reporting no fences at all.

## The census figure this job was held to

The held job names the Markdown filetype at "1.83 MB across 261 files with
no boundary bytes and no map support". No committed census carries that
figure: the census committed with the `horos-v9.2.3` epoch row (commit
`378e4755`) records `.md` at 256 files and 1,755,833 bytes with 0 boundary
bytes, so the job text's figure came from a scan of a tree never committed
as such. The tree holds far more prose now. This run's own corpus, the
tracked `.md` files at `0696638c`, is 900 files and 15,896,939 bytes, and a
fresh scan at the run's starting ref `bbb9de64` recorded 895 files,
15,799,627 bytes and 1,485 boundary bytes (the generated `CONTRIBUTORS.md`),
36.2% of the repository's readable bytes and its largest readable filetype.
The `no map support` half of the job text is what this delivery answers; the
committed `.horos/census.json` is stale against all of it and is regenerated
once, in the reconcile step, not here.

## Machine-readable capture lines

The consistency test parses these against the committed results document.

<!-- mdoutline:commit 0696638c2a00a88387ae2441851193d4bb23030a -->
<!-- mdoutline:files 900 -->
<!-- mdoutline:bytes 15896939 -->
<!-- mdoutline:crashes 0 -->
<!-- mdoutline:oracle 9527 -->
<!-- mdoutline:matched 9527 -->
<!-- mdoutline:missed 0 -->
<!-- mdoutline:missed_confessed 0 -->
<!-- mdoutline:extra 0 -->
<!-- mdoutline:fence_oracle 1130 -->
<!-- mdoutline:fence_matched 1130 -->
<!-- mdoutline:fence_missed 0 -->
<!-- mdoutline:fence_missed_confessed 0 -->
<!-- mdoutline:fence_extra 0 -->
<!-- mdoutline:regions 576 -->
<!-- mdoutline:files_with_regions 190 -->
