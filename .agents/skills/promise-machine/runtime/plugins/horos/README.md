# Horos

<!-- marketplace-context:start -->
## In one line

Horos records which repository paths an agent may usually leave unread, with the evidence for every exclusion and deterministic maps for what remains.

**Current frontier.** The v9.2.3 reopening's first job is done: a generated-file marker binds only on a comment-led line, horos.py and test_classify.py read as ordinary source again, and a repository-level test holds this tree to zero self-exclusions. Two held jobs remain: the content-addressed object rule, whose drafted rule already classifies 7,844,971 bytes of this repository's object stores in the committed boundary while the rule still owes its own frontier run, and the Markdown outline extractor, with maturity expected after both.

**Next Fiat job.** Use /hexaemeron:fiat to ship the content-addressed object rule whose evidence is the digest a file's own bytes produce. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Place in the collective

Horos runs before broad repository reading and reduces the files every later
specialist has to inspect. Its boundary is advisory outside the exact evidence
it records and is disabled for security review, so Warden, the Pashov suite,
Phylax, and Elenchus do not inherit an exclusion while investigating risk or a
failure. Horos changes reading scope, not the meaning or authority of another
skill.

## Why it exists

An agent working in a repository spends most of its reading budget on files
that return nothing: build output committed to the tree, vendored
dependencies, lockfiles, minified bundles, data blobs on a single line.
Measured against two Wildcat repositories, those files were 66% and 87% of
readable bytes. Rewriting code to save tokens was studied first and rejected;
the licensed saving was about 3% and published evidence prices aggressive
rewriting at up to 12 points of task completion. Not reading the sinks at all
is the mechanism that wins, and Horos makes it checkable. The full argument
is committed at [docs/study.md](./docs/study.md).

## What it ships

- a standard-library scanner that classifies token sinks and quotes the
  evidence line that earned each entry;
- a deterministic committed boundary at `.horos/boundary.json` holding
  hard evidence only (schema 2, git-tracked universe by default), verified
  against the tree by `check`, which fails on hard drift and reports
  candidate drift; advisory findings live beside it in
  `.horos/candidates.json`;
- one `check` that answers either question: at the repository root, whether
  the whole boundary is current; at any directory inside it, whether the
  boundary covering that subtree is current, resolved from the nearest
  ancestor boundary and reported as having evaluated nothing outside the
  scope. On this repository the scoped answer costs 24 ms against 60 ms;
  [examples/scoped-entry/](./examples/scoped-entry/README.md) runs both;
- a filetype census at `.horos/census.json` from the same walk, so
  walk-worthiness and the next extractor are decided from a recorded
  breakdown;
- skeleton maps for Python, TypeScript, Go, C++ and Solidity through a
  per-language extractor folder, so a large file can be oriented in without
  being read; the outliners quote declarations verbatim, confess what they
  did not understand, and are held against independent parsers over live
  repositories (2,237 of 2,239 TypeScript declarations over 866 files;
  21,648 of 21,648 Go declarations over 1,421 files; 7,013 of 7,013 C++
  declarations at declared altitudes over 842 files; 2,329 of 2,329
  Solidity declarations over the 151 files of v2-protocol itself);
- a shipped example at [examples/](./examples/) whose committed boundary a
  fresh scan reproduces byte for byte; and
- one binding rule: no boundary applies during security review.

The build trail is the runbook at [docs/runbook.md](./docs/runbook.md), one
reviewed step per verb.

## Day to day

**Developers.** An agent is pointed at a frontend repository where two thirds
of the readable bytes are a checked-in Storybook build, a lockfile and a data
file on one line. The committed boundary sends the reading budget to `src/`
instead, `check` catches the day the boundary goes stale, and a skeleton map
orients the agent in a thousand-line module without opening it whole.

## Adopting a boundary in any repository

The boundary binds agents that carry this skill; everyone else's agents
learn it from the adopting repository's own instructions file. `scan
--write` prints a short stanza for that repository's AGENTS.md or CLAUDE.md:
consult `.horos/boundary.json` before reading broadly, leave listed paths
unread unless the task demands one, and never apply the boundary during
security review. Harnesses load those files at session start, so one paste
makes the boundary effective for any instruction-following agent, with no
install.

## Where it is honest about limits

Classification is fail-open. A file Horos cannot evidence stays readable, so
Horos misses sinks a person would catch, and its report says what it skipped.
The scanner reads at most a fixed prefix of any file, so a scan never costs
more than a fraction of what it saves.
