# Decision: Keep Wildcat interval demonstration payloads in full checkouts

## Status

Accepted, 2026-09-22.

## Context

Composing #1731 with main produced 21,009,325 runtime payload bytes before
the manifest and outer package files. The unchanged 25 MiB cap and 5 MiB
reserve allow 20,971,520 bytes for the complete package. The source trees
fit separately; their composition does not.

## Decision

Omit direct JSON files and pre-plan probes from the portable copies of the
Wildcat V1 and V2 interval v0 demonstrations. Keep their documents and Python
entrypoints. Both metadata verification and rebuilding use the full source
checkout; rebuilding also needs the already external private staging archives.
Declare this boundary in the package manifest and PORTABLE.md.

## Alternatives

Raising the limit or consuming its reserve removes the existing protection.
Reformatting captured JSON changes digest-bound evidence. Removing collector,
verifier or schema files breaks runtime operations. Omitting source evidence
from the repository would prevent reproduction.

## Consequences

The source demonstrations, captured bytes and runtime code remain unchanged.
The portable metadata demonstrations are incomplete, so their entrypoints
must be run from a full checkout. Package checks verify retained documents
and programs, omitted payloads and the complete package budget. The 1,600-file
tripwire remains fixed. This is a distribution repair for the failed merge
composition; it changes neither Alexandria's capture contract nor its frontier.
## Extension: Ariadne dataset demonstration, 2026-09-22

Issue 1374 preserves both captures as Ariadne dataset inputs. The accepted
base package is 20,945,776 bytes, leaving 25,744 bytes below the unchanged
20,971,520-byte boundary. Exact specification copies alone exceed that space.
Lossless gzip of metadata still produces a 21,255,473-byte complete package.
These measurements include the manifest and outer package files.

Extend the omission to exactly `plugins/ariadne/examples/wildcat-datasets-v0/`,
except its README. Keep every file in the source repository. The retained
README names the full checkout required for both metadata verification and
the demonstration and links to its source evidence. Core Ariadne capture,
verifier and schema runtime files remain installed. The manifest declares
this boundary, and a regression checks the exact omitted subtree, retained
runtime and complete package against the unchanged budget.

Keeping the demonstration program without its inputs would leave an installed
entrypoint that cannot run. Raising the cap or reducing its reserve would
remove the existing protection. Neither is needed when the complete example
remains available in the full checkout. This extension changes no dataset
semantics, evidence bytes or skill frontier.
