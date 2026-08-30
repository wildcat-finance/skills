![Brevitas](./assets/characters/brevitas.png)

# Brevitas

<!-- marketplace-context:start -->
## In one line

Brevitas enforces mechanical volume and structure limits on engineering prose while protecting every item of evidence that can change the decision.

**Current frontier.** The linter has not been forward-tested across a held cross-model corpus of engineering reviews, and preservation of counterexamples and reproduction steps remains agent-checked.

**Next Fiat job.** Use /hexaemeron:fiat to Forward-test Brevitas across held x-ray, Solidity-auditor, gas, `invariant` and diff-review outputs, then add every confirmed structural bypass to the corpus without weakening evidence precedence. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Place in the collective

Imprimatur catches banned wording and unsupported technical terms; Vulgate
rewrites the same content into a plain register. Brevitas runs after those
passes when the document is an engineering review, audit finding, gas analysis,
protocol-property discussion, protocol analysis, or specification comment. Sapheneia
may shape the surrounding interaction or one bounded durable record. None of
the four may delete facts, uncertainty, counterexamples, or reproduction steps
to make prose tidier.

Synkrisis renders a comparison report from fixed templates, and Brevitas may
constrain that report's structure but cannot validate its findings. Rendering
refuses a finding that carries causal language, so neither skill can introduce
a claim the findings do not hold.

## How it works

Evidence outranks every budget. Transaction hashes, addresses, 4-byte selectors,
bare SHA-256-shaped digests, Git object ids, `file:line` references, numbers,
counterexamples, reproduction steps and statements of what could not be
established survive compression. Abbreviated Git ids require Markdown code
quoting, an explicit Git label, or an `owner/repository@oid` form. The linter
accepts a draft from a file or stdin, rejects mechanical breaches with
line-numbered diagnostics, and can compare a compressed draft with its source. A
marked evidence exception keeps an irreducible finding intact when the evidence
itself needs more than five lines.

## What it ships

- the standard-library [`brevitas.py`](./skills/brevitas/scripts/brevitas.py) linter;
- Make targets for written reports and source-preservation checks;
- three audit-derived before/after cases with pinned fixture digests; and
- tests for finding, heading, table, fence and banned-structure failures.

## Day to day

**Developers.** A diff review has two defects buried under setup and a repeated
summary. Brevitas keeps each defect to claim, location, mechanism, impact and fix,
then rejects the draft if its structure drifts.

**Security and audit.** A finding carries addresses, exact locations, numeric
traces and reproduction steps. Brevitas cuts connective prose first, checks the
machine-readable evidence against the source, and permits a marked exception when
the protected evidence needs more than five lines.

## Contract

Brevitas is the last structural pass for audit findings, security reviews, gas
analysis, `invariant` discussion, diff review and protocol commentary. It does
not choose words or voice. It controls line count, finding shape, headings,
tables, code fences and the prose between points.

The evidence rule comes first. Transaction hashes, addresses, 4-byte selectors,
bare SHA-256-shaped digests, Git object ids, `file:line` references, numbers,
counterexamples, reproduction steps and statements of what could not be
established survive every rewrite. `--source` checks literal survival of the
machine-readable subset; it does not establish that a digest, selector or Git
object exists or is valid. An explicit evidence exception keeps longer material
when the five-line finding form cannot hold it.

- one canonical [`SKILL.md`](skills/brevitas/SKILL.md) shared by Codex, Claude Code and portable agents;
- the standard-library [`brevitas.py`](skills/brevitas/scripts/brevitas.py) linter for files and stdin;
- a Make target for written reports and source-preservation checks; and
- three audit-derived corpus cases, including one that must retain the original finding rather than compress it.

## Examples

A diff review can hide two real defects under setup, transitions and a repeated
summary. Brevitas keeps each defect to claim, location, mechanism, impact and
fix, then rejects line-budget or structure drift.

For security and audit work, Brevitas cuts connective prose before addresses,
exact locations, numeric traces or reproduction steps. It checks machine-readable
evidence against the source and permits a marked exception when evidence needs
more than five lines.
