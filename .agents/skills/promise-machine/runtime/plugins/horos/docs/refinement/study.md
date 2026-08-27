# The classifier refinement, the study

This run executes the reopened frontier's second job: the maintainer's
budgeted two-tier classifier, specified in writing at
`plugins/horos/docs/refinement/maintainer-spec.md` and committed verbatim
with the epoch. The specification is the requirement; this study maps it
onto the shipped scanner and names what each change costs.

## Assumptions

Proceeding on these unless corrected:

1. The specification's six changes are all in scope for this one run, and
   its pipeline diagram is the classification order: metadata checks, then
   the 4 KiB prefix, then two 2 KiB windows for large unresolved
   candidates, with hard evidence binding, weak evidence reported, and no
   evidence staying readable.
2. The boundary schema advances to 2: entries carry an evidence `grade`,
   only `hard` entries are written to `boundary.json` and bind agents, and
   `candidate` findings go to a sibling `candidates.json` plus the scan
   report. The maintainer's specification is the ask-first approval for
   the schema change. The recorded schema-1 captures stay immutable
   evidence; the third job recaptures everything under schema 2.
3. The hard grade is exactly the specification's list: exact lockfile
   name, a Git attribute, a binary file signature, a generated marker, and
   valid sourcemap structure. Directory names alone, filename conventions
   alone and geometry heuristics alone are candidates unless corroborated
   as the specification defines.
4. The tracked-files default introduces Horos's first subprocess:
   `git ls-files -z` with a fixed argument list, no shell, the scan root
   pinned as the working directory, and a filesystem-walk fallback when
   the root is not a git repository or git is absent. `--include-untracked`
   adds untracked-but-not-ignored files through the same plumbing.
5. The completed job increments evolution: `horos-v7.2.2` becomes
   `horos-v8.2.2`, generation and epoch retained, and the next held job is
   the three-repository boundary marking.

## 1. Problem statement

The shipped classifier trusts three things the specification correctly
distrusts: a directory name alone can exclude a whole subtree, only the
repository root's `.gitattributes` is consulted, and a 4 KiB prefix is the
only content evidence. The refinement makes the boundary safer (nothing
binds on a name or a shape alone) and more complete (nested attributes,
file signatures, second samples), while keeping the scan linear in file
count under a strict byte budget: most files metadata-only or 4 KiB, at
most 8 KiB for large unresolved candidates, attribute files capped at
64 KiB.

Restated as checkable conditions:

- A directory named `build` holding hand-written source is walked
  file-by-file, not excluded; the same name corroborated by markers, an
  attribute, package-manager structure or an overwhelming sample excludes
  as hard, with the corroboration quoted as evidence.
- A nested `.gitattributes` deep in the tree classifies its own directory's
  files exactly as a root one would, via a rule stack pushed and popped
  during the walk.
- A file over 64 KiB that the prefix cannot classify gets two more 2 KiB
  windows, middle and end; a marker or single-line geometry found there
  classifies it (geometry still only as candidate).
- The first bytes name PNG, JPEG, GIF, ZIP, PDF, WebAssembly, WOFF and
  other common signatures as hard binary evidence, replacing reliance on a
  null byte happening to appear.
- `boundary.json` (schema 2) holds hard entries only; `candidates.json`
  holds the rest with the same determinism rules; `check` verifies the
  hard set and reports candidate drift without failing on it.
- Scanning a git repository covers exactly `git ls-files` by default;
  `--include-untracked` widens it; a non-git tree walks the filesystem as
  before, and the boundary artefact records which mode produced it.

A working prototype means all of that pinned by tests, the shipped example
regenerated under schema 2 with a candidates artefact, and both suites and
lints green.

## 2. Prior art

The maintainer's specification is the design; this study adds no options to
it. The shipped scanner supplies the walk, the atomic writer and the
determinism rules. GitHub Linguist corroborates directory heuristics with
attributes the same way; `git ls-files` as the default universe is how most
linters bound themselves.

## 3. Constraints and non-goals

- Stdlib only; the one subprocess is git, fixed argv, no shell.
- map, census and the extractors do not change; census keeps counting the
  whole walked universe with hard-boundary attribution.
- Non-goals: recapturing the recorded bundles (the third job's work),
  repository-specific approved-candidate rules (the specification names
  them as a maintainer action, not a scanner feature), and any content
  sniffing beyond the budgeted windows.

## 4. Design options

The specification fixes the design, so the only options are sequencing.
**Chosen: independent signals first (attribute stack, signatures), then the
graded pipeline (corroboration, second windows, hard and candidate split,
schema 2), then the tracked-files universe.** Trade: three implementation
steps each touching `horos.py`, accepted because each lands green and the
graded pipeline is the only step that changes artefact shape.

## 5. Risk register seed

- The attribute stack must pop exactly when the walk leaves a directory;
  a stale rule misclassifies everything after it. Pinned with nested and
  sibling-directory cases.
- Corroboration sampling reads at most eight files at 4 KiB inside a
  candidate directory; the sample is the first eight sorted names, so it
  is deterministic by construction.
- The second-window reads must never lift the budget: two 2 KiB reads only
  for files over 64 KiB that the prefix left unclassified.
- Geometry found in a window stays a candidate; the grade comes from the
  evidence class, never from how hard it was to find.
- The git subprocess: fixed argv, `-z` for NUL-separated paths, no shell,
  cwd pinned to the scan root, output decoded with `errors="replace"`, and
  a clean fallback when git is absent or the root untracked. Phylax gets
  an allow comment naming exactly that.
- `check` under schema 2: hard drift fails, candidate drift reports; both
  name paths.
- The adoption stanza stays true under schema 2 (the boundary lists only
  what binds); the SKILL.md discipline gains one line about candidates
  being advisory.

## 6. Glossary seeds

- Grade: `hard` or `candidate`; only hard binds.
- Corroboration: the second signal a directory name needs before it
  excludes as hard.
- Window: one of the two extra 2 KiB reads a large unresolved file gets.
- Universe: the file set a scan covers; tracked, tracked-plus-untracked,
  or the filesystem walk.

## 7. Boundaries

- **Always.** Both suites and the three tree lints before a commit;
  imprimatur on every shipped document; deterministic artefacts; the byte
  budget the specification states.
- **Ask first.** Any deviation from the specification's six changes; any
  further subprocess; changing the census's universe.
- **Never.** Let a candidate bind an agent; follow symlinks; run git with
  a shell; weaken the security-review exemption.

## 8. Success criteria

1. `python3 -m unittest discover -s tests` passes.
2. `python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
   passes, including the new grade, attribute-stack, signature, window,
   corroboration and universe tests.
3. `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`
   and the ephoros equivalent exit clean.
4. Demo path: `python3 plugins/horos/skills/horos/scripts/horos.py scan
   plugins/horos/examples/fixture --json` reproduces the committed schema-2
   fixture boundary byte for byte, and the committed fixture
   `candidates.json` likewise.

## 9. Sources

The maintainer's specification at
`plugins/horos/docs/refinement/maintainer-spec.md`, verbatim. The shipped
scanner and its pinned tests. GitHub Linguist's corroboration precedent.
The v7.2.2 ledger row holding this job.
