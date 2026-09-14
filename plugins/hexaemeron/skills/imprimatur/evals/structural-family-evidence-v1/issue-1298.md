<!-- wildcat-origin: shoggoth -->

This Imprimatur-specific wish was requested by the Creator after reviewing causal_subject_has_no. It preserves a catalogue of candidate grammatical moves for labelled-prose-v2. It does not authorise a regex, a score change, or tuning against the spent v1 holdout.

## Boundary and current evidence

This catalogue was checked against wildcat-finance/skills main at f4627a76600f0fa7b108f14b7f53d007ff31f098 on 27 August 2026.

Issue #422 owns the held labelled-prose-v2 job. It must refill structural holdout coverage, obtain two fresh blind annotations with sample-by-tier kappa and raw span F1 of at least 0.80, then run calibration and one sealed holdout without tuning on the v1 holdout. Issue #503 is closed and delivered source-prose extraction; it does not cover these families.

The v1 evaluation had only 2 actionable structural holdout spans. Its agreement gates failed, its holdout is spent, and its provisional scores cannot support tuning. This wish supplies candidate families and negative cases to the v2 work. It does not supersede #422.

A family still needs two independent examples of the same move plus negative specimens. Absence from structural.json or from the issue queue is not evidence that a pattern is safe. Exact live issue searches found no existing issue for causal_subject_has_no, stacked_epistemic_modal, empty_expletive_case, or redundant_connective_pair.

## Existing overlap and conflicts

The current structural catalogue already covers negation correction, not-because-but, less-X-than-Y, it-is-not-that, whether-or, fake from-to sweeps, rules of three, em dashes, bold lead bullets, title-case headings, unrequested summaries, apology theatre, unearned collective voice, emoji, and cadence signals.

Some proposed forms belong inside an existing family if evidence supports them. "The point is", "it should be noted", simplification openers, and ordering announcements perform work already owned by claude_tic or hedge_pivot. "Could arguably" already contains the hard-banned term "arguably". Balanced "whether ... or ..." forms already reach whether_or.

"In the sense that" must remain available. Imprimatur currently accepts it as an immediate definition that can license a gated technical term. A new rule must not turn that evidence form into a defect.

The broad forms discussed below remain in the catalogue even when the present disposition is "signal" or "do not add broadly". The disposition records the evidence question; it does not erase the grammatical move, example, reader cost, or boundary.

## Missing conditions and causal wrappers

### causal_subject_has_no

Form: "because this repository has no checked hand-off".

Reader cost: The sentence expresses an absence through possession by the causal subject. Its content may be correct, but the missing condition arrives indirectly.

Direct rewrite: "No checked hand-off exists for these clients, so they use the manual route." When responsibility matters: "The maintainers have not built and checked a hand-off for these clients, so they use the manual route."

Boundary: This family covers the bounded causal form, not standalone "has no", "there is no", "lacks", or a clause whose punctuation separates the subject from the verb. Those neighbouring forms need their own evidence.

Separator rule: Separators are one to three horizontal spaces or one line ending with at most three spaces on either side. This admits an ordinary wrapped line without joining separate paragraphs, masked inline material, or comment fragments across an intervening source line.

Disposition: Candidate for labelled-prose-v2 evidence.

### causal_absence_nominalised

Form: "Clients use the manual route because of the repository's lack of a checked hand-off" or "because of the absence of a checked hand-off".

Reader cost: An abstract noun carries the missing condition. The construction can also hide the person who failed to provide it.

Direct rewrite: "No checked hand-off exists, so clients use the manual route." When responsibility matters: "The maintainers have not provided a checked hand-off, so clients use the manual route."

Boundary: Match a causal connector immediately governing "lack", "absence", or "non-existence" plus its object. Do not flag those nouns outside a causal wrapper, inside a quotation, or where legal wording gives the noun a defined effect.

Disposition: Candidate for evidence. Keep it separate from causal_subject_has_no because the grammar and false-positive surface differ.

### causal_negative_passive

Form: "Clients use the manual route because a hand-off has not been built" or "because the release was not checked".

Reader cost: The negative passive delays both the missing condition and the actor who could have supplied it.

Direct rewrite: "No hand-off exists, so clients use the manual route." When the actor matters: "The maintainers have not built the hand-off, so clients use the manual route."

Boundary: Cover a negative passive inside a causal clause. Do not flag positive passives, passives outside causal clauses, or cases where the actor is unknown and the object is the point.

Disposition: Candidate for evidence, with a signal-first default.

### reason_is_because

Form: "The reason publication fails is because the digest changed."

Reader cost: "The reason" and "because" mark the same causal relation twice, delaying both event and cause.

Direct rewrite: "Publication fails because the digest changed."

Boundary: Cover the "the reason ... is because ..." scaffold. Do not flag a reason noun with a non-causal complement or a quoted specimen.

Disposition: Strong candidate for evidence.

### fact_clause_as_cause

Form: "The fact that the digest changed blocks publication."

Reader cost: The event becomes an abstract fact-subject before the sentence states its consequence.

Direct rewrite: "The digest changed, so publication is blocked."

Boundary: Cover a fact clause serving as the grammatical cause of a second event. Do not flag every "the fact that" clause; factivity, contrast, and object position can carry meaning.

Disposition: Signal first.

### causal_fact_clause_wrapper

Form: "Publication failed due to the fact that the digest changed", "because of the fact that", "owing to the fact that", or "given the fact that".

Reader cost: A causal connector wraps an already finite cause in a fact noun.

Direct rewrite: "Publication failed because the digest changed."

Boundary: Cover a closed list of causal connectors immediately followed by "the fact that". Keep bare fact clauses, quotations, and defined legal formulations outside the family.

Disposition: Strong candidate for evidence.

### backward_demonstrative_cause

Form: "Publication is blocked. This is because the digest changed" or "This is why the check fails."

Reader cost: The reader must resolve a backward demonstrative before reaching the cause. A sentence that could state one causal relation becomes two stages.

Direct rewrite: "The digest changed, so publication is blocked" or "The check fails because the digest changed."

Boundary: This is not a broad ban on "this". A demonstrative can join a genuinely complex prior proposition to a consequence. The rule needs evidence that the antecedent is recoverable and the rewrite loses nothing.

Disposition: Signal only.

### participial_consequence_tail

Form: "The flag enables retries, thereby reducing failures while ensuring continuity."

Reader cost: A chain of gerunds can make several consequences sound automatic and equally established. The finite action and the causal claim arrive in different grammatical layers.

Direct rewrite: Split the established consequences into finite clauses and name any causal evidence.

Boundary: Do not flag "thereby" or a participle merely for existing. Short consequence clauses can be precise. The candidate needs a bounded tail shape and negative examples with genuine causal compression.

Disposition: Signal only.

## Hidden actors, authority, and intent

### agentless_choice_passive

Form: "The manual route was chosen", "the schema was selected", or "it was decided that the release would wait".

Reader cost: Choosing and deciding require an actor. The passive records the outcome while hiding who made the judgement.

Direct rewrite: "The maintainers chose the manual route" or "The release owner decided to wait."

Boundary: Restrict the family to verbs of choice or judgement without a named by-agent. Do not flag all passive voice. A surrounding sentence may already identify the chooser.

Disposition: Signal only. When ownership is mandatory in a decision record, Hypomnema owns that record-level requirement.

### unowned_commitment_passive

Form: "The documentation will be updated before release."

Reader cost: The sentence makes a commitment without naming the person or tracked mechanism responsible for keeping it.

Direct rewrite: "The maintainers will update the documentation before release" or "Issue #123 tracks the documentation update required before release."

Boundary: Cover future passive commitments where ownership affects whether the reader can act. Do not flag forecasts, object-focused statements, or commitments whose owner is fixed by the surrounding host structure.

Disposition: Signal only.

### impersonal_requirement

Form: "It is necessary for maintainers to sign releases" or "It is recommended that the check run first."

Reader cost: An expletive subject hides both the authority behind the requirement and the actor who must perform it.

Direct rewrite: "The release policy requires maintainers to sign releases" or "Run the check first."

Boundary: Cover an anticipatory "it" plus a requirement or recommendation. Do not merge possibility, probability, or evidence claims into this family.

Disposition: Candidate for evidence.

### inanimate_intention

Form: "The repository wants clients to use the manual route" or "This document hopes to explain the process."

Reader cost: An artefact receives human intention. The sentence can hide whether a machine requirement or a maintainer preference controls the result.

Direct rewrite: "The client contract requires the manual route" or "The maintainers intend clients to use the manual route."

Boundary: Use a closed list of inanimate document or repository subjects and mental or intention verbs. Do not flag mechanisms that accurately "expect" an input token or reject a state.

Disposition: Candidate for evidence.

### passive_purpose_clause

Form: "The command is designed to validate the manifest", "is intended to", or "is meant to".

Reader cost: The passive can substitute an unowned design intention for a statement of behaviour.

Direct rewrite: "The command validates the manifest" when that behaviour is established, or name the designer and intended purpose when it is not.

Boundary: Design intention often carries real information. Do not add a broad rule. Evidence must distinguish a behaviour claim from a documented purpose and preserve uncertainty about whether the purpose is achieved.

Disposition: Hold as a negative-specimen family unless a narrower repeated form appears.

## Verb, capability, and purpose shells

### capability_noun_shell

Form: "The client has the ability to retry" or "does not have the capability to retry."

Reader cost: Possession of an abstract capability delays the modal claim.

Direct rewrite: "The client can retry" or "The client cannot retry."

Boundary: Capability and permission are different. Do not rewrite a security capability object, a named capability model, or a sentence whose point is that distinction.

Disposition: Candidate for evidence.

### enablement_shell

Form: "The flag makes it possible for clients to retry."

Reader cost: A causative shell places the actual capability at the end of the sentence.

Direct rewrite: "With the flag, clients can retry" or "The flag lets clients retry."

Boundary: Keep cases where "possible" marks uncertainty rather than capability. Do not infer that the flag alone causes success when another condition remains.

Disposition: Candidate for evidence.

### light_verb_nominalisation

Form: "The checker performs validation of the manifest", "conducts an evaluation of the result", or "makes a determination about validity."

Reader cost: A light verb plus an action noun hides the direct verb and often its actor.

Direct rewrite: "The checker validates the manifest", "evaluates the result", or "determines validity."

Boundary: Use a closed list of demonstrated verb-noun pairs. Do not detect nominalisation from suffixes, and do not rewrite a noun that names a durable artefact or a distinct process.

Disposition: Candidate for evidence.

### purpose_periphrasis

Form: "in order to validate", "so as to validate", "for the purpose of validating", "with the aim of validating", or "with the goal of validating".

Reader cost: A prepositional or infinitival shell announces purpose before stating the action.

Direct rewrite: "to validate" when that preserves the relationship.

Boundary: Protect defined legal purpose, negative purpose such as "in order not to", and contrasts where the longer form disambiguates which action has the purpose. The family must not become a raw phrase ban.

Disposition: Signal first.

### capacity_circumlocution

Form: "is able to retry", "to be able to retry", or "is in a position to retry."

Reader cost: A capacity phrase can replace a shorter modal and add ceremony.

Direct rewrite: "can retry" when tense, permission, and capability remain unchanged.

Boundary: "Be able to" carries tense where "can" has no equivalent and can separate permission from mechanics. "In a position to" is closer to the consultant family. Split those forms rather than imposing one broad rule.

Disposition: Consider "in a position to" as an existing-family expansion. Do not flag "be able to" broadly.

### relative_passive_modifier

Form: "a tool that is used for parsing" or "a check that is intended to reject stale state."

Reader cost: A relative clause can delay a modifier that fits next to the noun.

Direct rewrite: "a parsing tool" or "a stale-state check" only when the shorter noun phrase preserves behaviour and purpose.

Boundary: The proposed rewrite can change meaning. "Used for" may describe observed use, while an attributive noun may imply design. Keep this as a negative-specimen question until a narrower form is evidenced.

Disposition: Do not add broadly.

## Stacked hedges, emphasis, and redundant markers

### stacked_epistemic_modal

Form: "may potentially", "might possibly", "could conceivably", or "could arguably".

Reader cost: Two markers can qualify the same uncertainty and leave the reader with no clearer probability or source.

Direct rewrite: Keep the one marker that carries the intended uncertainty, or state the unknown condition.

Boundary: Use a closed pair list. Exclude normative RFC "MAY" and cases where one term marks permission while the other marks probability. "Could arguably" already overlaps the hard "arguably" term.

Disposition: Candidate as a signal before any scored treatment.

### redundant_connective_pair

Form: "but, however, the check failed" or "the checker validates and also records the digest."

Reader cost: Two connectors can express the same relation and pad the sentence for rhythm.

Direct rewrite: Use one adversative marker. For addition, remove "also" only when "and" carries the same emphasis and scope.

Boundary: Split adversative and additive forms. "But however difficult the task" uses "however" as a degree word and must not match. "And also" has more legitimate emphatic uses than "but, however,".

Disposition: Strong candidate for the narrow adversative form; signal only for the additive form.

### redundant_binomial

Form: "each and every", "first and foremost", or "one way or another."

Reader cost: The second member can repeat the first and add rhythm without information.

Direct rewrite: "each", "first", or the actual alternative.

Boundary: These are closed phrases, not evidence for a generic coordination rule. Some uses are deliberate emphasis. A family should explain why each admitted pair is semantically redundant.

Disposition: Low-priority candidate, probably as terms in an existing family rather than a new structural regex.

### litotic_double_negative

Form: "not unhelpful", "not impossible", "not without risk", or "not entirely unlike."

Reader cost: The reader must resolve two negatives before learning the degree of the claim.

Direct rewrite: State the supported degree when it is known.

Boundary: A mechanical positive rewrite is unsafe. "Not uncommon" is weaker than "common", and "not without risk" preserves a warning. Qualifications that carry scope or uncertainty must survive.

Disposition: Signal only.

### attention_adverb_opener

Form: A sentence opens with "Interestingly,", "Notably,", "Importantly,", "Crucially,", or a similar attention instruction.

Reader cost: The writer tells the reader how to rank the sentence before giving the evidence that earns the ranking.

Direct rewrite: State the fact and its consequence. Keep the adverb only when the comparison or ranking is explicit.

Boundary: Sentence-medial uses and evidence-backed ranking may be legitimate. This is a positional family, not authority to ban every token.

Disposition: Consider as an extension of hedge_pivot or the intensifier discipline after corpus evidence. Do not create a parallel family merely because the words are absent.

### empty_expletive_case

Form: "It is the case that the digest changed."

Reader cost: An expletive subject and a case noun postpone the actual subject.

Direct rewrite: "The digest changed."

Boundary: Restrict the rule to the exact "it is/was the case that" shell. "It remains the case that" carries persistence, and "it is possible that" carries modality.

Disposition: Strong candidate for evidence.

### cleft_emphasis

Form: "What it does is validate the manifest", "What matters is the digest", or "What is important is that the check ran."

Reader cost: The cleft postpones the subject or verb and manufactures emphasis before the content arrives.

Direct rewrite: "It validates the manifest", "The digest matters", or "The check ran."

Boundary: Clefts can answer a real contrast or focus question. "The point is" and importance announcements also overlap existing hard families. The match needs more than the word "what".

Disposition: Signal only.

### sequence_announcement

Form: "First of all", "To begin with", or "To start with" before an ordinary sequence.

Reader cost: The prose announces ordering that numbering or sentence order already supplies.

Direct rewrite: Start with the first action or fact.

Boundary: These forms can orient a long argument or distinguish chronology from priority. "First and foremost" also belongs to redundant_binomial. Avoid a general ban on "first".

Disposition: Existing-family expansion if repeated evidence supports it.

### emphatic_correction_shell

Form: "In fact,", "Actually,", "does actually", or "did in fact".

Reader cost: The construction asserts a correction or emphasis even when no prior claim has been identified.

Direct rewrite: State the observation and name the contradicted claim when one exists.

Boundary: Imprimatur and the Promise Machine rely on "actually" to distinguish what ran from what was claimed. A regex cannot decide whether the correction is earned from the token alone.

Disposition: Do not add broadly. Preserve evidence-bearing uses as negative specimens.

### fronted_concession

Form: "While this works, ..." or "Although the approach is valid, ..." when the following clause does not oppose the opener.

Reader cost: An empty concession makes the reader search for a conflict that the sentence never supplies.

Direct rewrite: State the two facts without concessive grammar, or name the real conflict.

Boundary: Whether the concession is empty is semantic. Genuine trade-offs and limitations must survive.

Disposition: Do not add as a regex without a narrower repeated form.

### balanced_exhaustive_pair

Form: "whether it compiles or not", "whether new or established", or another pair presented as exhaustive.

Reader cost: The second side can add symmetry without changing the scope of the first.

Direct rewrite: State the condition that changes the outcome, or remove the pair when the outcome is unconditional.

Boundary: Genuine alternatives and enumerations are common. The current whether_or rule already reports this family as a signal.

Disposition: Existing overlap. Supply negative specimens to whether_or instead of adding a new rule.

### sentence_stutter

Form: Two adjacent sentences repeat the same subject and claim with minor wording changes.

Reader cost: The second sentence makes the reader compare paraphrases and search for a difference that may not exist.

Direct rewrite: Keep the sentence that carries the complete claim.

Boundary: Detecting restatement requires lexical or semantic comparison. Repeated openers and sentence-length cadence already have advisory treatment, but they do not prove semantic duplication.

Disposition: Cadence or future semantic-analysis question, not a current regex family.

## Existential, reference, and scope constructions needing more evidence

### existential_relative_shell

Form: "There are three checks that reject stale state."

Reader cost: The existential opener delays the quantified subject and its action.

Direct rewrite: "Three checks reject stale state."

Boundary: Existence may be the point, especially before a list or contrast. Restrict any candidate to a sentence-opening existential plus a quantified noun and relative clause.

Disposition: Signal first.

### broad_existential_there

Form: "There is no checked hand-off", "There exists a way in which", or ordinary "there is/are" clauses.

Reader cost: Some uses postpone the real subject.

Direct rewrite: Lead with the subject when the sentence is not asserting existence.

Boundary: This is the explicit neighbour excluded from causal_subject_has_no. Existence claims, list introductions, and locative "there" are legitimate. No broad rule has earned inclusion.

Disposition: Do not add without separate evidence.

### nonrestrictive_relative_restatement

Form: A ", which ..." clause repeats a property already stated or implied by its noun.

Reader cost: The main clause pauses for a second statement that may add no information.

Direct rewrite: Remove the restatement or make the new consequence finite.

Boundary: A regex cannot establish that a relative clause is redundant. Nonrestrictive clauses often carry the qualification a rewrite must protect.

Disposition: Do not add as a regex.

### consequence_paraphrase

Form: "This means that ...", "which means that ...", or "effectively meaning ...".

Reader cost: The prose may restate an implication the prior clause already made explicit.

Direct rewrite: State the consequence once, joined to its cause.

Boundary: Explanatory consequences are often useful and may be the only place an operational effect is stated. Redundancy depends on the prior clause.

Disposition: Signal only if a bounded repeated form and negative corpus emerge.

### heavy_preverbal_subject

Form: A sentence places several embedded clauses or prepositional phrases between the subject and its main verb.

Reader cost: The reader must retain a large unresolved subject before reaching the action.

Direct rewrite: Move the main action earlier or split the sentence.

Boundary: This needs parsing and a measured depth or distance threshold. Length alone is not enough, and the current structural engine is regex-based.

Disposition: Future parser-backed cadence question, not a current pattern.

### generic_pluralisation

Form: "in cases like this", "situations such as these", or a generic plural around one concrete event.

Reader cost: The sentence can dilute a specific failure into an abstract class without supplying other members.

Direct rewrite: Name the event, or name the additional cases that justify the class.

Boundary: Determining whether more cases exist is factual rather than syntactic.

Disposition: Do not add as a prose regex.

### deictic_here

Form: "As mentioned here", "in this section", or another deictic reference whose target is not named.

Reader cost: The reader must infer a location from the current rendering or document position.

Direct rewrite: Name the section, path, or earlier claim.

Boundary: "Here" can refer to an immediately visible location, and section references can be exact. The rule needs a missing-target test rather than a word ban.

Disposition: Hold for a reference-integrity tool, not Imprimatur's current structural regexes.

### scope_setting_shell

Form: "in terms of performance", "in that respect", or "in the sense that".

Reader cost: Some scope phrases postpone the dimension or relation.

Direct rewrite: Name the dimension directly when nothing else changes.

Boundary: Scope language often carries precision. "In the sense that" is an explicit Imprimatur evidence licence and must remain available. "In terms of performance" may be the sentence's necessary dimension.

Disposition: Do not add broadly. Preserve licensed and dimension-bearing cases as negative specimens.

### so_or_such_that

Form: Purpose and result clauses using "so that" or technical constraints using "such that".

Reader cost: A vague antecedent can make the relation hard to recover.

Direct rewrite: Name the purpose, result, or constraint directly when the antecedent is unclear.

Boundary: These are ordinary grammatical and mathematical constructions. "Such that" is often the precise relation a specification needs.

Disposition: Do not add without a much narrower evidenced form.

### assumption_clause

Form: "on the assumption that", "on the premise that", or "assuming that".

Reader cost: A long wrapper can delay the condition.

Direct rewrite: Use the shortest form that preserves the assumption status.

Boundary: Assumption status is protected evidence. A rewrite that presents the assumption as fact is unacceptable.

Disposition: Do not add broadly.

### broad_fact_clause

Form: Any occurrence of "the fact that", including object position and factive complements.

Reader cost: Some instances add ceremony.

Direct rewrite: Remove the wrapper only when factivity and grammar survive.

Boundary: Examples such as "the checker discarded the fact that it had stopped" need the fact noun. The narrow causal_fact_clause_wrapper and fact_clause_as_cause candidates must not become a blanket ban.

Disposition: Explicit negative boundary for the two narrower families.

## Ideas that do not yet form a family

Possessive versus "of" relationships are a style choice until a recurring grammatical move and reader cost are shown. No rule is proposed.

Rare object-fronting or inversion has no demonstrated recurrence. No rule is proposed.

"For the sake of" has no bounded family or rewrite in this catalogue. It remains an observation to test, not a term to add.

"I.e." and other explicit technical restatements can be precise. No rule is proposed.

A bare "due to" rule would turn grammar preference into policy. No rule is proposed.

## Evidence packet for labelled-prose-v2

For every candidate family that advances, collect at least two independent shipped examples with the same grammatical move. Record the exact actionable span, the reader cost, the content-preserving rewrite, and negative specimens for the nearest legitimate forms.

Annotate whether the family is actionable or signal-only before reading lint output. Keep source selection independent of whether the current checker fires. Tune only on the new calibration split, freeze the candidate, and reveal the new holdout once.

The current high-value evidence targets are causal_subject_has_no, causal_fact_clause_wrapper, reason_is_because, empty_expletive_case, and the narrow adversative form of redundant_connective_pair. The signal targets are stacked_epistemic_modal, causal_negative_passive, purpose_periphrasis, agentless_choice_passive, litotic_double_negative, attention_adverb_opener, backward_demonstrative_cause, and existential_relative_shell.

The remaining entries are required negative boundaries or future questions. Their presence prevents a narrow candidate from silently becoming a blanket ban.

## Questions left open

1. Which candidate families have two independent shipped examples once labelled-prose-v2 applies its deterministic selection rules?
2. Which context-dependent families belong only as advisory signals?
3. Should decision ownership remain outside Imprimatur and be enforced only by Hypomnema's decision-record contract?
4. Can the regex engine express each accepted boundary without joining paragraphs, masked spans, or unrelated clauses?


---

Re-filed 2026-09-06 from wildcat-finance/skills#676, created 2026-08-27T15:47:37Z by shoggoth-wildcat and closed 2026-08-27T19:28:12Z. That issue now returns 404, as does the shoggoth-wildcat account, so GitHub is hiding everything that account authored. The body above is the original, recovered unchanged from local Codex session logs. The original close reason is not recorded.


Fiat-Required: 1

```carryover
restore-678 | duplicate | https://github.com/wildcat-finance/skills/issues/1314
```

