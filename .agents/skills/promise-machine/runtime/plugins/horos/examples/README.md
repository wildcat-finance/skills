# The Horos example

`fixture/` is a miniature repository holding one file per classifier rule
class across both evidence grades. Hard entries (they bind agents): a
signature-named font, a lockfile, a marker-generated file, a
sample-corroborated `dist/`, a package-manager-corroborated
`node_modules/`, a `.gitattributes`-vendored `lib/`, and a sourcemap.
Candidates (advisory, in `candidates.json`): a null-byte binary, an
uncorroborated `build/` walked file-by-file, a single-line blob, a minified
bundle, an SVG text asset, and a migration SQL file. Two hand-written
files, `src/app.py` and `build/util.py`, stay readable. Its committed boundary lives at
`fixture/.horos/boundary.json`.

Run everything from the repository root.

## Reproduce the boundary

```bash
python3 plugins/horos/skills/horos/scripts/horos.py scan plugins/horos/examples/fixture --json
```

prints the boundary document byte for byte as committed, and

```bash
python3 plugins/horos/skills/horos/scripts/horos.py check plugins/horos/examples/fixture
```

exits 0 with `boundary matches the tree`.

## The mutation that makes check fail

Delete the fixture's lockfile and the boundary no longer matches:

```bash
rm plugins/horos/examples/fixture/yarn.lock
python3 plugins/horos/skills/horos/scripts/horos.py check plugins/horos/examples/fixture
```

exits 1 and names the drift: `drift: yarn.lock: in the boundary but no longer
evidenced by the tree`. Restore it with `git checkout` afterwards. The same
failure fires in the other direction when a new sink appears that the
committed boundary lacks, which is the control against a boundary edited to
hide something.

## The census

```bash
python3 plugins/horos/skills/horos/scripts/horos.py scan plugins/horos/examples/fixture --census
```

prints one row per filetype (files, bytes, share, and the bytes already
inside the boundary), and with `--json` reproduces the committed
`fixture/.horos/census.json` byte for byte. The census shares the scan's
walk exactly, so it can never describe a different tree than the boundary
does.

## The skeleton map

```bash
python3 plugins/horos/skills/horos/scripts/horos.py map plugins/horos/examples/fixture/src/app.py
```

prints the module's skeleton instead of the module.
