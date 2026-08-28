---
name: imprimatur
description: >-
  Check prose that ships for banned AI writing tells, technical terms used
  without evidence, and repeated structural formulae that survive a wordlist.
  Use while drafting, editing, or reviewing public prose, or when the user
  names a term to ban. This is the diagnostic gate; Vulgate performs a
  content-preserving rewrite.
metadata:
  version: "2.3.0"
---

<p align="center">
  <img src="../../assets/characters/imprimatur.png" width="1200">
</p>

# Imprimatur

## Frontier

Imprimatur owns the prose-lint contract, not Hexaemeron's delivery or Solidity
frontier. Its version, held calibration target, next job, and maturity state
live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run another frontier
pass after that ledger becomes mature.

## Where this sits

Imprimatur diagnoses the vocabulary and formulae that make shipped prose read
as machine-produced. Vulgate then rewrites the surface while holding content
fixed, and Imprimatur runs again. Brevitas may impose engineering-prose
structure after the wording passes; Sapheneia may shape the surrounding
interaction or one bounded durable record. Fiat and Scribe own the phase order
and receipt, not this lint.

Synkrisis renders a comparison report from fixed templates, and Imprimatur
checks only its wording and supported terminology. This lint cannot
manufacture or validate a finding.

**Current state.** Imprimatur has a provenance-bound 64-sample evaluation, but labelled-prose-v1 failed the pre-registered annotation-agreement and structural-holdout coverage gates; its holdout is spent and its provisional scores cannot support tuning.

A banned lexicon with three enforcement tiers and a rule about why wordlists
fail on their own.

Ban a token and the model reaches for its neighbour. Ban "load-bearing" and the next draft says "does the heavy lifting", then "the crux", then "the operative word". The list here is organised by family for that reason, and the instruction is to reject the move, not the string.

## The three passes

| Pass | Content | Enforcement | Where |
| --- | --- | --- | --- |
| hard | Terms with no defensible use | Any hit is a defect | Script, blocking exit code |
| gated | Terms of art, real in context | Licensed by evidence in the same sentence | Skill, judgement |
| structural | Formulae, not vocabulary | Flagged for rewrite | Skill, judgement |

Only the hard pass suits a blocking hook (`scripts/hook_gate.py` ships for
anyone who wants to wire one; this plugin does not). Gated terms need the sentence read for a referent, and structural patterns need a decision about whether the formula earns its place. A hook that fires on those produces false positives, and a hook that cries wolf gets switched off within a week.

## Running it

```bash
python3 scripts/imprimatur.py draft.md              # all three passes
python3 scripts/imprimatur.py draft.md -v           # with excerpts and rationale
python3 scripts/imprimatur.py draft.md --format json
python3 scripts/imprimatur.py draft.md --hard-only  # hook fast path
python3 scripts/imprimatur.py *.md --fail-under 80  # CI gate
cat draft.md | python3 scripts/imprimatur.py -
```

Exit 1 when a threshold is breached, 0 otherwise. Read the defect list rather than the score: the score compresses severity and length into one number and loses the reason.

Paths ending in `.sol`, `.py`, `.ts`, or `.tsx` use source-prose extraction
under the default masking mode. Each such path must be a regular file no larger
than 1,048,576 bytes and valid UTF-8. Solidity comments and NatSpec, Python
comments and true module, class, function, or async-function docstrings, and
TypeScript or TSX comments, JSDoc, and an initial hashbang are retained. Code,
ordinary strings, templates, and regular-expression literals are blanked. The
mask keeps the source length and language-owned line terminators unchanged,
including CR and LF in Python and CR, LF, LS, and PS in TypeScript, so findings
carry their original source line and column. Solidity LF, VT, FF, and CR line
breaks are retained; NEL, LS, or PS outside a comment or string is a named
refusal because Solidity rejects that source. The TypeScript and TSX comment
scanner accepts at most 64 recursively entered code, template, or JSX regions.
A 65th such region is a named extraction refusal rather than a clean result or
an interpreter traceback; iteratively scanned type-argument depth is outside
that recursion budget.

Named extraction failures in supported source are not clean results. These
include an unterminated Solidity block comment, invalid Python syntax or parser
resource failure, an unterminated TypeScript string, template, JSX element, or
regular expression in an expression goal, and source beyond the file-size or
nesting boundary. A slash after contextual `await` or `yield` is refused when
its regular-expression and identifier readings would move a comment boundary;
a complete regular expression followed by a comment remains supported. An
extraction failure names the path and source position and exits 2 before any
partial multi-file report is printed.
Markdown, standard input, and other suffixes keep the existing Markdown
masking rules.
`--include-code` bypasses source extraction and scans the whole input, as it
already did for Markdown code.

## Workflow

1. Run the lint before handing over any prose. Hard hits are defects and get rewritten, no exceptions and no synonyms from the same family.
2. For each gated hit, decide whether the term has a referent. Fixing it usually means naming the thing the term is about, not deleting the term. "Orthogonal to the framing" fails; "orthogonal to `CrossMarketCapLib`" passes; "orthogonal in the sense that neither imports the other" passes, because the sentence supplies its own criterion.
3. For each structural hit, rewrite the formula. Negation-correction is the highest-yield one to kill: it manufactures a position nobody held so the sentence has something to defeat.
4. Read the cadence signals as prompts to look, not as defects. Repeated openers and flat sentence length are common in machine prose and also in good technical writing under a constraint.
5. Check what the rewrite cost. Removing a hard-banned term must not remove a qualifier that carried scope, risk, or uncertainty. When the two collide, keep the qualifier and rephrase around the ban.

## What the gate accepts as evidence

A gated term passes when the sentence holding it contains a numeral, a backticked identifier, a file path, a hex address, a CamelCase identifier, or a system named in the allowlist. It also passes when the term is immediately followed by its own definition ("in the sense that", "in that", "namely", "defined as"). Anaphora is honoured: a sentence opening with a pronoun inherits the previous sentence's evidence.

Intensifiers are stricter. "Materially", "significantly", "fundamentally" and the rest need a numeral, because each promises a magnitude. If no number can follow, the word was decoration.

## Protected against over-correction

The lexicon exists to remove filler, not precision. Three things are protected and must survive any rewrite:

Qualifiers that carry scope, causality, risk, or legal meaning. "Broadly" in a market summary is filler; "broadly" in a covenant is a defined scope and stays.

Statements of what was and was not verified. The `invented_confidence` family is marked critical because it is a truthfulness defect rather than a style one. The fix is never to delete the uncertainty; it is to state plainly what ran and what did not.

Named entities, numbers, dates, citations, and quotations. Quoting slop in order to discuss it is legitimate. Wrap it:

```
<!-- imprimatur:off -->
"At the end of the day, we leveraged a robust solution."
<!-- imprimatur:on -->
```

`<!-- imprimatur:ignore-file -->` anywhere in a file exempts it from the hook script; `IMPRIMATUR_DISABLE=1` disables that hook for a session. The lint script masks quoted spans on its own.

## Editing the lexicon

Three JSON files under `lexicon/`. Add to the family, not as a loose token, and write the note explaining what the family is doing. A term with no family is a term the model routes around.

- `hard.json` families: `structural_metaphor`, `claude_tic`, `hedge_pivot`, `closer`, `brochure`, `consultant`, `invented_confidence`, `register_cosplay`, `empty_hedge`
- `gated.json` families: `mathematical`, `engineering`, `intensifier`, `spatial`, plus the allowlist and the abstract-noun list that fails the gate
- `structural.json`: named regex patterns with a severity each, plus cadence thresholds

After editing, run `python3 tests/run_tests.py`. The suite holds a false-positive corpus of legitimate technical prose; a new term that fires on it needs gating, not banning.

## Provenance

Parts of the lexicon and doctrine are absorbed from slopkit (ehmo, MIT),
reorganised into the three tiers above and checked against itself.
Attribution, licence, and the list of deviations are in `NOTICE.md`.

## References

- `references/lexicon-rationale.md`: why each family is banned, and the substitution-drift argument
- `references/agent-replies.md`: rules for the agent's own turns while working
- `references/rewriting.md`: what to do once a defect is found
- `NOTICE.md`: attribution and licence for the absorbed material

## Hard rules

- Never swap a banned term for another member of its family. Rewrite the sentence.
- Never delete a qualifier that changes what the reader should do next in order to clear a hit.
- Never claim a draft is undetectable, human-passing, or clean because the score is high. The score counts known markers and nothing else.
- Never let the lint's own vocabulary leak into prose. Words like "defect", "gated", and "pass" belong in reports, not in the writing being fixed.
- Do not report the lint as run when it was not.

## Promise Machine contract

### imprimatur-prose-gate

- Promise: A successful Imprimatur run establishes that the exact prose crossed the configured hard, gated and structural pattern thresholds and that every reported defect was cleared or evidenced under the checker rules.
- Evidence: The exact input bytes and path suffix, lexicon and allowlist, selected mode and threshold, successful source extraction when default masking selects a `.sol`, `.py`, `.ts`, or `.tsx` path, defect and signal output, labelled-corpus provenance and zero exit status.
- Evidence classes: checked, recorded
- Boundary: Source mode covers only comments, an initial TypeScript hashbang and the documented Python docstring owners in `.sol`, `.py`, `.ts`, and `.tsx`; a default source path must be a valid UTF-8 regular file of at most 1,048,576 bytes. The TypeScript and TSX scanner refuses a 65th recursively entered code, template, or JSX region while scanning angle-group depth iteratively, and refuses contextual slash input whose comment boundary needs surrounding parser grammar. It does not establish source validity beyond successful extraction, inspect executable semantics, or extend to another suffix. The gate does not establish human authorship, factual accuracy, sound reasoning, an intended voice or absence of every machine-writing pattern.
- Authorises: Presentation or hand-off of the checked prose as Imprimatur-clean at the named checker version and threshold.
- Consequence: 0
- Refuses: Calling prose clean when the gate did not run or failed, returning a clean result after supported-source extraction fails, hiding a hard hit with a synonym, treating a cadence signal as a defect or deleting a scope-bearing qualifier to clear a word.
- Recovery: Read the named defect, rewrite the sentence without weakening evidence or uncertainty and rerun the exact gate.
- Exceptions: none
