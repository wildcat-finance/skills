# Decision: A constant template literal is not a message built by formatting

## Status

Accepted, 2026-09-11. The record takes its number at the integration
composition, where the merge composer assigns one from the base branch.

## Context

Ephoros E001 reports a log message assembled by formatting, because a sentence
with values welded into it cannot be queried by field. On the Python surface
the rule reads `ast`, and `ast` gives a placeholder-free f-string,
`log.info(f"Getting all markets...")`, the same `JoinedStr` node as an
interpolated one, so E001 has fired on both since the rule existed. The
TypeScript surface arrived with
[skills#1420](https://github.com/wildcat-finance/skills/issues/1420) and reads
the shared masked lexer rather than a grammar, so the rule had to say, for the
first time, what a backtick string with no `${}` in it is.

The pinned application clone, `wildcat-app-v2` at `564a189b`, decided the
stakes. It holds 21 logger call sites: 14 pass an interpolated template literal
and 7 pass a constant one, such as ``logger.debug(`Getting all markets...`)``.
The study measured those numbers before any recogniser existed, and the run's
verdict over the clone is the number the shipped checker reports.

Finding codes are stable interfaces: E000 to E005 keep their numbers and their
Python behaviour, and other tools cite the codes and read the counts.

## Decision

On the TypeScript surface a template literal carrying no `${}` is a constant
string and stays outside E001; on the Python surface a placeholder-free
f-string keeps firing, so the two readings of one code diverge and the
divergence is deliberate.

## Alternatives

**Fire on every template literal, matching Python.** One rule, one sentence,
no divergence to explain. Over the clone it reports 21 sites instead of 14 and
the 7 extra are stable messages with nothing welded in, which is exactly what
E001 exists to tell apart from the other kind. A count that includes them
carries less information than one that does not, and a reader would learn to
discount it.

**Stop firing on a placeholder-free f-string in Python, matching TypeScript.**
The two surfaces would agree and the rule would be one sentence again.
It loses on the constraint the run held from its first assumption: the Python
behaviour of every code is unchanged, because recorded counts over existing
trees would move without any of those trees changing. It also removes a
finding that is true in its own right: an `f` prefix with nothing to format is
a message somebody meant to interpolate and did not, or a habit that will
interpolate next time, and either way a field is the remedy.

**Report the constant template under a new code.** A sixth code would keep
E001's meaning identical on both surfaces and give the constant template its
own line. It puts a code on a shape the rule does not consider a defect on the
surface where it can tell, and the checker's codes are cited by other tools, so
a code added to name a non-finding would cost every reader something to earn
nothing.

## Consequences

A reader comparing the two surfaces will meet the difference and read it as a
bug unless they find this record, which is why `SKILL.md` points here rather
than restating the reason. The 14-against-21 arithmetic over the pinned clone
is the evidence a later reader can recompute.

The TypeScript rule is lexical: interpolation is any `${` in the first
argument once it opens with a backtick, escaped or not, so an escaped
``\${`` still reads as interpolation and fails toward reporting. That
limit sits with the concatenation half's proximity reading in the ledger's
held job, and narrowing it does not reopen this decision.

Any future change to the Python reading of a placeholder-free f-string is a
change to a stable code's recorded counts and supersedes this record rather
than amending it.
