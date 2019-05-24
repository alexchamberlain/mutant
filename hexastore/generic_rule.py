import logging
import pkgutil
from typing import List, Union, Tuple, Callable

import attr
from lark import Lark, Transformer, v_args

from . import engine
from .ast import IRI, Variable
from .model import Solution
from .namespace import Namespace
from .typing import Triple

logger = logging.getLogger(__name__)

MEMBER = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#member")
TYPE = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
IS_NOT = IRI("http://example.org/isNot")

TermPattern = Union[IRI, str, Variable]
TriplePattern = Tuple[TermPattern, TermPattern, TermPattern]

rule_parser = Lark(pkgutil.get_data("hexastore", "lark/rule.lark").decode(), start="document", parser="lalr")


@attr.s
class Rule:
    body = attr.ib()
    constraints = attr.ib()
    head = attr.ib()


@attr.s
class RecursiveRule:
    body = attr.ib()
    constraints = attr.ib()
    head = attr.ib()


def parse_and_register(document, store):
    rules = parse(document)

    def register_predicate_rule(p, callback, inferred_from):
        store.register_predicate_rule(p, 0, callback, inferred_from)

    for r in rules:
        _register_rule(r, register_predicate_rule, [])


def _register_rule(r, register_predicate_rule, inferred_from):
    logger.debug(f"Registering {r}")
    if len(r.body) == 1:
        pattern = r.body[0]

        if isinstance(r, RecursiveRule):
            logger.debug(f"Registering RecursiveRule1")
            register_predicate_rule(
                pattern[1], RecursiveRule1(pattern[0], pattern[2], r.constraints, r.head, inferred_from), inferred_from
            )
        else:
            register_predicate_rule(
                pattern[1], GeneralRule1(pattern[0], pattern[2], r.constraints, r.head, inferred_from), inferred_from
            )
    else:
        for i, pattern in enumerate(r.body):
            rest = [p for j, p in enumerate(r.body) if i != j]

            if isinstance(r, RecursiveRule):
                assert False
            else:
                register_predicate_rule(
                    pattern[1],
                    GeneralRuleMany(pattern[0], pattern[2], rest, r.constraints, r.head, inferred_from),
                    inferred_from,
                )


def parse(document):
    tree = rule_parser.parse(document)

    transformer = _Transformer()
    return transformer.transform(tree)


class GeneralRule1:
    def __init__(
        self,
        s: Variable,
        o: Variable,
        constraints: List[Callable[[Solution], bool]],
        head: List[TriplePattern],
        inferred_from: List[Triple],
    ):
        self._s = s
        self._o = o
        self._constraints = constraints
        self._head = head
        self._inferred_from = inferred_from

    def __repr__(self):
        return f"GeneralRule1({self._s} {self._o} {self._constraints} {self._head} {self._inferred_from})"

    def __call__(self, store, s, p, o):
        logger.debug(f"Applying {self} to {s}, {p}, {o}")
        for s, os in store.pso[p].items():
            if isinstance(self._s, Variable):
                s_solution = Solution({self._s: s}, [])
            elif s != self._s:
                continue
            else:
                s_solution = Solution({self._s: s}, [])

            for o, status in os.items():
                if not status.inserted:
                    continue

                if isinstance(self._o, Variable):
                    solution = s_solution.copy()
                    solution.update({self._o: o})
                elif o != self._o:
                    continue
                else:
                    solution = s_solution

                constraints_pass = True
                for constraint in self._constraints:
                    if not constraint(solution):
                        constraints_pass = False
                        break

                if not constraints_pass:
                    continue

                for triple_pattern in self._head:
                    triple = _resolve(triple_pattern, solution)
                    logger.debug(f"triple {triple}")
                    store.insert(triple, self._inferred_from + [(s, p, o)])


class RecursiveRule1:
    def __init__(
        self,
        s: Variable,
        o: Variable,
        constraints: List[Callable[[Solution], bool]],
        head: Rule,
        inferred_from: List[Triple],
    ):
        self._s = s
        self._o = o
        self._constraints = constraints
        self._head = head
        self._inferred_from = inferred_from

    def __repr__(self):
        return f"RecursiveRule1({self._s} {self._o} {self._constraints} {self._head} {self._inferred_from})"

    def __call__(self, store, s, p, o):
        logger.debug(f"Applying {self} to {s}, {p}, {o}")
        for s, os in store.pso[p].items():
            if isinstance(self._s, Variable):
                s_solution = Solution({self._s: s}, [])
            elif s != self._s:
                continue
            else:
                s_solution = Solution({self._s: s}, [])

            for o, status in os.items():
                if not status.inserted:
                    continue

                if isinstance(self._o, Variable):
                    solution = s_solution.copy()
                    solution.update({self._o: o})
                elif o != self._o:
                    continue
                else:
                    solution = s_solution

                constraints_pass = True
                for constraint in self._constraints:
                    if not constraint(solution):
                        constraints_pass = False
                        break

                if not constraints_pass:
                    continue

                for head in self._head:
                    new_rule = Rule(
                        _resolve_patterns(head.body, solution),
                        _resolve_constraints(head.constraints, solution),
                        _resolve_patterns(head.head, solution),
                    )
                    _register_rule(new_rule, store.register_predicate_rule, self._inferred_from + [(s, p, o)])


class GeneralRuleMany:
    def __init__(
        self,
        s: Variable,
        o: Variable,
        rest: List[TriplePattern],
        constraints: List[Callable[[Solution], bool]],
        head: List[TriplePattern],
        inferred_from: List[Triple],
    ):
        self._s = s
        self._o = o
        self._rest = rest
        self._constraints = constraints
        self._head = head
        self._inferred_from = inferred_from

    def __repr__(self):
        return f"GeneralRuleMany({self._s}, {self._o}, {self._rest}, {self._constraints}, {self._head}, {self._inferred_from})"

    def __call__(self, store, s, p, o):
        logger.debug(f"Applying {self} to {s}, {p}, {o}")
        for s, os in store.pso[p].items():
            if isinstance(self._s, Variable):
                s_solution = Solution({self._s: s}, [])
            elif s != self._s:
                continue
            else:
                s_solution = Solution({self._s: s}, [])

            for o, status in os.items():
                if not status.inserted:
                    continue

                if isinstance(self._o, Variable):
                    solution = s_solution.copy()
                    solution.update({self._o: o})
                elif o != self._o:
                    continue
                else:
                    solution = s_solution

                patterns = [_resolve(triple_pattern, solution) for triple_pattern in self._rest]
                logger.debug(f"patterns {patterns}")
                solutions = engine.execute(store, patterns, [], solution)

                for solution in solutions:
                    constraints_pass = True
                    for constraint in self._constraints:
                        if not constraint(solution):
                            constraints_pass = False
                            break

                    if not constraints_pass:
                        continue

                    for triple_pattern in self._head:
                        triple = _resolve(triple_pattern, solution)
                        store.insert(triple, self._inferred_from + [(s, p, o)])


def _resolve_patterns(patterns, solution):
    return [_resolve(p, solution) for p in patterns]


def _resolve_constraints(constraints, solution):
    for c in constraints:
        assert solution.variables().isdisjoint(set(c._variables))

    return constraints


def _resolve(triple_pattern, solution):
    logger.debug(f"_resolve {triple_pattern} {solution}")
    return (_s(triple_pattern[0], solution), _s(triple_pattern[1], solution), _s(triple_pattern[2], solution))


def _s(term: TermPattern, solution: Solution) -> TermPattern:
    if isinstance(term, Variable):
        return solution.get(term, term)

    return term


class ConstraintIsNot:
    def __init__(self, variables):
        self._variables = variables

    def __eq__(self, other):
        if not isinstance(other, ConstraintIsNot):
            return NotImplemented

        return self._variables == other._variables

    def __call__(self, solution):
        n = len({solution.get(v) for v in self._variables})
        return n == len(self._variables)


class _Transformer(Transformer):
    def __init__(self, namespaces=None):
        self._namespaces = namespaces or {}

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

    def terminating_rule(self, children):
        kwargs = {c.data: c.children for c in children}
        return Rule(kwargs["body"], kwargs.get("constraints", []), kwargs["head"])

    def recursive_rule(self, children):
        rule = children.pop()
        kwargs = {c.data: c.children for c in children}
        return RecursiveRule(kwargs["body"], kwargs.get("constraints", []), rule)

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

    @v_args(inline=True)
    def constraint(self, variable1, op, variable2):
        if op.data == "is_not":
            return ConstraintIsNot([variable1, variable2])
