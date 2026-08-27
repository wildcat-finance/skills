# Lexicon rationale

Why each family is in the list, and why the list is organised by family at all.

## Substitution drift

A model asked to avoid a token reaches for the nearest available synonym. Ban "load-bearing" and the next draft says "does the heavy lifting". Ban that and it says "the crux". Ban that and it says "the operative word". Each substitution satisfies the letter of the ban and reproduces the move exactly.

The move is what is wrong. The move is: reach for a borrowed metaphor from structural engineering to assert that something matters, in place of saying what it does. All three substitutions do it. So the unit of prohibition is the family, and the instruction attached to every hard hit is the same: rewrite the sentence, do not pick another word from the same drawer.

This is also why the list will never be finished. New members arrive with every model release. The families are stable; the tokens are not. When a new term shows up, the question is which family it belongs to, and the answer is almost always one of the nine already here.

## The families

### structural_metaphor

Architecture and physics borrowed to assert importance. The origin family. Its tell is that it can be deleted with no loss: "the qualifier here is load-bearing" and "this qualifier matters" carry the same information, and the second is shorter, so the first was doing something other than informing. What it was doing is signalling that the writer is the kind of person who notices which parts of a sentence bear weight.

### claude_tic

Model-specific conversational habits. These are the highest-frequency tells in agent output and the easiest to catch, because they cluster at the start of turns. "That's a great question" is the purest case: it evaluates the question instead of answering it. The model has no comparison class, so the evaluation is never true.

"There's a version of this where" deserves a separate mention. It reads as careful conditional reasoning and functions as a hedge that commits to nothing. If there is a version, describe it. If there is not, do not gesture at one.

### hedge_pivot

Filler that announces a turn rather than taking it. "It's worth noting that X" is longer than "X" and adds only the claim that X is worth noting, which the act of writing X already asserted. "That said" announces a contrast the next sentence would have carried anyway.

The test is deletion. Cut the phrase and read the sentence. If nothing was lost, it was filler.

### closer

Summary endings. These exist because the model was trained on documents that have them, not because the argument needs one. A closing move on a three-paragraph note is a wrapper around an absent conclusion.

"Hope this helps" and "let me know if you'd like" are separate: they are service-desk politeness applied to a colleague, and they read as filler in any register where the reader can simply reply.

### brochure

The marketing voice. Absorbed wholesale from the upstream catalogue (see `NOTICE.md`). `delve`, `tapestry`, `landscape`, `journey`, `ecosystem`, `seamless`. Nothing to add.

### consultant

Corporate residue. Every member has a shorter Anglo-Saxon equivalent that is also more precise: `leverage` means use, `utilise` means use, `facilitate` means help or run, `socialise` means tell people.

"Best practice" is worth singling out because it smuggles authority. Practices are best relative to constraints, and naming the constraint is the actual content.

### invented_confidence

Marked critical, because this is a truthfulness defect rather than a style one. "Everything should work now" claims verification that did not happen. The correct output states what was changed and what was run, separately, and the correction is never to delete the uncertainty.

This family is where the ban and the preservation rule can collide. When they do, the qualifier wins: keep the uncertainty and rephrase around the banned term.

### register_cosplay

The model doing Extremely Online. It never lands, because the register depends on timing and membership, and a model has neither.

### empty_hedge

Hedges that survive deletion with no loss of meaning. Distinct from scope qualifiers, which are protected. The distinction is testable: a scope qualifier changes what the reader should do next; an empty hedge does not.

"Generally, the market accrues interest continuously" is an empty hedge if there is no exception, and a scope qualifier if there is one. If there is one, name it.

## Structural families

### causal_subject_has_no

The form "because this repository has no checked hand-off" expresses an
absence through possession by the subject. Its content may be correct. The
form can still make the missing condition arrive indirectly, so Imprimatur
reports it for a direct rewrite.

Lead with the missing condition: "No checked hand-off exists for these
clients, so they use the manual route." Where responsibility matters, name the
actor and action instead: "The maintainers have not built and checked a
hand-off for these clients, so they use the manual route."

The family stays narrow. It covers one bounded causal form, not standalone
"has no", "there is no", "lacks", or a clause whose punctuation separates the
subject from the verb. Those neighbouring forms need their own evidence before
they become lint rules.

Separators are one to three horizontal spaces or one line ending with at most
three spaces on either side. This admits an ordinary wrapped line without
joining separate paragraphs, masked inline material, or comment fragments
across an intervening source line.

## The gated tier

Nine families are banned outright. Four are gated, because they are real terms in the domains this organisation writes about, and a lexicon that fires on "orthogonal" in a maths context is a lexicon that gets uninstalled in a week.

The gate is evidence in the same sentence: a numeral, a backticked identifier, a path, an address, a named system, or an immediate definition. The reason for same-sentence scope is that a referent two sentences away licenses nothing. The first draft of this lint used a character window and passed "orthogonal to the framing" because a backticked function name appeared in the next paragraph.

Intensifiers are stricter and need a numeral, because each one promises a magnitude. "Materially different" without a number is an assertion that the difference is large, offered without the size. If the size is unknown, say so; if it is known, give it.

## What the lint cannot do

It counts known markers. Prose can be free of every term here and still be machine-written, because the deeper tells are structural: claims with no owner, examples with no source, paragraphs that restate the previous paragraph in different words, and arguments that never risk being wrong. No regex catches those.

So a high score means the known markers are absent. It does not mean the writing is good, and it certainly does not mean the writing will pass a detector, which is a different and mostly unanswerable question. Read the defect list, fix what is real, and then read the prose.
