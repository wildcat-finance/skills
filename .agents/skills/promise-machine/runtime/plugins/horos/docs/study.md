# Horos, the study

Horos, ὅρος, the boundary stone. A skill that decides what an agent does not
read, and proves the decision instead of asserting it.

This study is the successor to the Epitome assessment of 2026-08-18, which
measured the code-compression premise against this marketplace and two Wildcat
repositories and rejected it: the licensed saving was about 3% of tokens,
published evidence prices representation-degrading transforms at up to 12
points of task completion, and not reading generated or vendored files at all
removed 66% to 87% of readable bytes at no semantic risk. Horos builds the
mechanism that wins that comparison.

## Assumptions

Proceeding on these unless corrected:

1. Python 3.11 and stdlib `unittest`, matching every other plugin here. No
   third-party dependency without asking first.
2. Horos ships as a new marketplace plugin at `plugins/horos/` in the house
   shape: `skills/horos/SKILL.md` with version metadata, `EVOLUTION.md`
   conforming to the marketplace evolution contract, scripts under
   `skills/horos/scripts/`, tests under `tests/`, registration in
   `.claude-plugin/marketplace.json`.
3. A target repository is a directory tree on disk. Horos walks the working
   tree; it does not need git, the network, or a subprocess.
4. TypeScript and JavaScript skeleton maps are out of the prototype. Stdlib
   Python cannot parse them honestly, and a regex sketch of a language is the
   kind of guess this marketplace refuses. Python skeletons via `ast` are in.

## 1. Problem statement

An agent asked to work in a repository spends most of its reading budget on
files that carry nothing for the task: build output committed to the tree,
vendored dependencies, lockfiles, minified bundles, single-line data blobs.
Measured this week: 87% of readable bytes in `v2-protocol` (9.7 MB of solc
output under `deployments/`), 66% in `wildcat-app-v2` (a checked-in Storybook
build, `package-lock.json`, and a 1.4 MB JSON file on one physical line worth
roughly 360,000 tokens on its own).

Horos gives the agent three verbs and a discipline:

- `scan` walks a tree, classifies each file it can evidence as a token sink,
  and writes `.horos/boundary.json`: a deterministic, sorted record where
  every entry carries its category, size and the evidence line that earned it.
- `check` re-derives the classification and compares it with the committed
  boundary, exiting non-zero on drift.
- `map` prints a skeleton of a Python file, meaning its signatures, class
  structure and the first line of each docstring, so a large file can be
  oriented in before it is read whole, or instead of being read whole.

The SKILL.md teaches the agent the discipline: consult the boundary before
reading, treat everything inside it as unread-by-default, use `map` before
opening any large Python file, and ignore the boundary entirely during
security review, where hiding a file is exactly what an adversary would want.

A working prototype means the demo path runs: `scan` over the committed
example fixture reproduces the committed expected boundary byte for byte,
`check` passes on the intact fixture and fails on a documented mutation of
it, and both test suites and the tree lints are green.

## 2. Prior art

Outside: GitHub Linguist's `linguist-generated` and `linguist-vendored`
attributes are the closest ancestor: a per-path classification that changes
what a reader (the diff view) shows, driven by heuristics plus maintainer
annotation. aider's repo-map and Repomix `--compress` build tree-sitter
skeletons under a token budget. LongCodeZip (arXiv 2510.00446) supplies the
evidence that selection-based reduction preserves task performance where
rewriting does not. None of these emits a checked-in, evidence-bearing,
verifiable boundary; that is the gap Horos occupies.

Inside this repository: the Epitome study (the measurement this design rests
on); Lemma's chunkers, which already separate quotation text from model text
per chunk; Hypomnema's `VENDORED` set, a hand-kept ancestor of the vendored
category; and Pandects' comment-stripper tests, which pin the
string-literal traps any content-sniffing pass must not repeat.

## 3. Constraints and non-goals

- Stdlib only. `os`, `ast`, `json`, `unittest`; no tree-sitter, no tokenizer.
- The marketplace contract tests govern the plugin shape: a conforming
  `EVOLUTION.md`, SKILL.md version metadata matching it, portable-skill and
  marketplace-prose rules. The phylax and ephoros lints must exit clean over
  `plugins tests`.
- Classification is fail-open. A file Horos cannot evidence stays readable.
  The asymmetry is deliberate: a wrongly excluded source file blinds the
  agent; a wrongly included sink merely wastes what it always wasted.
- Bounded reads. The classifier stats every file but reads at most a fixed
  prefix (4 KiB) of any of them. A scan must never cost more than a fraction of
  what it saves.
- Non-goals for the prototype: code transformation of any kind (Epitome's
  ground, already rejected), TS/JS skeletons, git-history signals, network
  fetches, automatic boundary regeneration, and any per-token accounting.
  Bytes are the unit; the Epitome study already established the conversion.

## 4. Design options

**A. One stdlib classifier, a checked-in boundary, Python skeletons.** Rule
classes: binary content (null byte in prefix); lockfiles by exact name;
generated files by marker in the read prefix ("DO NOT EDIT", "@generated",
"Code generated by", solc output shapes, `.map` sourcemaps) or by directory
convention (`dist/`, `build/`, `storybook-static/`, `deployments/` when
marker-confirmed); vendored directories by name and by `linguist-vendored`
attributes where a `.gitattributes` exists; blobs by physical-line geometry
(single line over a byte threshold, or mean line length over a minified-code
threshold). Trade: heuristics misclassify, so every entry must carry evidence
and the uncertain case defaults to readable, which caps recall: Horos will
miss sinks a human would catch, and says so in its report.

**B. Wrap repomix or aider's repo-map.** Trade: a Node dependency chain, no
evidence contract, no verifiable committed artefact. Rejected: it buys the
skeleton half and abandons the boundary half, in a toolchain this marketplace
does not carry.

**C. Prose-only SKILL.md heuristics, no script.** Trade: nothing to test,
nothing to verify, and every claim drifts. Rejected by Metron's rule: an
optimisation with no measurement attached is an opinion.

**D. Drive everything from `.gitattributes` annotations.** Trade: covers only
what maintainers already annotated, and the measured sinks in both Wildcat
repos carried no annotations at all. Folded into A as one input signal.

**Chosen: A.** It is the cheapest construction to comprehend that meets the
problem statement. Its one trade, bounded recall in exchange for zero false
exclusions of hand-written source, points the right way for a tool whose
worst error is hiding code from the reader.

## 5. Risk register seed

What the audit loop should look hardest at, phylax first:

- Symlinks. The walker must never follow a link out of the scan root; a
  hostile tree can otherwise walk the scanner into `$HOME`.
- Partial writes. `boundary.json` is written to a temporary file and renamed,
  so a killed run leaves either the old boundary or the new one, never half.
- Undecodable bytes. Marker search decodes the prefix with
  `errors="replace"`; classification must not raise on any byte sequence.
- Determinism. Same tree, same boundary, byte for byte: sorted paths, sorted
  keys, no timestamps, no absolute paths inside the artefact.
- The poisoned boundary. A committed `boundary.json` in a hostile repository
  could list source files as sinks to keep a reviewing agent from reading
  them. Two controls: `check` re-derives everything it asserts before an
  agent leans on it, and the SKILL.md forbids applying any boundary during
  security review. The skill text carries this rule verbatim, and the test
  suite asserts its presence so an edit cannot drop it silently.
- Evidence strings. The marker or geometry line that earned each entry is
  quoted exactly, never paraphrased, so a human can dispute a classification
  from the artefact alone.
- Ephoros: a scan that runs unattended must report counts (files walked,
  bytes classified per category, files skipped as unreadable), and `check`
  must name every drifted path, not just fail.

## 6. Glossary seeds

- Token sink: a file whose bytes cost reading budget and return nothing for
  the task at hand.
- Reading boundary: the committed set of paths an agent leaves unread by
  default, each with the evidence that put it there.
- Fail-open classification: uncertainty keeps a file readable; only evidence
  excludes.
- Skeleton map: the signatures-and-structure view of a file, printed instead
  of the file.
- Bounded read: the classifier's own reading limit, which is to stat
  everything and read at most a fixed prefix.
- Drift: any difference between the committed boundary and one derived fresh
  from the tree.

## 7. Boundaries

- **Always.** Both test suites before a commit (`python3 -m unittest discover
  -s plugins/horos/tests -t plugins/horos` and the root contract suite). The
  phylax and ephoros lints over `plugins tests`. The imprimatur lint on every
  shipped document. Atomic writes for every artefact Horos emits.
- **Ask first.** Any dependency. Any change to the boundary schema once one
  release has shipped. TS/JS skeleton support. Touching CI. Raising the read
  prefix or the blob thresholds once tests pin them.
- **Never.** Follow a symlink out of the scan root. Execute or import
  anything from a scanned repository. Apply a reading boundary during
  security review or an audit round. Fetch anything over the network. Delete
  a failing test to make a suite pass.

## 8. Success criteria

1. `python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
   passes.
2. `python3 -m unittest discover -s tests -t .` passes, which holds the
   evolution ledger, portability and marketplace-prose contracts.
3. `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`
   and the ephoros equivalent exit clean.
4. Demo path: `python3 plugins/horos/skills/horos/scripts/horos.py scan
   plugins/horos/examples/fixture --json` reproduces the committed expected
   boundary byte for byte; `check` exits 0 on the intact fixture and non-zero
   after the documented mutation in the example's README.
5. Recorded once as environmental evidence, not a repeatable gate: a scan of
   the wildcat-app-v2 clone classifies at least 60% of its readable bytes as
   sinks while excluding zero hand-written files under `src/`, checked
   against the file list from the Epitome study.

## 9. Sources

The Epitome protasis study (2026-08-18, this session; measurements of this
marketplace, v2-protocol and wildcat-app-v2). GitHub Linguist documentation
on `linguist-generated` and `linguist-vendored`. aider repo-map
(aider.chat/2023/10/22/repomap.html). Repomix compress
(repomix.com/guide/code-compress). LongCodeZip (arXiv 2510.00446). Minification
task-cost evidence (arXiv 2606.01326). In-repo: `plugins/lemma/chunkers/`,
`plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py` (the `VENDORED`
set), `plugins/pandects/tests/test_search_record.py` (stripper traps),
`tests/test_evolution_contract.py` (the ledger contract Horos must meet).
