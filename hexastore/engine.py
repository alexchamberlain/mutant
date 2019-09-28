import functools
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, AbstractSet, Any, Iterator, List, Sequence, Tuple, Union

import attr

from .ast import IRI, Order, OrderCondition, Variable
from .model import Solution
from .typing import Hexastore, Term, Triple
from .util import triple_map

IS_NOT = IRI("http://example.org/isNot")

SUBJECT = 1
PREDICATE = 2
OBJECT = 4

TermPattern = Union[IRI, str, Variable]
TermPatternPrime = Union[IRI, str, "VariableWithOrderInformation"]
TriplePattern = Tuple[TermPattern, TermPattern, TermPattern]
TriplePatternPrime = Tuple[TermPatternPrime, TermPatternPrime, TermPatternPrime]

logger = logging.getLogger(__name__)


@functools.total_ordering
@attr.s(frozen=True, cmp=False, hash=True)
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


def execute(
    store: Hexastore, patterns: Sequence[TriplePattern], order_by: List[OrderCondition], bindings: Solution = None
) -> Sequence[Solution]:
    if bindings is None:
        bindings = Solution({}, order_by, set())
    engine_ = _Engine(store, order_by)
    return engine_(patterns, bindings)


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

    def __call__(self, patterns: Sequence[TriplePattern], bindings: Solution) -> Sequence[Solution]:
        if not patterns:
            return [Solution({}, self.order_by, set())]

        patterns = sorted(patterns, key=_count_variables)

        solutions = list(map(_Merge(bindings), self._match(patterns[0])))

        for triple_pattern in patterns[1:]:
            solutions = list(self._process_pattern(triple_pattern, solutions))

        # TODO: Can we reorg the algorithm above so that solutions is already sorted?
        return sorted(solutions), self.stats

    def _process_pattern(self, triple_pattern: TriplePattern, solutions: Sequence[Solution]) -> Iterator[Solution]:
        for s in solutions:
            tp = (_s(triple_pattern[0], s), _s(triple_pattern[1], s), _s(triple_pattern[2], s))
            yield from map(_Merge(s), self._match(tp))

    def _match(self, triple_pattern_: TriplePattern) -> Iterator[Solution]:
        logger.debug(f"triple_pattern_ {triple_pattern_}")

        triple_pattern, index_key = tuple(
            zip(*sorted(zip(triple_map(self._preprocess_term, triple_pattern_), (SUBJECT, PREDICATE, OBJECT))))
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
            s = triple_pattern[0]
            po = index[s]
            variables_2 = (triple_pattern[1].to_variable(), triple_pattern[2].to_variable())
            for p, o_list in po.items(order=triple_pattern[1].order_by_direction):
                for o in o_list.iter(triple_pattern[2].order_by_direction, self.stats.increment_triples):
                    yield dzip(variables_2, (p, o), self.order_by, {transform((s, p, o))})
        elif isinstance(triple_pattern[2], VariableWithOrderInformation):
            s = triple_pattern[0]
            p = triple_pattern[1]
            po = index[s]
            o_list = po[p]
            variables_1 = (triple_pattern[2].to_variable(),)
            for o in o_list.iter(triple_pattern[2].order_by_direction, self.stats.increment_triples):
                yield dzip(variables_1, (o,), self.order_by, {transform((s, p, o))})
        else:
            if triple_pattern in self.store:
                yield Solution({}, self.order_by, {transform(triple_pattern)})


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
