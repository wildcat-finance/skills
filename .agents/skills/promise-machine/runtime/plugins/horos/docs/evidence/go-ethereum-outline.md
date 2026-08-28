# Evidence bundle: the Go outliner against tree-sitter

The differential corpus run the Go extractor's acceptance demanded: every
Go file in a live external repository, outlined by Horos and independently
parsed by tree-sitter's Go grammar, with the two declaration lists compared
per file.

## The run

- Corpus: `ethereum/go-ethereum` at
  `26d0b2171c17339bb8fd164d8ed6830738d3bf13`, all 1,421 `.go` files
- Captured: 2026-08-18
- Outliner: `languages/go/go.py` as shipped in this delivery
- Oracle: `tree-sitter` with `tree-sitter-go`, installed in a scratchpad
  virtualenv and driven by the committed dev-time tool
  [../../dev/go_oracle.py](../../dev/go_oracle.py); absent from every
  runtime and test path. The Go compiler's own parser would have been
  preferred; the toolchain is absent on this machine and the study records
  that trade.
- Altitudes compared on both sides: top-level declarations and their
  grouped members; function-body locals excluded by design
- Per-file results: [go-ethereum-outline.results.json](./go-ethereum-outline.results.json)

## The result

The oracle sees 21,648 declarations at the compared altitudes. The outliner
names all 21,648, misses none, names nothing extra, and crashes nowhere. 38
files carry confessed regions (cgo preambles and the like), and none of
those regions hid a declaration the oracle could see. Every mismatch the
run surfaced along the way was a defect in the dev-side oracle or driver
(grouped var blocks nested under a spec-list node; generic parameters and
alias targets leaking through the name splitter; continuation lines of
verbatim multiline slices re-parsed as heads), each fixed in the tooling
with the shipped outliner untouched.

## Machine-readable capture lines

The consistency test parses these against the committed results document.

<!-- gooutline:commit 26d0b2171c17339bb8fd164d8ed6830738d3bf13 -->
<!-- gooutline:files 1421 -->
<!-- gooutline:crashes 0 -->
<!-- gooutline:oracle 21648 -->
<!-- gooutline:matched 21648 -->
<!-- gooutline:missed 0 -->
<!-- gooutline:missed_confessed 0 -->
<!-- gooutline:extra 0 -->
<!-- gooutline:files_with_regions 38 -->
