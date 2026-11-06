# Recovering the comparison inputs

## Source and dependency bytes

Clone `https://github.com/wildcat-finance/v2-protocol.git`, create detached worktrees at the two commits in [sources.json](../sources.json), and run `git submodule update --init --recursive` in each. Compare every listed source SHA-256 and size. The three inherited Solady files are from `Vectorized/solady@2ba1cc1eaa3bffd5c093d94f76ef1b87b167ff3c`.

The report checker uses retained evidence only. Source recovery requires repository access; this bundle contains no Git object archive and does not promise future remote availability.

## Compiler and measurement records

[execution.json](execution.json) records Foundry, the native Solc version and digest, command arguments, output digests and the four coverage failures. The two preparation records preserve recursive submodule identities and GNU grep's scoped PATH prefix.

Given the recovered deployed source directory `/path/to/deployed`, rebuild its exact standard-JSON compiler input:

```sh
python3 docs/kickoff/1363/evidence/producers/rebuild_ast_input.py \
  deployed /path/to/deployed > /tmp/deployed-ast-input.json
solc --base-path /path/to/deployed --include-path /path/to/deployed/lib \
  --allow-paths /path/to/deployed --standard-json \
  < /tmp/deployed-ast-input.json > /tmp/deployed-ast.json
```

Use Solc 0.8.25 and repeat with the candidate role and directory. The helper refuses when source bytes do not reconstruct the recorded input digest. The AST-only request does not compile bytecode or run tests. Match the resulting AST digest to the role's retained `ast-result.json` before using it to revisit the action denominator.

The compiler inventories resolve concrete inheritance and canonical ABI types. The prose, effect summaries and event conditions also required source review; rerunning a parser does not replace that work. Producer scripts and extraction records preserve how the reports were assembled. Those producer scripts expect the ignored `.hexaemeron` layout recorded in their source; they are provenance records rather than another supported command interface.

The two `doc-extraction.txt` files retain the producer's transcript bytes. Relative links inside quoted documents belong to their original source tree; [doc-inputs.json](doc-inputs.json) records the pinned source locations.

## Diagrams and verification

From the Skills repository root:

```sh
python3 plugins/hexaemeron/skills/x-ray/scripts/generate_svg.py \
  docs/kickoff/1363/deployed/architecture.json /tmp/deployed-architecture.svg
python3 scripts/kickoff_xray_1363.py check
```

Repeat rendering for the candidate. The generator's digest is in [provenance.json](provenance.json). Visual inspection is a separate recorded act in [review.json](review.json).

The complete selection-probe source is retained as `producers/design-selection-probe.py`. To reproduce its recorded commands, copy it into `.hexaemeron/design-selection/probe.py` and recover the two source trees under `.hexaemeron/sources/`. The original time measurements describe that local packaging run; a new run need not have the same duration.
