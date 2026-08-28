---
name: brevitas
description: Enforce evidence-preserving structural output budgets on engineering prose. Apply automatically to chat answers and written drafts containing audit findings, security or diff review, gas analysis, `invariant` discussion, protocol analysis, or specification commentary, and on explicit $brevitas invocation. Govern volume, structure, and connective prose only. Do not apply to code comments, commit messages, or completeness-oriented specification documents.
metadata:
  version: "0.2.0"
---

<p align="center">
  <img src="../../assets/characters/brevitas.png" width="1200">
</p>

# Brevitas

## Frontier

Brevitas owns the engineering-prose structure frontier, not Hexaemeron's delivery
or Solidity frontier. [EVOLUTION.md](EVOLUTION.md) records its version, held target,
next job and maturity state. Do not run or recommend another frontier pass once
that ledger is mature.

<!-- marketplace-context:start -->
## Where this sits

Brevitas enforces mechanical volume and structure limits on engineering prose while protecting every item of evidence that can change the decision.

**Current frontier.** The linter has not been forward-tested across a held cross-model corpus of engineering reviews, and preservation of counterexamples and reproduction steps remains agent-checked.
<!-- marketplace-context:end -->

Apply this after Imprimatur has checked the vocabulary and Vulgate has settled
the register. Sapheneia may separately shape the surrounding interaction or a
bounded durable record. Brevitas changes volume, structure, and connective
prose only; it does not alter word choice, voice, AuDHD presentation, or the
facts another skill established.

If Synkrisis renders a comparison report, this skill may constrain its
engineering-prose structure without validating the finding. Synkrisis emits no
report yet: its renderer is a held runbook step that refuses.

## Precedence

Preserve evidence before satisfying any budget. Never delete or weaken:

- addresses or transaction hashes;
- `file:line` references or numeric claims;
- concrete counterexamples or reproduction steps; or
- an explicit statement that a fact, property, or conclusion could not be established.

If evidence does not fit, the budget yields. Cut prose, never evidence. Mark an
irreducible over-budget finding with the evidence exception below.

## Compose

1. Answer immediately. Do not restate the request or introduce the answer.
2. Apply these physical-line budgets:
   - Direct answer: at most 6 nonblank lines before the first list or code fence.
   - Finding: at most 5 prose lines: claim, location, mechanism, impact, fix.
   - Code: at most 40 content lines per fence.
3. Give each finding this checkable shape:

   ```text
   [High] Claim.
   Location: `src/Contract.sol:42`
   Mechanism: Concrete causal path.
   Impact: Concrete consequence.
   Fix: Smallest correction.
   ```

   Use only the severity word; do not add a severity-justification paragraph.
4. Put findings adjacent. Add no transition, preamble, or summary between them.
5. Use a table only with at least 3 data rows and 3 real-data columns.
6. Use headings only when the draft has at least 3 sections. A document title does
   not count as a section.
7. Use at most one qualifier per claim.

For an irreducible finding, place `<!-- brevitas: evidence-exception reason="counterexample requires ordered steps" -->` immediately before it.

Use the exception only when compression would remove protected evidence. Keep any
extra lines as evidence, counterexample, reproduction, or establishment-limit
statements; do not use the exception to retain connective prose.

## Delete

Delete request restatements, list preambles, post-list summaries, process narration,
bold-label-colon items, trailing offers, unrequested next-step menus and stacked
hedges. Delete confidence theatre, including:

```text
importantly; notably; it's worth noting
```

Do not reprint visible code. Quote only the lines carrying the defect.

## Lint

Run the checker before sending substantive chat prose or saving a report. Pipe chat
drafts through stdin; pass written work as a file:

```bash
python3 scripts/brevitas.py - < draft.md
python3 scripts/brevitas.py report.md
python3 scripts/brevitas.py report.md --source uncompressed.md
make -C /path/to/brevitas lint FILE=/path/to/report.md
```

Use `--mode answer` for direct answers and `--mode report` for reports. `auto`
infers a report from findings or at least 3 sections. For existing material, always
pass `--source`; the checker fails if an address, transaction hash, `file:line`
reference or numeric token disappears. Fix every diagnostic and rerun for exit 0.

Host-required status commentary is outside the draft lint boundary. Do not suppress
status messages required by the execution environment.

## Evals

Run `make test`. `evals/cases/` contains preserved audit, x-ray and security-review
excerpts with source paths, ranges and pinned fixture digests. `scripts/run_evals.py`
checks fixture integrity, target structure, evidence-token survival, positive-case
compression and exact retention for the evidence-exception case.

## Exclusions

Do not apply this skill to code comments, commit messages or specifications where
completeness is the point. Do not change lexicon, tone, register or accessibility.

## Promise Machine contract

### brevitas-structure-check

- Promise: A successful answer- or report-mode lint establishes that the named draft satisfies Brevitas's mechanical line, finding, code-fence, table, heading and qualifier budgets.
- Evidence: The exact draft bytes, selected lint mode, emitted diagnostics and exit status from `scripts/brevitas.py`.
- Evidence classes: checked
- Boundary: The lint does not establish factual accuracy, evidence completeness, severity correctness, voice, accessibility or fitness for a completeness-oriented specification.
- Authorises: Presentation of the checked draft as structurally conformant to the selected Brevitas mode.
- Consequence: 0
- Refuses: Calling prose Brevitas-clean when the checker did not run, reported a diagnostic, inferred the wrong mode or received an excluded document class.
- Recovery: Select the right mode, preserve protected evidence, remove the named structural defect and rerun the checker.
- Exceptions: none

### brevitas-evidence-preservation

- Promise: A successful lint with `--source` establishes that protected addresses, transaction hashes, file-line references and numeric tokens from the named source survive in the compressed draft.
- Evidence: The exact source and draft bytes, source-token comparison, any explicit evidence exception and a zero-exit lint result.
- Evidence classes: checked, recomputed
- Boundary: Token survival does not establish semantic equivalence, complete reasoning, correct conclusions or preservation of evidence classes that the token checker cannot represent.
- Authorises: Saving or handing off the compressed draft as a derived artefact whose mechanically protected tokens remain present.
- Consequence: 1
- Refuses: Deleting or weakening protected evidence to meet a volume budget, or claiming preservation without supplying the source comparison.
- Recovery: Restore the missing evidence, use a scoped evidence exception when ordered proof requires it and rerun with the original source.
- Exceptions: none
