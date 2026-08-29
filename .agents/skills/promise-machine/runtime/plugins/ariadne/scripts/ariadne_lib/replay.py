"""Re-run the deterministic half of a statement, and say what it did not run.

Gate 6 makes every command declare whether its output has to match byte for
byte. The declaration earns its place only if something acts on it, which is
what this does: the commands marked `exact` can be re-run and compared, and the
ones marked `nondeterministic` are listed as deliberately left alone. A fuzz
campaign that produced different coverage the second time has not failed.

The commands inside a statement are somebody else's data. They are not
instructions to this tool, so nothing runs without `--allow-execution`, nothing
runs through a shell, and four shapes are refused outright:

- A command whose arguments were redacted at capture. What is left is a
  different command, and running it while calling it a replay would be a lie.
- A program name carrying a path separator or Windows drive prefix, which would
  let a statement point the replay at a binary sitting beside it.
- A known shell name, which would hand back what `shell=False` was avoiding.
- A Windows batch program, because the operating system may run `.bat` and
  `.cmd` files through a system shell even when Python was given `shell=False`.

None of that is a sandbox. Replay runs the program named, with the arguments
given, under the caller's own account. What it offers is that the choice is the
caller's and the plan is printed first. Plan lines escape untrusted control
characters, and an argv value the host cannot encode or start is a contained
failure rather than an exception from the reader.
"""

import ntpath
import subprocess

from . import core_predicate, digests, gates

DEFAULT_TIMEOUT = 900

REDACTION = "<redacted>"

RUN = "run"
SKIP_NONDETERMINISTIC = "not run: declared nondeterministic"
SKIP_REDACTED = "not run: arguments were redacted at capture"
SKIP_PATH = "not run: the program name carries a path separator or drive prefix"
SKIP_SHELL = "not run: the program is a shell, which is what shell=False avoids"
SKIP_BATCH = "not run: Windows batch programs invoke a system shell"
SKIP_MALFORMED = "not run: the command has no argv of strings"
SKIP_STATE_FIXTURE_V2 = (
    "not run: state-fixture/v2 replay is local-file verification only"
)

STATE_FIXTURE_V2 = "https://ariadne.wildcat.finance/state-fixture/v2"

SEPARATORS = ("/", "\\")
"""Both, whatever this platform uses. A statement captured on one system gets
the same answer replayed on another, which is the point of a portable
format."""

SHELL_NAMES = frozenset(
    {
        "ash",
        "bash",
        "csh",
        "dash",
        "elvish",
        "fish",
        "git-shell",
        "ksh",
        "ksh93",
        "lksh",
        "mksh",
        "nu",
        "oksh",
        "osh",
        "pdksh",
        "posh",
        "rbash",
        "sh",
        "tcsh",
        "xonsh",
        "yash",
        "zsh",
        "cmd",
        "command",
        "powershell",
        "powershell_ise",
        "pwsh",
        "pwsh-preview",
    }
)
WINDOWS_EXECUTABLE_SUFFIXES = (".com", ".exe")
SHELLS = SHELL_NAMES | frozenset(
    "%s%s" % (name, suffix)
    for name in SHELL_NAMES
    for suffix in WINDOWS_EXECUTABLE_SUFFIXES
)
"""Running a shell as the program would hand back exactly what `shell=False`
was avoiding. The portable set covers the common direct POSIX and Windows
spellings, including Windows executable extensions. This is still a guard
against direct shell names rather than a sandbox; see the module docstring."""

WINDOWS_BATCH_SUFFIXES = (".bat", ".cmd")


class Step(object):
    """One command and what replay intends to do about it."""

    def __init__(self, name, argv, action, output_digest=None):
        self.name = name
        self.argv = argv
        self.action = action
        self.output_digest = output_digest
        self.predicate_type = None
        self.build_command = None
        self.status = None
        self.compared = None
        self.detail = ""

    @property
    def runnable(self):
        return self.action == RUN

    def line(self):
        if self.action != RUN:
            line = "%s: %s" % (self.name, self.action)
        elif self.status is None:
            line = "%s: would run %s" % (self.name, " ".join(self.argv))
        else:
            outcome = "exit %s" % self.status
            if self.compared is True:
                outcome += ", output matches the recorded digest"
            elif self.compared is False:
                outcome += ", output does NOT match the recorded digest"
            else:
                outcome += ", not compared (%s)" % self.detail
            line = "%s: %s" % (self.name, outcome)
        return gates.one_line(line)

    def to_dict(self):
        return {
            "name": self.name,
            "argv": self.argv,
            "action": self.action,
            "status": self.status,
            "compared": self.compared,
            "detail": self.detail,
        }


def plan(statement):
    """What replay would do with each recorded command, and why."""
    steps = []
    predicate = statement.predicate if isinstance(statement.predicate, dict) else {}
    build = predicate.get("build")
    build_command = build.get("command") if isinstance(build, dict) else None
    commands = core_predicate.commands(statement.predicate) or []
    for index, command in enumerate(commands):
        name = core_predicate.label(command, index, "command")
        if statement.predicate_type == STATE_FIXTURE_V2:
            argv = command.get("argv", []) if isinstance(command, dict) else []
            steps.append(Step(name, argv, SKIP_STATE_FIXTURE_V2))
            continue
        if not isinstance(command, dict):
            steps.append(Step(name, [], SKIP_MALFORMED))
            continue
        argv = command.get("argv")
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(word, str) for word in argv)
        ):
            # A non-string argument would reach subprocess and raise there,
            # which is a crash rather than a refusal. Gate 6 refuses the same
            # shape, but replay does not get to assume the gates ran.
            steps.append(Step(name, [], SKIP_MALFORMED))
            continue
        if command.get("determinism") != "exact":
            steps.append(Step(name, argv, SKIP_NONDETERMINISTIC))
            continue
        if any(REDACTION in str(word) for word in argv):
            steps.append(Step(name, argv, SKIP_REDACTED))
            continue
        drive, _ = ntpath.splitdrive(argv[0])
        if drive or any(separator in argv[0] for separator in SEPARATORS):
            steps.append(Step(name, argv, SKIP_PATH))
            continue
        # Win32 filename lookup ignores trailing spaces and periods. Normalise
        # them before checking executable and batch suffixes so a plan cannot
        # disagree with the program family that Windows would start.
        # Case-insensitive filesystems can resolve compatibility case forms as
        # the same executable name.  APFS, for example, resolves long-s `ſh`
        # to `/bin/sh`; Unicode case folding closes that direct-shell spelling
        # without compatibility-normalising unrelated program names.
        program = argv[0].casefold().rstrip(" .")
        if program.endswith(WINDOWS_BATCH_SUFFIXES):
            steps.append(Step(name, argv, SKIP_BATCH))
            continue
        if program in SHELLS:
            steps.append(Step(name, argv, SKIP_SHELL))
            continue
        steps.append(Step(name, argv, RUN, command.get("output_digest")))
    for step in steps:
        step.predicate_type = statement.predicate_type
        step.build_command = build_command
    return steps


def execute(step, cwd, timeout=DEFAULT_TIMEOUT):
    """Run one step without a shell, capturing what it printed.

    `shell=False` is the whole point: a semicolon inside an argument reaches
    the program as a semicolon rather than as a second command.
    """
    try:
        finished = subprocess.run(  # noqa: S603  (no shell, argv is a list)
            step.argv,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except FileNotFoundError:
        step.status = "not found"
        step.detail = "%s is not on PATH" % step.argv[0]
        return step
    except subprocess.TimeoutExpired:
        step.status = "timed out"
        step.detail = "after %d seconds" % timeout
        return step
    except (OSError, ValueError) as error:
        # A parsed JSON string may contain a NUL or a Unicode value this host
        # cannot put into an OS argv. Those are hostile input failures, not a
        # reason for the replay reader to escape with an exception.
        step.status = "failed to start"
        step.detail = str(error)
        return step
    step.status = finished.returncode
    step.printed = finished.stdout + finished.stderr
    return step


def compare(step, recomputed):
    """Compare a step's recorded output digest against a recomputed one.

    `recomputed` is None when nothing knows how to recompute this command's
    output. That is reported rather than treated as a match: an unrunnable
    comparison is not a passing one.
    """
    if step.output_digest is None:
        step.detail = "the command records no output digest"
        return step
    if recomputed is None:
        step.detail = (
            "nothing here knows how to recompute this command's output digest"
        )
        return step
    step.compared = digests.agree(step.output_digest, recomputed)
    return step


class Result(object):
    def __init__(self, steps, execution_allowed):
        self.steps = steps
        self.execution_allowed = execution_allowed
        # Permission to execute is evidence of authority, not evidence that a
        # process ran. A skipped or failed-to-start plan must not set the
        # machine-readable execution claim merely because the flag was present.
        self.executed = any(
            isinstance(step.status, int) or step.status == "timed out"
            for step in steps
        )

    @property
    def ok(self):
        """True when nothing that ran came back wrong.

        A plan that ran nothing is not a failure. It is a plan.
        """
        for step in self.steps:
            if step.status not in (None, 0):
                return False
            if step.status == 0 and step.compared is not True:
                return False
            if step.compared is False:
                return False
        return True

    def lines(self):
        out = [step.line() for step in self.steps]
        if not self.execution_allowed:
            out.append(
                "nothing was run; pass --allow-execution to replay the exact "
                "commands above"
            )
        elif not self.executed:
            out.append("nothing was run; no eligible command started")
        return out

    def to_dict(self):
        return {
            "executionAllowed": self.execution_allowed,
            "executed": self.executed,
            "steps": [step.to_dict() for step in self.steps],
            "ok": self.ok,
        }


def replay(statement, allow_execution=False, cwd=None, recompute=None, timeout=DEFAULT_TIMEOUT):
    """Plan, and run the plan when the caller has asked for it.

    `recompute` is a callable taking a Step and returning a digest set, or None
    when this statement's output digests cannot be recomputed here.
    """
    steps = plan(statement)
    if not allow_execution:
        return Result(steps, False)
    for step in steps:
        if not step.runnable:
            continue
        execute(step, cwd, timeout)
        if step.status == 0:
            compare(step, recompute(step) if recompute else None)
    return Result(steps, True)
