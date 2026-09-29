# Captured input preparation

## Prepare an input

Run `python3 plugins/lemma/preparation.py --request /absolute/request.json --root /absolute/evidence-root --out /absolute/new-directory`. The closed request pins the original input and each compiler component. The output contains `prepared.json` and a `manifest.json` written last. An interrupted write leaves an incomplete directory for inspection; retry in a new directory. Existing destinations are never replaced.

The public [metadata request](../examples/metadata-request.json) is a template: replace its compiler paths and placeholder runtime digest with your exact executable pins before running it. Its [original input](../examples/original.json) is a synthetic fixture.

The request schema is [preparation-request-v1.json](../schemas/preparation-request-v1.json). Its target names one source and contract. Selection patterns apply to prepared names, must match, and must retain the target. Each source must contain inline content. URL-backed sources, unknown fields, duplicate JSON keys, nonfinite numbers, and escaping filesystem paths refuse.

Three declared transformations are supported. Metadata extraction removes only an exact `compilationTarget` matching the named target. Target closure follows compiler-produced `ImportDirective.absolutePath` and `sourceUnit` edges until the source set stops changing; legal cycles terminate, while missing or inconsistent edges refuse. Citation mapping requires every original source key, unique canonical output keys, explicit remapping pairs, and unchanged compiler-resolved import relationships. A request combining mapping and target closure refuses; no combined transform is claimed.

Every retained source-content string stays byte-identical in UTF-8. Compiler output selection changes to AST and ABI extraction; other settings remain present. The manifest preserves original and prepared digests, the complete reverse map, removed sources, selected and excluded sources, source-content digests, and each compiler request and response. A prepared name is a citation key with a reverse map, not a claim that the original repository used that path. Ordinary chunker traversal refusal remains in force.

The compiler runner checks the Node runtime, heap-allocating driver, and soljson artifact against the request before and after execution. It uses argument arrays and an environment containing only `LANG=C`; it performs no downloads or credential lookup. The compiler components are trusted executable inputs selected by their pins. This is not an operating-system sandbox and does not establish that a malicious pinned compiler has no host capability. Concurrent executable replacement after validation remains outside the check.

Limits are 32 MiB for input JSON, 64 MiB for combined compiler output, 128 MiB for an artifact or preparation manifest, 10,000 sources, 1,000,000 decoded JSON values, depth 128, 64 closure rounds, and 180 seconds per compiler call. The runner kills its process group on an observed timeout or output-limit failure. These limits do not establish an aggregate disk quota or a universal compiler memory bound.

Cleanup retains the direct child until any required group signal has been sent. After both streams close and the direct child's exit is observed, cleanup reaps it without signalling. A child already reaped by another owner refuses group signalling. Descendants that detach or close their inherited streams after a successful compiler exit remain outside this cleanup guarantee.

## Corpus evidence

Run `python3 plugins/lemma/corpus_evidence.py --bundle /absolute/bundle.json --root /absolute/evidence-root`, adding `--complete` for complete original-input custody and `--full` for every joined partition. The [bundle schema](../schemas/corpus-evidence-v1.json) binds the exact registry, source records, input rows, preparation manifests, two corpus/provenance pairs per partition, and an independent AST declaration census.

Verification recomputes subject-to-source membership and subject hashes from the pinned source records. Every resolved registry row has one disposition; excluded registry rows remain visible. Input pins, partition assignments, original/prepared mappings, compiler component bytes, transcript sequences, output hashes, corpus identifiers, provenance selection, event quotations, and public aggregate counts must agree. A missing input is a missing row of custody, never a zero or a substitute input.

The complete chunk set is derived again from the recorded AST and source bytes using the production chunker and its default deduplication. Every unstamped chunk field must match, including event signatures, citation lines, owner metadata, model text and embedding text. Rebinding corpus hashes or counts cannot replace that comparison. The separate declaration census still checks that each selected event appears once. This replay checks transcript consistency without authenticating the compiler execution.

Two equal build pairs establish repeatability for those recorded bytes. Offline replay checks recorded compiler output and does not execute the compiler again or authenticate who captured the transcript. Source-only evidence does not establish deployed bytecode, runtime events, source truth, acceptance by another task, or full-population conformance from a sample. Keep private inputs, source names and subjects in private evidence; publish only the bounded aggregate and its evidence digest.

## Issue 1366 evidence

The five preparation examples and four Maple examples produced 354 events in 3,911 chunks, with two matching output pairs per example. The checked registry join requires 816 original inputs; 815 are available. Euler set-164 remains missing at its original digest. Production conformance passes for the nine examples; complete-input custody and Step 4 remain blocked.

The retained guards originally failed through existing chunking interfaces. Their final adapter calls explicit production preparation and preserves raw-refusal controls. With final tests fixed, removing only the preparation product produces one assertion failure in each four-test guard suite, with no errors or skips; restoring it passes all twelve tests. This is a product-revert counterfactual, not unchanged replay of the original adapter.

A 12,583,101-byte synthetic input exceeded the study driver's stack allocation. The pinned heap driver accepted the same input in one measured 2.45-second run, with a Python allocation peak of 147,332,443 bytes. That peak excludes Node and compiler memory. This is bounded compatibility evidence, not a speed-improvement claim.
