# Study

Produce one markdown study that someone competent could build from without
access to this conversation. Write it to `.hexaemeron/study.md` (the state
directory is self-gitignored; a repo copy gets committed later, in step 1 of
the runbook, after the prose pass).

## Required content

1. **Problem statement.** What is being built, for whom, and what "working
   prototype" means for this topic -- name the demo path or the check that
   proves it works.
2. **Prior art.** What already exists in the target repo, the organisation's
   other repos, and outside them. Name files, packages, and standards
   by identifier, not by vibe.
3. **Constraints and non-goals.** The starting point (empty, or the branch,
   repo, or commit the user named), toolchain and version pins, anything the
   user ruled out, and anything deliberately deferred past the prototype.
4. **Design options.** Two to four candidate constructions with the trade
   each makes. Pick one and say why. The pick should be the option cheapest
   to comprehend that still meets the problem statement -- the same rule the
   implementation phase runs on.
5. **Risk register seed.** What the audit loop should look hardest at:
   trust boundaries, external calls, arithmetic, upgrade paths, key custody,
   whatever the domain makes dangerous.
6. **Glossary seeds.** Terms the runbook and implementation will reuse, each with a
   one-line definition.
7. **Sources.** Repos, docs, and standards consulted, with enough of a
   pointer to find them again.

## Discipline

- Depth over breadth: a section that says "TBD" is a section to cut or fill.
- Where the user's spec is ambiguous, record the reading chosen and why,
  rather than silently picking one.
- Run the `hexaemeron:imprimatur` lint on the finished study and fix hard
  hits before receipting. Pass the skill list you actually applied to
  `done study --skills`.

## Receipt

```text
hexctl done study --artifact .hexaemeron/study.md --skills hexaemeron:imprimatur
```
