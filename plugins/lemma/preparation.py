#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Prepare captured Solidity inputs without changing retained source content."""
from __future__ import annotations

import argparse
import copy
import fnmatch
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import tempfile
import time

MAX_INPUT = 32 * 1024 * 1024
MAX_OUTPUT = 64 * 1024 * 1024
MAX_ARTIFACT = 128 * 1024 * 1024
MAX_NODES = 1_000_000
MAX_SOURCES = 10_000
MAX_DEPTH = 128
MAX_ROUNDS = 64
DEADLINE = 180


class Refusal(ValueError):
    """A stable category, without captured source or private diagnostics."""


def require(condition, category):
    if not condition:
        raise Refusal(category)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(document):
    return (json.dumps(document, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def decode(raw, limit=MAX_INPUT):
    """Reject duplicate keys, nonfinite numbers, excessive size and nesting."""
    require(isinstance(raw, bytes) and len(raw) <= limit, "json-size")
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, "json-duplicate-key")
            result[key] = value
        return result
    def constant(_):
        raise Refusal("json-nonfinite")
    try:
        result = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                            parse_constant=constant)
    except Refusal:
        raise
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise Refusal("json-invalid") from exc
    pending, visited = [(result, 0)], 0
    while pending:
        value, depth = pending.pop()
        visited += 1
        require(visited <= MAX_NODES and depth <= MAX_DEPTH, "json-complexity")
        if isinstance(value, dict):
            pending.extend((x, depth + 1) for x in value.values())
            pending.extend((key, depth + 1) for key in value)
        elif isinstance(value, list):
            pending.extend((x, depth + 1) for x in value)
        elif type(value) is float:
            require(math.isfinite(value), "json-nonfinite")
        elif isinstance(value, str):
            try:
                value.encode("utf-8")
            except UnicodeError as exc:
                raise Refusal("json-unicode") from exc
    return result


def closed(value, keys, category):
    require(type(value) is dict and set(value) == set(keys.split()), category)


def text(value, category):
    require(type(value) is str and 0 < len(value.encode()) <= 4096
            and all(ord(c) >= 32 and ord(c) != 127 for c in value), category)
    return value


def canonical(value):
    text(value, "source-path")
    require(not value.startswith("/") and "\\" not in value and ":" not in value
            and value == value.strip() and all(p not in ("", ".", "..")
                                               for p in value.split("/")), "source-path")
    return value


def pin(value):
    closed(value, "path sha256", "pin-fields")
    text(value["path"], "pin-path")
    require(type(value["sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", value["sha256"]) is not None,
            "pin-digest")


def read_regular(path, limit=MAX_INPUT):
    """Open every path component without following links; require stable bytes."""
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, "file-path")
    directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                              dir_fd=directory)
            os.close(directory)
            directory = next_fd
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=directory)
        try:
            before = os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, "file-type")
            require(before.st_size <= limit, "file-size")
            with os.fdopen(os.dup(fd), "rb") as stream:
                raw = stream.read(limit + 1)
            after = os.fstat(fd)
            named = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
            fields = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            require(fields(before) == fields(after) == fields(named)
                    and len(raw) == before.st_size, "file-changed")
            return raw
        finally:
            os.close(fd)
    except OSError as exc:
        raise Refusal("file-unavailable") from exc
    finally:
        os.close(directory)


def read_pin(value, root, limit=MAX_INPUT):
    pin(value)
    relative = canonical(value["path"])
    raw = read_regular(Path(root) / relative, limit)
    require(digest(raw) == value["sha256"], "pin-mismatch")
    return raw


def request_document(request):
    closed(request, "schema input compiler target transforms selection", "request-fields")
    require(request["schema"] == "lemma-preparation-request/v1", "request-schema")
    pin(request["input"])
    compiler = request["compiler"]
    closed(compiler, "runtime driver artifact version", "compiler-fields")
    for key in ("runtime", "driver", "artifact"):
        pin(compiler[key])
    require(type(compiler["version"]) is str and re.fullmatch(
        r"0\.[0-9]+\.[0-9]+\+commit\.[0-9a-f]{8}(?:\.Emscripten\.clang)?",
        compiler["version"]), "compiler-version")
    closed(request["target"], "source contract", "target-fields")
    text(request["target"]["source"], "target-source")
    require(type(request["target"]["contract"]) is str and re.fullmatch(
        r"[A-Za-z_$][A-Za-z0-9_$]*", request["target"]["contract"]), "target-contract")
    transforms = request["transforms"]
    closed(transforms, "metadata_target target_closure source_map remappings", "transform-fields")
    require(type(transforms["metadata_target"]) is bool
            and type(transforms["target_closure"]) is bool, "transform-boolean")
    require(type(transforms["source_map"]) is dict
            and len(transforms["source_map"]) <= MAX_SOURCES, "map-shape")
    require(type(transforms["remappings"]) is list
            and len(transforms["remappings"]) <= MAX_SOURCES, "remapping-shape")
    selection = request["selection"]
    closed(selection, "include exclude", "selection-fields")
    for key in ("include", "exclude"):
        require(type(selection[key]) is list and len(selection[key]) <= MAX_SOURCES,
                "selection-shape")
        for pattern in selection[key]:
            canonical(pattern)
        require(len(selection[key]) == len(set(selection[key])), "selection-duplicate")
    require(bool(selection["include"]), "selection-empty")
    return request


def source_document(raw):
    document = decode(raw)
    require(type(document) is dict and set(document) <= {"language", "sources", "settings"}
            and document.get("language") == "Solidity", "input-fields")
    sources = document.get("sources")
    require(type(sources) is dict and 0 < len(sources) <= MAX_SOURCES, "source-count")
    for key, value in sources.items():
        text(key, "source-key")
        closed(value, "content", "source-fields")
        require(type(value["content"]) is str, "source-content")
    require(type(document.get("settings", {})) is dict, "settings-shape")
    return document


def remapping(value):
    text(value, "remapping-value")
    require(value.count("=") == 1, "remapping-value")
    left, target = value.split("=")
    require(left and target and left.count(":") <= 1, "remapping-value")
    context, prefix = left.split(":") if ":" in left else ("", left)
    require(prefix and "\\" not in value, "remapping-value")
    return context, prefix, target


def map_sources(document, mapping, remappings):
    original = document["sources"]
    if not mapping:
        require(not remappings, "remapping-without-map")
        for key in original:
            canonical(key)
        return {key: key for key in original}
    require(set(mapping) == set(original), "map-domain")
    for key, value in mapping.items():
        text(key, "map-key")
        canonical(value)
    require(len(set(mapping.values())) == len(mapping), "map-collision")
    old = document.get("settings", {}).get("remappings", [])
    require(type(old) is list and len(old) == len(remappings), "remapping-count")
    new = []
    for before, row in zip(old, remappings):
        closed(row, "original prepared", "remapping-fields")
        require(row["original"] == before, "remapping-original")
        context, prefix, target = remapping(before)
        mapped_context, mapped_prefix, mapped_target = remapping(row["prepared"])
        require(prefix == mapped_prefix and bool(context) == bool(mapped_context),
                "remapping-prefix")
        canonical(mapped_target.rstrip("/"))
        if mapped_context:
            canonical(mapped_context.rstrip("/"))
        # Every affected retained key must commute with the declared prefix map.
        for source, prepared in mapping.items():
            if source.startswith(target):
                require(prepared == mapped_target + source[len(target):], "remapping-target")
            if context and source.startswith(context):
                require(prepared.startswith(mapped_context), "remapping-context")
        new.append(row["prepared"])
    document["sources"] = {mapping[k]: v for k, v in original.items()}
    document.setdefault("settings", {})["remappings"] = new
    return mapping


def checked_output(output):
    require(type(output) is dict, "compiler-output")
    errors = output.get("errors", [])
    require(type(errors) is list and all(type(e) is dict for e in errors), "compiler-errors")
    require(not any(e.get("severity") == "error" for e in errors), "compiler-refused")
    require(type(output.get("sources")) is dict, "compiler-sources")
    return output


def target_exists(output, source, contract):
    entry = output["sources"].get(source, {})
    nodes = entry.get("ast", {}).get("nodes", [])
    require(type(nodes) is list, "target-ast")
    found = [n for n in nodes if type(n) is dict and n.get("nodeType") == "ContractDefinition"
             and n.get("name") == contract]
    require(len(found) == 1, "target-missing-or-ambiguous")


def closure(document, target, compile_input):
    selected = {target["source"]}
    graph = {}
    for _ in range(MAX_ROUNDS):
        query = copy.deepcopy(document)
        query.setdefault("settings", {})["outputSelection"] = {
            path: {"": ["ast"], "*": ["abi"]} for path in sorted(selected)}
        output = checked_output(compile_input(query))
        require(set(output["sources"]) <= set(document["sources"]), "closure-extra-source")
        found = set(selected)
        for path in sorted(selected):
            entry = output["sources"].get(path)
            require(type(entry) is dict and type(entry.get("ast")) is dict, "closure-missing-ast")
            nodes = entry["ast"].get("nodes")
            require(type(nodes) is list, "closure-nodes")
            edges = []
            for node in nodes:
                if type(node) is dict and node.get("nodeType") == "ImportDirective":
                    other, unit = node.get("absolutePath"), node.get("sourceUnit")
                    require(type(other) is str and other in document["sources"]
                            and type(unit) is int and unit >= 0, "closure-import")
                    edges.append((other, unit))
                    found.add(other)
            graph[path] = edges
        require(len(found) <= MAX_SOURCES, "closure-size")
        if found == selected:
            for edges in graph.values():
                for other, unit in edges:
                    require(output["sources"][other]["ast"].get("id") == unit,
                            "closure-edge")
            target_exists(output, target["source"], target["contract"])
            return sorted(selected)
        selected = found
    raise Refusal("closure-round-limit")


def _derive(raw, request, compile_input):
    """Return prepared bytes and manifest using only declared transformations.

    compile_input accepts one standard-JSON object and returns checked compiler
    JSON. The CLI supplies PinnedCompiler; tests replay retained compiler bytes.
    """
    request_document(request)
    require(digest(raw) == request["input"]["sha256"], "input-digest")
    document = source_document(raw)
    original = copy.deepcopy(document)
    target = copy.deepcopy(request["target"])
    require(target["source"] in document["sources"], "target-source-missing")
    transforms = request["transforms"]
    settings = document.setdefault("settings", {})
    metadata = settings.get("compilationTarget")
    if transforms["metadata_target"]:
        require(type(metadata) is dict and metadata == {target["source"]: target["contract"]},
                "metadata-target")
        del settings["compilationTarget"]
    else:
        require("compilationTarget" not in settings, "metadata-undeclared")
    transcripts = []
    transcript_bytes = 0
    def compile_record(query):
        nonlocal transcript_bytes
        output = compile_input(query)
        output_bytes = encode(output)
        decode(output_bytes, MAX_OUTPUT)
        transcript_bytes += len(encode(query)) + len(output_bytes)
        require(transcript_bytes <= MAX_ARTIFACT, "transcript-total-size")
        transcripts.append({"input": query, "output": output,
                            "input_sha256": digest(encode(query)),
                            "output_sha256": digest(encode(output))})
        return output
    map_sources(copy.deepcopy(document), transforms["source_map"], transforms["remappings"])
    original_graph = None
    if transforms["source_map"]:
        require(not transforms["target_closure"], "combined-map-closure-unsupported")
        query = copy.deepcopy(document)
        query["settings"]["outputSelection"] = {"*": {"": ["ast"], "*": ["abi"]}}
        original_graph = checked_output(compile_record(query))
    mapping = map_sources(document, transforms["source_map"], transforms["remappings"])
    target["source"] = mapping[target["source"]]
    if transforms["target_closure"]:
        retained = closure(document, target, compile_record)
        document["sources"] = {key: document["sources"][key] for key in retained}
    else:
        retained = sorted(document["sources"])
    # outputSelection names compiler work, independently of corpus selection.
    document["settings"]["outputSelection"] = {"*": {"": ["ast"], "*": ["abi"]}}
    output = checked_output(compile_record(copy.deepcopy(document)))
    require(set(output["sources"]) == set(document["sources"]), "compiler-source-set")
    target_exists(output, target["source"], target["contract"])
    if original_graph is not None:
        def edges(graph, path):
            nodes = graph["sources"][path]["ast"]["nodes"]
            found = []
            for node in nodes:
                if node.get("nodeType") == "ImportDirective":
                    other = node.get("absolutePath")
                    require(other in graph["sources"] and
                            graph["sources"][other]["ast"].get("id") == node.get("sourceUnit"),
                            "mapping-import-edge")
                    found.append((node.get("file"), other))
            return found
        require(set(original_graph["sources"]) == set(mapping), "mapping-original-sources")
        for original_path, mapped in mapping.items():
            require([(name, mapping[other]) for name, other in edges(original_graph, original_path)]
                    == edges(output, mapped), "mapping-import-changed")
    selected = set()
    selection = request["selection"]
    for pattern in selection["include"]:
        matches = {key for key in retained if fnmatch.fnmatchcase(key, pattern)}
        require(bool(matches), "include-unmatched")
        selected.update(matches)
    for pattern in selection["exclude"]:
        matches = {key for key in retained if fnmatch.fnmatchcase(key, pattern)}
        require(bool(matches), "exclude-unmatched")
        selected.difference_update(matches)
    require(bool(selected) and target["source"] in selected, "selection-target")
    reverse = {value: key for key, value in mapping.items()}
    source_rows = [{"original": reverse[key], "prepared": key,
                    "sha256": digest(original["sources"][reverse[key]]["content"].encode()),
                    "selected": key in selected} for key in retained]
    prepared = encode(document)
    manifest = {"schema": "lemma-preparation-manifest/v1", "request": request,
                "request_sha256": digest(encode(request)), "original_sha256": digest(raw),
                "prepared_sha256": digest(prepared), "target": target,
                "sources": source_rows, "reverse_map": reverse,
                "removed": sorted(set(mapping.values()) - set(retained)),
                "selected": sorted(selected), "excluded": sorted(set(retained) - selected),
                "transcripts": transcripts}
    require(len(encode(manifest)) <= MAX_ARTIFACT, "manifest-size")
    return prepared, manifest


def derive(raw, request, compile_input):
    """Derive one input; malformed compiler or request structures refuse."""
    try:
        return _derive(raw, request, compile_input)
    except (KeyError, IndexError, TypeError, AttributeError, RecursionError) as exc:
        raise Refusal("input-or-compiler-shape") from exc


def verify_manifest(raw, prepared, manifest):
    """Recompute every transform from the manifest's exact transcript sequence."""
    require(type(manifest) is dict and manifest.get("schema") == "lemma-preparation-manifest/v1",
            "manifest-schema")
    calls = manifest.get("transcripts")
    require(type(calls) is list and 0 < len(calls) <= MAX_ROUNDS + 1, "transcript-count")
    cursor = 0
    def replay(query):
        nonlocal cursor
        require(cursor < len(calls), "transcript-missing")
        call = calls[cursor]
        cursor += 1
        closed(call, "input output input_sha256 output_sha256", "transcript-fields")
        require(call["input"] == query and call["input_sha256"] == digest(encode(query))
                and call["output_sha256"] == digest(encode(call["output"])), "transcript-mismatch")
        return call["output"]
    expected, record = derive(raw, manifest.get("request"), replay)
    require(cursor == len(calls) and expected == prepared and record == manifest,
            "manifest-mismatch")
    return record


class PinnedCompiler:
    """Run pinned Node, heap-safe driver and soljson with bounded pipes."""
    def __init__(self, compiler, root):
        self.compiler, self.root = compiler, Path(root)
        self.argv = []
        for field in ("runtime", "driver", "artifact"):
            read_pin(compiler[field], root, MAX_ARTIFACT)
            self.argv.append(str(self.root / compiler[field]["path"]))
        version = self.run(b"", "--version").decode().strip().removeprefix("Version: ")
        require(version.removesuffix(".Emscripten.clang") ==
                compiler["version"].removesuffix(".Emscripten.clang"), "compiler-version-mismatch")

    def run(self, raw, mode):
        require(len(raw) <= MAX_INPUT, "compiler-input-size")
        require(all(hasattr(os, name) for name in
                    ("waitid", "P_PID", "WEXITED", "WNOWAIT", "WNOHANG", "CLD_EXITED")),
                "compiler-platform")
        with tempfile.TemporaryFile() as source:
            source.write(raw)
            source.seek(0)
            command = [*self.argv, mode]
            process = subprocess.Popen(command, stdin=source, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, env={"LANG": "C"},
                                       start_new_session=True)
            buffers = {process.stdout: bytearray(), process.stderr: bytearray()}
            deadline = time.monotonic() + DEADLINE
            exited_after_eof = False
            try:
                with selectors.DefaultSelector() as poll:
                    for stream in buffers:
                        os.set_blocking(stream.fileno(), False)
                        poll.register(stream, selectors.EVENT_READ)
                    while poll.get_map():
                        require(time.monotonic() < deadline, "compiler-timeout")
                        for key, _ in poll.select(min(0.1, max(0, deadline-time.monotonic()))):
                            block = os.read(key.fd, 65536)
                            if not block:
                                poll.unregister(key.fileobj)
                            else:
                                buffers[key.fileobj].extend(block)
                                require(sum(map(len, buffers.values())) <= MAX_OUTPUT, "compiler-output-size")
                    # Retain the leader until cleanup: reaping would release its
                    # PID before the process-group signal uses that identity.
                    while True:
                        result = os.waitid(os.P_PID, process.pid,
                                           os.WEXITED | os.WNOWAIT | os.WNOHANG)
                        if result is not None:
                            exited_after_eof = True
                            break
                        require(time.monotonic() < deadline, "compiler-timeout")
                        time.sleep(0.01)
                    require(result.si_code == os.CLD_EXITED and result.si_status == 0,
                            "compiler-process")
                    for field in ("runtime", "driver", "artifact"):
                        read_pin(self.compiler[field], self.root, MAX_ARTIFACT)
                    return bytes(buffers[process.stdout])
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise Refusal("compiler-process") from exc
            finally:
                try:
                    if not exited_after_eof:
                        # A running or unreaped child reserves the group identity.
                        # If another reaper took it, refuse without signalling.
                        require(process.returncode is None, "compiler-child-ownership")
                        try:
                            os.waitid(os.P_PID, process.pid,
                                      os.WEXITED | os.WNOWAIT | os.WNOHANG)
                        except ChildProcessError as exc:
                            raise Refusal("compiler-child-ownership") from exc
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    # EOF plus an observed exit needs only reaping. Darwin can
                    # refuse group signals when the unreaped leader is all that
                    # remains; descendants which detach are outside this runner.
                    process.wait()
                finally:
                    process.stdout.close()
                    process.stderr.close()

    def __call__(self, document):
        return decode(self.run(encode(document), "--standard-json"), MAX_OUTPUT)


def publish(destination, prepared, manifest):
    """Reserve a new directory; manifest is the final completion record.

    A write interruption preserves the incomplete directory for inspection.
    Existing destinations are refused before any write.
    """
    destination = Path(destination)
    require(destination.is_absolute() and ".." not in destination.parts, "output-path")
    # Open parents without symlinks before reserving the destination name.
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in destination.parts[1:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = next_fd
        os.mkdir(destination.name, mode=0o700, dir_fd=parent)
        directory = os.open(destination.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            for name, raw in (("prepared.json", prepared), ("manifest.json", encode(manifest))):
                fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=directory)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
            os.fsync(directory)
            require(os.stat(destination.name, dir_fd=parent, follow_symlinks=False).st_ino
                    == os.fstat(directory).st_ino, "output-moved")
        finally:
            os.close(directory)
        os.fsync(parent)
    except OSError as exc:
        raise Refusal("output-unavailable") from exc
    finally:
        os.close(parent)


def prepare(request_path, root, destination):
    """Validate pinned inputs, prepare, replay the manifest and publish once."""
    request = request_document(decode(read_regular(request_path)))
    raw = read_pin(request["input"], root)
    compiler = PinnedCompiler(request["compiler"], root)
    prepared, manifest = derive(raw, request, compiler)
    verify_manifest(raw, prepared, manifest)
    require(read_pin(request["input"], root) == raw, "input-changed")
    publish(destination, prepared, manifest)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        manifest = prepare(args.request, args.root, args.out)
    except (Refusal, OSError) as exc:
        print(json.dumps({"status": "refused", "category": str(exc) if isinstance(exc, Refusal)
                          else "filesystem"}))
        return 1
    print(json.dumps({"status": "prepared", "original_sha256": manifest["original_sha256"],
                      "prepared_sha256": manifest["prepared_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
