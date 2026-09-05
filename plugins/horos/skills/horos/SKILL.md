---
name: horos
description: Emit and verify an evidence-backed reading boundary over a repository. Classify token sinks (generated files, vendored trees, lockfiles, minified bundles, single-line blobs), write the deterministic boundary agents consult before reading, and print Python skeleton maps for oriented reading. Use when a user names Horos or asks to cut the reading cost of a repository without rewriting its code. Never apply a boundary during security review.
metadata:
  version: "12.3.3"
---

<p align="center">
  <img src="../../assets/characters/horos.png" width="1200">
</p>

# Horos

From *horos*, the boundary stone. Horos decides what an agent does not read,
and proves the decision instead of asserting it.

## Where this sits

Horos owns the reading boundary: which files in a repository an agent leaves
unread by default, each exclusion carrying the evidence that earned it. Later
siblings may use that boundary for oriented reading, but it is disabled during
security review and does not narrow Warden, the Pashov suite, Phylax, or
Elenchus while they investigate risk or a failure. Its version, held frontier,
next job, and maturity state live in [EVOLUTION.md](EVOLUTION.md).

A Synkrisis finding may suggest a Horos review when validated observations
repeat. The finding does not write or widen a reading boundary; Horos still
checks the repository evidence before changing one.

**Current frontier.** The v9.2.3 reopening's third and last job is done: map reads Markdown through a per-language extractor, held against markdown-it-py over all 900 tracked Markdown files of this repository with 9,527 of 9,527 headings and 1,130 of 1,130 fenced code blocks matched, zero misses, zero extras and zero crashes. Every filetype above 1% of this tree's readable bytes is now mapped or is a data format with no declarations to outline, so the frontier closes mature.

## The verbs

All three live in one standard-library script,
[scripts/horos.py](./scripts/horos.py):

```bash
python3 scripts/horos.py scan <root> --write
```

walks the tree and commits `.horos/boundary.json`: every file it can
evidence as a token sink, with its category, size and the exact evidence
line that earned the entry. The write is atomic; a killed run leaves the old
boundary or the new one, never half. `--json` prints the same canonical
bytes instead of writing them.

```bash
python3 scripts/horos.py check <path>
```

re-derives the classification and compares it with the committed boundary.
Exit 0 means the boundary matches the tree. Drift names every path, in both
directions: a new sink the boundary lacks, and a committed entry the tree no
longer evidences.

`<path>` may be the repository root or any directory inside it. For a
descendant, Horos walks upward to the nearest `.horos/boundary.json`, stops at
the worktree root git reports, classifies only that subtree, and compares it
with the matching slice of the committed boundary:

```text
boundary root: /path/to/repo
scope: plugins/alexandria
hard boundary: matches
candidates: 12 findings, advisory
outside-scope drift: not evaluated
counters: classified 210, listed outside scope 3, attribute files above scope 0
```

Exit 1 means hard drift inside the scope, and every drifted path is named.
Exit 2 means no usable ancestor boundary, or a path that resolves out of the
worktree. Candidate drift never changes a scoped check's exit code. At the
root, candidate classification or content drift at the same file count remains
advisory, but every raw canonical boundary count binds; adding or removing a
tracked candidate therefore drifts `files_walked`. A scoped pass is not a
whole-repository pass, which is why the output says so in those words: the
release-time answer is still `check` at the root. The walk begins at the
boundary root even for a scope, because a `.gitattributes` above the scope
decides how the files inside it classify; those reads are counted rather than
hidden, and nothing outside the scope is stat'd, read or classified.

```bash
python3 scripts/horos.py scan <root> --census [--write]
```

prints one row per filetype: files, bytes, share of the tree, and the bytes
already inside the boundary, from exactly the walk the boundary uses. With
`--write` it commits `.horos/census.json` beside the boundary. The census
is how walk-worthiness and the next extractor get decided from a record
rather than a guess: a tree whose readable weight sits in mapped languages
needs nothing new, and one whose weight sits in an unmapped filetype names
the candidate.

```bash
python3 scripts/horos.py map <file>
```

prints the file's skeleton so it can be oriented in without being read
whole. Extractors live one folder per language under
[scripts/languages/](./scripts/languages/) and a suffix registry dispatches
between them; an unregistered suffix is refused naming the supported list.
Python (`.py`) parses through the standard library's own ast. TypeScript
(`.ts`, `.tsx`), Go (`.go`), C++ (`.cpp`, `.h`, `.hpp`, `.cc`, `.cxx`),
Solidity (`.sol`) and Markdown (`.md`) are lexed, never parsed:
declarations are quoted as verbatim source slices (grouped Go declarations
one line per member, C++ template prefixes and Solidity inheritance lists
and attribute chains riding along; a Markdown declaration is a heading or a
fenced code block, read by CommonMark's block rules and never its inline
ones), and every region the recognisers do not understand is confessed by
count and line range instead of guessed at. No path imports or executes
what it reads.

The TypeScript extractor exists by revision of a recorded refusal. Parsing
TypeScript or taking a parser dependency was refused on 2026-08-18 and
stays refused; the maintainer directed the design that needs neither, and
it was held against the real compiler before shipping: across all 866
hand-written TypeScript files of a live repository, 2,237 of 2,239
compiler-visible declarations matched, with zero misses outside the
outliner's own confessions, zero extras and zero crashes. The recorded run
lives at
[../../docs/evidence/wildcat-app-v2-outline.md](../../docs/evidence/wildcat-app-v2-outline.md).
The Go extractor was held against tree-sitter's Go grammar over all 1,421
files of go-ethereum: 21,648 of 21,648 declarations matched, zero misses,
zero extras, zero crashes, recorded at
[../../docs/evidence/go-ethereum-outline.md](../../docs/evidence/go-ethereum-outline.md).
The C++ extractor was held against tree-sitter's C++ grammar over all 842
files of the Solidity compiler: 7,013 of 7,013 declarations matched at
declared altitudes with zero crashes anywhere, recorded at
[../../docs/evidence/solidity-outline.md](../../docs/evidence/solidity-outline.md).
The Solidity extractor was held against tree-sitter's Solidity grammar over
all 151 files of v2-protocol: 2,329 of 2,329 declarations matched with zero
confessions and every file oracle-parsed, recorded at
[../../docs/evidence/v2-protocol-outline.md](../../docs/evidence/v2-protocol-outline.md).
The Markdown extractor was held against markdown-it-py in its CommonMark
preset over all 900 tracked `.md` files of this repository: 9,527 of 9,527
headings and 1,130 of 1,130 fenced code blocks matched at declared
altitudes, zero misses, zero extras and zero crashes, recorded at
[../../docs/evidence/skills-markdown-outline.md](../../docs/evidence/skills-markdown-outline.md).
Front matter is named by line range and outlined inside on neither side, and
a fence that never closes is confessed rather than invented.

## The discipline

1. Entering a repository, look for `.horos/boundary.json`. If it exists, run
   `check` before trusting it; a stale or forged boundary fails by name. If
   it does not exist and the repository is large, offer a scan. Entering one
   directory of a large repository to work in it, run `check` on that
   directory instead: the answer covers the files about to be read, costs a
   fraction of the whole tree, and says plainly that it evaluated nothing
   outside the scope. Before a release, check the root.
2. Treat every path inside a checked boundary as unread-by-default. The entry
   itself carries what a reader needs: category, size, evidence.
3. Before opening a file over a few hundred lines in a language the
   registry supports, run `map` and read the skeleton first. Open the file
   whole only when the skeleton was not enough, and mind the confession
   line: a large unparsed region means the skeleton understates the file.
4. Classification is fail-open, so the boundary understates the sinks. What
   it lists is evidenced; what it omits is merely unproven. Evidence comes
   in two grades: only hard evidence (an exact lockfile name, a Git
   attribute, a binary signature, a generated marker, sourcemap structure,
   a corroborated directory, the digest of a file's own bytes) reaches
   `boundary.json` and binds; candidates (a name, a convention or geometry
   alone) live in
   `.horos/candidates.json` as an advisory report a maintainer can promote
   to a repository-specific rule. Scans of git repositories cover tracked
   files by default, so local build products never contaminate a committed
   boundary; `--include-untracked` widens the universe deliberately. A
   directory entry, binding or advisory, has to cover at least one file in
   that universe: one holding nothing tracked excludes no bytes a reader would
   have reached, and emitting it would make the same check answer differently
   on two machines. A checked-out worktree stays outside either report on the
   same rule, even where nothing ignores the directory holding it: its files
   belong to another checkout's index, never to this one's.
   Where git cannot answer at all, the fail-open position stands and the entry
   is kept.
   The content-addressed rule is the one rule whose evidence a repository
   cannot write: it reads a whole file, chunked, and only for a path already
   shaped as `blobs/<algorithm>/<digest>` or
   `objects/<algorithm>/<shard>/<digest>` under sha1, sha256, sha384 or
   sha512. It runs before the other rules because a matching digest is
   evidence no other reading can overturn, and it refuses git's own object
   store, uppercase or wrong-width names and deeper shards; the comments
   above `CONTENT_ADDRESSED_ALGORITHMS` in
   [scripts/horos.py](./scripts/horos.py) carry the reasons.
5. When writing a boundary into a repository other agents will work in, add
   the adoption stanza that `scan --write` prints to that repository's
   AGENTS.md or CLAUDE.md. Agent harnesses load those files at session
   start, so the discipline travels with the repository; without the
   stanza, the boundary binds only agents carrying this skill.

## The one rule that outranks the rest

No reading boundary applies during security review. A committed boundary in a
hostile repository could list source files as sinks precisely so a reviewing
agent never opens them. During any audit, review or incident work, read as if
no boundary exists. `check` re-derives everything it asserts for the same
reason.

## The shipped example

[../../examples/fixture/](../../examples/fixture/) holds one file per rule
class and its committed boundary; [../../examples/README.md](../../examples/README.md)
shows the demo commands and the mutation that makes `check` fail.

## Promise Machine contract

### horos-boundary-scan

- Promise: A successful `scan --write` records every tracked path that the current hard rules classify as a token sink, with category, byte count and the evidence that earned the entry.
- Evidence: The walked tracked-file universe, hard classification rules, file evidence, canonical `.horos/boundary.json` bytes and atomic write result.
- Evidence classes: checked, recomputed, recorded
- Boundary: Classification is fail-open and may omit sinks; candidates do not bind, untracked files are excluded unless requested and no boundary applies during security review.
- Authorises: Committing the generated reading boundary and adoption stanza for non-security repository reading.
- Consequence: 2
- Refuses: Listing an unevidenced path as a hard exclusion, treating an empty directory as covered or using the boundary to hide audit, review or incident scope.
- Recovery: Inspect the classification evidence, amend the repository-specific rule or source marker, rerun the scan and review the resulting diff.
- Exceptions: none

### horos-boundary-check

- Promise: A successful `check` establishes that the committed hard boundary equals the current re-derived classification for the stated root or subtree.
- Evidence: The nearest confined boundary, current tracked-file walk, applicable attributes, recomputed entries, scope counters and zero-drift result.
- Evidence classes: checked, recomputed
- Boundary: A scoped pass says nothing about outside-scope drift; root candidate classification or content drift is advisory only while canonical boundary metadata remains equal; and a clean boundary does not prove omitted files are cheap to read.
- Authorises: Leaving listed hard-boundary paths unread by default within the checked non-security scope.
- Consequence: 0
- Refuses: Trusting a stale, forged, missing or out-of-scope boundary, or applying any boundary during security review.
- Recovery: Read the drifted paths as ordinary inputs, rerun `scan --write` for an authorised update and check the intended root again.
- Exceptions: none

### horos-census

- Promise: A successful `scan --census` counts the files and bytes by suffix from the same walk as the boundary and records how many bytes already sit inside it.
- Evidence: The walked universe, suffix roll-up, boundary membership counts and canonical census output or `.horos/census.json` bytes.
- Evidence classes: measured, recomputed
- Boundary: The census measures file bytes under the selected walk; it does not measure model tokens, reading time, semantic importance or untracked content unless included.
- Authorises: Choosing the next extractor or classification investigation from the recorded weight distribution, and writing the census when requested.
- Consequence: 1
- Refuses: Presenting suffix bytes as token counts or a scoped census as a whole-repository measurement.
- Recovery: Select the intended root and trackedness mode, rerun the census and keep its scope beside any conclusion.
- Exceptions: none

### horos-skeleton-map

- Promise: A successful `map` emits the supported source file's recognised declaration skeleton and explicitly counts every region the extractor did not understand.
- Evidence: The exact source bytes, suffix-selected extractor, verbatim declaration slices, line locations and confession ranges.
- Evidence classes: checked, recomputed
- Boundary: A skeleton is an orientation aid, not the full file, an execution trace, a parser proof or evidence about meaning inside confessed regions.
- Authorises: Using the map to choose bounded follow-up reads of the same source file.
- Consequence: 0
- Refuses: Mapping an unsupported suffix, importing or executing the source, or treating omitted and confessed regions as absent behaviour.
- Recovery: Read the source directly or add and validate an extractor before relying on a map for that language.
- Exceptions: none
