# Evidence bundle: the TypeScript outliner against the compiler

The differential corpus run the outline extractor's acceptance demanded:
every hand-written TypeScript file in the wildcat-app-v2 clone, outlined by
Horos and independently parsed by the TypeScript compiler API, with the two
declaration lists compared per file.

## The run

- Corpus: `wildcat-finance/wildcat-app-v2` at commit
  `9b8b6d5d6db06428c5b539f267623277b65315cd`, all 866 `.ts` and `.tsx`
  files under `src/`
- Captured: 2026-08-18
- Outliner: `languages/typescript/typescript.py` as shipped in this
  delivery, run through the same code path as `map`
- Oracle: the TypeScript compiler API (`typescript@5.9.3` under node
  v26.6.0), driven by the committed dev-time tool
  [../../dev/ts_oracle.mjs](../../dev/ts_oracle.mjs), installed outside the
  repository and absent from every runtime and test path
- Altitudes compared on both sides: module level, namespace and module
  blocks, class members; function-body locals excluded by design
- Per-file results: [wildcat-app-v2-outline.results.json](./wildcat-app-v2-outline.results.json)

## The result

The compiler sees 2,239 declarations at the compared altitudes. The
outliner names 2,237 of them, misses 0 outside its own confessions, and
names nothing the compiler does not see. Zero files crashed. The two
unmatched declarations sit inside confessed regions of one file
(`src/components/CookieBanner/index.tsx`), which is the confession contract
doing its job: the outliner said it did not understand those lines rather
than guessing. 169 files carry at least one confessed region, almost all
module-level side-effect statements and JSX render expressions the
recogniser list deliberately excludes.

Three defects were found by the corpus and fixed during the run, each now
pinned by a unit test: blanked string literals left a stale continuation
character that swallowed semicolon-free declarations; a bare `>` at line
end (a generic or JSX close) was wrongly treated as a continuation; and a
statement position could fail to advance on a stray closing brace.

## Machine-readable capture lines

The consistency test parses these against the committed results document.

<!-- outline:commit 9b8b6d5d6db06428c5b539f267623277b65315cd -->
<!-- outline:files 866 -->
<!-- outline:crashes 0 -->
<!-- outline:oracle 2239 -->
<!-- outline:matched 2237 -->
<!-- outline:missed 0 -->
<!-- outline:missed_confessed 2 -->
<!-- outline:extra 0 -->
<!-- outline:files_with_regions 169 -->
