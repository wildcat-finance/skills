#!/usr/bin/env python3
"""Phylax boundary lint.

The mechanical subset of the skill: the rules a parser can settle without
reading intent. Everything else in SKILL.md stays a judgement.

  P001  a shell invocation, which invites a command built from data
  P002  a subprocess command passed as a string rather than an argument list
  P003  a requirement with no exact pin
  P004  a credential in source, command arguments, or output
  P005  raw HTML reaches a renderer without a later trusted sanitiser
  P006  a session credential reaches persisted browser storage
  P007  a runtime-selected absolute fetch host has no prior allowlist check
  P008  unsafe deserialization or non-literal dynamic execution

Exit 0 clean, 1 findings, 2 bad invocation.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from lib.typescript_lexer import lex  # noqa: E402

RUNNERS = {"run", "call", "check_call", "check_output", "Popen"}
WRITERS = {"print", "debug", "info", "warning", "warn", "error", "critical", "exception"}
BOUNDARY_CALLS = {
    "pickle": frozenset({"load", "loads"}),
    "marshal": frozenset({"load"}),
    "yaml": frozenset({"load"}),
    "builtins": frozenset({"eval", "exec"}),
}
SAFE_YAML_LOADERS = frozenset({"SafeLoader", "CSafeLoader"})
LOCAL_RESOLUTION_MAX_DEPTH = 8
P008_MESSAGES = {
    "pickle": "pickle deserialization may execute untrusted code",
    "marshal": "marshal deserialization accepts untrusted data",
    "yaml": "yaml.load has no resolved SafeLoader or CSafeLoader",
    "builtins": "dynamic execution receives non-literal source",
}
P008_AMBIGUOUS_MESSAGE = (
    "source-local bindings leave the boundary call family unresolved"
)

CREDENTIAL = re.compile(
    r"(?:^|_)(?:priv(?:ate)?_?key|secret|passwd|password|mnemonic|seed_?phrase"
    r"|api_?key|access_?token|auth_?token|bearer|credential)s?(?:_|$)",
    re.IGNORECASE,
)
# A value that is plainly not a live credential.
PLACEHOLDER = re.compile(r"^(?:|x{3,}|\.{3}|<[^>]*>|\{[^}]*\}|\$\{?[A-Z_]+\}?|changeme|todo)$", re.I)
PIN = re.compile(r"(==|@(?:git\+)?[0-9a-f]{40})")
SKIP_REQ = re.compile(r"^\s*(?:#|-r\s|--|$)")


ALLOW = re.compile(r"(?:#|//)\s*phylax:\s*allow\s+(?P<reason>\S.*)$")

IDENTIFIER = r"[A-Za-z_$][\w$]*"
SESSION_MARKER = re.compile(
    rf"(?<![\w$])(?:session[_-]?token|auth[_-]?token|access[_-]?token|jwt|bearer)(?![\w$])",
    re.IGNORECASE,
)
RAW_HTML_MARKER = re.compile(r"(?:raw|html|markdown|content)", re.IGNORECASE)
TRUSTED_DIRECT_SANITISERS = frozenset(
    {"sanitize-html", "dompurify", "isomorphic-dompurify"}
)
TYPESCRIPT_MAX_BYTES = 1024 * 1024


def suppressed(text: str, line: int) -> bool:
    """True when the finding's line, or the one above it, states a reason."""
    lines = text.splitlines()
    for number in (line, line - 1):
        if 1 <= number <= len(lines) and ALLOW.search(lines[number - 1]):
            return True
    return False


class Finding:
    __slots__ = ("path", "line", "code", "message")

    def __init__(self, path: Path, line: int, code: str, message: str) -> None:
        self.path, self.line, self.code, self.message = path, line, code, message

    def as_dict(self) -> dict:
        return {"path": str(self.path), "line": self.line, "code": self.code,
                "message": self.message}

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.message}"


def _attr_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _is_str_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _is_formatted(node: ast.AST) -> bool:
    """A string built at runtime rather than written out whole.

    `a + b` is only string building when one side is plainly a string.
    Concatenating two lists to assemble an argument list is the correct
    construction, and flagging it teaches people to ignore the tool.
    """
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        return any(_is_str_literal(side) or isinstance(side, ast.JoinedStr)
                   for side in (node.left, node.right))
    if isinstance(node, ast.Call) and _attr_name(node.func) in {"format", "join"}:
        return True
    return False


def _is_string(node: ast.AST) -> bool:
    return _is_str_literal(node) or _is_formatted(node)


def _is_dynamic_literal(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (str, bytes))
    )


def _position(node: ast.AST) -> tuple[int, int]:
    return (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))


class _FunctionBindings:
    """Eligible direct assignments in one exact function body."""

    def __init__(
        self,
        assignments: dict[str, tuple[tuple[int, int], ast.AST]],
    ) -> None:
        self.assignments = assignments

    def preceding(
        self,
        name: str,
        before: tuple[int, int],
    ) -> tuple[tuple[int, int], ast.AST] | None:
        assignment = self.assignments.get(name)
        if assignment is None or assignment[0] >= before:
            return None
        return assignment


class _FunctionBindingCollector(ast.NodeVisitor):
    """Collect one exact function without borrowing bindings from nested scopes."""

    def __init__(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.candidates: dict[str, tuple[tuple[int, int], ast.AST]] = {}
        self.binding_counts: dict[str, int] = {}
        arguments = node.args
        for argument in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        ):
            self._bind(argument.arg)
        if arguments.vararg is not None:
            self._bind(arguments.vararg.arg)
        if arguments.kwarg is not None:
            self._bind(arguments.kwarg.arg)
        for parameter in getattr(node, "type_params", ()):
            self._bind(parameter.name)

        for statement in node.body:
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                self.candidates[statement.targets[0].id] = (
                    _position(statement),
                    statement.value,
                )
            elif (
                isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
                and statement.value is not None
            ):
                self.candidates[statement.target.id] = (
                    _position(statement),
                    statement.value,
                )
            self.visit(statement)
        self.bindings = _FunctionBindings({
            name: candidate
            for name, candidate in self.candidates.items()
            if self.binding_counts.get(name) == 1
        })

    def _bind(self, name: str) -> None:
        self.binding_counts[name] = self.binding_counts.get(name, 0) + 1

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self._bind(node.id)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._bind(alias.asname or alias.name.split(".", 1)[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name != "*":
                self._bind(alias.asname or alias.name)

    def visit_Global(self, node: ast.Global) -> None:
        for name in node.names:
            self._bind(name)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        for name in node.names:
            self._bind(name)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self._bind(node.name)
        self.generic_visit(node)

    def visit_MatchAs(self, node: ast.MatchAs) -> None:
        if node.name:
            self._bind(node.name)
        if node.pattern is not None:
            self.visit(node.pattern)

    def visit_MatchStar(self, node: ast.MatchStar) -> None:
        if node.name:
            self._bind(node.name)

    def visit_MatchMapping(self, node: ast.MatchMapping) -> None:
        if node.rest:
            self._bind(node.rest)
        self.generic_visit(node)

    def _visit_function_header(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda,
    ) -> None:
        arguments = node.args
        for argument in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        ):
            if argument.annotation is not None:
                self.visit(argument.annotation)
        if arguments.vararg is not None and arguments.vararg.annotation is not None:
            self.visit(arguments.vararg.annotation)
        if arguments.kwarg is not None and arguments.kwarg.annotation is not None:
            self.visit(arguments.kwarg.annotation)
        for default in (*arguments.defaults, *arguments.kw_defaults):
            if default is not None:
                self.visit(default)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._bind(node.name)
        for decorator in node.decorator_list:
            self.visit(decorator)
        self._visit_function_header(node)
        if node.returns is not None:
            self.visit(node.returns)
        for parameter in getattr(node, "type_params", ()):
            self.visit(parameter)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._bind(node.name)
        for expression in (
            *node.decorator_list,
            *node.bases,
            *(keyword.value for keyword in node.keywords),
            *getattr(node, "type_params", ()),
        ):
            self.visit(expression)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._visit_function_header(node)


def _function_bindings(tree: ast.AST) -> dict[ast.AST, _FunctionBindings]:
    return {
        node: _FunctionBindingCollector(node).bindings
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _boundary_bindings(
    tree: ast.AST,
) -> tuple[
    dict[str, set[str]],
    dict[str, set[str]],
    set[str],
    set[str],
    set[str],
]:
    """Collect source-local import evidence before descending function bodies.

    A depth-first visitor reaches a function's calls before module imports that
    follow its definition, even though those imports bind before normal calls.
    Conflicting imports remain conservative evidence because scope and runtime
    rebinding are outside this rule.
    """
    modules: dict[str, set[str]] = {}
    direct: dict[str, set[str]] = {}
    identities: dict[str, set[tuple[int, str | None, str]]] = {}
    imports = (
        node for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )
    for node in imports:
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".", 1)[0]
                identities.setdefault(local, set()).add((-1, alias.name, ""))
                if alias.name in BOUNDARY_CALLS:
                    modules.setdefault(local, set()).add(alias.name)
            continue

        for alias in node.names:
            if alias.name == "*":
                continue
            local = alias.asname or alias.name
            identities.setdefault(local, set()).add(
                (node.level, node.module, alias.name)
            )
            if node.level != 0 or node.module not in BOUNDARY_CALLS:
                continue
            if alias.name in BOUNDARY_CALLS[node.module]:
                direct.setdefault(local, set()).add(node.module)

    safe_yaml_modules = {
        local
        for local, imported in identities.items()
        if all(
            level == -1 and module == "yaml"
            for level, module, _name in imported
        )
    }
    safe_yaml_loaders = {
        local
        for local, imported in identities.items()
        if all(
            level == 0 and module == "yaml" and name in SAFE_YAML_LOADERS
            for level, module, name in imported
        )
    }
    ambiguous_calls = set()
    for local, imported in identities.items():
        families = set()
        for level, module, name in imported:
            if level == -1 and module in BOUNDARY_CALLS:
                families.add(module)
            elif (
                level == 0
                and module in BOUNDARY_CALLS
                and name in BOUNDARY_CALLS[module]
            ):
                families.add(module)
            else:
                families.add(None)
        # a direct import elsewhere in the file does not prove that it shadows
        # a bare built-in at this call site; scope analysis is outside P008.
        if local in BOUNDARY_CALLS["builtins"]:
            families.add("builtins")
        if len(families) > 1:
            ambiguous_calls.add(local)
    return (
        modules,
        direct,
        safe_yaml_modules,
        safe_yaml_loaders,
        ambiguous_calls,
    )


class Visitor(ast.NodeVisitor):
    """Flag only calls resolved by the source-local import grammar.

    A broad terminal-name match is worthless here: ordinary `.load`, `.loads`,
    `run` and `.call` methods must stay outside the rule that owns each name.
    """

    def __init__(self, path: Path, tree: ast.AST) -> None:
        self.path = path
        self.findings: list[Finding] = []
        self.modules: set[str] = set()
        self.direct: set[str] = set()
        self.function_bindings = _function_bindings(tree)
        self.local_bindings: _FunctionBindings | None = None
        (
            self.boundary_modules,
            self.boundary_direct,
            self.safe_yaml_modules,
            self.safe_yaml_loaders,
            self.ambiguous_boundary_calls,
        ) = _boundary_bindings(tree)

    def _visit_function_header(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda,
    ) -> None:
        arguments = node.args
        for argument in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        ):
            if argument.annotation is not None:
                self.visit(argument.annotation)
        if arguments.vararg is not None and arguments.vararg.annotation is not None:
            self.visit(arguments.vararg.annotation)
        if arguments.kwarg is not None and arguments.kwarg.annotation is not None:
            self.visit(arguments.kwarg.annotation)
        for default in (*arguments.defaults, *arguments.kw_defaults):
            if default is not None:
                self.visit(default)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        self._visit_function_header(node)
        if node.returns is not None:
            self.visit(node.returns)
        for parameter in getattr(node, "type_params", ()):
            self.visit(parameter)

        previous = self.local_bindings
        self.local_bindings = self.function_bindings[node]
        try:
            for statement in node.body:
                self.visit(statement)
        finally:
            self.local_bindings = previous

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for expression in (
            *node.decorator_list,
            *node.bases,
            *(keyword.value for keyword in node.keywords),
            *getattr(node, "type_params", ()),
        ):
            self.visit(expression)
        previous = self.local_bindings
        self.local_bindings = None
        try:
            for statement in node.body:
                self.visit(statement)
        finally:
            self.local_bindings = previous

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._visit_function_header(node)
        previous = self.local_bindings
        self.local_bindings = None
        try:
            self.visit(node.body)
        finally:
            self.local_bindings = previous

    def _visit_comprehension_scope(self, node: ast.AST) -> None:
        previous = self.local_bindings
        self.local_bindings = None
        try:
            self.generic_visit(node)
        finally:
            self.local_bindings = previous

    visit_ListComp = _visit_comprehension_scope
    visit_SetComp = _visit_comprehension_scope
    visit_DictComp = _visit_comprehension_scope
    visit_GeneratorExp = _visit_comprehension_scope

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "subprocess":
                self.modules.add(alias.asname or "subprocess")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "subprocess":
            for alias in node.names:
                if alias.name in RUNNERS:
                    self.direct.add(alias.asname or alias.name)
        self.generic_visit(node)

    def _starts_process(self, func: ast.AST) -> bool:
        if isinstance(func, ast.Attribute):
            base = func.value
            return (isinstance(base, ast.Name) and base.id in self.modules
                    and func.attr in RUNNERS)
        return isinstance(func, ast.Name) and func.id in self.direct

    def _resolve_local(
        self,
        node: ast.AST,
        *,
        before: tuple[int, int] | None = None,
        seen: frozenset[str] = frozenset(),
        depth: int = 0,
    ) -> ast.AST:
        if self.local_bindings is None or not isinstance(node, ast.Name):
            return node
        if depth >= LOCAL_RESOLUTION_MAX_DEPTH or node.id in seen:
            return node
        assignment = self.local_bindings.preceding(
            node.id,
            before if before is not None else _position(node),
        )
        if assignment is None:
            return node
        position, value = assignment
        return self._resolve_local(
            value,
            before=position,
            seen=seen | {node.id},
            depth=depth + 1,
        )

    def _credential_names(
        self,
        node: ast.AST,
        *,
        before: tuple[int, int] | None = None,
        seen: frozenset[str] = frozenset(),
        depth: int = 0,
    ):
        if isinstance(node, ast.Name):
            if CREDENTIAL.search(node.id):
                yield node.id
                return
            if (
                self.local_bindings is None
                or depth >= LOCAL_RESOLUTION_MAX_DEPTH
                or node.id in seen
            ):
                return
            assignment = self.local_bindings.preceding(
                node.id,
                before if before is not None else _position(node),
            )
            if assignment is None:
                return
            position, value = assignment
            yield from self._credential_names(
                value,
                before=position,
                seen=seen | {node.id},
                depth=depth + 1,
            )
            return
        for child in ast.iter_child_nodes(node):
            yield from self._credential_names(
                child,
                before=before,
                seen=seen,
                depth=depth,
            )

    def _add(self, node: ast.AST, code: str, message: str) -> None:
        self.findings.append(Finding(self.path, node.lineno, code, message))

    def _boundary_modules(self, func: ast.AST) -> set[str]:
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            return {
                module
                for module in self.boundary_modules.get(func.value.id, set())
                if func.attr in BOUNDARY_CALLS[module]
            }
        if isinstance(func, ast.Name):
            resolved = set(self.boundary_direct.get(func.id, set()))
            if func.id in BOUNDARY_CALLS["builtins"]:
                resolved.add("builtins")
            return resolved
        return set()

    def _safe_yaml_loader(self, loader: ast.AST) -> bool:
        if isinstance(loader, ast.Attribute) and isinstance(loader.value, ast.Name):
            return (
                loader.value.id in self.safe_yaml_modules
                and loader.attr in SAFE_YAML_LOADERS
            )
        return isinstance(loader, ast.Name) and loader.id in self.safe_yaml_loaders

    def _check_p008(self, node: ast.Call) -> None:
        function = self._resolve_local(node.func)
        binding = (
            function.value.id
            if isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            else function.id if isinstance(function, ast.Name) else None
        )
        loader = next(
            (keyword.value for keyword in node.keywords if keyword.arg == "Loader"),
            node.args[1] if len(node.args) > 1 else None,
        )
        if loader is not None:
            loader = self._resolve_local(loader)
        dynamic_source = self._resolve_local(node.args[0]) if node.args else None
        for module in sorted(self._boundary_modules(function)):
            if module == "yaml":
                if loader is not None and self._safe_yaml_loader(loader):
                    continue
            elif module == "builtins":
                if dynamic_source is None or _is_dynamic_literal(dynamic_source):
                    continue
            message = (
                P008_AMBIGUOUS_MESSAGE
                if binding in self.ambiguous_boundary_calls
                else P008_MESSAGES[module]
            )
            self._add(node, "P008", message)
            return

    def visit_Call(self, node: ast.Call) -> None:
        self._check_p008(node)
        if self._starts_process(node.func):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self._add(node, "P001", "shell invocation; pass an argument list instead")
            command = node.args[0] if node.args else next(
                (kw.value for kw in node.keywords if kw.arg == "args"), None
            )
            resolved_command = (
                self._resolve_local(command) if command is not None else None
            )
            if resolved_command is not None and _is_string(resolved_command):
                built = (
                    " built by formatting" if _is_formatted(resolved_command) else ""
                )
                self._add(node, "P002", f"command passed as a string{built}; pass a list")
            if command is not None:
                for name in self._credential_names(command):
                    self._add(
                        node,
                        "P004",
                        f"credential-named value `{name}` passed in command arguments",
                    )

        if _attr_name(node.func) in WRITERS:
            for arg in node.args + [kw.value for kw in node.keywords]:
                if isinstance(arg, ast.Name) and CREDENTIAL.search(arg.id):
                    self._add(node, "P004", f"credential-named value `{arg.id}` written to output")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            if not PLACEHOLDER.match(node.value.value):
                for target in node.targets:
                    label = _attr_name(target)
                    if label and CREDENTIAL.search(label):
                        self._add(node, "P004", f"credential `{label}` assigned a literal")
        self.generic_visit(node)


def check_python(path: Path, text: str) -> list[Finding]:
    try:
        tree = ast.parse(text)
    except SyntaxError as err:
        return [Finding(path, err.lineno or 1, "P000", f"could not parse: {err.msg}")]
    visitor = Visitor(path, tree)
    visitor.visit(tree)
    return visitor.findings


def check_requirements(path: Path, text: str) -> list[Finding]:
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        if SKIP_REQ.match(line):
            continue
        if not PIN.search(line.split("#", 1)[0]):
            findings.append(Finding(path, number, "P003",
                                    f"requirement `{line.strip()}` has no exact pin"))
    return findings


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _masked(text: str, spans, *, keep_strings: bool = False) -> str:
    """Blank lexical non-code while preserving offsets and newlines."""
    parts = []
    for kind, start, end in spans:
        segment = text[start:end]
        if kind == "code" or (keep_strings and kind == "string"):
            parts.append(segment)
        else:
            parts.append("".join(ch if ch == "\n" else " " for ch in segment))
    return "".join(parts)


def _matching(mask: str, opening: int) -> int | None:
    pairs = {"(": ")", "[": "]", "{": "}"}
    if opening >= len(mask) or mask[opening] not in pairs:
        return None
    stack = [pairs[mask[opening]]]
    for index in range(opening + 1, len(mask)):
        current = mask[index]
        if current in pairs:
            stack.append(pairs[current])
        elif stack and current == stack[-1]:
            stack.pop()
            if not stack:
                return index
    return None


def _split_ranges(mask: str, start: int, end: int) -> list[tuple[int, int]]:
    """Split a comma list at lexical depth zero, retaining source offsets."""
    ranges = []
    stack = []
    pairs = {"(": ")", "[": "]", "{": "}"}
    item = start
    for index in range(start, end):
        current = mask[index]
        if current in pairs:
            stack.append(pairs[current])
        elif stack and current == stack[-1]:
            stack.pop()
        elif current == "," and not stack:
            ranges.append((item, index))
            item = index + 1
    ranges.append((item, end))
    return ranges


def _local_bindings(clause: str) -> set[str]:
    """Return local names from one TypeScript import clause."""
    bindings = set()
    clause = re.sub(r"\btype\s+", "", clause).strip()
    default = re.match(rf"({IDENTIFIER})(?:\s*,|$)", clause)
    if default:
        bindings.add(default.group(1))
    namespace = re.search(rf"\*\s+as\s+({IDENTIFIER})", clause)
    if namespace:
        bindings.add(namespace.group(1))
    named = re.search(r"\{(?P<body>[^}]*)\}", clause, re.DOTALL)
    if named:
        for item in named.group("body").split(","):
            words = re.findall(IDENTIFIER, item)
            if words:
                bindings.add(words[-1])
    return bindings


def _imports(mask_with_strings: str) -> dict[str, set[str]]:
    packages: dict[str, set[str]] = {}
    pattern = re.compile(
        r"\bimport\s+(?!['\"])(?P<clause>.{1,500}?)\s+from\s+"
        r"(?P<quote>['\"])(?P<package>[^'\"]+)(?P=quote)",
        re.DOTALL,
    )
    for match in pattern.finditer(mask_with_strings):
        clause = match.group("clause")
        if ";" in clause or len(clause.splitlines()) > 20:
            continue
        packages.setdefault(match.group("package"), set()).update(
            _local_bindings(clause)
        )
    return packages


def _trusted_sanitiser(expression: str, bindings: set[str]) -> bool:
    for binding in bindings:
        if re.search(rf"\b{re.escape(binding)}(?:\s*\.\s*sanitize)?\s*\(", expression):
            return True
    return False


def _check_raw_html(path: Path, text: str, mask: str,
                    imports: dict[str, set[str]]) -> list[Finding]:
    findings = []
    raw_bindings = imports.get("rehype-raw", set())
    clean_bindings = imports.get("rehype-sanitize", set())

    plugin_pattern = re.compile(r"\brehypePlugins\s*=\s*\{\s*\[")
    for match in plugin_pattern.finditer(mask):
        opening = mask.find("[", match.start(), match.end())
        closing = _matching(mask, opening)
        if closing is None:
            continue
        items = []
        for start, end in _split_ranges(mask, opening + 1, closing):
            item = mask[start:end].strip()
            name = re.match(IDENTIFIER, item)
            if name:
                items.append((name.group(0), start + mask[start:end].find(name.group(0))))
        for position, (name, offset) in enumerate(items):
            if name in raw_bindings and not any(
                later in clean_bindings for later, _ in items[position + 1:]
            ):
                findings.append(Finding(
                    path, _line_of(text, offset), "P005",
                    "raw HTML renderer has no later trusted sanitiser",
                ))

    direct_bindings = set()
    for package in TRUSTED_DIRECT_SANITISERS:
        direct_bindings.update(imports.get(package, set()))
    dangerous = re.compile(r"\bdangerouslySetInnerHTML\s*=\s*\{\s*\{\s*__html\s*:")
    for match in dangerous.finditer(mask):
        outer = mask.find("{", match.start(), match.end())
        inner = mask.find("{", outer + 1, match.end())
        closing = _matching(mask, inner)
        if closing is None:
            continue
        colon = mask.find(":", inner, match.end())
        expression = mask[colon + 1:closing]
        if RAW_HTML_MARKER.search(expression) and not _trusted_sanitiser(
            expression, direct_bindings
        ):
            findings.append(Finding(
                path, _line_of(text, match.start()), "P005",
                "raw HTML value is not passed through a trusted sanitiser",
            ))
    return findings


def _call_ranges(mask: str, binding: str):
    pattern = re.compile(rf"(?<![\w$.]){re.escape(binding)}\s*\(")
    for match in pattern.finditer(mask):
        opening = mask.find("(", match.start(), match.end())
        closing = _matching(mask, opening)
        if closing is not None:
            yield match.start(), opening, closing, _split_ranges(mask, opening + 1, closing)


def _assigned_object(mask: str, name: str, before: int) -> tuple[int, int] | None:
    pattern = re.compile(
        rf"\b(?:const|let|var)\s+{re.escape(name)}(?:\s*:[^=\n]+)?\s*=\s*\{{"
    )
    matches = [match for match in pattern.finditer(mask, 0, before)]
    if not matches:
        return None
    opening = mask.find("{", matches[-1].start(), matches[-1].end())
    closing = _matching(mask, opening)
    return (opening, closing + 1) if closing is not None else None


def _config_text(text: str, mask: str, start: int, end: int,
                 call_offset: int) -> tuple[str, str]:
    expression_mask = mask[start:end].strip()
    expression_text = text[start:end].strip()
    identifier = re.fullmatch(IDENTIFIER, expression_mask)
    if identifier:
        assigned = _assigned_object(mask, identifier.group(0), call_offset)
        if assigned:
            left, right = assigned
            return text[left:right], mask[left:right]
    return expression_text, expression_mask


def _array_property(text: str, mask: str, name: str) -> str | None:
    match = re.search(rf"\b{re.escape(name)}\s*:\s*\[", mask)
    if not match:
        return None
    opening = mask.find("[", match.start(), match.end())
    closing = _matching(mask, opening)
    return text[opening + 1:closing] if closing is not None else None


def _persist_excludes_sensitive(text: str, mask: str, sensitive: set[str],
                                source_mask: str) -> bool:
    blacklist = _array_property(text, mask, "blacklist")
    if blacklist is not None and any(
        re.search(rf"(?<![\w$]){re.escape(field)}(?![\w$])", blacklist, re.I)
        for field in sensitive
    ):
        return True
    whitelist = _array_property(text, mask, "whitelist")
    if whitelist is not None and not any(
        re.search(rf"(?<![\w$]){re.escape(field)}(?![\w$])", whitelist, re.I)
        for field in sensitive
    ):
        return True
    transforms = _array_property(text, mask, "transforms")
    if transforms is not None:
        for transform in re.findall(IDENTIFIER, transforms):
            declaration = re.search(
                rf"\b(?:const|let|var)\s+{re.escape(transform)}\s*=\s*"
                r"createTransform\s*\(",
                source_mask,
            )
            if not declaration:
                continue
            opening = source_mask.find("(", declaration.start(), declaration.end())
            closing = _matching(source_mask, opening)
            if closing is None:
                continue
            body = source_mask[opening + 1:closing]
            if "..." in body or "delete" in body:
                if any(re.search(
                    rf"(?<![\w$]){re.escape(field)}(?![\w$])", body, re.I
                ) for field in sensitive):
                    return True
    return False


def _sensitive_state_fields(mask: str) -> set[str]:
    fields = set()
    marker = r"(?:session[_-]?token|auth[_-]?token|access[_-]?token|jwt|bearer)"
    for pattern in (
        re.compile(rf"(?<![\w$])(?P<field>{marker})(?![\w$])\s*\??\s*:", re.I),
        re.compile(rf"\b(?:state|initialState)\s*\.\s*(?P<field>{marker})(?![\w$])", re.I),
    ):
        fields.update(match.group("field") for match in pattern.finditer(mask))
    return fields


def _check_persistence(path: Path, text: str, mask: str,
                       imports: dict[str, set[str]]) -> list[Finding]:
    findings = []
    storage = re.compile(
        r"(?<![\w$])(?:window\s*\.\s*)?(?:localStorage|sessionStorage)"
        r"\s*\.\s*setItem\s*\("
    )
    for match in storage.finditer(mask):
        opening = mask.find("(", match.start(), match.end())
        closing = _matching(mask, opening)
        if closing is None:
            continue
        arguments = _split_ranges(mask, opening + 1, closing)
        persisted = " ".join(text[start:end] for start, end in arguments[:2])
        if SESSION_MARKER.search(persisted):
            findings.append(Finding(
                path, _line_of(text, match.start()), "P006",
                "session credential written to persisted client storage",
            ))

    sensitive = _sensitive_state_fields(mask)
    for binding in imports.get("redux-persist", set()):
        if binding != "persistReducer" and "persist" not in binding.lower():
            continue
        for offset, _opening, _closing, arguments in _call_ranges(mask, binding):
            if not sensitive or not arguments:
                continue
            start, end = arguments[0]
            config_text, config_mask = _config_text(text, mask, start, end, offset)
            if not _persist_excludes_sensitive(
                config_text, config_mask, sensitive, mask
            ):
                findings.append(Finding(
                    path, _line_of(text, offset), "P006",
                    "session credential included in a persisted reducer",
                ))
    return findings


def _statement_expression(text: str, mask: str, start: int) -> tuple[str, str]:
    stack = []
    pairs = {"(": ")", "[": "]", "{": "}"}
    end = start
    while end < len(mask):
        current = mask[end]
        if current in pairs:
            stack.append(pairs[current])
        elif stack and current == stack[-1]:
            stack.pop()
        elif not stack and current in ";\n":
            break
        end += 1
    return text[start:end].strip(), mask[start:end].strip()


def _runtime_host(expression: str, expression_mask: str, text: str,
                  mask: str, before: int) -> str | None:
    template = re.search(
        rf"https?://\$\{{\s*(?P<host>{IDENTIFIER})\s*\}}", expression, re.I
    )
    if template:
        return template.group("host")
    new_url = re.search(
        rf"\bnew\s+URL\s*\([^,]+,\s*(?P<host>{IDENTIFIER})\s*\)",
        expression_mask,
        re.DOTALL,
    )
    if new_url and "window.location.origin" not in expression_mask:
        return new_url.group("host")
    reference = re.fullmatch(
        rf"(?P<name>{IDENTIFIER})(?:\s*\.\s*toString\s*\(\s*\))?",
        expression_mask.strip(),
    )
    if not reference:
        return None
    name = reference.group("name")
    assignment = re.compile(
        rf"\b(?:const|let|var)\s+{re.escape(name)}(?:\s*:[^=\n]+)?\s*=\s*"
    )
    matches = [match for match in assignment.finditer(mask, 0, before)]
    if not matches:
        return None
    value_text, value_mask = _statement_expression(text, mask, matches[-1].end())
    return _runtime_host(value_text, value_mask, text, mask, matches[-1].start())


def _scope_start(mask: str, offset: int) -> int:
    stack = []
    for index, current in enumerate(mask[:offset]):
        if current == "{":
            stack.append(index)
        elif current == "}" and stack:
            stack.pop()
    for opening in reversed(stack):
        header = mask[max(0, opening - 300):opening]
        if re.search(r"(?:\bfunction\b|=>)[^{}]*$", header, re.DOTALL):
            return opening + 1
    return (stack[-1] + 1) if stack else 0


def _allowlist_guard(mask: str, start: int, end: int, host: str) -> bool:
    prefix = mask[start:end]
    membership = (
        rf"(?P<list>{IDENTIFIER})\s*\.\s*(?:has|includes)\s*"
        rf"\(\s*{re.escape(host)}\s*\)"
    )
    fail_closed = re.compile(
        rf"\bif\s*\(\s*!\s*{membership}\s*\)\s*"
        r"(?:\{[^{}]*\b(?:throw|return)\b[^{}]*\}|"
        r"(?:throw|return)\b[^;\n]*(?:;|\n))",
        re.IGNORECASE,
    )
    for match in fail_closed.finditer(prefix):
        if _allowlist_name(match.group("list")):
            return True

    # A positive membership test dominates a fetch inside its still-open
    # consequent block. Closed conditionals do not earn trust for later code.
    stack = []
    for index, current in enumerate(prefix):
        if current == "{":
            stack.append(index)
        elif current == "}" and stack:
            stack.pop()
    positive = re.compile(rf"\bif\s*\(\s*{membership}\s*\)\s*$", re.I)
    for opening in stack:
        header = prefix[max(0, opening - 500):opening]
        match = positive.search(header)
        if match and _allowlist_name(match.group("list")):
            return True
    return False


def _allowlist_name(name: str) -> bool:
    return bool(
        re.search(r"(?:^|_)(?:allow|allowed)(?:_|$)", name, re.I)
        or re.search(r"(?:Allowlist|AllowedHosts|AllowedOrigins)$", name)
    )


def _check_fetch_hosts(path: Path, text: str, mask: str) -> list[Finding]:
    findings = []
    for offset, _opening, _closing, arguments in _call_ranges(mask, "fetch"):
        if not arguments:
            continue
        start, end = arguments[0]
        host = _runtime_host(text[start:end].strip(), mask[start:end].strip(),
                             text, mask, offset)
        if host and not _allowlist_guard(mask, _scope_start(mask, offset), offset, host):
            findings.append(Finding(
                path, _line_of(text, offset), "P007",
                "runtime-selected absolute fetch host has no prior allowlist check",
            ))
    return findings


def check_typescript(path: Path, text: str) -> list[Finding]:
    spans, errors = lex(text)
    if errors:
        return [Finding(path, _line_of(text, offset), "P000", reason)
                for offset, reason in errors]
    mask = _masked(text, spans)
    imports = _imports(_masked(text, spans, keep_strings=True))
    return (
        _check_raw_html(path, text, mask, imports)
        + _check_persistence(path, text, mask, imports)
        + _check_fetch_hosts(path, text, mask)
    )


def check(path: Path) -> list[Finding]:
    requirements = path.name.startswith("requirements") and path.suffix == ".txt"
    typescript = path.suffix in {".ts", ".tsx"}
    if not requirements and path.suffix != ".py" and not typescript:
        return []
    try:
        if typescript:
            with path.open("rb") as source:
                raw = source.read(TYPESCRIPT_MAX_BYTES + 1)
            if len(raw) > TYPESCRIPT_MAX_BYTES:
                return [Finding(
                    path, 1, "P000",
                    f"TypeScript source exceeds {TYPESCRIPT_MAX_BYTES}-byte analysis cap",
                )]
            text = raw.decode("utf-8")
        else:
            text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        return [Finding(path, 1, "P000", f"unreadable: {err}")]
    if requirements:
        found = check_requirements(path, text)
    elif typescript:
        found = check_typescript(path, text)
    else:
        found = check_python(path, text)
    return [f for f in found if not suppressed(text, f.line)]


def walk(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        root = Path(raw)
        if root.is_dir():
            for child in sorted(root.rglob("*")):
                if child.is_file() and "__pycache__" not in child.parts:
                    out.append(child)
        else:
            out.append(root)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phylax boundary lint.")
    parser.add_argument("paths", nargs="*", default=["."])
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    for path in walk(args.paths or ["."]):
        findings.extend(check(path))

    if args.format == "json":
        print(json.dumps([f.as_dict() for f in findings], indent=2))
    else:
        for finding in findings:
            print(finding)
        print(f"{len(findings)} finding(s)" if findings else "clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
