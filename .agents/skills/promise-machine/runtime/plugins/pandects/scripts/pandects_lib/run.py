"""A campaign, and the record of how it was searched.

A result without its settings is an anecdote. The corpus already refuses a
tolerance that does not name its arithmetic; a campaign that does not name its
engine, its configuration, its seed and the corpus it searched is the same
refusal at a different scale, and this is where it is written down.

The record is shaped as an `ariadne` command entry, so a campaign drops into a
release statement without translation. Shaped as, not built by: the two plugins
share no code, and `tests/test_search_record.py` pins the shape so a change on
either side is a failing test rather than a document nobody can verify.

An engine that did not run is absent. Not present with a null result, not
present with zero findings -- absent, because a reader counting entries is
counting engines that ran, and an empty result reads like a search that found
nothing.
"""

import hashlib
import json
import os
import subprocess

#: The two classes ariadne's determinism gate allows.
EXACT = "exact"
NONDETERMINISTIC = "nondeterministic"

#: Every field an ariadne command entry may carry, and nothing else.
COMMAND_FIELDS = frozenset({"name", "argv", "determinism", "output_digest", "detail"})


class RunError(Exception):
    """A campaign that cannot be run, or a record that cannot be built."""


def strip_comments(source):
    """Source with comments removed and string literals left alone.

    The corpus digest has to change when a law changes and hold still when
    somebody rewrites a docstring, so comments come out. String literals stay
    in, because a law's `statement()` and every `detail` it returns are string
    literals, and those are the law.

    Written as a scan rather than a regex because the two cases interleave: a
    `//` inside a string is not a comment, and a quote inside a comment is not a
    string. A regex that took either side first gets the other one wrong.
    """
    out = []
    i, n = 0, len(source)
    while i < n:
        ch = source[i]
        if ch in '"\'':
            quote = ch
            out.append(ch)
            i += 1
            while i < n:
                out.append(source[i])
                if source[i] == "\\":
                    if i + 1 < n:
                        out.append(source[i + 1])
                        i += 2
                        continue
                elif source[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        if source.startswith("//", i):
            while i < n and source[i] != "\n":
                i += 1
            continue
        if source.startswith("/*", i):
            end = source.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        out.append(ch)
        i += 1
    lines = [line.rstrip() for line in "".join(out).split("\n")]
    return "\n".join(line for line in lines if line)


def digest_of(data):
    return {"sha256": hashlib.sha256(data).hexdigest()}


def corpus_digest(root, catalogue):
    """One digest over the catalogue, its law components and its specimens.

    Built from what the catalogue claims rather than from what is on disk, so a
    file nobody has filed cannot change the digest and a filed file that has
    gone missing raises rather than being skipped. `check` is what refuses an
    unfiled component; this only has to be honest about what it hashed.
    """
    parts = [json.dumps(catalogue.raw, sort_keys=True, separators=(",", ":")).encode("utf-8")]
    seen = set()
    for law in catalogue.laws:
        for field in ("component", "specimen"):
            relative = law.get(field)
            if not isinstance(relative, str) or relative in seen:
                continue
            seen.add(relative)
            path = os.path.join(root, relative)
            try:
                with open(path, "rb") as handle:
                    source = handle.read().decode("utf-8")
            except (OSError, UnicodeDecodeError) as error:
                raise RunError("cannot digest %s: %s" % (relative, error))
            parts.append(relative.encode("utf-8"))
            parts.append(strip_comments(source).encode("utf-8"))
    return digest_of(b"\x00".join(parts))


def command(name, argv, determinism, detail, output_digest=None):
    """One ariadne command entry, refused if it is not one.

    The checks here are the ones ariadne's determinism gate makes, made at the
    point of writing rather than at the point of verifying. A record that fails
    its own shape should never reach a statement.
    """
    if not isinstance(argv, list) or not argv or not all(isinstance(w, str) for w in argv):
        raise RunError("%s: argv must be a non-empty list of strings" % name)
    if determinism not in (EXACT, NONDETERMINISTIC):
        raise RunError(
            "%s: determinism must be %r or %r, not %r"
            % (name, EXACT, NONDETERMINISTIC, determinism)
        )
    entry = {
        "name": name,
        "argv": list(argv),
        "determinism": determinism,
        "detail": detail,
    }
    if determinism == EXACT:
        if not output_digest:
            raise RunError(
                "%s: an exact command needs an output digest; there would be "
                "nothing to compare a replay against" % name
            )
        entry["output_digest"] = output_digest
    elif output_digest is not None:
        entry["output_digest"] = output_digest
    unknown = sorted(set(entry) - COMMAND_FIELDS)
    if unknown:
        raise RunError("%s: unknown fields %s" % (name, ", ".join(unknown)))
    return entry


#: The section headings Foundry accepts for invariant settings. Both are in use
#: in the wild, and a reader that knew only one would report an empty
#: configuration for half the projects it met.
INVARIANT_SECTIONS = ("invariant", "profile.default.invariant")


def foundry_settings(root):
    """The invariant settings the campaign actually ran under.

    Read from `foundry.toml` rather than restated here, so a record cannot
    describe a configuration nobody used.

    An empty result is refused rather than returned. A record carrying
    `"configuration": {}` says the campaign ran under no settings, when what
    happened is that nobody could read them -- and the whole point of the record
    is that a search which cannot be described is not reported as one.
    """
    path = os.path.join(root, "foundry.toml")
    settings = {}
    section = None
    try:
        with open(path) as handle:
            for line in handle:
                line = line.split("#", 1)[0].strip()
                if line.startswith("[") and line.endswith("]"):
                    section = line[1:-1].strip()
                    continue
                if section not in INVARIANT_SECTIONS or "=" not in line:
                    continue
                key, value = (part.strip() for part in line.split("=", 1))
                settings[key] = value
    except OSError as error:
        raise RunError("cannot read foundry.toml: %s" % error)
    if not settings:
        raise RunError(
            "foundry.toml declares no invariant settings under %s; a record "
            "with an empty configuration would claim the campaign ran under "
            "none" % " or ".join("[%s]" % s for s in INVARIANT_SECTIONS)
        )
    return settings


def run_foundry(root, match=None, timeout=1800):
    """Run the Foundry campaign and return what happened.

    Returns None only when the engine is not there to run: no `forge` on the
    path, or the operating system refusing to start it. That is what makes an
    engine absent from a record rather than present and empty.

    A timeout is not that. The engine ran, searched for as long as it was
    given, and was killed; reporting it as absent would hide a campaign that
    happened, and reporting it as passed would be worse. It comes back with an
    outcome of its own.
    """
    argv = ["forge", "test"]
    if match:
        argv += ["--match-contract", match]
    try:
        finished = subprocess.run(
            argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as expired:
        return {
            "argv": argv,
            "returncode": None,
            "timed_out_after": timeout,
            "output": (expired.output or b"").decode("utf-8", "replace"),
        }
    except (OSError, subprocess.SubprocessError):
        return None
    return {
        "argv": argv,
        "returncode": finished.returncode,
        "output": finished.stdout.decode("utf-8", "replace"),
    }


def engine_version(argv, timeout=60):
    try:
        finished = subprocess.run(
            argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if finished.returncode != 0:
        return None
    return finished.stdout.decode("utf-8", "replace").strip().split("\n")[0]


def outcome_of(result):
    """What happened, in three words rather than two.

    A campaign that was killed part way through neither passed nor failed. It
    searched less than it was asked to, and a reader deciding whether to trust
    the result needs that in the record rather than folded into either verdict.
    """
    if result.get("returncode") is None:
        return "timed out"
    return "passed" if result["returncode"] == 0 else "failed"


def foundry_record(root, catalogue, result, seed=None):
    """The command entry for a Foundry campaign that ran."""
    settings = foundry_settings(root)
    detail = {
        "engine": "foundry",
        "configuration": settings,
        "sequence_length": settings.get("depth"),
        "corpus_digest": corpus_digest(root, catalogue),
        "laws_searched": len(catalogue.laws),
        "outcome": outcome_of(result),
    }
    if result.get("timed_out_after") is not None:
        detail["timed_out_after_seconds"] = result["timed_out_after"]
    # Two fields, one rule: what nobody could read is absent, never null. A
    # `"seed": null` says the run had no seed when what is true is that Foundry
    # does not report the one it used, and an `"engine_version": null` says the
    # same thing about a binary that would not answer. Absent asks a reader to
    # go and find out; null tells them there is nothing to find.
    version = engine_version(["forge", "--version"])
    if version is not None:
        detail["engine_version"] = version
    if seed is not None:
        detail["seed"] = seed
    return command(
        "fuzz campaign: foundry invariant",
        result["argv"],
        NONDETERMINISTIC,
        detail,
    )


def search_record(root, catalogue, match=None, seed=None):
    """Every engine that ran, and no entry for any that did not."""
    commands = []
    result = run_foundry(root, match=match)
    if result is not None:
        commands.append(foundry_record(root, catalogue, result, seed=seed))
    return {
        "corpus": {
            "version": catalogue.version,
            "laws": len(catalogue.laws),
            "digest": corpus_digest(root, catalogue),
        },
        "commands": commands,
    }
