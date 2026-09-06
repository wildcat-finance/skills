# Study: ship the Markdown outline extractor

Held job, verbatim from `plugins/horos/skills/horos/EVOLUTION.md`
(`horos-v11.3.3`, frontier revision `markdown-outline-extractor`): "Ship the
Markdown outline extractor the census names at 1.83 MB across 261 files with
no boundary bytes and no map support."

Assuming, unless corrected:

1. The exact interpreter in `.python-version` (3.14.6) with stdlib
   `unittest`; no new runtime or test dependency. The differential oracle
   runs dev-time only, under a scratchpad virtualenv, as the tree-sitter
   oracles under `plugins/horos/dev/` did.
2. "Outline" for a Markdown file means, for an agent orienting in a prose
   file: its headings with level, line and verbatim text; its fenced code
   blocks with info string and line range; a front-matter block by line
   range; and a confession, by line range, of every region the outliner
   did not read, which is each raw HTML block and the remainder after a
   fence that never closes. A "declaration" is a heading or a fence. Link
   reference definitions are not outlined: the corpus holds none (section
   2), so nothing could hold that altitude to an oracle.
3. The extractor lives at `languages/markdown/markdown.py` behind the
   registry, covering `.md` only. Output register, confession contract,
   evidence bundle shape and dev-time oracle placement are unchanged from
   the five shipped extractors.
4. The oracle is markdown-it-py 4.2.0 in its `commonmark` preset, the
   CommonMark 0.31.2 reference behaviour reachable offline through pip. The
   corpus is this repository's tracked `.md` files at the commit each bundle
   names; the study measured `git ls-files '*.md'` at the starting ref.
5. `plugins/horos/skills/horos/SKILL.md` is bound by whole-file digest in
   `tests/fixtures/agent-instruction-v1/manifest.json`, so the step that
   edits it also re-pins the seven-file fixture chain named in section 3,
   carrying the recorded token counts and parity responses unchanged, as
   pull request 1231 did.
6. The completed job records `horos-v12.3.3` with `Frontier status: mature`
   and `Next Fiat job: None -- mature`. Section 12 carries the evidence; the
   decision is the study's reading of the versioning contract, not a
   maintainer instruction, and one literal question would reverse it.
7. The run starts from `main` at
   `bbb9de64b23da28cdcc56e3fcf975a0ecbed45e8`; every entry state below means
   that commit.
8. Regenerating `.horos/boundary.json` and `.horos/candidates.json` belongs
   to the same commit as any change that moves them
   (`tests/test_boundary_currency.py`). `.horos/census.json` is regenerated
   once, in the reconcile step, with `scan . --census --write`, because it is
   stale at the starting ref (section 2) and this job is census-derived.

I will proceed on these unless corrected.

## 1. Problem statement

`horos.py map` prints a declaration skeleton so a file can be oriented in
without being read whole. Five languages have extractors; Markdown, the
heaviest readable filetype in this repository at 36.2% of readable bytes,
has none, so `map` refuses every `.md` file and an agent entering a
documentation tree reads it whole or guesses from `grep`.

The user is an agent reading a repository under a Horos boundary, and the
maintainer who defends the extractor's claims. A working prototype means:

- `python3 plugins/horos/skills/horos/scripts/horos.py map <file>.md` prints
  the outline defined in assumption 2, in the register of section 4, and
  exits 0, or 1 when a fence never closed, exactly as the other extractors
  exit 1 on an unterminated construct.
- A pinned fixture at `plugins/horos/examples/fixture-md/GUIDE.md` outlines
  byte for byte to the expected text in
  `plugins/horos/tests/test_md_outline.py`, and every named trap in section
  5 has a test.
- The extractor is held against markdown-it-py over every tracked `.md` file
  of this repository at a named commit, at declared altitudes (headings by
  level and line; fences by first and last line), recorded as a
  machine-checked bundle at
  `plugins/horos/docs/evidence/skills-markdown-outline.md` with
  `.results.json` beside it: zero crashes, zero unconfessed misses, zero
  extras. Measured on the study's prototype at the starting ref: 895 files,
  9,494 headings and 1,124 fences all matched, 575 confessed regions.
- `SKILL.md`, the plugin README, `AGENTS.md` and `FUTUREPROOFING.md` name
  Markdown among the mapped languages; the ledger carries `horos-v12.3.3`
  and `SKILL.md` carries `version: "12.3.3"`.

The proving demo path, from the repository root at the last step, with
`GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false`
exported:

```bash
python3 plugins/horos/skills/horos/scripts/horos.py map plugins/horos/examples/fixture-md/GUIDE.md
python3 plugins/horos/skills/horos/scripts/horos.py map plugins/horos/skills/horos/SKILL.md
python3 -m unittest discover -s plugins/horos/tests -t plugins/horos
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 scripts/agent_instruction.py check --manifest tests/fixtures/agent-instruction-v1/manifest.json
python3 -m unittest discover -s tests
```

The first prints the pinned outline and exits 0. The second prints the skill
file's own outline: `module: Horos`, `front matter: lines 1-6`, the section
headings, four `bash` and one `text` fence under "The verbs", the four
promise headings, `declarations: 16`, one confessed region (the image
paragraph, lines 8 to 10). The third is green at the count step 2 records
(239 at entry). The fourth exits 0 with `boundary matches the tree`. The
fifth prints a `run.summary` with outcome `accepted`. The last is green in a
clean detached snapshot of the run head (1,233 at entry); inside the run
worktree it stays red on the two tests issue 1228 names.

## 2. Prior art

In this repository:

- The extractor family: `plugins/horos/skills/horos/scripts/languages/`
  holds one folder per language, each exposing `outline(path, source, out)`
  returning an exit code, dispatched by suffix from `EXTRACTORS` in
  `languages/__init__.py` (eleven suffixes, five extractors) through
  `map_file` in `horos.py` (lines 1184 to 1202), which reads the file as
  UTF-8 with replacement and refuses an unregistered suffix naming the
  supported list. `languages/python/python.py` (52 lines) parses through
  `ast`; `typescript.py` (576), `go.py` (364), `cpp.py` (587) and
  `solidity.py` (373) lex, slice verbatim and confess. The register every
  lexed extractor prints: a `module:` line, one line per declaration
  indented four spaces per depth, `lexer: <reason> at line N` per error,
  `declarations: N`, then `unparsed: none` or
  `unparsed: K region(s): lines a-b, ...` with adjacent regions merged.
  `horos.py` line 1228 still describes `map` as printing "a Python file's
  skeleton"; the step that registers `.md` corrects that help text.
- The differential pattern: `plugins/horos/dev/{ts_oracle.mjs, go_oracle.py,
  cpp_oracle.py, sol_oracle.py}` run by hand in a scratchpad virtualenv and
  emit per-file declarations at declared altitudes; each bundle under
  `plugins/horos/docs/evidence/<repo>-outline.md` carries prose plus
  `<!-- <prefix>:<key> <value> -->` capture lines that
  `plugins/horos/tests/test_evidence.py` holds to the committed
  `.results.json` totals (`files`, `crashes`, `oracle`, `matched`, `missed`,
  `missed_confessed`, `extra`, `oracle_unparsed`) and to the acceptance
  (zero crashes, misses, extras). The Solidity study
  (`plugins/horos/docs/sol-outline/study.md`) and runbook fix the four-step
  shape: spec copies, lexer and outliner with a pinned fixture, differential
  corpus, reledger and reconcile.
- Lemma's Markdown chunker, `plugins/lemma/chunkers/markdown.py` (1,521
  lines) with `plugins/lemma/schema.py` (599): `scan_structure` is a
  line-state machine over bytes that tracks fences, HTML comments, raw HTML
  blocks, open paragraphs and containers together, and its comments record
  the traps it met on a live GitBook corpus: a heading inside a fence or a
  `<div>` is not a heading, `---` is a setext underline only under an open
  paragraph, and a lazy continuation under a list item or blockquote cannot
  take a setext underline. The pattern is prior art; the code is measured
  as a candidate in section 4 and refused, on the same reasoning the
  Solidity study recorded for Lemma's Solidity chunker.
- The previous frontier run: `plugins/horos/docs/content-addressed-objects/`
  study and runbook, audit record
  `audit/rounds/fiat-ship-the-content-addressed-object-rule-whose-evi.md`,
  integrated as pull request 1231. Its study's section 3 defers this job by
  name and its runbook's fifth amendment records the `SKILL.md` fixture
  binding this study carries in section 3.
- The census. The job text's figure, 1.83 MB across 261 files, is not
  recoverable from any committed census: the census committed with the
  `horos-v9.2.3` epoch row (commit `378e4755`, 2026-08-19) records `.md` at
  256 files, 1,755,833 bytes, 0 boundary bytes, so the row's figure came
  from a scan of a tree not committed as such. Today, a fresh
  `horos.py scan . --census` at `bbb9de64` records `.md` at 895 files,
  15,799,627 bytes, 1,485 boundary bytes (the generated `CONTRIBUTORS.md`),
  36.2% of the 43,623,156 readable bytes and the largest readable filetype.
  The committed `.horos/census.json` (last written 2026-08-31, commit
  `302381ae`) says 1,114 files, 16,330,361 bytes, 3,395,842 boundary bytes
  over a 3,133-file universe against 2,550 walked today: it is stale,
  because `scan --write` writes the boundary and the candidates, never the
  census, and no test holds it (issue 1130's shape). Assumption 8 answers
  it.

The last two merged pull requests touching `plugins/horos`, by merge time:
1231 "Ship the content-addressed object rule: guard tests, documentation,
evidence and the horos-v11.3.3 row" (merged 2026-09-05T00:53:35Z) and 1230
"Demonstrate the shipped content-addressed rule at the run head" (merged
2026-09-05T00:45:19Z, step 4 of the same run). Both bodies were read. 1230
carries nothing forward beyond the issue 1228 note repeated below. 1231's
`carryover` block has six rows, each answered here by name:

- `prover-reads-any-run-design-record`, filed as issue 1228. Stays open. It
  is why the root suite is red on `test_a_candidate_outside_the_design_record_is_refused`
  and `test_prover_selftest_exits_zero_and_writes_a_closed_report` inside
  this worktree and green in a clean snapshot; every root-suite exit in this
  run is held against such a snapshot (measured at entry: `Ran 1233 tests in
  179.528s`, `OK`, in a detached worktree of `bbb9de64` without
  `.hexaemeron/`). Not this run's defect and not fixed here.
- `fixture-repin-carried-counts`, duplicate of issue 1192. Stays open. This
  run edits `SKILL.md` before its reviewed span again and pays the same
  carried re-pin (section 3); the offset-relative binding 1192 asks for is
  Hexaemeron's, not Horos's.
- `counts-in-currency-guard`, duplicate of issue 842. Stays open; section 3
  regenerates the boundary in the same commit as any file the run adds.
- `candidates-json-currency`, duplicate of issue 1130. Stays open; the
  stale census above is the same asymmetry on a third artefact, and this
  run regenerates it once rather than adding the guard the issue asks for.
- `store-directory-entries`, duplicate of issue 896. Not touched: the
  extractor adds no boundary entry of any kind.
- `horos-ci-workflow`, none: the ask-first lead open since pull requests
  256 and 261. Stays open; the root `repo` workflow runs the horos suite
  through `tests/check-map-v1.json` (`horos-suite`), which is this run's
  gate.

Audit records. `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the target root on 2026-09-05 and exited 0 with every committed
synopsis matching its source (`committed=match` on all 43 pairs), so
synopsis views are the normal reading view here. Sources and what was read:

- `audit/rounds/fiat-ship-the-content-addressed-object-rule-whose-evi.md`
  (source, 114 lines, digest
  `da88333008ff2f7e350df2ac0cab6e447d7bcfe8dca30caec02b7555baff0711`): read
  through its synopsis (8 lines, `h2_count=7`) and grepped in the source
  for finding rows, verdicts and leads. Seven round records over four steps
  (step 1 rounds 1 and 2, step 2 rounds 1 and 2, step 3 round 1, step 4
  rounds 1 and 2). Findings, all low: S1-R1-01 (the committed study copy
  misdescribed the currency guard; fixed), S1-R1-02 (the two root-suite
  tests red inside the worktree; accepted and filed as issue 1228),
  S1-R1-03 (`report format unittest text output` is not a format
  `elenchus.py` accepts; answered by three amendments naming
  `plugins/horos/tests/run_tests.py --elenchus-report {report}` and
  `unittest-json-v1`), S2-R1-01 and S4-R1-01 (the committed runbook copy
  trailing the receipted amendments; fixed). Elenchus verdicts: unguarded,
  unguarded, unguarded, null, null, unguarded, null. `Covered` lines carry
  the ten register ids per round. `Not checked` in every round: CI was
  neither read nor run, and the Pashov pair did not run under the
  `security_suite` waiver. `Leads not pursued`: whether `counts.files_walked`
  should leave the currency comparison (issue 842); whether the #1098 prover
  should locate its record by digest rather than path (issue 1228); the
  imprimatur cadence notes on the runbook copy under exit 0, which are the
  amendment grammar. Each is answered above or in section 3.
- `audit/rounds/fiat-854-stage-the-portable-sync-before-the-horos-sca.md`
  (source, 95 lines): read through its synopsis (6 rounds). Its
  `boundary-counts-churn` id is the issue 842 shape; nothing else touches
  the extractor family.
- `audit/AUDIT.md` (source, 14,172 lines): the Horos rows were grepped in
  `audit/AUDIT_SYNOPSIS.md` (426 lines). The `horos.yml` lead and
  `E319-S2-R1-04` (a boundary not regenerated after fixtures were added,
  resolved by regeneration) are the two that bear on this run; both are
  answered in section 3. Legacy rows print `[missing legacy field: ...]`
  for audit-schema, covered, not-checked and elenchus-verdict; those fields
  remain unknown.
- `plugins/horos/audit/` does not exist.

Open issues touching Horos, each read on 2026-09-05:

- 378, 379, 380 (directory-level map, promote verb, verified exclusion
  list; open): generation wishes whose wave-atlas review verdict is "keep
  behind the current frontier". Not frontier jobs; untouched here and named
  in section 12 as the reason maturity is not blocked by them.
- 842 (boundary and tree disagree in a run worktree; open): refused by
  name, as above.
- 896 (file and directory entries mixed; open): no entry added; stays open.
- 1130 (`candidates.json` checked by nothing; open): the census is the same
  shape; regenerated once here, guard not built.
- 1228 (the #1098 prover reads any run's design record; open): the
  clean-snapshot rule above.
- 1192 (before-span re-pin cost; open): paid again here, not designed.

In the organisation's other repositories: the two censuses Horos holds
record `.md` at 15 files, 87,645 bytes in v2-protocol
(`plugins/horos/docs/evidence/v2-protocol-census.json`, 236 files) and 2
files, 27,545 bytes in wildcat-app-v2 (`wildcat-app-v2-census.json`, 1,113
files), no boundary bytes in either. Both become mappable; neither owes a
re-marking, because an extractor changes no boundary.

Outside: the CommonMark specification 0.31.2 defines ATX and setext
headings, fenced and indented code, the seven HTML block start conditions,
container blocks and lazy continuation. Reference implementations reachable
offline through pip: markdown-it-py 4.2.0 (MIT, one dependency `mdurl`
0.1; 7,877 Python lines across both), mistune 3.3.4; through npm,
commonmark.js 0.31.2. The oracle survey of the corpus through markdown-it-py
(`.hexaemeron/design-reports/md_oracle.py`, 1.8 s over 895 files): 9,494
headings after front-matter exclusion (760 h1, 6,868 h2, 1,840 h3, 26 h4,
none deeper), of which 4 setext and 0 inside a blockquote or list item;
1,124 fences (25 inside list items, 72 without an info string); 12 indented
code blocks; 644 HTML blocks, one of which hides a `#`-led line; 44 files
with YAML front matter, which CommonMark reads as a thematic break and a
setext h2 unless stripped first; 0 link reference definitions; 0 files with
a carriage return.

## 3. Constraints and non-goals

Constraints:

- Starting ref: `main` at `bbb9de64b23da28cdcc56e3fcf975a0ecbed45e8`, on
  branch `fiat/ship-the-markdown-outline-extractor-the-census-n`.
- Toolchain: the interpreter in `.python-version` (3.14.6), stdlib only in
  everything that ships; `pyproject.toml` declares the supported minor. The
  oracle virtualenv holds markdown-it-py 4.2.0 and lives in the scratchpad,
  never in the tree; only `plugins/horos/dev/md_oracle.py` and the recorded
  results are committed.
- Entry state, measured on 2026-09-05: root suite `Ran 1233 tests in
  179.528s`, `OK`, in a clean detached snapshot; horos suite `Ran 239 tests
  in 9.998s`, `OK`; `horos.py check .` exits 0 with `boundary matches the
  tree`; `scan . --census --json` leaves `.horos/` unchanged (the census
  is only written with `--write`).
- Host condition: this machine sets `commit.gpgsign=true` globally, so
  every `unittest` invocation carries
  `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false`.
- The repository's check rule (`AGENTS.md`, "Checks for changes to this
  repository"): `python3 scripts/run_checks.py` selects from the diff
  through `tests/check-map-v1.json`, where `horos-suite` owns
  `plugins/horos/tests`. Every step exit names the root suite and the horos
  suite directly as well. Each runbook step's Tests field names the Elenchus
  runner `python3 plugins/horos/tests/run_tests.py --elenchus-report {report}`
  (root-level steps `python3 tests/run_tests.py --elenchus-report {report}`),
  report format `unittest-json-v1`, report file
  `.hexaemeron/elenchus-step-N.json`.
- `plugins/horos/skills/horos/SKILL.md` is bound in
  `tests/fixtures/agent-instruction-v1/manifest.json` (fixture
  `horos-boundary-check`, source sha256
  `24f121a3f8929bd6ca2e39fe5e0caac5e289d955687232a1fc0bdff217925eaf`,
  reviewed span bytes 11633 to 12651, the `### horos-boundary-check`
  promise, span sha256
  `0f2fb54b8f737de4b8ec42b88bdc6d9238f65de8525847c81381cbb83d0e91a2`). The
  map paragraph, the "Current frontier" block and the frontmatter version
  all sit before the span, so the one step that edits the file re-pins
  seven files with `~/.claude/tools/repin_fixture.py` and
  `repin_evidence.py`, carrying the recorded token counts and parity
  responses unchanged: `tests/fixtures/agent-instruction-v1/manifest.json`,
  `tests/fixtures/agent-instruction-v1/horos-boundary-check/model.json`,
  `.../horos-boundary-check/source-spans.json`,
  `.../horos-boundary-check/compact.wai`,
  `tests/fixtures/agent-instruction-v1/evidence/measurement.json`,
  `tests/fixtures/agent-instruction-v1/evidence/parity.json` and
  `tests/promise_machine_coverage.json`. The exit for that step is
  `python3 scripts/agent_instruction.py check --manifest
  tests/fixtures/agent-instruction-v1/manifest.json` printing a
  `run.summary` with outcome `accepted`, `python3 scripts/promise_machine.py
  coverage` printing `clean`, and `span_sha256` unchanged. Every other edit
  to `SKILL.md` waits for that step, so the run pays one re-pin.
- Boundary schema stays 2; no rule, evidence string or CLI flag changes.
  The `map` subcommand gains one suffix in the registry and a corrected
  help string; `scan` and `check` are untouched.
- Adding a tracked file moves `counts.files_walked`, so
  `.horos/boundary.json` and `.horos/candidates.json` are regenerated in
  the same commit as any step that adds one, from a tree where `git status`
  is clean apart from the run's own tracked changes (pull request 1062's
  lesson), and `tests/test_boundary_currency.py` is green at every exit.
- `plugins/horos/AGENTS.md` holds: no network, no execution of inspected
  source, writes confined to the target's `.horos/`. The extractor reads
  one file and prints.
- Prose gates: `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`
  exit 0 on every shipped document; `tests/test_marketplace_prose.py` (23
  tests) on every mutable block.

Boundary tiers for the build:

- Always: both suites before a commit; the imprimatur lint on every shipped
  document; `horos.py check .` exit 0 at every step exit; regenerate the
  boundary and candidates in the same commit as any change that moves them;
  a differential run recorded as a bundle before any claim about recall;
  the fixture chain re-pinned in the same commit as any `SKILL.md` edit.
- Ask first: adding a dependency, vendoring one, or importing across the
  plugin boundary; widening the compared altitudes; changing the
  `SKILL.md` frontmatter `description` (bound across hosts by
  `test_short_descriptions_agree_across_hosts`); touching `.github/`;
  registering a suffix other than `.md`; changing an existing extractor.
- Never: import or execute what is mapped; hand-edit `.horos/boundary.json`;
  edit `plugins/horos/examples/` to dodge a failing test; delete a failing
  test; edit the reviewed span of `SKILL.md`; claim a corpus run that did
  not happen.

Non-goals, deferred past this prototype:

- Inline structure: emphasis, links, images, code spans, autolinks, entity
  and backslash escapes. Heading text is the verbatim line.
- Link reference definitions and footnotes (zero in the corpus).
- Tables, task lists, strikethrough and every other GitHub or GitBook
  extension; `{% ... %}` template tags are prose.
- Indented code blocks as declarations: outlined as nothing, never
  confessed, because they are content, not structure.
- `.markdown`, `.mdx`, `.rst` and `.txt` suffixes; `.js` for the
  TypeScript extractor.
- Any change to the census, the boundary rules, or the three generation
  wishes 378, 379 and 380.
- A census or candidates currency guard (issue 1130); the `horos.yml`
  workflow; an offset-relative fixture binding (issue 1192).
- The `SOURCES.md` refresh: owed by Alexandria, Tabularium, Lazarus and
  Probitas runs, not Horos.

## 4. Design options

Four candidates, each a real construction under
`.hexaemeron/design-reports/candidates/`, measured by
`python3 .hexaemeron/design-reports/resolve.py <candidate> <criterion>` from
the repository root over the 895-file corpus (`corpus-list.txt`, the
`git ls-files '*.md'` of the starting ref) and the recorded oracle
(`oracle.json`, produced once by `md_oracle.py` under the virtualenv). The
closed record at `.hexaemeron/design-evidence.json` selects one.

- `line-scanner`. A line-oriented scanner in the fixed extractor shape:
  ATX and setext headings and fenced code blocks sliced verbatim, front
  matter named by line range, blockquote markers and list-item content
  indents stripped per line so a heading or fence inside a container is
  still seen, raw HTML blocks and an unterminated fence confessed as
  unparsed regions. 324 lines, stdlib only. Trade: recall is bounded by the
  block rules it implements (no link reference definitions, no inline
  parsing, no tables), and a CommonMark corner it does not model surfaces
  as a differential mismatch rather than a parse error.
- `heading-only`. An ATX regex per line, nothing else. Trade: the cheapest
  construction, and it reads `# comment` lines inside `bash` fences as
  headings and sees no fence at all.
- `vendor-parser`. Vendor markdown-it-py 4.2.0 and mdurl under
  `languages/markdown/` and adapt its block tokens to the register.
  Measured against the real package, byte for byte what a vendored copy
  would be. Trade: exact CommonMark for 7,877 lines of third-party Python
  the skill would have to carry, and a parser that reads inline content it
  will never print.
- `lemma-reuse`. Import `scan_structure` from
  `plugins/lemma/chunkers/markdown.py` across the plugin boundary and adapt
  its heading list. Trade: a proven scanner for a cross-plugin import that
  couples two independently shipped skills, and it reports headings only.

Criteria, all at stage `selection` blocking `design-lock`, five concerns
covered:

| id | concern | form | rule | line-scanner | heading-only | vendor-parser | lemma-reuse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `unconfessed-misses` | correctness | gate | equals 0 | 0 | 1,128 (fail) | 0 | 1,165 (fail) |
| `extras` | correctness | gate | equals 0 | 0 | 135 (fail) | 0 | 0 |
| `foreign-source-lines` | compatibility | gate | equals 0 | 0 | 0 | 7,877 (fail) | 2,120 (fail) |
| `corpus-outline-ms` | time | metric | minimise | 319 | 91 | 2,135 | 4,065 |
| `peak-heap-bytes` | space | metric | minimise | 1,654,625 | 1,623,773 | 18,359,390 | 3,922,303 |
| `hostile-input-crashes` | recovery | gate | equals 0 | 0 | 0 | 1 (fail) | 1 (fail) |
| `unterminated-fence-confessed` | recovery | gate | equals true | true | false (fail) | true | false (fail) |

How each was measured:

- `unconfessed-misses` and `extras` run the candidate's `declarations()`
  over every corpus file and compare heading `(level, line)` and fence
  `(first, last)` sets with the oracle; a miss whose line lies inside a
  confessed region is not counted, a crash counts as a miss. `heading-only`
  misses the 4 setext headings and all 1,124 fences and adds 135 headings
  from `#`-led lines inside fences. `lemma-reuse` returns no fences and
  misses 41 headings, all round headings in `audit/rounds/*.md` files
  following a pipe table; the cause was not traced.
- `foreign-source-lines` counts Python lines outside `plugins/horos` that
  `map` would execute: the two Lemma files, or every `.py` under the
  installed `markdown_it` and `mdurl` packages. The gate is the recorded
  refusal of a parser dependency (`horos-v1.1.0`) and the Solidity study's
  refusal of a cross-plugin import.
- `corpus-outline-ms` is the median of three in-process runs over the
  corpus; `peak-heap-bytes` is the largest `tracemalloc` peak over any one
  file.
- `hostile-input-crashes` runs eight inputs under a 10 s alarm: an empty
  file, CR-only line endings, 64 KiB of every byte value, a fence that
  never closes over 1,000 lines, one 2 MiB line of `#`, 5,000 nested `>`
  markers, a 2,000-deep nested list, and 100,000 lines alternating
  headings and fences. markdown-it-py times out on the 2 MiB line; Lemma's
  scanner times out on the 100,000-line file.
- `unterminated-fence-confessed` feeds `# a\n```\n# not\n` and requires the
  candidate to flag the open fence and confess line 2.

Selection: three gates remove `heading-only`, `vendor-parser` and
`lemma-reuse`; `line-scanner` is the unique frontier.
`python3 <plugin_root>/skills/protasis/scripts/design_evidence.py
.hexaemeron/design-evidence.json --transition design-lock` exits 0.
`heading-only`'s time and space advantages are real and recorded; it is
refused on correctness and recovery, not on cost. Beyond the corpus, 35
synthetic cases in `.hexaemeron/design-reports/synthetic.py` (headings in
quotes and items, fences in items closed by the item's end, lazy setext
traps, HTML that hides a heading, tilde and longer closing fences, CRLF)
match the oracle in 33; the two that differ are both an unterminated fence,
which the oracle reads as a fence to end of file and the scanner confesses
by declaration.

What `line-scanner` prints, the register the fixture pins:

```text
module: <text of the first h1, or (no title)>
front matter: lines 1-N            (only when present)
# Title  (line 12)
    ## Section  (line 17)
        ``` bash  (lines 37-39)
    Setext title  (setext h2)  (line 40)
lexer: unterminated fence at line N (only when one never closed)
declarations: N
unparsed: K region(s): lines a-b, line c
```

A heading is its verbatim line indented four spaces per level below one; a
fence sits one level under the heading above it with its info string and
line range; a setext heading prints its paragraph's first line with the
marker. Exit 1 only for an unterminated fence.

What `line-scanner` builds, by home:

- `plugins/horos/skills/horos/scripts/languages/markdown/__init__.py` and
  `markdown.py`; `languages/__init__.py` gains one registry line (`.md`);
  `horos.py` line 1228's help text names supported languages.
- `plugins/horos/examples/fixture-md/GUIDE.md` and
  `plugins/horos/tests/test_md_outline.py`: the pinned outline, one test
  per section 5 trap, the registry dispatch. Expected: about fifteen tests.
- `plugins/horos/dev/md_oracle.py` (from the study's copy) and the
  differential driver; `plugins/horos/docs/evidence/skills-markdown-outline.md`
  with `.results.json` and capture prefix `mdoutline`;
  `plugins/horos/tests/test_evidence.py` extended by two tests (bundle
  matches results; acceptance holds, including `fence_matched` equal to
  `fence_oracle`). Expected horos suite: about 256.
- `plugins/horos/docs/markdown-outline/study.md` and `runbook.md`: the
  receipted copies.
- `plugins/horos/skills/horos/EVOLUTION.md`, `SKILL.md`, the fixture chain,
  `plugins/horos/README.md`, `plugins/horos/AGENTS.md`, `FUTUREPROOFING.md`,
  `.horos/census.json`: section 12.

## 5. Risk register seed

The audit loop should look hardest at the container and HTML rules, because
that is where a heading is silently suppressed or invented, and at the
`SKILL.md` step, because the fixture re-pin is where the previous run's
findings landed.

```risk-register
fence-shadowed-heading | a #-led line inside a fenced block | never a heading; backtick and tilde fences, indented up to three spaces, closing at the same character and at least the opening length with nothing after it, pinned by test
html-hidden-heading | a heading-shaped line inside an HTML block of any of the seven start kinds | not a heading and the block is confessed by line range; a type 7 block cannot interrupt a paragraph, pinned by test
setext-under-lazy-line | a --- or === under a lazy continuation of a list item or blockquote | a thematic break or text, never a heading; a --- under an open top-level paragraph is an h2, pinned by test
container-prefix | a heading or fence behind > markers or a list item's content indent | seen at its level, and a fence inside an item closes when the item does; the corpus holds 25 such fences and no such heading, so the synthetic cases carry this altitude
front-matter-phantom | a --- opener on line 1 with a closing --- | named as front matter and excluded on both sides of the differential; without the exclusion the oracle reads title: x as a setext h2 in 44 corpus files
unterminated-fence | a fence that never closes | the remainder is confessed, a lexer line names the opener, exit 1; the oracle reads it as a fence to end of file and the bundle declares the difference
hostile-input | an empty, binary, CR-only, 2 MiB single-line or 2,000-deep nested file | no exception and under 10 s each, pinned by the resolve.py hostile set and a test for the empty and CR-only cases
declared-altitudes | headings by level and line, fences by first and last line | the bundle compares exactly these, names front matter and link definitions as excluded, and its capture lines equal the results totals
boundary-regeneration | .horos/boundary.json and candidates.json after any tracked file is added | regenerated in the same commit from a clean tree; tests/test_boundary_currency.py green at every exit
census-regeneration | .horos/census.json, stale at entry | regenerated once with scan . --census --write in the reconcile step and its .md row quoted in the bundle
fixture-repin | the seven-file agent-instruction chain bound to SKILL.md | re-pinned in the one step that edits SKILL.md, span_sha256 unchanged, agent_instruction.py check accepted, promise_machine.py coverage clean, counts carried and said so in the audit record
prose-reconciliation | every marketplace-context block, the plugin README, AGENTS.md, FUTUREPROOFING.md, the SKILL.md map paragraph | every surface names Markdown among the mapped languages, none says it has no extractor, tests/test_marketplace_prose.py green
ledger-row | EVOLUTION.md and the SKILL.md version | horos-v12.3.3, status mature, next job None -- mature, with the digest hexctl computes and the census evidence of section 12 in the row
no-execution | map over an untrusted .md file | the file is read once as UTF-8 with replacement and never imported, executed or written
```

## 6. Glossary seeds

- Outline: the heading, fence and front-matter skeleton of one Markdown
  file, plus the confessed regions.
- Declaration: a heading or a fenced code block; the `declarations:` count.
- ATX heading: one to six `#` at up to three spaces of indent, then a space
  or the line's end; closing hashes are stripped from the text.
- Setext heading: a paragraph followed by a `=` (h1) or `-` (h2) underline
  at the same container depth, with no lazy continuation between.
- Fence: three or more backticks or tildes opening a code block; the info
  string follows the opener; a backtick fence's info string holds no
  backtick.
- Container prefix: the `>` markers and list-item content indent stripped
  from a line before the leaf rules apply.
- HTML block: a region opened by one of CommonMark's seven start
  conditions, closed by its terminator or a blank line; confessed whole.
- Front matter: a `---` line at line 1 through the next `---` or `...`
  line; outlined by range and excluded from the differential.
- Unparsed region: a confessed line range, adjacent ranges merged.
- Declared altitudes: headings by `(level, line)` and fences by
  `(first, last)`; what the bundle compares.
- Oracle: markdown-it-py 4.2.0, `commonmark` preset, driven by
  `md_oracle.py` with front matter stripped identically.
- Fixture chain: the seven files bound to `SKILL.md` through the
  agent-instruction manifest.
- Frontier digest: SHA-256 over `status|revision|frontier|next_job` plus a
  newline, as `hexctl` computes it for the ledger's final row.

## 7. Sources

- `plugins/horos/skills/horos/scripts/horos.py` lines 1184 to 1229;
  `scripts/languages/__init__.py`; `languages/solidity/solidity.py`;
  `languages/python/python.py`, all at `bbb9de64`.
- `plugins/horos/dev/sol_oracle.py`; `plugins/horos/docs/evidence/solidity-outline.md`
  and `.results.json`; `plugins/horos/tests/test_evidence.py` lines 209 to
  230; `plugins/horos/tests/test_sol_outline.py`;
  `plugins/horos/tests/run_tests.py`.
- `plugins/horos/docs/sol-outline/study.md` and `runbook.md`;
  `plugins/horos/docs/content-addressed-objects/study.md` (sections 2, 3,
  12) and `runbook.md` (amendments 4 and 5).
- `plugins/lemma/chunkers/markdown.py` lines 1 to 130 and 354 to 560;
  `plugins/lemma/schema.py`.
- `plugins/horos/skills/horos/EVOLUTION.md`, rows `horos-v9.2.3` to
  `horos-v11.3.3`; `plugins/hexaemeron/skills/VERSIONING.md`, "Frontier
  discipline" and "What every frontier run owes".
- Pull requests 1231 and 1230 in `wildcat-finance/skills` (bodies read via
  `gh pr view --json body` on 2026-09-05); the merged list from
  `gh pr list --state merged --search horos`.
- Issues 378, 379, 380, 842, 896, 1130, 1192, 1228, read on 2026-09-05.
- `audit/rounds/fiat-ship-the-content-addressed-object-rule-whose-evi.md`
  and `.synopsis.md`; `audit/rounds/fiat-854-stage-the-portable-sync-before-the-horos-sca.synopsis.md`;
  `audit/AUDIT_SYNOPSIS.md`; the synopsis check output of 2026-09-05.
- `.horos/census.json` at `bbb9de64` and at `378e4755`; the fresh
  `scan . --census` output of 2026-09-05;
  `plugins/horos/docs/evidence/v2-protocol-census.json` and
  `wildcat-app-v2-census.json`; `.horos/boundary.json`.
- `tests/fixtures/agent-instruction-v1/manifest.json` (fixture
  `horos-boundary-check`); `~/.claude/tools/repin_fixture.py` and
  `repin_evidence.py`; `tests/check-map-v1.json` (`horos-suite`);
  `tests/test_boundary_currency.py`; `tests/test_marketplace_prose.py`.
- `plugins/horos/README.md` lines 10 to 24 and 69; `plugins/horos/AGENTS.md`
  line 4; `FUTUREPROOFING.md` line 110; `plugins/horos/.codex-plugin/plugin.json`
  `longDescription`.
- `.hexaemeron/design-reports/`: `resolve.py`, `md_oracle.py`,
  `differential.py`, `synthetic.py`, `oracle.json`, `corpus-list.txt`,
  `candidates/`, and the 28 reports.
- CommonMark specification 0.31.2 (spec.commonmark.org), sections on ATX
  headings, setext headings, fenced code blocks, HTML blocks, container
  blocks; markdown-it-py 4.2.0 (PyPI, MIT).

## 8. Signals, and the questions behind them

None for on-call, and here is why: `map` is a command a person or an agent
runs from a terminal on one file, prints, and exits; nothing this run ships
runs unattended or writes anything. The questions that do get asked are
answered by lines already in the register: "does the skeleton understate the
file?" is the `unparsed:` line; "did the fence ever close?" is the `lexer:`
line and exit 1; "did the extractor keep its recall?" is the bundle's
capture lines held by `test_evidence.py`.
[ephoros](../../../hexaemeron/skills/ephoros/SKILL.md) owns what
a signal must carry; none is added.

## 9. Boundaries, per capability

One boundary, the same one every extractor opens: `map` reads one file the
agent does not trust and prints derived lines. Worth taking there: time, by
a very long line or a very deep nesting; a crash, by bytes that are not
text; a hidden heading, by an HTML block or fence written to shadow one.
Controls: the file is read once as UTF-8 with replacement and never
imported or executed; every rule is a bounded regular expression applied
per line, so the cost is linear in lines and the container stack is walked
at most once per line (2,000-deep nesting and a 2 MiB line finish under the
10 s alarm, measured); a shadowed heading is a confessed region, so the
reader is told the skeleton understates the file rather than shown a false
one. No network, no subprocess, no secret and no dependency is added; the
oracle stays in a virtualenv outside the tree.
[phylax](../../../hexaemeron/skills/phylax/SKILL.md) owns the
boundary list and the controls.

## 10. The budget, or its absence

One budget, measured on this tree on 2026-09-05: outlining every tracked
`.md` file of this repository (895 files, 15,799,627 bytes) in one process
stays at or under 1,000 ms. Measured: 319 ms, median of three runs
(design report `line-scanner-corpus-outline-ms`), against 2,135 ms for the
reference parser. Command:
`python3 .hexaemeron/design-reports/resolve.py line-scanner corpus-outline-ms`.
Peak heap over any one file is 1,654,625 bytes (`line-scanner-peak-heap-bytes`),
with no budget beyond staying under the parser's 18,359,390. The horos
suite is expected to stay under 15 s (10.0 s at entry). No step may claim a
cost without rerunning the first command.
[metron](../../../hexaemeron/skills/metron/SKILL.md) owns what a
budget carries and how it is checked.

## 11. The fail-closed posture

What stops the run: a red root suite in a clean snapshot or a red horos
suite; `horos.py check .` exiting 1 at a step exit;
`tests/test_boundary_currency.py` naming drift; a differential bundle with
any unconfessed miss, extra or crash; `agent_instruction.py check` refusing
a record after the re-pin; `tests/test_marketplace_prose.py` naming a
block; `imprimatur.py` exiting non-zero on a shipped document; a design
report whose digest no longer matches the record. The guard convention: a
fix ships with a test that fails without it, named for the failure it pins,
in `test_md_outline.py` for an outliner rule and in `test_evidence.py` for
a bundle figure; a corpus mismatch found in the differential step becomes a
fixture case before the rule is changed. The extractor itself fails closed:
a fence that never closes confesses the remainder and exits 1 rather than
printing headings it cannot vouch for.
[elenchus](../../../hexaemeron/skills/elenchus/SKILL.md) owns the
triage order and the guard rule.

## 12. Decisions and their homes

[hypomnema](../../../hexaemeron/skills/hypomnema/SKILL.md) owns
which decisions earn a record and where each lives.

- The outline definition (assumption 2) and the register (section 4), and
  the refusal of the vendored parser and the Lemma import on measured
  gates, are expensive to reverse: every fixture and the bundle pin them.
  Home: the closed design record `.hexaemeron/design-evidence.json` and its
  reports, the committed copies at `plugins/horos/docs/markdown-outline/`,
  and the module docstring of `languages/markdown/markdown.py`.
- The declared altitudes and the two declared exclusions (front matter on
  both sides, an unterminated fence confessed rather than matched). Home:
  the bundle `plugins/horos/docs/evidence/skills-markdown-outline.md` and
  the docstring of `plugins/horos/dev/md_oracle.py`.
- The ledger row and the maturity call. Home:
  `plugins/horos/skills/horos/EVOLUTION.md`, written by the reconcile
  step: `horos-v12.3.3`, axis `evolution`, `Frontier status: mature`,
  `Next Fiat job: None -- mature`, evidence linking the committed study and
  the bundle, with the frontier digest `hexctl` computes; `SKILL.md`
  frontmatter to `version: "12.3.3"` in the same commit. The evidence the
  row records: the `horos-v9.2.3` epoch named three jobs and expected
  maturity after the third, and this is the third. After it, every
  filetype above 1% of this tree's readable bytes has an extractor or is a
  data format with no declarations to outline: `.md` 36.2% and `.py` 24.9%
  and `.sol` 1.2% mapped; `.json` 28.9% and `.jsonl` 8.0% are records, not
  source; `.js` is 0.4% (13 files), `.yml` 0.2%, everything else under
  0.1%. The two external censuses show v2-protocol 87.6% Solidity and
  wildcat-app-v2 TypeScript, both mapped, with `.md` the only other
  readable text of weight in either and now mapped. The open issues are
  generation wishes held behind the frontier (378, 379, 380) or defects
  whose owner is Hexaemeron or the root suite (842, 896, 1130, 1192,
  1228). A `.js` registration or a `.rst` extractor would be an extension
  without a census that names it, which the contract says does not
  qualify. Reopening needs a maintainer's new external evidence recorded
  as an epoch entry.
- The marketplace-prose reconciliation. Cold-read findings at the starting
  ref: `plugins/horos/README.md` line 24 says "Markdown has no outline
  extractor yet" and line 69 lists five languages; the "Current frontier"
  and "Next Fiat job" text in the ledger header, `plugins/horos/README.md`
  lines 10 and 12, `plugins/horos/AGENTS.md` line 4 and the `SKILL.md`
  block all name the Markdown extractor as the remaining job; the
  `SKILL.md` map paragraph lists five languages; `FUTUREPROOFING.md` line
  110 lists five; `horos.py` line 1228 says "a Python file's skeleton";
  the `SKILL.md` frontmatter `description` says "print Python skeleton
  maps" and the `.codex-plugin/plugin.json` `longDescription` is in the
  same family, both bound across hosts and left as ask-first. Home: the
  mutable blocks themselves, held by `tests/test_marketplace_prose.py`,
  with the decision recorded in the run's audit log.
- The stale census regenerated once (assumption 8). Home: the bundle's
  census paragraph and the reconcile step's commit message.
