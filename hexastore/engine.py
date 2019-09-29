import functools
import itertools
from dataclasses import dataclass
from typing import TYPE_CHECKING, AbstractSet, Any, Iterator, List, Optional, Sequence, Tuple, Union

import attr

from .ast import IRI, Order, OrderCondition, Variable
from .engine_ast import (
    BGP,
    Distinct,
    Filter,
    GroupAggregate,
    LeftJoin,
    Limit,
    Project,
    Reduced,
    TermPattern,
    TriplePattern,
)
from .model import Key, Solution
from .typing import Hexastore, Term, Triple
from .util import triple_map

IS_NOT = IRI("http://example.org/isNot")

SUBJECT = 1
PREDICATE = 2
OBJECT = 4


@functools.total_ordering
@attr.s(frozen=True, eq=False, hash=True)
class VariableWithOrderInformation:
    variable_name: str = attr.ib()
    order_by_index: int = attr.ib()
    order_by_direction: Order = attr.ib()

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, VariableWithOrderInformation):
            return False

        return self.order_by_index < other.order_by_index or (
            self.order_by_index == other.order_by_index and self.variable_name < other.variable_name
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, VariableWithOrderInformation):
            return False

        return self.variable_name == other.variable_name

    def to_variable(self) -> Variable:
        return Variable(self.variable_name)


TermPatternPrime = Union[IRI, str, VariableWithOrderInformation]
TriplePatternPrime = Tuple[TermPatternPrime, TermPatternPrime, TermPatternPrime]


def execute(
    store: Hexastore,
    patterns: Union[Sequence[TriplePattern], BGP, LeftJoin, Distinct],
    order_by: List[OrderCondition],
    bindings: Solution = None,
) -> Sequence[Solution]:
    if bindings is None:
        bindings = Solution({}, order_by, set())
    engine_ = _Engine(store, order_by)

    return list(engine_(patterns, bindings)), engine_.stats


class _Engine:
    def __init__(self, store: Hexastore, order_by: List[OrderCondition]):
        self.store = store
        self.order_by = order_by

        self.variable_map = {c.variable_name: (i, c.direction) for i, c in enumerate(order_by)}
        self.len_order_by = len(order_by)
        self.stats = Stats()

    def _preprocess_term(self, term: TermPattern) -> TermPatternPrime:
        if isinstance(term, Variable):
            index, direction = self.variable_map.get(term.value, (self.len_order_by, Order.ASCENDING))
            return VariableWithOrderInformation(term.value, index, direction)

        return term

    def __call__(self, patterns, bindings):
        if isinstance(patterns, list):
            patterns = BGP(patterns)

        if isinstance(patterns, BGP):
            return self.apply_bgp(patterns.patterns, patterns.limit, bindings)
        elif isinstance(patterns, Limit):
            lhs_solutions = self(patterns.patterns, bindings)
            return itertools.islice(lhs_solutions, patterns.limit)
        elif isinstance(patterns, LeftJoin):
            lhs_solutions = self(patterns.lhs, bindings)

            solutions = []
            for bindings in lhs_solutions:
                rhs_solutions = self(patterns.rhs.patterns, bindings)
                if rhs_solutions:
                    solutions.extend(rhs_solutions)
                else:
                    solutions.append(bindings)
            return sorted(solutions)
        elif isinstance(patterns, Filter):
            solutions = self(patterns.pattern, bindings)
            return filter(patterns.filter, solutions)
        elif isinstance(patterns, Project):
            rhs_solutions = self(patterns.pattern, bindings)
            return (
                Solution({v: s.get(v) for v in patterns.variables}, self.order_by, s.triples) for s in rhs_solutions
            )
        elif isinstance(patterns, Distinct) or isinstance(patterns, Reduced):
            solutions = self(patterns.pattern, bindings)
            return (s for s, _ in itertools.groupby(solutions))
        elif isinstance(patterns, GroupAggregate):
            rhs_solutions = self(patterns.pattern, bindings)
            return self._group_aggregate(patterns.variables, patterns.function, rhs_solutions)
        else:
            print(f"type {type(patterns)}")
            assert False

    def apply_bgp(
        self, patterns: Sequence[TriplePattern], limit: Optional[int], bindings: Solution
    ) -> Sequence[Solution]:
        if not patterns:
            return [Solution({}, self.order_by, set())]

        patterns = sorted(patterns, key=_count_variables)

        tp = (_s(patterns[0][0], bindings), _s(patterns[0][1], bindings), _s(patterns[0][2], bindings))
        solutions = map(_Merge(bindings), self._match(tp))

        for triple_pattern in patterns[1:]:
            solutions = self._process_pattern(triple_pattern, solutions)

        if limit is not None:
            solutions = itertools.islice(solutions, limit)

        # TODO: Can we reorg the algorithm above so that solutions is already sorted?
        return sorted(solutions)

    def _process_pattern(self, triple_pattern: TriplePattern, solutions: Sequence[Solution]) -> Iterator[Solution]:
        for s in solutions:
            tp = (_s(triple_pattern[0], s), _s(triple_pattern[1], s), _s(triple_pattern[2], s))
            yield from map(_Merge(s), self._match(tp))

    def _match(self, triple_pattern_: TriplePattern) -> Iterator[Solution]:
        triple_pattern, index_key = tuple(
            zip(
                *sorted(
                    zip(triple_map(self._preprocess_term, triple_pattern_), (SUBJECT, PREDICATE, OBJECT)),
                    key=lambda t: (t[0] if isinstance(t[0], VariableWithOrderInformation) else Key(t[0]), t[1]),
                )
            )
        )

        if TYPE_CHECKING:
            assert isinstance(index_key, Tuple[int, int, int])

        index, transform = {
            (SUBJECT, PREDICATE, OBJECT): (self.store.spo, lambda t: t),
            (PREDICATE, OBJECT, SUBJECT): (self.store.pos, lambda t: (t[2], t[0], t[1])),
            (OBJECT, SUBJECT, PREDICATE): (self.store.osp, lambda t: (t[1], t[2], t[0])),
            (SUBJECT, OBJECT, PREDICATE): (self.store.sop, lambda t: (t[0], t[2], t[1])),
            (OBJECT, PREDICATE, SUBJECT): (self.store.ops, lambda t: (t[2], t[1], t[0])),
            (PREDICATE, SUBJECT, OBJECT): (self.store.pso, lambda t: (t[1], t[0], t[2])),
        }[index_key]

        if isinstance(triple_pattern[0], VariableWithOrderInformation):
            variables_3 = (
                triple_pattern[0].to_variable(),
                triple_pattern[1].to_variable(),
                triple_pattern[2].to_variable(),
            )
            order = (
                triple_pattern[0].order_by_direction,
                triple_pattern[1].order_by_direction,
                triple_pattern[2].order_by_direction,
            )
            for s, po in index.items(order=order[0]):
                for p, oid in po.items(order=order[1]):
                    for o in oid.iter(order[2], self.stats.increment_triples):
                        yield dzip(variables_3, (s, p, o), self.order_by, {transform((s, p, o))})
        elif isinstance(triple_pattern[1], VariableWithOrderInformation):
            try:
                s = triple_pattern[0]
                po = index[s]
                variables_2 = (triple_pattern[1].to_variable(), triple_pattern[2].to_variable())
                for p, o_list in po.items(order=triple_pattern[1].order_by_direction):
                    for o in o_list.iter(triple_pattern[2].order_by_direction, self.stats.increment_triples):
                        yield dzip(variables_2, (p, o), self.order_by, {transform((s, p, o))})
            except KeyError:
                return
        elif isinstance(triple_pattern[2], VariableWithOrderInformation):
            try:
                s = triple_pattern[0]
                p = triple_pattern[1]
                po = index[s]
                o_list = po[p]
                variables_1 = (triple_pattern[2].to_variable(),)
                for o in o_list.iter(triple_pattern[2].order_by_direction, self.stats.increment_triples):
                    yield dzip(variables_1, (o,), self.order_by, {transform((s, p, o))})
            except KeyError:
                return
        else:
            if triple_pattern[2] in index[triple_pattern[0]][triple_pattern[1]]:
                self.stats.increment_triples()
                yield Solution({}, self.order_by, {transform(triple_pattern)})

    def _group_aggregate(self, variables, function, rhs_solutions):
        for key, subsolutions in itertools.groupby(
            rhs_solutions, lambda s: Solution({v: s.get(v) for v in variables}, self.order_by, s.triples)
        ):
            yield function(key, subsolutions)


def _s(term: TermPattern, solution: Solution) -> TermPattern:
    if isinstance(term, Variable):
        return solution.get(term, term)

    return term


def _count_variables(pattern: TriplePattern) -> int:
    return sum(1 for t in pattern if isinstance(t, Variable))


def dzip(
    variables: Sequence[Variable], values: Sequence[Term], order_by: List[OrderCondition], triples: AbstractSet[Triple]
) -> Solution:
    return Solution(dict(zip(variables, values)), order_by, triples)


# def order_index(order_by: Sequence[OrderCondition], x: ):
#     return next((i for i, v in enumerate(order_by) if v[0] == x), len(order_by))


class _Merge:
    def __init__(self, lhs: Solution):
        self.lhs = lhs

    def __call__(self, rhs: Solution) -> Solution:
        return self.lhs.mutate(rhs)


@dataclass
class Stats:
    triples_visited: int = 0

    def increment_triples(self):
        self.triples_visited += 1
