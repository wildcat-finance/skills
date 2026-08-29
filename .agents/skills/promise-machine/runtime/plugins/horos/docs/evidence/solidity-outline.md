# Evidence bundle: the C++ outliner against tree-sitter

The differential corpus run the C++ extractor's acceptance demanded: every
C++ file in a live external repository, outlined by Horos and independently
parsed by tree-sitter's C++ grammar, with the two declaration lists
compared per file at declared altitudes.

## The run

- Corpus: `ethereum/solidity` at
  `60dfdc91f476fcab91513f5aa6694c0fdc6271ed`, all 842 `.cpp`, `.h`,
  `.hpp`, `.cc` and `.cxx` files
- Captured: 2026-08-18
- Outliner: `languages/cpp/cpp.py` as shipped in this delivery
- Oracle: `tree-sitter` with `tree-sitter-cpp`, installed in a scratchpad
  virtualenv and driven by the committed dev-time tool
  [../../dev/cpp_oracle.py](../../dev/cpp_oracle.py); absent from every
  runtime and test path
- Declared altitudes: named types (class, struct, union, enum definitions)
  and named functions and methods at translation-unit, namespace,
  extern-block, template, preprocessor-conditional and class depth.
  Excluded by declaration on both sides: operators, destructors,
  namespaces, variables and fields, all-caps names (macro invocations and
  all-caps types alike), and function-body locals.
- Oracle parse failures: 170 of the 842 files carry tree-sitter parse
  errors (macro-bearing signatures such as `SOLC_NOEXCEPT` defeat the
  grammar); those files are compared for crash-freedom only and counted
  separately. The outliner itself crashed on none of them.
- Per-file results: [solidity-outline.results.json](./solidity-outline.results.json)

## The result

Across the 672 files the oracle parses, it sees 7,013 declarations at the
declared altitudes. The outliner names all 7,013, misses none, names
nothing extra, and crashes nowhere in the full 842.

The corpus surfaced five outliner defects, each fixed and rerun: a broken
template-prefix reattachment; a function body's close consuming the
following statement; Allman-style bodies orphaned from their heads; a
template prefix followed by a newline losing its declaration entirely; and
constructor initialiser lists using brace-initialisation splitting the head
at the wrong brace. Allman-style parameter lists on their own line joined
their declarations in the final round. The remaining mismatches along the
way were oracle- and driver-side (declarator descent through reference and
pointer wrappers, preprocessor-conditional scopes, literal operators,
most-vexing-parse lookalikes), each named in the run's history and fixed in
the tooling.

## Machine-readable capture lines

The consistency test parses these against the committed results document.

<!-- cppoutline:commit 60dfdc91f476fcab91513f5aa6694c0fdc6271ed -->
<!-- cppoutline:files 842 -->
<!-- cppoutline:crashes 0 -->
<!-- cppoutline:oracle 7013 -->
<!-- cppoutline:matched 7013 -->
<!-- cppoutline:missed 0 -->
<!-- cppoutline:missed_confessed 0 -->
<!-- cppoutline:extra 0 -->
<!-- cppoutline:oracle_unparsed 170 -->
