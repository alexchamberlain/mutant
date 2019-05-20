import logging
import pkgutil
from typing import List, Union, Tuple

import attr
from lark import Lark, Transformer, v_args

from . import engine
from .ast import IRI, Variable
from .model import Solution
from .namespace import Namespace

logger = logging.getLogger(__name__)

MEMBER = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#member")
TYPE = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")

TermPattern = Union[IRI, str, Variable]
TriplePattern = Tuple[TermPattern, TermPattern, TermPattern]

rule_parser = Lark(pkgutil.get_data("hexastore", "lark/rule.lark").decode(), start="document", parser="lalr")


def parse_and_register(document, store):
    rules = parse(document)

    for r in rules:
        if len(r.body) == 1:
            pattern = r.body[0]
            store.register_predicate_rule(pattern[1], GeneralRule1(pattern[0], pattern[2], r.head))
        else:
            for i, pattern in enumerate(r.body):
                rest = [p for j, p in enumerate(r.body) if i != j]
                store.register_predicate_rule(pattern[1], GeneralRuleMany(pattern[0], pattern[2], rest, r.head))


def parse(document):
    tree = rule_parser.parse(document)

    transformer = _Transformer()
    return transformer.transform(tree)


class GeneralRule1:
    def __init__(self, s: Variable, o: Variable, head: List[TriplePattern]):
        self._s = s
        self._o = o
        self._head = head

    def __call__(self, store, s, p, o, insert):
        for s, os in store.pso[p].items():
            for o, status in os.items():
                if not status.inserted:
                    continue

                solution = Solution({self._s: s, self._o: o}, [])

                for triple_pattern in self._head:
                    triple = _resolve(triple_pattern, solution)
                    logger.debug(f"triple {triple}")
                    insert(triple, (s, p, o))


class GeneralRuleMany:
    def __init__(self, s: Variable, o: Variable, rest: List[TriplePattern], head: List[TriplePattern]):
        self._s = s
        self._o = o
        self._rest = rest
        self._head = head

    def __call__(self, store, s, p, o, insert):
        for s, os in store.pso[p].items():
            for o, status in os.items():
                if not status.inserted:
                    continue

                solution = Solution({self._s: s, self._o: o}, [])

                patterns = [_resolve(triple_pattern, solution) for triple_pattern in self._rest]
                solutions = engine.execute(store, patterns, [], solution)

                for solution in solutions:
                    for triple_pattern in self._head:
                        triple = _resolve(triple_pattern, solution)
                        insert(triple, (s, p, o))


def _resolve(triple_pattern, solution):
    logger.debug(f"_resolve {triple_pattern} {solution}")
    return (_s(triple_pattern[0], solution), _s(triple_pattern[1], solution), _s(triple_pattern[2], solution))


def _s(term: TermPattern, solution: Solution) -> TermPattern:
    if isinstance(term, Variable):
        return solution.get(term, term)

    return term


@attr.s
class Rule:
    body = attr.ib()
    head = attr.ib()


class _Transformer(Transformer):
    def __init__(self):
        self._namespaces = {}

    @v_args(inline=True)
    def document(self, preamble, rules):
        return rules

    @v_args(inline=True)
    def prefix(self, prefix, iri):
        n = Namespace(prefix, iri)
        self._namespaces[prefix] = n
        return n

    def rules(self, children):
        return children

    @v_args(inline=True)
    def rule(self, r):
        return r

    @v_args(inline=True)
    def terminating_rule(self, body, head):
        return Rule(body.children, head.children)

    @v_args(inline=True)
    def recursive_rule(self, body, rule):
        return Rule(body.children, rule)

    @v_args(inline=True)
    def triple(self, s, p, o):
        return (s, p, o)

    @v_args(inline=True)
    def prefixed_name(self, prefix, local):
        n = self._namespaces[prefix]
        return n.term(local)

    @v_args(inline=True)
    def var(self, name):
        return Variable(str(name))

    @v_args(inline=True)
    def iriref(self, iri):
        return IRI(str(iri))

    @v_args(inline=True)
    def predicate(self, p):
        return p

    @v_args(inline=True)
    def a(self):
        return TYPE

    @v_args(inline=True)
    def member_of(self):
        return MEMBER
