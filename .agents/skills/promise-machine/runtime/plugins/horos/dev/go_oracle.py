"""Dev-time oracle for the Horos Go outliner. Never imported or executed by
the shipped plugin or its test suite: the differential corpus run drives it
by hand inside a scratchpad virtualenv holding `tree-sitter` and
`tree-sitter-go`, and only the recorded results are committed.

Usage: <venv-python> go_oracle.py <file.go> [...] > oracle.json

Emits, per file, the declarations tree-sitter sees at the altitudes the
outliner claims: top-level functions, methods, types, consts and vars,
grouped members included. Function-body locals are absent on both sides.
"""

import json
import sys

import tree_sitter_go
from tree_sitter import Language, Parser

PARSER = Parser(Language(tree_sitter_go.language()))


def names_from(node, source):
    decls = []

    def ident(n):
        return source[n.start_byte : n.end_byte].decode("utf-8", errors="replace")

    def push(n, kind):
        decls.append({"name": ident(n), "line": n.start_point[0] + 1, "kind": kind})

    for child in node.children:
        if child.type == "function_declaration":
            name = child.child_by_field_name("name")
            if name is not None:
                push(name, "function")
        elif child.type == "method_declaration":
            name = child.child_by_field_name("name")
            if name is not None:
                push(name, "method")
        elif child.type == "type_declaration":
            for spec in child.children:
                if spec.type in ("type_spec", "type_alias"):
                    name = spec.child_by_field_name("name")
                    if name is not None:
                        push(name, "type")
        elif child.type in ("const_declaration", "var_declaration"):
            kind = child.type.split("_", 1)[0]
            # Grouped var blocks nest their specs under a var_spec_list
            # node, so walk a small stack instead of one level.
            stack = list(child.children)
            while stack:
                spec = stack.pop()
                if spec.type in ("const_spec", "var_spec"):
                    seen = set()
                    for part in spec.children:
                        if part.type == "identifier" and id(part) not in seen:
                            seen.add(id(part))
                            push(part, kind)
                        if part.type not in ("identifier", ","):
                            break
                elif spec.type == "var_spec_list":
                    stack.extend(spec.children)
    return decls


def main():
    out = {}
    for path in sys.argv[1:]:
        with open(path, "rb") as handle:
            source = handle.read()
        tree = PARSER.parse(source)
        out[path] = names_from(tree.root_node, source)
    sys.stdout.write(json.dumps(out))


if __name__ == "__main__":
    main()
