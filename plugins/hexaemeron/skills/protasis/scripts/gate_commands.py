#!/usr/bin/env python3
"""Bounded inert command parsing and full-source interface receipts.

No target module is imported. Registered argparse declarations are read as AST
and translated to a local parser containing only built-in scalar operations.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import shlex
import stat

SCHEMA = "protasis-gate-commands/v1"
MAX_DOCUMENT = 256 * 1024
MAX_SOURCE = 2 * 1024 * 1024
MAX_COMMANDS = 64
MAX_EXPANDED = 256
PREFIX = "plugins/hexaemeron/skills/"
REGISTRY = {
    "plugins/brevitas/skills/brevitas/scripts/brevitas.py": "build_parser",
    "scripts/run_checks.py": "build_parser",
    "plugins/hexaemeron/tests/run_tests.py": "argument_parser",
    **{PREFIX + name + "/scripts/" + name + ".py": "main"
       for name in ("protasis", "imprimatur", "phylax", "ephoros", "hypomnema")},
}
MODULE_BINDINGS = {'plugins/brevitas/skills/brevitas/scripts/brevitas.py': '31831215f698b63ff87e84f46a3288ea20270a94e3e7e9cce201a9237442dddb', 'scripts/run_checks.py': '52f2bd7aa98a71154647dfda5cb3eac2692b08f91f8ae0d804c917f002d2d8ad', 'plugins/hexaemeron/tests/run_tests.py': '79981b3478b8e067a4e151c3ff6ca164ae2a5ef4ae585ebb8cf4a4a54b4001a5', 'plugins/hexaemeron/skills/protasis/scripts/protasis.py': '0d3742b85957171503269e60397d8829459f08eac21cf6b4d50f55c44fc602d5', 'plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py': '2705bc498170025f540b88f3fa3440ae4d0a54692171991282dc82c0b5a39c55', 'plugins/hexaemeron/skills/phylax/scripts/phylax.py': 'df7c9fcfefe85e2aaacfeedbfa40a3330f581e4cfd3cfa8ba88f2336c7ba2061', 'plugins/hexaemeron/skills/ephoros/scripts/ephoros.py': '9a5e09dc66da1c4263e9b05f2688fb34d2866e02441acabe166afe32b6548ace', 'plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py': '0ce0d4baf1771060f0f5d0c3093de353b7a2012896dd9e8650c26e940eda140a'}
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})([^\n]*)$")
LOOP = re.compile(r'\Afor file in (?P<items>[^;\n]+)(?:;|\n)\s*do(?:[ \t]+|\n)(?P<body>[^;\n]+)(?:;|\n)\s*done\s*\Z')
ELENCHUS = re.compile(r'Elenchus command:\s*`([^`\n]+)`;\s*format:\s*`([^`\n]+)`;\s*report file:\s*`([^`\n]+)`')
# These converters have reviewed scalar semantics. Their AST hashes, including
# referenced range constants, are pinned below; source changes require review.
CONVERTERS = {'positive_int': ('880e1021a8298bf36803950dff742879faa38f86b0d99d6e6493385df849a8fe', None), 'positive_jobs': ('97379d9639332efc57a0c47232f257cf5ca1efef668324ce90463d0f0d8f29ba', 256)}


class Refusal(ValueError):
    """A command cannot earn an inert interface receipt."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_source(root: Path, relative: str, cap: int = MAX_SOURCE) -> bytes:
    """Read regular no-follow components with bounded bytes and stable identity."""
    parts = relative.split('/')
    if not parts or any(p in ('', '.', '..') for p in parts) or relative.startswith('/'):
        raise Refusal('unsafe-source-path')
    descriptors = []
    try:
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        descriptors.append(fd)
        for part in parts[:-1]:
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            descriptors.append(fd)
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        descriptors.append(leaf)
        before = os.fstat(leaf)
        if not stat.S_ISREG(before.st_mode) or before.st_size > cap:
            raise Refusal('source-not-bounded-regular')
        chunks = []
        remaining = cap + 1
        while remaining:
            part = os.read(leaf, min(65536, remaining))
            if not part:
                break
            chunks.append(part)
            remaining -= len(part)
        data = b''.join(chunks)
        after = os.fstat(leaf)
        fields = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_mode)
        if len(data) > cap or fields(before) != fields(after):
            raise Refusal('source-changed-during-read')
        return data
    except OSError as exc:
        raise Refusal('source-unavailable: ' + relative) from exc
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


class InertParser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal('cli-arguments: ' + message)

    def exit(self, status=0, message=None):
        raise Refusal('cli-exit-option')


def literal(node, tree=None):
    if isinstance(node, ast.Constant) and type(node.value) in (str, int, bool, type(None)):
        return node.value
    if isinstance(node, (ast.Tuple, ast.List)):
        return [literal(value, tree) for value in node.elts]
    if isinstance(node, ast.Name) and tree is not None:
        constants = [statement for statement in tree.body
                     if isinstance(statement, ast.Assign) and len(statement.targets) == 1
                     and isinstance(statement.targets[0], ast.Name)
                     and statement.targets[0].id == node.id]
        if len(constants) != 1:
            raise Refusal('ambiguous-cli-constant')
        # The module binding was checked before reaching this declaration.
        # Read one literal assignment; aliases and expressions stay unsupported.
        return literal(constants[0].value)
    raise Refusal('nonliteral-cli-declaration')


def scalar_converter(name, tree):
    if name in ('int', 'float'):
        return {'int': int, 'float': float}[name]
    expected = CONVERTERS.get(name)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    if expected is None or len(functions) != 1:
        raise Refusal('unsupported-cli-converter')
    function = functions[0]
    binding = ast.dump(function, include_attributes=False)
    if name == 'positive_jobs':
        constants = [n for n in tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'MAX_JOBS' for t in n.targets)]
        if len(constants) != 1:
            raise Refusal('converter-range-missing')
        binding += ast.dump(constants[0], include_attributes=False)
    if digest(binding.encode()) != expected[0]:
        raise Refusal('cli-converter-source-drift')
    def convert(raw):
        try:
            value = int(raw)
        except ValueError as exc:
            raise argparse.ArgumentTypeError('expected integer') from exc
        if value < 1 or (expected[1] is not None and value > expected[1]):
            raise argparse.ArgumentTypeError('integer outside registered range')
        return value
    return convert


def parser_bindings(tree, builder, path):
    """Bind all module-level semantics outside the one supported builder body.

    This is a reviewed registration boundary, not an arbitrary Python alias
    analysis. Only the builder's closed declaration prefix is interpreted.
    """
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == builder]
    if len(functions) != 1:
        raise Refusal('ambiguous-cli-builder')
    function = functions[0]
    original_body = function.body
    try:
        function.body = []
        actual = digest(ast.dump(tree, include_attributes=False).encode())
    finally:
        function.body = original_body
    if actual != MODULE_BINDINGS[path]:
        raise Refusal('unregistered-cli-module-bindings')


def interface(root: Path, path: str):
    if path not in REGISTRY:
        raise Refusal('unregistered-cli')
    data = read_source(root, path)
    try:
        tree = ast.parse(data, filename=path)
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise Refusal('invalid-cli-source') from exc
    parser_bindings(tree, REGISTRY[path], path)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == REGISTRY[path]]
    if len(functions) != 1 or functions[0].decorator_list:
        raise Refusal('unsupported-cli-builder')
    parser = InertParser(add_help=False, allow_abbrev=False)
    constructed = False
    parser_name = 'ap' if path == PREFIX + 'imprimatur/scripts/imprimatur.py' else 'parser'
    declarations = []
    for statement in functions[0].body:
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
            continue
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name) and statement.targets[0].id == parser_name:
            call = statement.value
            if constructed or not isinstance(call, ast.Call) or ast.unparse(call.func) != 'argparse.ArgumentParser' or call.args:
                raise Refusal('unsupported-cli-constructor')
            for kw in call.keywords:
                if kw.arg == 'formatter_class' and ast.unparse(kw.value) == 'argparse.RawDescriptionHelpFormatter':
                    continue
                if kw.arg == 'epilog' and isinstance(kw.value, ast.Constant) and type(kw.value.value) is str:
                    continue
                if kw.arg not in ('description', 'prog') or not (isinstance(kw.value, ast.Constant) or isinstance(kw.value, ast.Name) and kw.value.id == '__doc__'):
                    raise Refusal('unsupported-cli-constructor-option')
            constructed = True
            continue
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call) and ast.unparse(statement.value.func) == parser_name + '.add_argument':
            if not constructed:
                raise Refusal('cli-parser-not-constructed')
            call = statement.value
            args = [literal(value) for value in call.args]
            if not args or any(not isinstance(value, str) for value in args):
                raise Refusal('invalid-cli-option-name')
            kwargs = {}
            for kw in call.keywords:
                if kw.arg not in ('nargs', 'default', 'help', 'metavar', 'choices', 'action', 'required', 'type', 'dest'):
                    raise Refusal('unsupported-cli-option-shape')
                if kw.arg == 'type':
                    if not isinstance(kw.value, ast.Name):
                        raise Refusal('unsupported-cli-converter')
                    kwargs['type'] = scalar_converter(kw.value.id, tree)
                elif kw.arg == 'help' and isinstance(kw.value, ast.Attribute) and ast.unparse(kw.value) == 'argparse.SUPPRESS':
                    kwargs['help'] = argparse.SUPPRESS
                else:
                    if isinstance(kw.value, ast.Name) and kw.arg == 'default':
                        constants = [n for n in tree.body if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == kw.value.id]
                        if len(constants) != 1:
                            raise Refusal('ambiguous-cli-default')
                        kwargs[kw.arg] = literal(constants[0].value)
                    else:
                        kwargs[kw.arg] = literal(kw.value, tree)
            nargs = kwargs.get('nargs')
            if not (nargs is None or type(nargs) is int and 0 <= nargs <= 128 or type(nargs) is str and nargs in ('?', '*', '+')):
                raise Refusal('unsupported-cli-nargs')
            if kwargs.get('action', 'store') not in ('store', 'append', 'store_true', 'store_false'):
                raise Refusal('unsupported-cli-action')
            if any(value.startswith('--_') for value in args):
                # Public gates may not invoke the producer's private worker mode.
                declarations.append(ast.dump(statement, include_attributes=False))
                continue
            try:
                parser.add_argument(*args, **kwargs)
            except (ValueError, TypeError, argparse.ArgumentError) as exc:
                raise Refusal('unsupported-cli-argument-declaration') from exc
            declarations.append(ast.dump(statement, include_attributes=False))
            continue
        # Only a direct parser return or its direct parse_args consumption ends
        # the declaration prefix. A conditional/mutating prefix is unsupported.
        if isinstance(statement, ast.Return) and isinstance(statement.value, ast.Name) and statement.value.id == parser_name:
            break
        if isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Call) and ast.unparse(statement.value.func) == parser_name + '.parse_args':
            call = statement.value
            parameters = {arg.arg for arg in functions[0].args.args}
            if (len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name)
                    or call.keywords or len(call.args) > 1
                    or call.args and not (isinstance(call.args[0], ast.Name) and call.args[0].id == 'argv' and 'argv' in parameters)):
                raise Refusal('unsupported-cli-parse-arguments')
            break
        raise Refusal('unsupported-cli-builder-statement')
    else:
        raise Refusal('cli-parser-terminal-missing')
    if not constructed or not declarations:
        raise Refusal('empty-cli-interface')
    return parser, {'path': path, 'sha256': digest(data), 'declarations_sha256': digest('\n'.join(declarations).encode())}


def argv(source: str, *, variable: bool = False) -> list[str]:
    if not source or len(source.encode()) > 65536 or any(c in source for c in ('\x00', '\r', '\n', '`', '|', '&', ';', '<', '>', '#', '~')):
        raise Refusal('unsupported-shell-form')
    # Preserve quote provenance: the sole variable must be a whole, double-
    # quoted operand in the loop body. Single-quoted "$file" is not expansion.
    if variable and not re.search(r'(?:^|\s)"\$file"(?:\s|$)', source):
        raise Refusal('loop-variable-quote-context')
    probe = source.replace('"$file"', 'LOOP_VALUE') if variable else source
    if any(c in probe for c in ('$', '*', '?', '[', ']', '\\')):
        raise Refusal('unsupported-shell-expansion')
    try:
        values = shlex.split(source, posix=True)
    except ValueError as exc:
        raise Refusal('invalid-command-quotes') from exc
    if not values or len(values) > 128 or any(len(x.encode()) > 8192 for x in values):
        raise Refusal('argv-bound')
    if variable and (values.count('$file') != 1 or source.count('"$file"') != 1):
        raise Refusal('loop-variable-binding')
    return values


def expand(source: str) -> list[list[str]]:
    if source.lstrip().startswith('for '):
        match = LOOP.fullmatch(source)
        if match is None:
            raise Refusal('unsupported-loop')
        items = argv(match['items'])
        if len(items) > 64:
            raise Refusal('loop-item-bound')
        body = argv(match['body'], variable=True)
        return [[item if x == '$file' else x for x in body] for item in items]
    return [argv(source)]


def report_operand(root: Path, declared: str) -> str:
    parts = declared.split('/')
    if (not declared or declared.startswith('/') or '\\' in declared or '\x00' in declared
            or any(p in ('', '.', '..') or p.casefold() == '.git' for p in parts)):
        raise Refusal('report-escape')
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise Refusal('report-escape')
    return str(current.absolute())


def validate_command(root: Path, source: str, report: dict | None = None) -> dict:
    expanded = expand(source)
    results = []
    for values in expanded:
        if len(values) < 2 or values[0] != 'python3':
            raise Refusal('unregistered-executable')
        parser, binding = interface(root, values[1])
        resolved = list(values)
        if report is not None:
            if values.count('{report}') != 1 or report.get('format') != 'unittest-json-v1':
                raise Refusal('report-contract')
            resolved[values.index('{report}')] = report_operand(root, report['file'])
        elif any('{report}' in value for value in values):
            raise Refusal('unbound-report-substitution')
        if any('{' in value or '}' in value for value in resolved):
            raise Refusal('unsupported-placeholder')
        parser.parse_args(resolved[2:])
        results.append({'argv': values, 'execution_argv': resolved, 'cli': binding, 'result': 'interface-valid'})
    return {'command': source, 'sha256': digest(source.encode()), 'report': report, 'invocations': results}


def effective_ranges(text: str) -> list[tuple[int, int]]:
    """Select the latest explicit Exit/Tests field for each numbered step.

    Protasis/controller still own amendment shape, chronology and receipts.
    This selector never turns an unknown fence into non-executable text.
    """
    original_text = text
    masked = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = FENCE.fullmatch(line.rstrip('\n'))
        if marker or fence is not None:
            masked.append(''.join('\n' if char == '\n' else ' ' for char in line))
            if marker:
                if fence is None:
                    fence = marker[1]
                elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                    fence = None
        else:
            masked.append(line)
    text = ''.join(masked)
    latest = {}
    all_ranges = []
    baseline, *amendments = re.split(r"(?m)(?=^### Amendment -- )", text)
    headings = list(re.finditer(r"(?m)^## Step ([0-9]+):.*$", baseline))
    for i, heading in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(baseline)
        fields = list(re.finditer(r"(?m)^\*\*(Goal|Entry|Exit|Files|Tests|Disciplines)\.\*\*", baseline[heading.end():end]))
        for j, field in enumerate(fields):
            if field[1] in ('Exit', 'Tests'):
                start = heading.end() + field.start()
                stop = heading.end() + fields[j + 1].start() if j + 1 < len(fields) else end
                latest[(int(heading[1]), field[1])] = (start, stop)
                all_ranges.append((start, stop))
    cursor = len(baseline)
    for amendment in amendments:
        touched = re.search(r"(?m)^\*\*Steps touched\.\*\*([^\n]+)", amendment)
        replacements = list(re.finditer(r"Complete replacement (Goal|Entry|Exit|Files|Tests|Disciplines):", amendment))
        if replacements and touched is None:
            raise Refusal('amendment-steps-missing')
        numbers = [int(n) for n in re.findall(r"[0-9]+", touched[1])] if touched else []
        for j, field in enumerate(replacements):
            if field[1] in ('Exit', 'Tests'):
                start = cursor + field.start()
                next_field = replacements[j + 1].start() if j + 1 < len(replacements) else amendment.find('\n\n', field.end())
                stop = cursor + (next_field if next_field >= 0 else len(amendment))
                all_ranges.append((start, stop))
                for number in numbers:
                    if (number, field[1]) not in latest:
                        raise Refusal('amendment-unknown-step')
                    latest[(number, field[1])] = (start, stop)
        cursor += len(amendment)
    convert = lambda ranges: [(len(original_text[:start].encode()), len(original_text[:stop].encode())) for start, stop in ranges]
    return convert(latest.values()), convert(all_ranges)


def commands(data: bytes) -> list[dict]:
    if len(data) > MAX_DOCUMENT:
        raise Refusal('document-bound')
    try:
        text = data.decode('utf-8')
    except UnicodeError as exc:
        raise Refusal('document-encoding') from exc
    records = []
    active_ranges, all_ranges = effective_ranges(text)
    active = None
    body = []
    offset = 0
    for line in text.splitlines(keepends=True):
        stripped = line.rstrip('\n')
        match = FENCE.fullmatch(stripped)
        if active is not None:
            if match:
                if match[1][0] != active[0][0] or len(match[1]) < len(active[0]) or match[2].strip():
                    raise Refusal('malformed-fence')
                payload = ''.join(body)
                if active[1] in ('sh', 'bash', 'shell'):
                    if payload.lstrip().startswith('for '):
                        records.append({'offset': active[2] + len(payload[:len(payload) - len(payload.lstrip())].encode()), 'command': payload.strip(), 'report': None})
                    else:
                        start = active[2]
                        for item in payload.splitlines(keepends=True):
                            if item.strip():
                                records.append({'offset': start + len(item[:len(item) - len(item.lstrip())].encode()), 'command': item.strip(), 'report': None})
                            start += len(item.encode())
                elif active[1] == 'design-lock':
                    if not re.fullmatch(r'schema \| protasis-design-evidence/v1\nsha256 \| [0-9a-f]{64}\ncandidate \| [a-z0-9-]+\n', payload):
                        raise Refusal('invalid-data-fence')
                elif active[1] == 'version-relations':
                    if not payload.strip() or any(not re.fullmatch(r'[a-z][a-z0-9-]* \| plugins/[a-z0-9/-]+/EVOLUTION\.md \| next-generation-after-integration-base', row) for row in payload.splitlines()):
                        raise Refusal('invalid-data-fence')
                else:
                    raise Refusal('unclassified-fence')
                active = None
                body = []
            else:
                body.append(line)
        elif match:
            label = match[2].strip()
            if label not in ('sh', 'bash', 'shell', 'design-lock', 'version-relations'):
                raise Refusal('unclassified-fence')
            active = (match[1], label, offset + len(line.encode()))
        else:
            contract = ELENCHUS.search(line)
            if contract:
                records.append({'offset': offset + len(line[:contract.start(1)].encode()), 'command': contract[1], 'report': {'format': contract[2], 'file': contract[3]}})
            elif 'Elenchus command:' in line:
                raise Refusal('malformed-report-contract')
            if line.startswith('**Exit.**') or 'Complete replacement Exit:' in line:
                for code in re.finditer(r'`([^`\n]+)`', line):
                    records.append({'offset': offset + len(line[:code.start(1)].encode()), 'command': code[1], 'report': None})
        offset += len(line.encode())
    if active is not None:
        raise Refusal('unclosed-fence')
    if not records or len(records) > MAX_COMMANDS:
        raise Refusal('command-count-bound')
    for record in records:
        # Commands outside step fields (standalone command specimens) remain active.
        record['effective'] = not any(a <= record['offset'] < b for a, b in all_ranges) or any(a <= record['offset'] < b for a, b in active_ranges)
    return records


def validate(root: Path, data: bytes) -> dict:
    root = root.resolve(strict=True)
    records = commands(data)
    results = []
    total = 0
    for record in records:
        if not record['effective']:
            results.append({**record, 'sha256': digest(record['command'].encode()), 'result': 'superseded-source'})
            continue
        total += len(expand(record['command']))
        if total > MAX_EXPANDED:
            raise Refusal('expanded-command-bound')
        result = validate_command(root, record['command'], record['report'])
        results.append({'offset': record['offset'], **result})
    return {'schema': SCHEMA, 'artifact_sha256': digest(data), 'source_root': str(root),
            'adapter_sha256': digest(Path(__file__).read_bytes()),
            'commands': results, 'operation_ran': False}


def _success_criteria_module():
    """Load the sibling declaration parser without importing a target module."""
    path = Path(__file__).with_name('success_criteria.py')
    spec = importlib.util.spec_from_file_location('protasis_success_criteria_gate', path)
    if spec is None or spec.loader is None:
        raise Refusal('success-criteria-parser-unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_with_criteria(root: Path, declaration: bytes, runbook: bytes) -> dict:
    """Admit a declaration only after the registered runbook interface is bound.

    This composes the existing inert command receipt with the pure declaration
    join.  It deliberately returns ``operation_ran=False`` and never imports or
    executes a producer module.
    """
    parser = _success_criteria_module()
    record = parser.parse(declaration)
    if record is None:
        raise Refusal('success-criteria-missing')
    gate = validate(root, runbook)
    joined = parser.join(record, runbook, command_records=gate['commands'])
    if joined is None:
        raise Refusal('success-criteria-missing')
    return {
        'schema': 'protasis-success-criteria-admission/v1',
        'gate_commands': gate,
        'declaration': record,
        'declaration_sha256': parser.declaration_digest(record),
        'join': joined,
        'operation_ran': False,
    }


def replay(root: Path, data: bytes, receipt: dict) -> None:
    # Resolve and check the current destination independently. Stored absolute
    # operands only describe the original inert capture, never execution rights.
    current = validate(root, data)
    captured_root = receipt.get('source_root')
    if (not isinstance(captured_root, str) or not captured_root.startswith('/')
            or '\x00' in captured_root or '\\' in captured_root
            or str(Path(captured_root)) != captured_root
            or any(part in ('.', '..') for part in captured_root.split('/')[1:])):
        raise Refusal('gate-source-root-invalid')
    current['source_root'] = captured_root
    for command in current['commands']:
        if command.get('report') is not None and command.get('result') != 'superseded-source':
            for invocation in command['invocations']:
                position = invocation['argv'].index('{report}')
                invocation['execution_argv'][position] = str(Path(captured_root) / command['report']['file'])
    if current != receipt:
        raise Refusal('gate-receipt-drift')
