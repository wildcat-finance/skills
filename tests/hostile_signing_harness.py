#!/usr/bin/env python3
"""The hostile signing configuration the disposable-fixture guard proves hostile.

A disposable git repository inherits the contributor's signing configuration
unless it declares otherwise, so fixture history gets signed with a real key: a
GPG contributor's suite stalls on a pinentry prompt, and an SSH contributor's
fixture commits come out signed with their own identity. Showing that a fixture
declines to sign needs a configuration that is genuinely hostile, meaning
signing on and a signing program that records the attempt and then refuses.

That configuration is written here, once. ``tests/test_disposable_fixture_signing.py``
imports this module and proves each arm hostile; ``--emit <dir>`` writes the same
files for a shell caller, so the configuration a later runbook step runs a whole
suite under is the one the guard proved. Three filenames are fixed --
``hostile.gitconfig``, ``hostile-signer`` and ``sentinel.log`` -- so a caller
names them without parsing any output.

The configuration has to arrive as ``GIT_CONFIG_GLOBAL``. The
``GIT_CONFIG_COUNT``/``GIT_CONFIG_KEY_n``/``GIT_CONFIG_VALUE_n`` triple carries
``git -c`` precedence, which outranks repository-local config, so a fixture that
declares the rule correctly still reaches the signer under it and the whole
exercise reads as a failure of the fix. ``GIT_CONFIG_PARAMETERS`` carries the
same precedence and arrives by a route nobody types: git converts its own
``-c`` into it and hands it to every process it spawns, so a suite launched
from inside ``git -c ... bisect run`` inherits it. Both are dropped.

Boundaries, per section 9 of the study. Everything written lands in the
directory the caller names. The signer body is fixed text with no interpolated
caller input, and it is never placed on ``PATH``: git reaches it only through a
config value written here. ``child_environment`` returns a copy for one child
process and never touches ``os.environ``, so a failure part way through a test
cannot leave the contributor's git pointed at a temporary file.
"""

from collections import namedtuple
from pathlib import Path
import argparse
import os
import sys

CONFIG_NAME = "hostile.gitconfig"
SIGNER_NAME = "hostile-signer"
SENTINEL_NAME = "sentinel.log"

OPENPGP = "openpgp"
SSH = "ssh"
UNSIGNED = "unsigned"
ARMS = (OPENPGP, SSH, UNSIGNED)

# The arm `--emit` writes, and therefore the arm a later step runs a suite
# under. The guard's negative control proves this one hostile by name.
EMITTED_ARM = OPENPGP

# Fixed body, no interpolation. The sentinel is found beside the script, so the
# only thing this program can be told is what git passes it as arguments, and a
# guard that builds its own hostile directory records into that directory rather
# than into an outer one a suite is already running under.
SIGNER_BODY = """#!/bin/sh
printf '%s\\n' "hostile signer reached: $*" >> "$(dirname "$0")/sentinel.log"
exit 1
"""

# An identity, so that a fixture which sets none fails for the reason under test
# rather than because git cannot name the committer.
IDENTITY = (
    "[user]\n"
    "\tname = Hostile Inherited Contributor\n"
    "\temail = hostile@example.invalid\n"
)

ARM_TEMPLATES = {
    OPENPGP: IDENTITY + (
        "\tsigningkey = 0123456789ABCDEF\n"
        "[commit]\n"
        "\tgpgsign = true\n"
        "[gpg]\n"
        "\tformat = openpgp\n"
        "\tprogram = {program}\n"
    ),
    SSH: IDENTITY + (
        "\tsigningkey = ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHostileFixtureNotReal\n"
        "[commit]\n"
        "\tgpgsign = true\n"
        "[gpg]\n"
        "\tformat = ssh\n"
        '[gpg "ssh"]\n'
        "\tprogram = {program}\n"
    ),
    # The control: the same signer wired in, signing off. A commit here must
    # succeed and leave the sentinel empty, which is what shows the sentinel
    # records signing attempts rather than commits.
    UNSIGNED: IDENTITY + (
        "[commit]\n"
        "\tgpgsign = false\n"
        "[gpg]\n"
        "\tformat = openpgp\n"
        "\tprogram = {program}\n"
    ),
}

# Git exports these into every process it spawns -- a hook, `git bisect run`, a
# rebase `exec` line -- and any one of them points a fixture's git at the outer
# checkout instead of its own temporary directory. The last two carry `git -c`
# precedence, which outranks repository-local config and would defeat the
# declaration this harness exists to test: GIT_CONFIG_COUNT leads the triple a
# caller sets by hand, and GIT_CONFIG_PARAMETERS is the form git itself hands a
# child after `git -c`. Measured against git 2.54.0: either one carrying
# commit.gpgsign=true reaches the signer from a fixture that declared the rule
# correctly. All are dropped rather than overridden, so an unset one cannot
# fall through. GIT_CONFIG_KEY_n and GIT_CONFIG_VALUE_n are inert once the
# count that introduces them is gone.
REPOINTING_VARIABLES = (
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_WORK_TREE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
    "GIT_PREFIX",
    "GIT_INTERNAL_SUPER_PREFIX",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS",
)

HostileFiles = namedtuple("HostileFiles", ("config", "signer", "sentinel"))


def quoted(value):
    """One git-config value, quoted so a path with a space or a slash survives."""
    if any(character in value for character in "\r\n\x00"):
        raise ValueError("a hostile-configuration path cannot contain a newline or NUL")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def config_text(arm, signer):
    """The git configuration for one arm, pointed at the signer at that path."""
    if arm not in ARM_TEMPLATES:
        raise ValueError(f"unknown hostile arm: {arm}")
    return ARM_TEMPLATES[arm].format(program=quoted(str(signer)))


def write_arm(directory, arm):
    """Write one arm's configuration, signer and empty sentinel into a directory.

    The directory must already exist. Returns the three absolute paths under the
    three fixed names.
    """
    root = Path(directory).resolve()
    signer = root / SIGNER_NAME
    config = root / CONFIG_NAME
    sentinel = root / SENTINEL_NAME
    signer.write_text(SIGNER_BODY, encoding="utf-8")
    signer.chmod(0o700)
    config.write_text(config_text(arm, signer), encoding="utf-8")
    sentinel.write_text("", encoding="utf-8")
    return HostileFiles(config=config, signer=signer, sentinel=sentinel)


def child_environment(config, base=None):
    """The environment for one child process, with git's own configuration replaced.

    A copy is returned. Nothing here writes to ``os.environ``.
    """
    environment = dict(os.environ if base is None else base)
    for name in REPOINTING_VARIABLES:
        environment.pop(name, None)
    environment["GIT_CONFIG_GLOBAL"] = str(config)
    environment["GIT_CONFIG_SYSTEM"] = os.devnull
    return environment


def main(argv=None):
    """Write the emitted arm into the named directory, and say nothing."""
    parser = argparse.ArgumentParser(description="Write the hostile signing configuration.")
    parser.add_argument(
        "--emit",
        metavar="DIR",
        required=True,
        help="an existing directory to write the three fixed filenames into",
    )
    arguments = parser.parse_args(sys.argv[1:] if argv is None else argv)
    directory = Path(arguments.emit)
    if not directory.is_dir():
        parser.error(f"--emit needs an existing directory, not {arguments.emit}")
    write_arm(directory, EMITTED_ARM)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
