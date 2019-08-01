import ast
import copy
import pkgutil
import sys
from collections import defaultdict
from itertools import count

from hexastore import IRI, InMemoryHexastore, Order, OrderCondition, Variable, engine, make_default_forward_reasoner
from hexastore.util import LABEL, SUBCLASS_OF, TYPE
from hexastore.util import plot as util_plot

UNIT = IRI(f"http://example.com/unit")
PACKAGE = IRI(f"http://example.com/python-package")
MODULE = IRI(f"http://example.com/python-module")
FUNCTION = IRI(f"http://example.com/function")
CLASS = IRI(f"http://example.com/class")
IMPORTS = IRI(f"http://example.com/imports")
DEFINED_IN = IRI(f"http://example.com/defined-in")


class ModuleVisitor(ast.NodeVisitor):
    def __init__(self, module_name, iri, store):
        self.store = store

        self.module_name = module_name
        self.iri = iri

        self.parents = []

    def visit(self, node):
        # indent = " " * len(self.parents)
        # print(f"{indent}>{node}")
        self.parents.append(node)
        super().visit(node)
        self.parents.pop()
        # print(f"{indent}<{node}")

    def visit_FunctionDef(self, node):
        function_iri = IRI(f"{self.iri.value}/{node.name}")
        self.store.insert(function_iri, TYPE, FUNCTION)
        self.store.insert(function_iri, LABEL, node.name)
        self.store.insert(function_iri, DEFINED_IN, self.iri)

        visitor = FunctionVisitor(f"{self.module_name}.{node.name}", function_iri, self.parents, self.store)
        visitor.generic_visit(node)

    def visit_ClassDef(self, node):
        class_iri = IRI(f"{self.iri.value}/{node.name}")
        self.store.insert(class_iri, TYPE, CLASS)
        self.store.insert(class_iri, LABEL, node.name)
        self.store.insert(class_iri, DEFINED_IN, self.iri)

        class_visitor = ClassVisitor(f"{self.module_name}.{node.name}", class_iri, self.parents, self.store)
        class_visitor.generic_visit(node)

    def visit_Import(self, node):
        for n in node.names:
            # label = "" if n.asname is None else n.asname
            # print(f'{self.module_label} -> {n.name} [label="{label}"]')
            import_iri = IRI(f"http://example.com/{n.name}")
            self.store.insert(import_iri, TYPE, UNIT)
            self.store.insert(import_iri, LABEL, n.name)
            self.store.insert(self.iri, IMPORTS, import_iri)

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        #  TODO: What does node.module is None mean?
        if node.module is not None:
            # print(f"{self.module_label} -> {self._label(node.module, node.level)}")

            name = self._sub_module_name(node.module, node.level)
            import_iri = IRI(f"http://example.com/{name}")
            self.store.insert(import_iri, TYPE, UNIT)
            self.store.insert(import_iri, LABEL, name)
            self.store.insert(self.iri, IMPORTS, import_iri)

        self.generic_visit(node)

    def _sub_module_name(self, module_name, level):
        if level != 0:
            module_name = ".".join(self.module_name.split(".")[:-level] + [module_name])

        return module_name


class ClassVisitor(ast.NodeVisitor):
    def __init__(self, qname, iri, parents, store):
        self.store = store

        self.qname = qname
        self.iri = iri

        self.parents = copy.copy(parents)

    def visit(self, node):
        # indent = " " * len(self.parents)
        # print(f"{indent}>{node}")
        self.parents.append(node)
        super().visit(node)
        self.parents.pop()
        # print(f"{indent}<{node}")

    def visit_FunctionDef(self, node):
        function_iri = IRI(f"{self.iri.value}/{node.name}")
        self.store.insert(function_iri, TYPE, FUNCTION)
        self.store.insert(function_iri, LABEL, node.name)
        self.store.insert(function_iri, DEFINED_IN, self.iri)

        visitor = FunctionVisitor(f"{self.qname}.{node.name}", function_iri, self.parents, self.store)
        visitor.generic_visit(node)

    def visit_Import(self, node):
        for n in node.names:
            # label = "" if n.asname is None else n.asname
            # print(f'{self.module_label} -> {n.name} [label="{label}"]')
            import_iri = IRI(f"http://example.com/{n.name}")
            self.store.insert(import_iri, TYPE, UNIT)
            self.store.insert(import_iri, LABEL, n.name)
            self.store.insert(self.iri, IMPORTS, import_iri)

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        #  TODO: What does node.module is None mean?
        if node.module is not None:
            # print(f"{self.module_label} -> {self._label(node.module, node.level)}")

            name = self._sub_module_name(node.module, node.level)
            import_iri = IRI(f"http://example.com/{name}")
            self.store.insert(import_iri, TYPE, UNIT)
            self.store.insert(import_iri, LABEL, name)
            self.store.insert(self.iri, IMPORTS, import_iri)

        self.generic_visit(node)

    def _sub_module_name(self, module_name, level):
        if level != 0:
            module_name = ".".join(self.module_name.split(".")[:-level] + [module_name])

        return module_name


class FunctionVisitor(ast.NodeVisitor):
    def __init__(self, qname, iri, parents, store):
        self.store = store

        self.qname = qname
        self.iri = iri

        self.parents = copy.copy(parents)

    def visit(self, node):
        # indent = " " * len(self.parents)
        # print(f"{indent}>{self.qname} {type(node)} {node}")
        self.parents.append(node)
        super().visit(node)
        self.parents.pop()
        # print(f"{indent}<{self.qname} {type(node)} {node}")

    def visit_Call(self, node):
        # print(node)
        # print(dir(node))
        if type(node.func) == ast.Name:
            name = f"{node.func.id}"
        elif type(node.func) == ast.Attribute:
            name = f"{node.func.value}.{node.func.attr}"
        else:
            print(node.func)
            name = str(node.func)

        print(f"{name}(*{node.args}, **{node.keywords})")

    def visit_FunctionDef(self, node):
        function_iri = IRI(f"{self.iri.value}/{node.name}")
        self.store.insert(function_iri, TYPE, FUNCTION)
        self.store.insert(function_iri, LABEL, node.name)
        self.store.insert(function_iri, DEFINED_IN, self.iri)

        # self.generic_visit(node)

    def visit_Import(self, node):
        for n in node.names:
            # label = "" if n.asname is None else n.asname
            # print(f'{self.module_label} -> {n.name} [label="{label}"]')
            import_iri = IRI(f"http://example.com/{n.name}")
            self.store.insert(import_iri, TYPE, UNIT)
            self.store.insert(import_iri, LABEL, n.name)
            self.store.insert(self.iri, IMPORTS, import_iri)

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        #  TODO: What does node.module is None mean?
        if node.module is not None:
            # print(f"{self.module_label} -> {self._label(node.module, node.level)}")

            name = self._sub_module_name(node.module, node.level)
            import_iri = IRI(f"http://example.com/{name}")
            self.store.insert(import_iri, TYPE, UNIT)
            self.store.insert(import_iri, LABEL, name)
            self.store.insert(self.iri, IMPORTS, import_iri)

        self.generic_visit(node)

    def _sub_module_name(self, module_name, level):
        if level != 0:
            module_name = ".".join(self.module_name.split(".")[:-level] + [module_name])

        return module_name


def _alias(n):
    if n.asname is None:
        return n.name
    else:
        return f"{n.name} as {n.asname}"


def iter_modules(filename):
    for info in pkgutil.iter_modules([filename]):
        if info.ispkg:
            yield info

            path = getattr(sys.modules[info.name], "__path__", None) or []

            yield from pkgutil.walk_packages(path, info.name + ".")


def plot(store, filename):
    with open(filename, "w") as fo:
        fo.write(f"# {len(store)}\n")

        units = [
            (s.get(Variable("unit_iri")), s.get(Variable("unit_name")))
            for s in engine.execute(
                store,
                [(Variable("unit_iri"), TYPE, UNIT), (Variable("unit_iri"), LABEL, Variable("unit_name"))],
                [OrderCondition("unit_name", Order.ASCENDING)],
            )[0]
        ]

        n_map = {s[0]: i for i, s in enumerate(units)}

        fo.write("digraph G {\n")
        fo.write('    rankdir = "TB"\n')
        fo.write("    newrank = true\n")
        fo.write("    K = 1.5\n")
        fo.write("    node [shape=box]\n")

        for unit_iri, unit_name in units:
            fo.write(f'    n{n_map[unit_iri]} [label="{unit_name}"]')

        for s in engine.execute(
            store, [(Variable("a"), IMPORTS, Variable("b"))], [OrderCondition("a", Order.ASCENDING)]
        )[0]:
            fo.write(f'    n{n_map[s.get(Variable("a"))]} -> n{n_map[s.get(Variable("b"))]}')

        fo.write("}\n")


def plot_functions(store, filename):
    with open(filename, "w") as fo:
        fo.write(f"# {len(store)}\n")

        units = [
            (s.get(Variable("unit_iri")), s.get(Variable("unit_name")))
            for s in engine.execute(
                store,
                [(Variable("unit_iri"), TYPE, UNIT), (Variable("unit_iri"), LABEL, Variable("unit_name"))],
                [OrderCondition("unit_name", Order.ASCENDING)],
            )[0]
        ]

        counter = count()
        n_map = defaultdict(lambda: next(counter))

        fo.write("digraph G {\n")
        fo.write('    rankdir = "TB"\n')
        fo.write("    newrank = true\n")
        fo.write("    K = 1.5\n")
        fo.write("    node [shape=box]\n")

        for unit_iri, unit_name in units:
            _subgraph(fo, store, n_map, unit_iri, unit_name)

        fo.write("}\n")


def _subgraph(fo, store, n_map, unit_iri, unit_name):
    fo.write(f"   subgraph cluster_n{n_map[unit_iri]} {{")
    fo.write(f'       label="{unit_name}"')

    functions = [
        (s.get(Variable("a")), s.get(Variable("function_name")), s.get(Variable("type")))
        for s in engine.execute(
            store,
            [
                (Variable("a"), DEFINED_IN, unit_iri),
                (Variable("a"), LABEL, Variable("function_name")),
                (Variable("a"), TYPE, Variable("type")),
            ],
            [OrderCondition("a", Order.ASCENDING)],
        )[0]
    ]

    for i, (function_iri, function_name, type) in enumerate(functions):
        if type == FUNCTION:
            fo.write(f'        n{n_map[unit_iri]}_{i} [label="{function_name}"]')
        elif type == CLASS:
            _subgraph(fo, store, n_map, function_iri, function_name)

    fo.write("    }")


def main(filename):
    store = InMemoryHexastore()
    reasoner = make_default_forward_reasoner(store)

    reasoner.insert(PACKAGE, SUBCLASS_OF, UNIT)
    reasoner.insert(MODULE, SUBCLASS_OF, UNIT)

    # print("digraph G {")

    for finder, sub_module_name, ispkg in iter_modules(filename):
        spec = finder.find_spec(sub_module_name)
        iri = IRI(f"http://example.com/{sub_module_name}")
        reasoner.insert(iri, TYPE, PACKAGE if ispkg else MODULE)
        reasoner.insert(iri, LABEL, sub_module_name)

        with open(spec.origin) as fo:
            source = fo.read()

        tree = ast.parse(source, spec.origin)
        visitor = ModuleVisitor(sub_module_name, iri, reasoner)
        visitor.visit(tree)

        # for module_label, module_name in visitor.modules:
        #     print(f'{module_label} [label="{module_name}"]')

        if ispkg:
            loader, _ = finder.find_loader(sub_module_name)
            loader.load_module(sub_module_name)

    # print("}")

    util_plot(store, "foo_raw.dot")
    plot(store, "foo.dot")
    plot_functions(store, "foo_functions.dot")


main(*sys.argv[1:])
