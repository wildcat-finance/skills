# ADR-051: Encode a closed agent-instruction model

## Status

Accepted, 2026-08-30, for the bounded prototype in issue
[#909](https://github.com/wildcat-finance/skills/issues/909).

## Context

The repository carries repeated agent-facing rules in Markdown. Those rules
need to preserve negation, order, scope, precedence, evidence, authority,
refusal, recovery, unknowns, and exact literals. Shortening prose by judgement
cannot establish that those distinctions survived.

The accepted [study](../compact-agent-instruction-language/study.md) separates
three things that prose compression often joins:

1. Human Markdown remains the authored statement.
2. A reviewed, closed JSON model states the subset of its meaning that version
   1 can carry.
3. A compact line form is a deterministic derived view of that model.

This direction is expensive to reverse once compact files are consumed. The
authority source, supported semantic domain, and compatibility rule therefore
need one standing record before the codec is built.

## Decision

Define `wildcat-agent-instruction/v1` as a closed instruction model with a
canonical JSON representation and a deterministic compact line encoding. The
normative interface is [the version-1 contract](../agent-instruction-language-v1.md),
and its closed JSON shape is
[`schemas/agent-instruction-v1.schema.json`](../../schemas/agent-instruction-v1.schema.json).

Markdown remains authoritative. A source-to-model binding is reviewed and
bound to source bytes; the compact form is generated from a validated model.
Neither the model nor the compact form may silently add, remove, infer,
normalise, merge, or reorder an instruction. An unsupported construct refuses
encoding.

For this prototype, lossless means exact canonical-model equality:
`decode(format(model))` produces the same canonical JSON bytes. Fresh-context
questions and hostile mutations may disprove a reviewed source binding, but a
model answer cannot create authority or prove that every meaning in arbitrary
English was captured.

The prototype is a root framework capability. It does not belong to Horos or
Brevitas, it creates no marketplace plugin, and it changes no external
repository. A later authority reversal, broader conversion, plugin assignment,
or Shoggoth migration needs a separate decision and delivery boundary.

## Alternatives

- **Canonical JSON only.** This has the smallest parser and remains the control
  representation. Repeated keys and punctuation are unlikely to repay decoder
  bootstrap cost across the bounded corpus, so it does not test the compact
  language proposed by issue #909.
- **The closed model encoded with TOON.** A generic deterministic line format
  avoids owning all lexical rules, but it adds a working external specification
  to the trust base and still needs a separate instruction vocabulary,
  precedence model, and recovery contract.
- **Model-assisted prompt compression.** A model may remove more tokens, but
  observed task performance does not establish exact model equality. It also
  puts a model in the instruction-authority path.
- **Make compact files authoritative now.** This would remove the inspectable
  source before the three-fixture prototype has established its structural,
  mutation, tokenizer, and family-parity evidence.

## Consequences

Consumers need one versioned decoder bootstrap, but repeated documents can use
short fixed opcodes. Unknown versions, opcodes, fields, relations, evidence
classes, and escapes fail closed. Adding a construct or changing an existing
meaning requires a new language version rather than a permissive version-1
reader.

Review remains necessary at the Markdown-to-model boundary. Deterministic
round trips establish equality only after that review. The committed corpus
must therefore retain source digests and spans, hostile mutations, and closed
questions beside every derived form.

The standard-library codec stays independent of tokenizers and model runtimes.
Measurement and family-parity adapters remain outside its authority and may
support only the exact profiles and observations they record.

Version 1 cannot be called ready for a repository-wide conversion from this
decision alone. The [runbook](../compact-agent-instruction-language/runbook.md)
keeps that migration out of scope and names the checks needed for the bounded
prototype.
