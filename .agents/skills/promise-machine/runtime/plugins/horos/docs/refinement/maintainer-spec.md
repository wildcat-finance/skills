I’d use a budgeted, two-tier classifier. That would make the boundary safer and more complete while keeping the scan approximately linear in file count.

1. Strengthen whole-directory exclusions

Today, names such as `build`, `dist`, `out`, and `vendor` are sufficient to exclude an entire subtree. That is the riskiest rule because legitimate source can use those names.

Treat the directory name as a candidate signal, then require one corroborating signal:

- `.gitattributes` marks it generated or vendored.
- Files contain generated markers.
- The directory has a known package-manager structure.
- A small deterministic sample is overwhelmingly minified/binary/generated.

Sample perhaps the first eight sorted files, capped at 4 KiB each. If corroboration fails, classify individual files instead of excluding the directory.

2. Read nested `.gitattributes`

Horos currently consults only the repository-root `.gitattributes`, capped at 4 KiB. Git attributes are directory-scoped, so this can miss authoritative classifications deeper in the tree.

Maintain an attribute-rule stack during the existing recursive walk. These files are normally tiny, so a 64 KiB per-file cap would add little cost while improving correctness substantially.

3. Add a selective second sampling pass

Keep the existing 4 KiB prefix pass. For only large, still-unclassified files—say files above 64 KiB—read two additional 2 KiB windows from the middle and end.

This catches:

- generated notices occurring later;
- concatenated or minified content with an atypical header;
- large single-line blobs whose opening section is misleading.

The maximum becomes 8 KiB for unresolved large files, while most files remain metadata-only or 4 KiB reads.

4. Recognize file signatures

Checking the first 8–16 bytes for PNG, JPEG, ZIP, PDF, WebAssembly, fonts, and other common formats is nearly free and more reliable than depending on a null byte appearing within the prefix.

5. Separate hard exclusions from candidates

Use deterministic evidence grades:

- `hard`: exact lockfile name, Git attribute, binary signature, generated marker, valid sourcemap structure.
- `candidate`: directory name alone, filename convention, or geometry heuristic alone.

Only `hard` entries should bind agents. Put candidates in the report so maintainers can approve a repository-specific rule. This improves coverage without silently hiding questionable source.

6. Default to tracked files

For a committed boundary, scan Git-tracked files by default and offer `--include-untracked`. That avoids environment-specific caches and local build products contaminating the boundary, and often makes scanning faster.

I’d preserve the current safety rule: security reviews ignore the boundary entirely.

The resulting scan would still be `O(files)`, with a strict byte budget:

```text
metadata checks
    ↓
strong metadata match → boundary
    ↓
4 KiB prefix
    ↓
large unresolved candidate → two 2 KiB samples
    ↓
hard evidence → boundary
weak evidence → candidates report
no evidence → readable
```

The first change I’d make is nested `.gitattributes`; the second is corroborating whole-directory exclusions. Those offer the largest correctness improvement for the smallest compute increase.