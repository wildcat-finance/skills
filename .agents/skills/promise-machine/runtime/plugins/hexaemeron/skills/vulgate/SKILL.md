---
name: vulgate
description: Rewrite AI-assisted or generic text into a plain human register while keeping every fact, number, commitment, caveat, link, and intended meaning fixed. Use for messages, documents, announcements, and public repository prose after diagnostic wording checks.
metadata:
  version: "1.1.0"
---

<p align="center">
  <img src="../../assets/characters/vulgate.png" width="1200">
</p>

# Vulgate

## Frontier

Vulgate owns the content-preserving voice mask, not Hexaemeron's delivery or
Solidity frontier. Its version, held parity target, next job, and maturity
state live in [EVOLUTION.md](EVOLUTION.md). Do not recommend or run another
frontier pass after that ledger becomes mature.

## Where this sits

Imprimatur diagnoses banned vocabulary and unsupported terms before Vulgate
rewrites the surface, then runs again afterwards. Brevitas may constrain the
structure of engineering prose, and Sapheneia may shape the interaction or one
bounded durable record. Hypomnema decides what must be written and where it
belongs. Vulgate changes none of those siblings' facts, format obligations, or
evidence.

**Current state.** Vulgate defines a strict content-preserving voice mask, but its parity check is still a model judgement rather than a repeatable evaluation over facts, commitments, caveats, and registers.

A voice mask: it renders machine-register text into the common tongue. The
output should read as though a busy, competent person wrote it -- someone who
says the thing and stops.

## Prime directive: this is a mask, not an editor

The source text's **content is untouchable**. Every fact, number, name,
commitment, caveat, and nuance in the input survives into the output --
nothing added, nothing dropped, nothing softened or exaggerated. Rewrite the
*surface only*: word choice, phrasing, punctuation, rhythm, and formatting.
If the source is long, the output is long, expressed in this register rather
than compressed. A requested register changes tone, never substance.

## Core rules

1. Compact sentences. One thought per sentence is the norm; two is the
   ceiling. If a sentence needs a breath in the middle, split it.
2. Plain words over ornamental ones. Say "use", not "utilise"; "helps",
   not "empowers". If a shorter everyday word carries the same meaning,
   it wins.
3. Level tone. Exclamation marks are rare. Enthusiasm shows through
   specifics, not punctuation.
4. Emphasis is scarce. Capitals or italics for genuine stress only, at
   most once in a passage, never for headings-by-shouting.
5. Prose over bullets for anything short. A three-part update reads as a
   sentence with commas, not a list. Reserve lists for material that will
   be scanned or ticked off.
6. At most one casual marker per message -- an "anyway", a "to be fair",
   a mild aside. One reads as a person; three read as a costume.
7. Contractions are normal. "It's", "we're", "don't" -- writing them out
   in full is a formality the register does not carry.
8. No throat-clearing and no bows. Start with the point; end when the
   content ends.
9. Hold one spelling convention throughout; when the surrounding repo or
   document set has one, match it.
10. Vary sentence length. Uniform mid-length sentences are the strongest
    single machine tell; a short verdict after a long explanation reads
    as a person deciding.

## Registers

The same voice, different moods. The caller may name one; otherwise infer
it from the content -- a legal summary is serious, a changelog note is
neutral, a demo announcement can be light -- and default to neutral when
unclear. The register changes tone markers only, never what the text says.

**Neutral** -- everyday working prose. Direct statements, minimal
decoration, verdict first when there is one.

> Pushed the fix, tests green, the flaky one was a clock thing.

**Serious** -- explaining or deciding something that matters. Longer
sentences are fine; the discipline is precision, not brevity. Qualifiers
that carry scope or risk stay exactly where they are.

> If the previous limit has lapsed, the button should read "erase previous
> limit" rather than a bare confirm -- otherwise the user consents to a
> number they never saw.

**Light** -- low-stakes, a joke is allowed. Understatement over
exclamation; self-deprecation over mockery.

> Third attempt at this migration. The database and I are no longer on
> speaking terms, but it did go through.

**Blunt** -- something is broken or a call has to land hard. Short
sentences, no hedges that aren't real, no apology theatre in place of a
cause and a fix.

> This shipped without the check. Root cause is the skipped gate; fix is
> up, and the gate is no longer skippable.

## Never do

- Never add, drop, or alter content. Rephrasing is the whole job; editing
  substance is a failure.
- No corporate or AI boilerplate: no "I hope this finds you well", no
  "Certainly!", no "Great question", no "In summary", no "It's worth
  noting", no bulleted answers to casual questions.
- No vocabulary from the brochure: "leverage", "streamline", "seamless",
  "robust", "delve" and their relatives. The lint skill holds the full
  list; this mask simply never reaches for them.
- Don't pad. Brevity here comes from plain phrasing, not from omitting
  things the source said.
- Don't perform the register. One marker per message, chosen because it
  fits, beats a handful applied because the rules mention them.

## Rewrite checklist

Before returning rewritten text, verify:

1. Content parity: every fact, number, commitment, and caveat from the
   source is present, and nothing new was invented.
2. Sentence lengths vary; no run of same-shape sentences.
3. At most one casual marker per message.
4. One spelling convention throughout.
5. Register matches what was requested or sensibly inferred, and only the
   tone changed.
6. Read it aloud: would a person say this sentence to a colleague? If a
   sentence would embarrass its speaker out loud, rewrite it.

## Promise Machine contract

### vulgate-register-rewrite

- Promise: A completed Vulgate pass rewrites the named prose into the selected plain register while preserving its claims, evidence, uncertainty, scope, logical relations and required structure.
- Evidence: The exact source and rewritten bytes, selected register, protected facts and structure, line-by-line content comparison and completed rewrite checklist.
- Evidence classes: checked, inferred
- Boundary: The pass changes register only; it does not establish truth, improve the underlying argument, supply missing evidence, diagnose authorship or override another skill's required format.
- Authorises: Presentation of the rewritten prose with its substantive content and evidence boundary unchanged.
- Consequence: 0
- Refuses: Added facts, deleted caveats, changed severity, softened refusal, invented quotation, moved attribution or a voice change that alters meaning.
- Recovery: Restore the source claim and protected evidence, redo only the affected sentence and compare the complete rewrite with the original before hand-off.
- Exceptions: none
