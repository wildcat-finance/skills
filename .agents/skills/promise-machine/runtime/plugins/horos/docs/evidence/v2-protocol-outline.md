# Evidence bundle: the Solidity outliner against tree-sitter

The differential corpus run the Solidity extractor's acceptance demanded:
every Solidity file in the protocol repository, outlined by Horos and
independently parsed by tree-sitter's Solidity grammar, with the two
declaration lists compared per file at declared altitudes.

## The run

- Corpus: `wildcat-finance/v2-protocol` at
  `c7be4039f8f383a9dda4e45f63331c17d63f9ed9`, all 151 `.sol` files,
  contracts and Foundry tests alike
- Captured: 2026-08-18
- Outliner: `languages/solidity/solidity.py` as shipped in this delivery
- Oracle: `tree-sitter` with `tree-sitter-solidity`, installed in a
  scratchpad virtualenv and driven by the committed dev-time tool
  [../../dev/sol_oracle.py](../../dev/sol_oracle.py); absent from every
  runtime and test path
- Declared altitudes: contracts, interfaces and libraries; named functions,
  events, errors, structs and enums at file and container depth. Excluded
  by declaration on both sides: constructors, receive and fallback
  functions, modifiers, state variables, using-for and user-defined value
  types.
- Per-file results: [v2-protocol-outline.results.json](./v2-protocol-outline.results.json)

## The result

The oracle sees 2,329 declarations at the declared altitudes and parses
every file. The outliner names all 2,329, misses none, names nothing extra,
and crashes nowhere. Zero confessed regions across the corpus: every
statement in 151 files of live protocol Solidity fell to a recogniser.

One defect was found by the corpus and fixed with a pinned regression: a
multiline inheritance list broke the container head at the newline after
`is`, orphaning the body brace and silently swallowing every member of the
two main market contracts. Container braces are now found structurally (the
first depth-zero brace before any depth-zero semicolon) rather than by line
heuristics, and an orphan brace steps over its own close and nothing more.

## Machine-readable capture lines

The consistency test parses these against the committed results document.

<!-- soloutline:commit c7be4039f8f383a9dda4e45f63331c17d63f9ed9 -->
<!-- soloutline:files 151 -->
<!-- soloutline:crashes 0 -->
<!-- soloutline:oracle 2329 -->
<!-- soloutline:matched 2329 -->
<!-- soloutline:missed 0 -->
<!-- soloutline:missed_confessed 0 -->
<!-- soloutline:extra 0 -->
<!-- soloutline:oracle_unparsed 0 -->
