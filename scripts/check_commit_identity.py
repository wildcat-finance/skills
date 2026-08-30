#!/usr/bin/env python3
"""Reject runtime-host attribution in one bounded pull-request commit range."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

import contributors


SCHEMA = "wildcat-commit-identity-check/v1"
SHA_RE = re.compile(r"\A(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
GITHUB_LOGIN_RE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})(?:\[bot\])?$"
)
IDENT_LINE_RE = re.compile(
    r"\A(?P<name>[^<>\x00-\x1f\x7f]{1,256}) "
    r"<(?P<email>[^<>\x00-\x20\x7f]{1,320})> "
    r"(?P<timestamp>-?[0-9]+) (?P<timezone>[+-][0-9]{4})\Z"
)
COAUTHOR_RE = re.compile(
    r"^Co-authored-by:\s*(?P<name>.+?)\s*<(?P<email>[^<>]+)>$",
    re.IGNORECASE,
)
HOST_BYLINE_RE = re.compile(
    r"(?:generated\s+(?:by|with)|(?:co-)?authored\s+by)\s+"
    r"(?:\[(?:claude(?: code)?|codex|chatgpt|copilot|gemini(?: code assist)?)\]"
    r"\([^\)]+\)|claude(?: code)?|codex|chatgpt|copilot|gemini(?: code assist)?)",
    re.IGNORECASE,
)

SHOGGOTH_NAME = "Shoggoth"
SHOGGOTH_EMAIL = "shoggoth@wildcat.finance"
COAUTHOR_TRAILER = "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>"
ORIGIN_TRAILER = "Wildcat-Origin: shoggoth"

COMMIT_COUNT_MAX = 1024
COMMIT_BYTES_MAX = 128 * 1024
COMMIT_TOTAL_BYTES_MAX = 8 * 1024 * 1024
GIT_OUTPUT_MAX = 256 * 1024
GIT_TIMEOUT_SECONDS = 10
COAUTHOR_COUNT_MAX = 32


class Refusal(Exception):
    """An identity result that must keep the required check red."""


def _repository_path(value: str) -> Path:
    """Accept one real, non-symlinked bare object database."""
    handed = os.path.abspath(value)
    resolved = os.path.realpath(handed)
    if handed != resolved:
        raise Refusal("candidate repository path contains a symlink")
    path = Path(resolved)
    try:
        mode = path.stat(follow_symlinks=False).st_mode
    except OSError as error:
        raise Refusal("candidate repository path cannot be read") from error
    if not stat.S_ISDIR(mode):
        raise Refusal("candidate repository path is not a directory")
    if (path / ".git").exists():
        raise Refusal("candidate repository is not bare")
    return path


def _git_environment() -> dict[str, str]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "LC_ALL": "C",
        }
    )
    return environment


def _git(
    repository: Path,
    arguments: list[str],
    label: str,
    *,
    output_max: int = GIT_OUTPUT_MAX,
    allowed_exits: frozenset[int] = frozenset({0}),
) -> tuple[int, bytes]:
    """Run one fixed, bounded metadata read against the bare repository."""
    try:
        completed = subprocess.run(
            ["git", f"--git-dir={repository}", *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
            env=_git_environment(),
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Refusal(f"{label} could not complete") from error
    if len(completed.stdout) > output_max or len(completed.stderr) > GIT_OUTPUT_MAX:
        raise Refusal(f"{label} exceeded its output ceiling")
    if completed.returncode not in allowed_exits:
        raise Refusal(f"{label} failed with exit {completed.returncode}")
    return completed.returncode, completed.stdout


def _one_line(repository: Path, arguments: list[str], label: str) -> str:
    _, raw = _git(repository, arguments, label, output_max=256)
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise Refusal(f"{label} returned non-ASCII output") from error
    value = text.rstrip("\n")
    if not value or "\n" in value or "\r" in value:
        raise Refusal(f"{label} returned a malformed value")
    return value


def _full_sha(value: str, label: str, object_format: str) -> str:
    if SHA_RE.fullmatch(value) is None:
        raise Refusal(f"{label} is not a full lowercase object identifier")
    expected = 40 if object_format == "sha1" else 64
    if len(value) != expected:
        raise Refusal(f"{label} does not match repository object format {object_format}")
    return value


def _commit_range(repository: Path, base: str, head: str) -> list[str]:
    exit_code, _ = _git(
        repository,
        ["merge-base", "--is-ancestor", base, head],
        "base ancestry check",
        output_max=0,
        allowed_exits=frozenset({0, 1}),
    )
    if exit_code != 0:
        raise Refusal("pull-request head does not contain the exact base commit")
    _, raw = _git(
        repository,
        [
            "rev-list",
            "--reverse",
            "--topo-order",
            f"--max-count={COMMIT_COUNT_MAX + 1}",
            f"{base}..{head}",
        ],
        "commit range read",
        output_max=(COMMIT_COUNT_MAX + 1) * 65,
    )
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise Refusal("commit range returned non-ASCII output") from error
    if not lines:
        raise Refusal("pull-request range contains no commit")
    if len(lines) > COMMIT_COUNT_MAX:
        raise Refusal(f"pull-request range exceeds {COMMIT_COUNT_MAX} commits")
    if len(lines) != len(set(lines)) or any(SHA_RE.fullmatch(line) is None for line in lines):
        raise Refusal("commit range returned malformed or duplicate object identifiers")
    return lines


def _commit_bytes(repository: Path, commit_sha: str) -> bytes:
    object_type = _one_line(
        repository, ["cat-file", "-t", commit_sha], f"commit {commit_sha} type"
    )
    if object_type != "commit":
        raise Refusal(f"object {commit_sha} is not a commit")
    size_text = _one_line(
        repository, ["cat-file", "-s", commit_sha], f"commit {commit_sha} size"
    )
    if re.fullmatch(r"(?:0|[1-9][0-9]*)", size_text) is None:
        raise Refusal(f"commit {commit_sha} size is malformed")
    size = int(size_text)
    if size > COMMIT_BYTES_MAX:
        raise Refusal(f"commit {commit_sha} exceeds {COMMIT_BYTES_MAX} bytes")
    _, data = _git(
        repository,
        ["cat-file", "commit", commit_sha],
        f"commit {commit_sha} read",
        output_max=COMMIT_BYTES_MAX,
    )
    if len(data) != size:
        raise Refusal(f"commit {commit_sha} changed during its bounded read")
    return data


def _identity(line: str, commit_sha: str, role: str) -> tuple[str, str]:
    match = IDENT_LINE_RE.fullmatch(line)
    if match is None:
        raise Refusal(f"commit {commit_sha} has malformed {role} identity")
    name = match.group("name").strip()
    email = match.group("email")
    if not name or name != match.group("name"):
        raise Refusal(f"commit {commit_sha} has malformed {role} identity")
    exact_shoggoth = name == SHOGGOTH_NAME and email == SHOGGOTH_EMAIL
    partial_shoggoth = (
        name.casefold() == SHOGGOTH_NAME.casefold()
        or email.casefold() == SHOGGOTH_EMAIL.casefold()
    )
    if partial_shoggoth and not exact_shoggoth:
        raise Refusal(f"commit {commit_sha} has ambiguous Shoggoth {role} identity")
    if contributors.is_host_identity(name, email):
        raise Refusal(f"commit {commit_sha} names a runtime host as {role}")
    return name, email


def _parsed_commit(data: bytes, commit_sha: str) -> tuple[tuple[str, str], tuple[str, str], str]:
    if b"\x00" in data or b"\r" in data:
        raise Refusal(f"commit {commit_sha} contains unsupported control bytes")
    try:
        header_bytes, message_bytes = data.split(b"\n\n", 1)
    except ValueError as error:
        raise Refusal(f"commit {commit_sha} has no header-message boundary") from error
    try:
        headers = header_bytes.decode("utf-8").splitlines()
        message = message_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Refusal(f"commit {commit_sha} identity or message is not UTF-8") from error
    authors = [line[7:] for line in headers if line.startswith("author ")]
    committers = [line[10:] for line in headers if line.startswith("committer ")]
    if len(authors) != 1 or len(committers) != 1:
        raise Refusal(f"commit {commit_sha} does not carry one author and one committer")
    return (
        _identity(authors[0], commit_sha, "author"),
        _identity(committers[0], commit_sha, "committer"),
        message,
    )


def _message_policy(message: str, commit_sha: str, author: tuple[str, str]) -> None:
    if HOST_BYLINE_RE.search(message):
        raise Refusal(f"commit {commit_sha} carries a runtime-host generated-by byline")
    coauthor_count = 0
    for line in message.splitlines():
        match = COAUTHOR_RE.fullmatch(line)
        if match is None:
            continue
        coauthor_count += 1
        if coauthor_count > COAUTHOR_COUNT_MAX:
            raise Refusal(
                f"commit {commit_sha} exceeds {COAUTHOR_COUNT_MAX} co-author trailers"
            )
        name, email = match.group("name"), match.group("email")
        if len(name) > 256 or len(email) > 320:
            raise Refusal(f"commit {commit_sha} has malformed co-author identity")
        if contributors.is_host_identity(name, email):
            raise Refusal(f"commit {commit_sha} names a runtime host as co-author")
        partial_shoggoth = (
            name.strip().casefold() == SHOGGOTH_NAME.casefold()
            or email.strip().casefold() == SHOGGOTH_EMAIL.casefold()
        )
        if partial_shoggoth and line != COAUTHOR_TRAILER:
            raise Refusal(f"commit {commit_sha} has ambiguous Shoggoth co-author identity")
    if author == (SHOGGOTH_NAME, SHOGGOTH_EMAIL):
        lines = message.splitlines()
        if lines.count(COAUTHOR_TRAILER) != 1:
            raise Refusal(
                f"commit {commit_sha} does not carry one exact Shoggoth co-author trailer"
            )
        if lines.count(ORIGIN_TRAILER) != 1:
            raise Refusal(
                f"commit {commit_sha} does not carry one exact Wildcat-Origin trailer"
            )


def evaluate(repository_value: str, base_value: str, head_value: str, login: str) -> dict:
    """Return one bounded success record or raise ``Refusal``."""
    repository = _repository_path(repository_value)
    bare = _one_line(
        repository,
        ["rev-parse", "--is-bare-repository"],
        "bare repository check",
    )
    if bare != "true":
        raise Refusal("candidate repository is not bare")
    shallow = _one_line(
        repository,
        ["rev-parse", "--is-shallow-repository"],
        "shallow repository check",
    )
    if shallow != "false":
        raise Refusal("candidate repository is shallow")
    object_format = _one_line(
        repository,
        ["rev-parse", "--show-object-format"],
        "object format read",
    )
    if object_format not in {"sha1", "sha256"}:
        raise Refusal("candidate repository uses an unsupported object format")
    base = _full_sha(base_value, "base SHA", object_format)
    head = _full_sha(head_value, "head SHA", object_format)
    if not isinstance(login, str):
        raise Refusal("pull-request login is malformed")
    if contributors.is_host_login(login):
        raise Refusal("pull request was opened by a runtime-host account")
    if GITHUB_LOGIN_RE.fullmatch(login) is None:
        raise Refusal("pull-request login is malformed")

    commits = _commit_range(repository, base, head)
    total_bytes = 0
    shoggoth_authors = 0
    for commit_sha in commits:
        data = _commit_bytes(repository, commit_sha)
        total_bytes += len(data)
        if total_bytes > COMMIT_TOTAL_BYTES_MAX:
            raise Refusal(
                f"pull-request commit objects exceed {COMMIT_TOTAL_BYTES_MAX} bytes"
            )
        author, _committer, message = _parsed_commit(data, commit_sha)
        _message_policy(message, commit_sha, author)
        if author == (SHOGGOTH_NAME, SHOGGOTH_EMAIL):
            shoggoth_authors += 1
    return {
        "schema": SCHEMA,
        "status": "passed",
        "base": base,
        "head": head,
        "pull_request_login": login,
        "commit_count": len(commits),
        "shoggoth_author_count": shoggoth_authors,
        "human_author_count": len(commits) - shoggoth_authors,
    }


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description="Reject runtime-host attribution in a pull-request commit range."
    )
    command.add_argument("--repository", required=True, help="bare Git object database")
    command.add_argument("--base", required=True, help="exact protected base SHA")
    command.add_argument("--head", required=True, help="exact pull-request head SHA")
    command.add_argument(
        "--pull-request-login", required=True, help="GitHub pull-request author login"
    )
    return command


def main(arguments: list[str] | None = None) -> int:
    options = parser().parse_args(arguments)
    try:
        result = evaluate(
            options.repository,
            options.base,
            options.head,
            options.pull_request_login,
        )
    except Refusal as error:
        print(f"identity: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
