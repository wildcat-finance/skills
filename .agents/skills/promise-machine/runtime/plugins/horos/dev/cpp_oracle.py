"""Dev-time oracle for the Horos C++ outliner. Never imported or executed
by the shipped plugin or its test suite: the differential corpus run drives
it by hand inside a scratchpad virtualenv holding `tree-sitter` and
`tree-sitter-cpp`, and only the recorded results are committed.

Usage: <venv-python> cpp_oracle.py <file.cpp> [...] > oracle.json

Emits, per file, the declarations tree-sitter sees at the declared
altitudes: named types (class, struct, union, enum) and named functions and
methods at translation-unit, namespace, extern-block, template and class
depth. Operators, destructors, namespaces, variables and fields are
excluded by declaration, matching the differential's declared comparison.
"""

import json
import sys

import tree_sitter_cpp
from tree_sitter import Language, Parser

PARSER = Parser(Language(tree_sitter_cpp.language()))

TYPE_NODES = {
    "class_specifier": "type",
    "struct_specifier": "type",
    "union_specifier": "type",
    "enum_specifier": "type",
}
SCOPE_NODES = {
    "translation_unit",
    "namespace_definition",
    "declaration_list",
    "linkage_specification",
    "template_declaration",
    "field_declaration_list",
    # Declarations inside preprocessor conditionals are still declarations.
    "preproc_ifdef",
    "preproc_if",
    "preproc_else",
    "preproc_elif",
}


def text_of(node, source):
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def function_name(declarator, source):
    node = declarator
    while node is not None:
        if node.type == "function_declarator":
            inner = node.child_by_field_name("declarator")
            if inner is None:
                return None
            name = text_of(inner, source)
            last = name.split("::")[-1]
            tail = last[len("operator"):] if last.startswith("operator") else None
            if last.startswith("~") or (
                tail is not None and not (tail[:1].isalnum() or tail[:1] == "_")
            ):
                return None
            return last.split("<")[0] or None
        next_node = node.child_by_field_name("declarator")
        if next_node is None:
            # Reference and pointer declarators wrap positionally, without
            # a named field; descend into the first declarator-ish child.
            next_node = next(
                (
                    child
                    for child in node.named_children
                    if child.type.endswith("declarator")
                ),
                None,
            )
        if next_node is None:
            return None
        node = next_node
    return None


def collect(node, source, decls):
    for child in node.children:
        kind = child.type
        if kind in TYPE_NODES:
            name = child.child_by_field_name("name")
            if name is not None and name.type in ("type_identifier", "qualified_identifier"):
                decls.append(
                    {
                        "name": text_of(name, source).split("::")[-1],
                        "line": name.start_point[0] + 1,
                        "kind": "type",
                    }
                )
            body = child.child_by_field_name("body")
            if body is not None:
                collect(body, source, decls)
        elif kind in ("function_definition", "declaration", "field_declaration"):
            type_node = child.child_by_field_name("type")
            if (
                type_node is not None
                and type_node.type in TYPE_NODES
                and type_node.child_by_field_name("body") is not None
            ):
                # Only definitions: `struct X {...} y;` declares X, while
                # `struct termios y;` merely uses an elaborated type.
                name = type_node.child_by_field_name("name")
                if name is not None and name.type == "type_identifier":
                    decls.append(
                        {
                            "name": text_of(name, source),
                            "line": name.start_point[0] + 1,
                            "kind": "type",
                        }
                    )
                body = type_node.child_by_field_name("body")
                if body is not None:
                    collect(body, source, decls)
            declarator = child.child_by_field_name("declarator")
            if declarator is not None:
                name = function_name(declarator, source)
                if name is not None:
                    decls.append(
                        {
                            "name": name,
                            "line": declarator.start_point[0] + 1,
                            "kind": "function",
                        }
                    )
        if kind in SCOPE_NODES or kind in (
            "namespace_definition",
            "linkage_specification",
            "template_declaration",
        ):
            body = child.child_by_field_name("body")
            if body is not None and body.type not in (
                "declaration_list",
                "field_declaration_list",
                "compound_statement",
            ):
                # A single-declaration body (extern "C" int f(...);) is a
                # declaration itself, so walk the wrapper's children.
                collect(child, source, decls)
            else:
                collect(body if body is not None else child, source, decls)


def main():
    out = {}
    for path in sys.argv[1:]:
        with open(path, "rb") as handle:
            source = handle.read()
        tree = PARSER.parse(source)
        decls = []
        collect(tree.root_node, source, decls)
        unique = {(d["name"], d["line"]): d for d in decls}
        out[path] = {
            "decls": list(unique.values()),
            "parse_errors": bool(tree.root_node.has_error),
        }
    sys.stdout.write(json.dumps(out))


if __name__ == "__main__":
    main()
