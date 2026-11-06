#!/usr/bin/env python3
"""Fetch the protocol source this harness tests, at the commits its records pin.

The emitter files and their import closure belong to other repositories, so
this repository holds only their identity: the repository, the commit, and
each file's path, size and SHA-256. Two records exist. `PROVENANCE.json` pins
the V2 source for the default profile under `src/vendor/`, and
`v1/PROVENANCE.json` pins the V1 source for the `v1` profile under
`v1/src/vendor/`. This script materialises the files and refuses to leave one
whose bytes differ from its record.

    python3 fetch_protocol.py                              fetch every record over HTTPS, then verify
    python3 fetch_protocol.py --check                      verify what is already present
    python3 fetch_protocol.py --record R --from-git DIR    read one record from a local clone

A clone holds one repository, so `--from-git` needs `--record` naming the
record that clone serves.

Exit status: 0 when every recorded file is present with its recorded bytes,
1 when a file is missing, has the wrong size or digest, or cannot be fetched,
2 on a usage or record error.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RECORD = os.path.join(HERE, "PROVENANCE.json")
RECORDS = (RECORD, os.path.join(HERE, "v1", "PROVENANCE.json"))
ALLOWED_HOST = "raw.githubusercontent.com"
MAX_FILE_BYTES = 1024 * 1024
TIMEOUT_SECONDS = 30


class SourceError(Exception):
    """A recorded file could not be produced with its recorded bytes."""


def load_record(path=RECORD):
    with open(path, "rb") as fh:
        record = json.loads(fh.read().decode("utf-8"))
    destination = record["destination"].rstrip("/") + "/"
    for entry in record["files"]:
        relative = entry["path"]
        if os.path.isabs(relative) or ".." in relative.split("/"):
            raise ValueError(f"record path escapes the harness: {relative}")
        if not relative.startswith(destination):
            raise ValueError(f"record path is outside {destination}: {relative}")
    return record


def verify_bytes(entry, data):
    if len(data) != entry["bytes"]:
        raise SourceError(f"{entry['path']}: {len(data)} bytes, recorded {entry['bytes']}")
    digest = hashlib.sha256(data).hexdigest()
    if digest != entry["sha256"]:
        raise SourceError(f"{entry['path']}: sha256 {digest}, recorded {entry['sha256']}")


def from_https(record, entry):
    url = record["source_url_template"].format(
        repository=record["repository"],
        ref=record["ref"],
        upstream_path=urllib.parse.quote(entry["upstream_path"]),
    )
    if urllib.parse.urlsplit(url).hostname != ALLOWED_HOST:
        raise SourceError(f"{entry['path']}: source host is not {ALLOWED_HOST}")
    request = urllib.request.Request(url, headers={"User-Agent": "hexaemeron-harness-fetch"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # phylax: allow url: fixed host, pinned commit, digest-verified
        if urllib.parse.urlsplit(response.geturl()).hostname != ALLOWED_HOST:
            raise SourceError(f"{entry['path']}: redirected away from {ALLOWED_HOST}")
        data = response.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise SourceError(f"{entry['path']}: larger than {MAX_FILE_BYTES} bytes")
    return data


def from_git(record, entry, clone):
    result = subprocess.run(  # phylax: allow subprocess: fixed git argv, pinned ref
        ["git", "-C", clone, "show", f"{record['ref']}:{entry['upstream_path']}"],
        capture_output=True,
        timeout=TIMEOUT_SECONDS,
        check=False,
    )
    if result.returncode != 0:
        raise SourceError(f"{entry['path']}: git show failed in {clone}")
    return result.stdout


def write_atomically(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".fetch-")
    try:
        with os.fdopen(descriptor, "wb") as fh:
            fh.write(data)
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def check(record, root=HERE):
    problems = []
    for entry in record["files"]:
        path = os.path.join(root, entry["path"])
        try:
            with open(path, "rb") as fh:
                verify_bytes(entry, fh.read())
        except FileNotFoundError:
            problems.append(f"{entry['path']}: missing; run fetch_protocol.py")
        except SourceError as error:
            problems.append(str(error))
    return problems


def fetch(record, root=HERE, clone=None):
    for entry in record["files"]:
        path = os.path.join(root, entry["path"])
        data = from_git(record, entry, clone) if clone else from_https(record, entry)
        verify_bytes(entry, data)
        write_atomically(path, data)
    return check(record, root)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify files already present")
    mode.add_argument("--from-git", metavar="DIR", help="read from a local clone instead of HTTPS")
    parser.add_argument("--record", choices=[os.path.relpath(r, HERE) for r in RECORDS],
                        help="process only this record; required with --from-git")
    args = parser.parse_args(argv)
    if args.from_git and not args.record:
        parser.error("--from-git reads one repository; name its record with --record")
    paths = [os.path.join(HERE, args.record)] if args.record else list(RECORDS)
    try:
        records = [load_record(path) for path in paths]
    except (OSError, ValueError, KeyError) as error:
        print(f"fetch_protocol: unreadable record: {error}", file=sys.stderr)
        return 2
    failed = False
    for record in records:
        try:
            problems = check(record) if args.check else fetch(record, clone=args.from_git)
        except (OSError, SourceError, subprocess.SubprocessError) as error:
            print(f"fetch_protocol: {error}", file=sys.stderr)
            return 1
        for problem in problems:
            print(f"fetch_protocol: {problem}", file=sys.stderr)
        if problems:
            failed = True
            continue
        print(
            f"{len(record['files'])} files, {record['total_bytes']} bytes, "
            f"{record['repository']} at {record['ref']}: verified"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
