#!/usr/bin/env python3
"""Execute exact guard bodies admitted by a finite, inert Python source filter.

The filter is not a Python interpreter. Accepted function bodies are compiled
unchanged; imports, dispatch hooks and reflective Python remain unsupported.
Only this fixed driver owns the report and assertion observations.
"""
import ast
import hashlib
import json
import keyword
from pathlib import Path
import sys

SCHEMA = "fiat-inoculation-execution/v1"
MAX_SOURCE = 1024 * 1024
MAX_NODES = 20000
MAX_GUARDS = 4096
SAFE = {"abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
        "enumerate": enumerate, "int": int, "len": len, "list": list,
        "max": max, "min": min, "range": range, "round": round,
        "sorted": sorted, "str": str, "sum": sum, "tuple": tuple,
        "zip": zip, "ValueError": ValueError, "TypeError": TypeError}
ASSERTIONS = {"assertEqual", "assertNotEqual", "assertTrue", "assertFalse",
              "assertLess", "assertLessEqual", "assertGreater", "assertGreaterEqual"}
NODES = (ast.FunctionDef, ast.arguments, ast.arg, ast.Return, ast.Assign,
         ast.AugAssign, ast.Expr, ast.If, ast.For, ast.While, ast.Break,
         ast.Continue, ast.Pass, ast.Raise, ast.Name, ast.Load, ast.Store,
         ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.Subscript, ast.Slice,
         ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, ast.IfExp, ast.Call,
         ast.keyword, ast.Attribute, ast.Add, ast.Sub, ast.Mult, ast.Div,
         ast.FloorDiv, ast.Mod, ast.Pow, ast.USub, ast.UAdd, ast.Not,
         ast.And, ast.Or, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
         ast.In, ast.NotIn, ast.Is, ast.IsNot)


class Refusal(ValueError):
    """Unsupported source cannot authorize guard acceptance."""


def require(condition, code):
    if not condition:
        raise Refusal(code)


def read_source(root, descriptor):
    require(type(descriptor) is dict and set(descriptor) == {"path", "sha256"}, "source-shape")
    path = descriptor["path"]
    require(type(path) is str and path and all(p not in ("", ".", "..")
            for p in path.split("/")) and not path.startswith("/") and "\\" not in path,
            "source-path")
    target = root / path
    require(not target.is_symlink(), "source-symlink")
    with target.open("rb") as stream:
        data = stream.read(MAX_SOURCE + 1)
    require(len(data) <= MAX_SOURCE and hashlib.sha256(data).hexdigest() == descriptor["sha256"],
            "source-digest")
    tree = ast.parse(data, filename=path)
    require(sum(1 for _ in ast.walk(tree)) <= MAX_NODES, "source-node-cap")
    return tree, path


def check_function(function, calls, *, guard=False):
    require(not function.decorator_list and not function.returns
            and not function.type_params and not function.args.defaults
            and not function.args.kw_defaults and not function.args.kwonlyargs
            and not function.args.vararg and not function.args.kwarg
            and not function.args.posonlyargs, "unsupported-function-binding")
    arguments = [a.arg for a in function.args.args]
    require(all(not name.startswith("_") and name not in calls | set(SAFE)
                for name in arguments), "argument-binding")
    require(all(a.annotation is None for a in function.args.args), "unsupported-annotation")
    require((arguments == ["self"]) if guard else "self" not in arguments, "guard-arguments")
    require(not function.name.startswith("_") and function.name not in SAFE, "function-name")
    for node in ast.walk(function):
        require(isinstance(node, NODES), "unsupported-python-node")
        if isinstance(node, ast.FunctionDef):
            require(node is function, "nested-function")
        if isinstance(node, ast.Name):
            require(not node.id.startswith("_"), "reflective-name")
            if isinstance(node.ctx, ast.Store):
                require(node.id not in calls and node.id not in SAFE and node.id != "self", "binding-mutation")
        if isinstance(node, ast.Assign):
            require(all(isinstance(t, ast.Name) for t in node.targets), "assignment-target")
        if isinstance(node, ast.AugAssign):
            require(isinstance(node.target, ast.Name), "assignment-target")
        if isinstance(node, ast.For):
            require(isinstance(node.target, ast.Name), "loop-target")
        if isinstance(node, ast.Constant):
            require(type(node.value) in (type(None), bool, int, float, str, bytes), "constant-type")
            if isinstance(node.value, (str, bytes)):
                require(len(node.value) <= 4096, "constant-cap")
            if type(node.value) is int:
                require(node.value.bit_length() <= 1024, "constant-cap")
        if isinstance(node, ast.Attribute):
            require(guard and isinstance(node.value, ast.Name) and node.value.id == "self"
                    and node.attr in ASSERTIONS and isinstance(node.ctx, ast.Load), "unsupported-attribute")
            require(any(isinstance(parent, ast.Call) and parent.func is node
                        for parent in ast.walk(function)), "assertion-reference")
        if isinstance(node, ast.Call):
            require(not any(k.arg is None for k in node.keywords), "dynamic-keywords")
            require((isinstance(node.func, ast.Name) and node.func.id in calls | set(SAFE))
                    or (guard and isinstance(node.func, ast.Attribute)
                        and node.func.attr in ASSERTIONS), "unsupported-call")
        # Passing self elsewhere would expose the fixed assertion observer.
        if isinstance(node, ast.Name) and node.id == "self":
            require(any(isinstance(parent, ast.Attribute) and parent.value is node
                        for parent in ast.walk(function)), "observer-reference")


class Assertions:
    def __init__(self):
        self.count = 0

    def _observe(self, condition):
        self.count += 1
        if not condition:
            raise AssertionError("guard assertion failed")

    def assertEqual(self, a, b): self._observe(a == b)
    def assertNotEqual(self, a, b): self._observe(a != b)
    def assertTrue(self, value): self._observe(bool(value))
    def assertFalse(self, value): self._observe(not value)
    def assertLess(self, a, b): self._observe(a < b)
    def assertLessEqual(self, a, b): self._observe(a <= b)
    def assertGreater(self, a, b): self._observe(a > b)
    def assertGreaterEqual(self, a, b): self._observe(a >= b)


def prepare(root, request):
    require(type(request) is dict and set(request) == {"schema", "guards", "dependencies"}
            and request["schema"] == "fiat-inoculation-request/v1", "request-shape")
    require(type(request["guards"]) is list and 0 < len(request["guards"]) <= MAX_GUARDS,
            "guard-count")
    require(type(request["dependencies"]) is list and len(request["dependencies"]) <= 128,
            "dependency-count")
    definitions = {}; dependencies = []; modules = {}
    for descriptor in request["dependencies"]:
        tree, filename = read_source(root, descriptor)
        module_name = filename.removesuffix(".py")
        require(filename.endswith(".py") and "/" not in filename
                and module_name.isascii() and module_name.isidentifier()
                and not keyword.iskeyword(module_name) and module_name != "unittest",
                "unsupported-module-path")
        require(all(isinstance(n, ast.FunctionDef) for n in tree.body), "dependency-top-level")
        for function in tree.body:
            require(function.name not in definitions and function.name != "unittest", "duplicate-dependency")
            definitions[function.name] = function
            modules[function.name] = filename.removesuffix(".py").replace("/", ".")
        dependencies.append((tree, filename))
    calls = set(definitions)
    for tree, filename in dependencies:
        local_calls = {function.name for function in tree.body}
        for function in tree.body:
            check_function(function, local_calls)
    guards = []; identities = set()
    for descriptor in request["guards"]:
        require(type(descriptor) is dict and set(descriptor) ==
                {"id", "family", "source", "class", "method", "body_sha256"}, "guard-shape")
        identity = descriptor["id"]
        require(type(identity) is str and identity and identity not in identities, "duplicate-guard")
        identities.add(identity)
        require(type(descriptor["family"]) is str and descriptor["family"], "guard-family")
        tree, filename = read_source(root, descriptor["source"])
        # No target module is imported. Only simple TestCase declarations and
        # explicit imports of the already bound dependency names are accepted.
        classes = []; imported = set(); unittest_bound = False; class_names = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                require(len(node.names) == 1 and node.names[0].name == "unittest"
                        and node.names[0].asname is None, "unsupported-import")
                unittest_bound = True
            elif isinstance(node, ast.ImportFrom):
                require(node.level == 0 and node.module and all(a.name in calls
                        and a.asname is None and modules[a.name] == node.module
                        for a in node.names), "unsupported-import")
                imported.update(a.name for a in node.names)
            else:
                require(isinstance(node, ast.ClassDef), "guard-top-level")
                require(unittest_bound and node.name not in class_names | calls | set(SAFE)
                        and node.name != "unittest", "class-binding")
                class_names.add(node.name)
                require(not node.decorator_list and not node.keywords and not node.type_params
                        and len(node.bases) == 1 and isinstance(node.bases[0], ast.Attribute)
                        and isinstance(node.bases[0].value, ast.Name)
                        and node.bases[0].value.id == "unittest"
                        and node.bases[0].attr == "TestCase", "unsupported-test-class")
                for method in node.body:
                    require(isinstance(method, ast.FunctionDef) and method.name.startswith("test_"),
                            "unsupported-lifecycle")
                classes.append(node)
        for declared_class in classes:
            for method in declared_class.body:
                check_function(method, imported, guard=True)
        selected = [m for c in classes if c.name == descriptor["class"]
                    for m in c.body if m.name == descriptor["method"]]
        require(len(selected) == 1, "guard-not-found")
        method = selected[0]
        body = ast.get_source_segment((root / filename).read_text(), method)
        require(hashlib.sha256(body.encode()).hexdigest() == descriptor["body_sha256"], "guard-body-digest")
        guards.append((descriptor, method, filename, imported))
    return dependencies, guards


def execute(root, request):
    dependencies, guards = prepare(root, request)
    bindings = {}
    for tree, filename in dependencies:
        namespace = {"__builtins__": SAFE.copy()}
        # phylax: allow prepare admits only source-bound function ASTs with closed module globals; native policy confines execution.
        exec(compile(tree, filename, "exec"), namespace)
        bindings.update({function.name: namespace[function.name] for function in tree.body})
    rows = []
    for descriptor, method, filename, imported in guards:
        local = {"__builtins__": SAFE.copy(), **{name: bindings[name] for name in imported}}
        methods = {}
        # phylax: allow the preserved method passed the closed AST/import/body filter; fixed assertions observe its actual execution.
        exec(compile(ast.Module(body=[method], type_ignores=[]), filename, "exec"), local, methods)
        observer = Assertions()
        row = {"id": descriptor["id"], "family": descriptor["family"],
               "source": descriptor["source"], "body_sha256": descriptor["body_sha256"],
               "entered": True, "completed": False, "assertions": 0, "status": "failed"}
        try:
            methods[method.name](observer)
            row["completed"] = True
            row["status"] = "passed" if observer.count > 0 else "no-assertion-executed"
        except Exception as error:
            row["failure_type"] = type(error).__name__
        row["assertions"] = observer.count
        rows.append(row)
    return {"schema": SCHEMA, "rows": rows,
            "passed": all(row["status"] == "passed" for row in rows)}


def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    try:
        result = execute(Path(sys.argv[2]), request)
    except Refusal as error:
        result = {"schema": SCHEMA, "passed": False, "rows": [], "refusal": str(error)}
    Path(sys.argv[3]).write_text(json.dumps(result, sort_keys=True) + "\n")
    # Successful report production retains negative observations too. The
    # controller separately requires passed plus every exact execution row.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
