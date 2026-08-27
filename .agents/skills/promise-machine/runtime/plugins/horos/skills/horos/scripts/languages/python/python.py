"""Python outline extraction for Horos's map verb."""

import ast


def first_docstring_line(node):
    docstring = ast.get_docstring(node)
    if not docstring:
        return None
    return docstring.strip().splitlines()[0]


def skeleton_lines(node, depth=0):
    """Signatures and class structure, one line each, bodies left behind."""
    lines = []
    pad = "    " * depth
    for child in node.body if hasattr(node, "body") else []:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in child.decorator_list:
                lines.append(f"{pad}@{ast.unparse(decorator)}")
            keyword = "async def" if isinstance(child, ast.AsyncFunctionDef) else "def"
            returns = f" -> {ast.unparse(child.returns)}" if child.returns else ""
            line = f"{pad}{keyword} {child.name}({ast.unparse(child.args)}){returns}:"
            summary = first_docstring_line(child)
            if summary:
                line += f"  # {summary}"
            lines.append(line)
        elif isinstance(child, ast.ClassDef):
            for decorator in child.decorator_list:
                lines.append(f"{pad}@{ast.unparse(decorator)}")
            bases = ", ".join(ast.unparse(base) for base in child.bases)
            line = f"{pad}class {child.name}" + (f"({bases}):" if bases else ":")
            summary = first_docstring_line(child)
            if summary:
                line += f"  # {summary}"
            lines.append(line)
            lines.extend(skeleton_lines(child, depth + 1))
    return lines


def outline(path, source, out):
    """Print the module's skeleton; 0 on success, 1 on a syntax error."""
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        print(f"horos: syntax error in {path} at line {error.lineno}", file=out)
        return 1
    summary = first_docstring_line(tree)
    print(f"module: {summary}" if summary else "module: (no docstring)", file=out)
    for line in skeleton_lines(tree):
        print(line, file=out)
    return 0
