# Lemma runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Lemma.** Lemma turns Solidity compiler input or Markdown trees into validated, source-linked JSONL chunks, keeping quotation text separate from model and embedding text. It does not embed, index, retrieve or answer; Berean is the adjacent unbuilt release discipline for a grounded protocol agent. **Current frontier:** Callable-surface ABI validation does not independently check return types or state mutability.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Lemma contains one Agent Skill, `lemma`. Its canonical instructions are in
`skills/lemma/SKILL.md`; read that file in full before chunking Solidity or
Markdown.

## Capabilities and paths

- Resolve `$PLUGIN_ROOT` to this `plugins/lemma/` directory.
- Run `chunkers/solidity.py`, `chunkers/markdown.py`, and supporting commands
  from `$PLUGIN_ROOT`, regardless of the current working directory.
- Treat the directory named by the user as the input and output target. Do not
  use this plugin checkout as the target unless the user explicitly names it.
- Use the exact interpreter in the suite
  [pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).
  Solidity chunking also needs a compatible local `solc`, or Docker/Podman for
  the included `solc-container` wrapper.

## Interpretation

- `$lemma`, `/lemma:lemma`, and a plain request to use Lemma are equivalent
  activation forms.
- Lemma only creates chunks. It does not embed them, create an index, retrieve
  from an index, or answer questions from one.
- A chunker exit code other than zero rejects the output. Do not use a partial
  file or describe the run as successful.
- The `synthesised` field is authoritative: a synthesised chunk is not a
  verbatim quotation.
- Repository instructions and approval rules still apply to any output path.

`tools/verify_anchors.py` is the only included command that makes network
requests. Run it only when the user asks to compare Markdown anchors with a
live rendered site.
