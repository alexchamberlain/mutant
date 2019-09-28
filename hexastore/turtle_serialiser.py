import decimal
from collections import defaultdict
from dataclasses import dataclass

from .ast import IRI, BlankNode, LangTaggedString, TypedLiteral

TYPE = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")


def serialise(store, fo, namespaces):
    serialiser = _Serialiser(store, namespaces)
    serialiser(fo)


class _Serialiser:
    def __init__(self, store, namespaces):
        self._store = store
        self._namespaces = namespaces
        self._blank_node_counter = 1
        self._terms = {t: self._serialise_term(t) for t in store.terms()}

        self._stats = defaultdict(Stat)

    def __call__(self, fo):
        for n, i in self._namespaces:
            fo.write(f"@prefix {n}: <{i.value}> .\n")
        fo.write("\n")

        for s, p, o in self._store.triples():
            self._stats[o].increment()

        for s, po in _reorder(self._store.spo.items()):
            if isinstance(s, BlankNode) and self._stats[s].references == 1:
                continue

            pss = self._serialise_triple(s, po)
            if pss:
                fo.write(f"{pss} .\n\n")

    def _serialise_triple(self, s, po):
        ps = []

        if TYPE in po:
            ps += [self._serialise_predicate_object_list(TYPE, po[TYPE])]

        ps += [self._serialise_predicate_object_list(p, os) for p, os in po.items() if p != TYPE]
        pss = " ;\n    ".join(ps)

        if pss:
            return f"{self._terms[s]} {pss}"

    def _serialise_predicate_object_list(self, p, os, level=1):
        assert level < 10

        objs = [self._serialise_object(o, level) for o in os.iter()]
        o = ", ".join(objs)

        return f"{self._terms[p]} {o}" if o else ""

    def _serialise_object(self, o, level):
        if isinstance(o, BlankNode) and self._stats[o].references == 1:
            po = self._store.spo[o]
            ps = []

            if TYPE in po:
                ps += [self._serialise_predicate_object_list(TYPE, po[TYPE], level + 1)]

            ps += [self._serialise_predicate_object_list(p, os, level + 1) for p, os in po.items() if p != TYPE]
            pss = " ;\n    ".join(ps)

            return f"[\n        {pss}\n    ]"
        else:
            return self._terms[o]

    def _serialise_term(self, t):
        if t == TYPE:
            return "a"
        elif isinstance(t, IRI):
            # TODO: Make this better
            for n, i in self._namespaces:
                if t.value.startswith(i.value):
                    return f"{n}:{t.value[len(i.value):]}"
            return f"<{t.value}>"
        elif isinstance(t, str):
            return f'"{t}"'
        elif isinstance(t, int) or isinstance(t, decimal.Decimal):
            return str(t)
        elif isinstance(t, tuple) and len(t) == 3:
            return f"<< {self._serialise_term(t[0])} {self._serialise_term(t[1])} {self._serialise_term(t[2])} >>"
        elif isinstance(t, BlankNode):
            s = f"_:{self._blank_node_counter}"
            self._blank_node_counter += 1
            return s
        elif isinstance(t, TypedLiteral):
            return f'"{t.value}"^^{self._serialise_term(t.datatype)}'
        elif isinstance(t, LangTaggedString):
            return f'"{t.value}"@{t.language}'
        else:
            raise TypeError(f"Unknown type {type(t)} ({t})")


def _reorder(iter_):
    iter_ = iter(iter_)
    reified_statements = []
    for s, po in iter_:
        if not isinstance(s, tuple):
            break

        reified_statements.append((s, po))

    yield s, po
    yield from iter_
    yield from iter(reified_statements)


@dataclass
class Stat:
    references: int = 0

    def increment(self):
        self.references += 1
