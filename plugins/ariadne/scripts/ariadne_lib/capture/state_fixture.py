"""Read a Lazarus fixture directory into a statement.

A capture reads what is already there rather than producing it, so what ends up in
the statement is what the fixture actually contains. Nothing here reaches a network,
and nothing here guesses.

The evidence counts are the point. They come from the manifest verbatim, because
Lazarus wrote them and Lazarus is the only thing that knows which of its records were
checked against the state root. Recomputing them here would mean reimplementing that
judgement from the files, and a capture that recomputed one and got a larger number
would upgrade recorded evidence into proved evidence -- the one thing Lazarus's own
skill forbids outright. So the counts are read, the manifest digest is checked, and a
manifest that disagrees with its own directory is refused rather than corrected.

What the caller supplies, and why the files cannot answer it:

- **The tool name.** The manifest carries a `tool_version` and does not name the
  tool that wrote it. Reading a Lazarus-shaped manifest and writing "lazarus" into
  the field gate 2 reads as the thing that made the fixture would be this capture
  asserting something nobody recorded. The version comes from the manifest, and a
  version supplied by the caller that disagrees with it is refused.
- **The command.** The argv that produced the fixture is not in the fixture.
- **A previous capture, or the reason there is none.** Same as every other predicate
  here: a first capture carries a null baseline and says why.

What the caller cannot supply:

- **Replay authority.** `reaches_network` and `canonical_chain_claim` are written
  false for both versions. Version 2 also writes `provider_independence_claim`
  false. Ariadne reaches no network, neither tool re-derives a chain, and source
  labels do not establish independent providers.
"""

import errno
import hashlib
import json
import os
import re
import stat
import tempfile
import unicodedata

from .. import digests, safejson
from ..predicates import state_fixture as predicate
from . import tree
from .tree import CaptureError, confined


class ComponentLimitError(CaptureError):
    """A stable component crossed the caller's pre-read byte ceiling."""


MANIFEST = "manifest.json"
HEADER = "header.json"

DIGEST = re.compile(r"^[0-9a-f]{64}$")
"""A sha256 digest as Lazarus writes one into a manifest: lowercase hex, no prefix."""

MAX_MANIFEST_BYTES = 4 * 1024 * 1024
"""A manifest listing a thousand components is a few hundred kilobytes. A cap keeps
a mistaken path from reading a multi-gigabyte file into memory to parse it."""

MAX_FIXTURE_BYTES_V2 = 2 * 1024 * 1024 * 1024
"""The aggregate component ceiling enforced by Lazarus manifest-v2.

The capture does not import Lazarus at runtime, so it repeats the public bound
beside the version mapping it consumes.  Checking the declared sum before a tree
walk keeps 1,024 individually valid components from expanding one capture into
as much as 512 GiB of reads.
"""

MANIFEST_REQUIRED = (
    "schema_version",
    "tool_version",
    "chain_id",
    "block",
    "components",
    "evidence_counts",
    "fixture_digest",
)
"""What this capture reads out of a manifest, which is a subset of what Lazarus's own
schema requires. `optional_failures` is required there and not read here, because
nothing in this predicate carries it."""

SCHEMA_VERSIONS = (1, 2)
"""The manifest versions with an exact, separately versioned predicate mapping."""

MAX_JSON_DEPTH = 64
"""Fixture JSON uses shallow objects and arrays. Refuse pathological nesting
before handing bytes to Python's recursive parser."""


class _DuplicateJSONKey(ValueError):
    """Internal marker that deliberately retains no attacker-chosen key."""


_HEADER_NOT_READ = object()


def predicate_for(version):
    """The exact statement contract for one supported manifest version."""
    if version == 1:
        return {
            "type": predicate.TYPE,
            "evidence_classes": predicate.EVIDENCE_CLASSES,
            "replay_fields": predicate.REPLAY_REQUIRED,
        }
    if version == 2:
        return {
            "type": predicate.V2.TYPE,
            "evidence_classes": predicate.V2.EVIDENCE_CLASSES,
            "replay_fields": predicate.V2.REPLAY_REQUIRED,
        }
    return None


def refuse_constant(token):
    """Refuse `NaN`, `Infinity` and `-Infinity`, which `json.loads` accepts.

    They are a Python extension rather than JSON, and every comparison against a
    `nan` is false including `!=`, so one reaching a count would be neither refused
    nor ordered.
    """
    raise CaptureError(
        "manifest carries %s, which is not JSON; every comparison against it is "
        "false, including one that would refuse it" % token
    )


def refuse_duplicate_keys(pairs):
    """Build one object only when every key occurs once."""
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise _DuplicateJSONKey()
        seen.add(key)
    return dict(pairs)


def parse_json(raw, what):
    """Parse bounded bytes without ambiguous keys or retained hostile context."""
    problem = None
    try:
        safejson.check_depth(raw, MAX_JSON_DEPTH)
        found = json.loads(
            raw.decode("utf-8"),
            parse_constant=refuse_constant,
            object_pairs_hook=refuse_duplicate_keys,
        )
    except _DuplicateJSONKey:
        problem = "has a duplicate key; two readers could choose different values"
    except UnicodeDecodeError as error:
        problem = "is not UTF-8 at byte %d" % error.start
    except CaptureError as error:
        # `refuse_constant` emits only one of JSON's three fixed extension names.
        problem = str(error)
    except safejson.InputError:
        problem = "is nested deeper than %d levels" % MAX_JSON_DEPTH
    except ValueError as error:
        line = getattr(error, "lineno", None)
        column = getattr(error, "colno", None)
        if isinstance(line, int) and isinstance(column, int):
            problem = "is not JSON at line %d column %d" % (line, column)
        else:
            problem = "is not JSON"
    if problem is not None:
        # Raised after every parser handler has ended. The rejected document is
        # not retained as an implicit exception context for a caller to log.
        raise CaptureError("%s %s" % (what, problem))
    if not isinstance(found, dict):
        raise CaptureError(
            "%s is a %s rather than an object" % (what, type(found).__name__)
        )
    return found


def _open_component(root, relative, what):
    """Open one fixture-relative file without following any path segment."""
    parts = relative.split("/")
    directory_flags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    current = None
    descriptor = None
    failure = None
    try:
        current = os.open(root, directory_flags)
        for part in parts[:-1]:
            following = os.open(part, directory_flags, dir_fd=current)
            os.close(current)
            current = following
        file_flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        descriptor = os.open(parts[-1], file_flags, dir_fd=current)
    except OSError as error:
        failure = error.errno
    finally:
        if current is not None:
            os.close(current)
    if descriptor is None:
        if failure in (errno.ELOOP, errno.ENOTDIR):
            raise CaptureError(
                "%s is a symlink or has a non-directory parent" % what
            )
        raise CaptureError("cannot read %s" % what)
    return descriptor


def read_component(root, relative, what, max_bytes, keep_bytes=False):
    """Digest one stable regular-file descriptor under a pre-read byte cap."""
    descriptor = _open_component(root, relative, what)
    problem = None
    error_type = CaptureError
    raw = bytearray() if keep_bytes else None
    digest = hashlib.sha256()
    size = 0
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            problem = "%s is not a regular file" % what
        elif before.st_size > max_bytes:
            error_type = ComponentLimitError
            problem = "%s is %d bytes, over the %d this capture will read" % (
                what,
                before.st_size,
                max_bytes,
            )
        else:
            with os.fdopen(descriptor, "rb", closefd=False) as handle:
                while size <= max_bytes:
                    block = handle.read(min(65536, max_bytes + 1 - size))
                    if not block:
                        break
                    size += len(block)
                    digest.update(block)
                    if raw is not None:
                        raw.extend(block)
            if size > max_bytes:
                error_type = ComponentLimitError
                problem = "%s grew past the %d byte cap while being read" % (
                    what,
                    max_bytes,
                )
            else:
                after = os.fstat(descriptor)
                before_state = (
                    before.st_size,
                    before.st_mtime_ns,
                    before.st_ctime_ns,
                )
                after_state = (
                    after.st_size,
                    after.st_mtime_ns,
                    after.st_ctime_ns,
                )
                if before_state != after_state or size != before.st_size:
                    problem = "%s changed while it was read" % what
    except OSError:
        error_type = CaptureError
        problem = "cannot read %s" % what
    finally:
        os.close(descriptor)
    if problem is not None:
        raise error_type(problem)
    return {"sha256": digest.hexdigest()}, size, bytes(raw) if raw is not None else None


def read_json(path, what):
    """One root-level fixture document, read through a stable descriptor."""
    root, relative = os.path.split(path)
    _, _, raw = read_component(
        root or ".", relative, what, MAX_MANIFEST_BYTES, keep_bytes=True
    )
    return parse_json(raw, what)


def quantity(value, what):
    """A hex quantity string from the wire, as the integer this predicate compares.

    `"0xc7da16" < "0x2"` is true, because that orders text. The predicate refuses the
    wire form for that reason, so the conversion happens here or not at all.
    """
    if not isinstance(value, str) or not value.startswith("0x"):
        raise CaptureError(
            "%s must be a 0x-prefixed hex quantity, got %r" % (what, value)
        )
    body = value[2:]
    if not body or not all(character in "0123456789abcdef" for character in body):
        raise CaptureError(
            "%s must be lowercase hex after the prefix, got %r" % (what, value)
        )
    if len(body) > 1 and body[0] == "0":
        # Lazarus's own schema refuses a leading zero, and two spellings of one
        # number would give two statements for one fixture.
        raise CaptureError(
            "%s has a leading zero, which is two spellings of one number: %r"
            % (what, value)
        )
    return int(body, 16)


def hash32(value, what):
    """A 32-byte hash, lowercased for the predicate and refused if it is unset.

    Lazarus accepts either case for a block hash and this predicate accepts only
    lowercase, because two spellings of one value compare unequal. Lowercasing here
    is a conversion between two things that are the same. The all-zero value is not
    lowercased into acceptability: it matches the shape and identifies nothing.
    """
    if not isinstance(value, str):
        raise CaptureError("%s must be a string, got %s" % (what, type(value).__name__))
    lowered = value.lower()
    if not predicate.hash32(lowered):
        raise CaptureError(
            "%s is not a 32-byte hash that identifies something: %r" % (what, value)
        )
    return lowered


def manifest_of(root):
    """The manifest, checked for the fields this capture reads."""
    path = os.path.join(root, MANIFEST)
    if not os.path.lexists(path):
        raise CaptureError(
            "fixture %s has no %s; a fixture directory is one Lazarus wrote"
            % (root, MANIFEST)
        )
    found = read_json(path, MANIFEST)
    absent = [field for field in MANIFEST_REQUIRED if field not in found]
    if absent:
        raise CaptureError("%s is missing %s" % (MANIFEST, ", ".join(absent)))
    # `True == 1` in Python, so a plain inequality let `"schema_version": true`
    # through the one check that refuses a manifest this capture cannot read. The
    # type is tested before the value.
    version = found["schema_version"]
    contract = predicate_for(version) if predicate.whole_number(version) else None
    if contract is None:
        raise CaptureError(
            "%s is schema_version %r and this capture reads only %s; an unknown "
            "manifest may spell evidence differently and is never upgraded"
            % (MANIFEST, version, " or ".join(str(item) for item in SCHEMA_VERSIONS))
        )
    if not isinstance(found["tool_version"], str) or not found["tool_version"].strip():
        raise CaptureError("%s tool_version names no version" % MANIFEST)
    # Required and unused, which needs saying. This capture does not compute a
    # fixture digest from Lazarus's, because that digest is over Lazarus's listing
    # by a method this tool has not reimplemented. The field is checked for shape
    # anyway: requiring a field and accepting any value for it is a presence test
    # that carries nothing, and it would let this capture call a document a Lazarus
    # manifest on the strength of a key holding `{"a": 1}`.
    if not isinstance(found["fixture_digest"], str) or not DIGEST.fullmatch(
        found["fixture_digest"]
    ):
        raise CaptureError(
            "%s fixture_digest is not a sha256 digest: %r; this capture does not use "
            "it and checks it, because a manifest that cannot carry one is not a "
            "manifest" % (MANIFEST, found["fixture_digest"])
        )
    if not isinstance(found["block"], dict):
        raise CaptureError("%s block must be an object" % MANIFEST)
    for field in ("number", "hash"):
        if field not in found["block"]:
            raise CaptureError("%s block is missing %s" % (MANIFEST, field))
    if not isinstance(found["components"], list) or not found["components"]:
        raise CaptureError("%s components must be a non-empty array" % MANIFEST)
    if version == 2:
        if len(found["components"]) > predicate.V2.MAX_FIXTURE_SUBJECTS:
            raise CaptureError(
                "%s carries %d components and state-fixture/v2 records at most %d"
                % (
                    MANIFEST,
                    len(found["components"]),
                    predicate.V2.MAX_FIXTURE_SUBJECTS,
                )
            )
        if "receipts_root" not in found:
            raise CaptureError("%s is missing receipts_root" % MANIFEST)
        found["receipts_root"] = hash32(
            found["receipts_root"], "%s receipts_root" % MANIFEST
        )
    return found


def state_root_of(root, header_bytes=_HEADER_NOT_READ):
    """The state root, from the header Lazarus captured.

    Absent is not fatal here. A capture that proved nothing against the trie has no
    use for a root, and the predicate's evidence check is what refuses a proof-backed
    count without one. Refusing here would refuse an honest fixture.
    """
    if header_bytes is _HEADER_NOT_READ:
        path = os.path.join(root, HEADER)
        if not os.path.lexists(path):
            return None
        header = read_json(path, HEADER)
    elif header_bytes is None:
        return None
    else:
        header = parse_json(header_bytes, HEADER)
    if "state_root" not in header:
        return None
    return hash32(header["state_root"], "%s state_root" % HEADER)


def evidence_of(manifest):
    """The versioned counts, read from the manifest and not recomputed.

    Recomputing one would mean deciding for Lazarus which of its records were checked
    against the state root, and a capture that decided a larger number would upgrade
    recorded evidence into proved evidence. Reading them keeps the judgement where it
    was made, and the predicate's own check is what refuses a count the pin cannot
    support.
    """
    counts = manifest["evidence_counts"]
    if not isinstance(counts, dict):
        raise CaptureError("%s evidence_counts must be an object" % MANIFEST)
    contract = predicate_for(manifest["schema_version"])
    classes = contract["evidence_classes"]
    unknown = sorted(set(counts) - set(classes))
    if unknown:
        raise CaptureError(
            "%s evidence_counts carries %s, which is not a class this predicate "
            "defines; a count in an unknown class is a count nobody can read"
            % (MANIFEST, ", ".join(unknown))
        )
    out = {}
    for name in classes:
        if name not in counts:
            raise CaptureError(
                "%s evidence_counts has no %s; a class left out reads as nothing of "
                "that kind rather than as nobody having said" % (MANIFEST, name)
            )
        value = counts[name]
        if not predicate.whole_number(value) or not 0 <= value <= predicate.MAX_COUNT:
            raise CaptureError(
                "%s evidence_counts %s must be a whole number of records from 0 to "
                "%d, got %r" % (MANIFEST, name, predicate.MAX_COUNT, value)
            )
        out[name] = value
    return out


def components_of(root, manifest):
    """One entry per component the manifest declares, checked against the directory.

    Both directions. A component the manifest declares and the directory lacks is a
    statement describing a file nobody has; a file the directory holds and the
    manifest does not declare is a file the fixture digest does not cover, which is
    the silent absence every other refusal here exists for.
    """
    declared = {}
    path_check = (
        predicate.usable_path_v2
        if manifest["schema_version"] == 2
        else predicate.usable_path
    )
    for index, entry in enumerate(manifest["components"]):
        label = "component %d" % (index + 1)
        if not isinstance(entry, dict):
            raise CaptureError("%s %s is not an object" % (MANIFEST, label))
        for field in ("path", "bytes", "sha256"):
            if field not in entry:
                raise CaptureError("%s %s is missing %s" % (MANIFEST, label, field))
        path = entry["path"]
        if not path_check(path):
            raise CaptureError(
                "%s %s path is not a fixture-relative path accepted by this "
                "manifest version" % (MANIFEST, label)
            )
        if path in declared:
            raise CaptureError(
                "%s declares %s twice; one file cannot carry two digests, and the "
                "fixture digest is over this listing" % (MANIFEST, path)
            )
        if (
            not predicate.whole_number(entry["bytes"])
            or not 0 <= entry["bytes"] <= predicate.MAX_BYTES
        ):
            raise CaptureError(
                "%s %s bytes must be a whole number from 0 to %d, got %r"
                % (MANIFEST, label, predicate.MAX_BYTES, entry["bytes"])
            )
        if (
            not isinstance(entry["sha256"], str)
            or not DIGEST.fullmatch(entry["sha256"])
        ):
            raise CaptureError(
                "%s %s sha256 must be a lowercase 32-byte digest"
                % (MANIFEST, label)
            )
        declared[path] = entry

    if manifest["schema_version"] == 2:
        total_bytes = sum(entry["bytes"] for entry in declared.values())
        if total_bytes > MAX_FIXTURE_BYTES_V2:
            raise CaptureError(
                "%s declares %d component bytes, over the %d-byte "
                "state-fixture/v2 capture limit"
                % (MANIFEST, total_bytes, MAX_FIXTURE_BYTES_V2)
            )

    present = dict(tree.files(root, "fixture"))
    missing = sorted(set(declared) - set(present))
    if missing:
        raise CaptureError(
            "%s declares %s, which the fixture does not hold"
            % (MANIFEST, ", ".join(missing))
        )
    # The manifest is one of the files, and it cannot list its own digest.
    undeclared = sorted(set(present) - set(declared) - {MANIFEST})
    if undeclared:
        raise CaptureError(
            "fixture holds %s, which %s does not declare; the fixture digest would "
            "not cover it and nothing would say so"
            % (", ".join(undeclared), MANIFEST)
        )

    out = []
    documents = {}
    for path in sorted(declared):
        entry = declared[path]
        # The manifest's count is both an integrity claim and the tightest safe
        # read bound.  Reading to the format-wide ceiling first would let a file
        # grow by hundreds of megabytes before the later size mismatch refused
        # it.  Header parsing keeps its smaller independent ceiling.
        limit = entry["bytes"]
        if path == HEADER:
            limit = min(limit, MAX_MANIFEST_BYTES)
        found, size, raw = read_component(
            root,
            path,
            "fixture component %s" % path,
            limit,
            keep_bytes=path == HEADER,
        )
        if found["sha256"] != entry["sha256"]:
            raise CaptureError(
                "%s says %s digests to %s and it digests to %s; a manifest that "
                "disagrees with its own directory is not a fixture this will "
                "describe" % (MANIFEST, path, entry["sha256"], found["sha256"])
            )
        if size != entry["bytes"]:
            raise CaptureError(
                "%s says %s is %d bytes and it is %d"
                % (MANIFEST, path, entry["bytes"], size)
            )
        out.append({"name": path, "path": path, "digest": found, "bytes": size})
        if raw is not None:
            documents[path] = raw
    return out, documents


def parameters_digest(parameters):
    """A digest over the parameters this capture was given, canonically serialised."""
    return digests.of_bytes(
        json.dumps(dict(parameters or {}), sort_keys=True).encode("utf-8")
    )


def bundle(entries):
    """One digest over the whole component listing.

    Both sides of a delta name this rather than one component's digest, because a
    comparison is about the fixture and not about its manifest.

    The manifest's own `fixture_digest` is not used for this. It is Lazarus's digest
    over Lazarus's listing, computed a way this tool has not reimplemented, and
    presenting it as the digest of what Ariadne read would be asserting a derivation
    nobody here performed.
    """
    return digests.of_bytes(
        json.dumps(
            [[entry["path"], entry["digest"]] for entry in entries], sort_keys=True
        ).encode("utf-8")
    )


def claim(name, subject, disposition, reason=None, detail=None):
    out = {"name": name, "subject": subject, "disposition": disposition}
    if reason:
        out["reason"] = reason
    if detail:
        out["detail"] = detail
    return out


def require_portable_v2(value, what):
    """Refuse a v2 machine-read identifier no portable reader can display."""
    if not predicate.portable_name_v2(value):
        raise CaptureError("%s must contain a portable graphic" % what)


def unique_subject_names_v2(entries, name):
    """Hold capture output to release-v2's normalised subject-name rule."""
    seen = set()
    for value in [entry["name"] for entry in entries] + [name]:
        settled = unicodedata.normalize("NFC", value)
        if settled in seen:
            raise CaptureError(
                "state-fixture/v2 statement subject names must be unique after "
                "Unicode normalisation"
            )
        seen.add(settled)


def capture(
    fixture,
    name,
    capture_tool,
    capture_command,
    capture_version=None,
    parameters=None,
    previous=None,
    previous_name=None,
    first_capture_reason=None,
):
    """A state-fixture statement, read from a Lazarus fixture directory on disk."""
    if not isinstance(capture_tool, str) or not capture_tool.strip():
        raise CaptureError(
            "--capture-tool is required; the manifest carries a version and does not "
            "name the tool that wrote it, and gate 2 reads this field as the thing "
            "that made the fixture"
        )
    if (
        not isinstance(capture_command, (list, tuple))
        or not capture_command
        or not all(isinstance(word, str) and word.strip() for word in capture_command)
    ):
        raise CaptureError(
            "--capture-command is required, as an argv nobody has to guess at"
        )
    if not isinstance(name, str) or not name.strip():
        raise CaptureError(
            "--name is required; it identifies the current side of the comparison "
            "and names the fixture among the statement's subjects"
        )
    if previous and (
        not isinstance(previous_name, str) or not previous_name.strip()
    ):
        raise CaptureError("--previous needs --previous-name to identify it")

    root = confined(fixture, "fixture")
    manifest = manifest_of(root)
    if capture_version is not None and capture_version != manifest["tool_version"]:
        raise CaptureError(
            "--capture-version says %r and %s says %r; the manifest is what the tool "
            "wrote" % (capture_version, MANIFEST, manifest["tool_version"])
        )

    if manifest["schema_version"] == 2:
        require_portable_v2(capture_tool, "--capture-tool")
        require_portable_v2(manifest["tool_version"], "%s tool_version" % MANIFEST)
        for word in capture_command:
            require_portable_v2(word, "--capture-command word")
        require_portable_v2(name, "--name")
        if previous:
            require_portable_v2(previous_name, "--previous-name")

    # Settle the manifest-only fields before traversing any component.  A
    # malformed pin or evidence count cannot justify spending the declared
    # component-read budget merely to reach the refusal later.
    chain_id = quantity(manifest["chain_id"], "%s chain_id" % MANIFEST)
    block_number = quantity(
        manifest["block"]["number"], "%s block number" % MANIFEST
    )
    block_hash = hash32(
        manifest["block"]["hash"], "%s block hash" % MANIFEST
    )
    evidence = evidence_of(manifest)
    contract = predicate_for(manifest["schema_version"])

    entries, documents = components_of(root, manifest)
    if manifest["schema_version"] == 2:
        unique_subject_names_v2(entries, name)
    current = bundle(entries)
    state_root = state_root_of(root, documents.get(HEADER))

    chain = {
        "chain_id": chain_id,
        "block_number": block_number,
        "block_hash": block_hash,
    }
    if state_root is not None:
        chain["state_root"] = state_root
    if manifest["schema_version"] == 2:
        chain["receipts_root"] = manifest["receipts_root"]

    if previous:
        previous_root = confined(previous, "previous fixture")
        if previous_root == root:
            raise CaptureError(
                "--previous is the same directory as --fixture; a comparison against "
                "itself records nothing"
            )
        previous_manifest = manifest_of(previous_root)
        if previous_manifest["schema_version"] != manifest["schema_version"]:
            raise CaptureError(
                "--previous is manifest-v%d and --fixture is manifest-v%d; "
                "cross-version comparisons are never upgraded implicitly"
                % (
                    previous_manifest["schema_version"],
                    manifest["schema_version"],
                )
            )
        previous_entries, _ = components_of(previous_root, previous_manifest)
        deltas = {
            "baseline": {
                "name": previous_name,
                "digest": bundle(previous_entries),
            },
            "current": {"name": name, "digest": current},
        }
    else:
        if not isinstance(first_capture_reason, str) or not first_capture_reason.strip():
            raise CaptureError(
                "a fixture with no --previous needs --first-capture-reason; a null "
                "baseline carries the reason there is nothing to compare against"
            )
        deltas = {
            "baseline": None,
            "current": {"name": name, "digest": current},
            "reason": first_capture_reason,
        }

    claims = [
        claim(
            "digest and byte count read from the component on disk",
            entry["digest"],
            "passed",
            detail={"path": entry["path"], "bytes": entry["bytes"]},
        )
        for entry in entries
    ]
    claims.append(
        claim(
            "evidence counts read from the manifest",
            current,
            "passed",
            detail=dict(evidence),
        )
    )
    if manifest["schema_version"] == 2:
        claims.extend(
            [
                claim(
                    "receipt-trie relations re-checked by this capture",
                    current,
                    "skipped",
                    reason=(
                        "this capture reads local manifest evidence and component "
                        "bytes; Lazarus verification owns receipt-trie proof"
                    ),
                ),
                claim(
                    "independent providers established",
                    current,
                    "skipped",
                    reason=(
                        "operator-chosen source labels do not establish provider "
                        "independence"
                    ),
                ),
                claim(
                    "transaction hash attributed by the receipt trie",
                    current,
                    "skipped",
                    reason=(
                        "transaction hashes are recorded RPC decorations outside "
                        "the consensus receipt and log-projection proof"
                    ),
                ),
            ]
        )
    if evidence[predicate.PROVED] and state_root is None:
        # Unreachable through the predicate, which refuses the statement, but the
        # claim is written before the statement is verified and a reader of the
        # capture's output should see why it will fail.
        claims.append(
            claim(
                "state proofs checked against the pinned root",
                current,
                "failed",
                reason=(
                    "the manifest counts proof-backed records and the fixture "
                    "carries no state root to have proved them against"
                ),
            )
        )
    else:
        claims.append(
            claim(
                "state proofs re-checked by this capture",
                current,
                "skipped",
                reason=(
                    "this capture reads what Lazarus recorded and does not re-verify "
                    "a trie proof; the counts come from the manifest and re-deriving "
                    "one would put a judgement in the statement that Ariadne did not "
                    "make"
                ),
            )
        )
    claims.append(
        claim(
            "the pinned block placed on the canonical chain",
            current,
            "skipped",
            reason=(
                "neither tool re-derives a chain, so whether this block is canonical "
                "is not established here"
            ),
        )
    )
    if previous:
        claims.append(
            claim(
                "component-level comparison against the baseline",
                current,
                "skipped",
                reason=(
                    "both sides are identified by digest and no per-component "
                    "difference is recorded, because naming one needs a component "
                    "identity across two captures that this tool does not have"
                ),
            )
        )

    replay = {field: False for field in contract["replay_fields"]}
    body = {
        "chain": chain,
        "capture": {
            "tool": capture_tool,
            "tool_version": manifest["tool_version"],
            "command": list(capture_command),
            "parameters_digest": parameters_digest(parameters),
        },
        "fixture_subjects": entries,
        "evidence": evidence,
        "replay": replay,
        "deltas": deltas,
        "claims": claims,
        "commands": [],
    }

    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {"name": entry["name"], "digest": entry["digest"]} for entry in entries
        ]
        + [{"name": name, "digest": current}],
        "predicateType": contract["type"],
        "predicate": body,
    }


def write(path, body):
    """Write a statement so a reader never sees half of one.

    The temporary file lands in the same directory so the replace is on one
    filesystem.
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=directory,
        prefix=".ariadne-",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, path)
    except BaseException:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise
