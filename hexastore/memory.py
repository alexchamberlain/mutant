import functools
import itertools
from collections import defaultdict
from dataclasses import dataclass
from typing import (
    AbstractSet,
    Any,
    Callable,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    ValuesView,
)

from .ast import BlankNode, Order, TripleStatus, TripleStatusItem
from .model import Key
from .sorted import DefaultSortedMapping, SortedList, SortedMapping
from .typing import MutableIndex, MutableOrderedMapping, Term, Triple
from .util import triple_map


@dataclass
class TrunkPayload:
    map: MutableOrderedMapping[Term, MutableOrderedMapping[Term, TripleStatus]]
    n: int = 0

    def __getitem__(
        self, k: Union[Sequence[Term], Term]
    ) -> Union[
        Sequence[Tuple[Term, MutableOrderedMapping[Term, TripleStatus]]], MutableOrderedMapping[Term, TripleStatus]
    ]:
        return self.map[k]

    def items(self, order: Order = Order.ASCENDING):
        return self.map.items(order)

    def __iter__(self) -> Iterator[Term]:
        return iter(self.map)

    def keys(self) -> AbstractSet[Term]:
        return self.map.keys()

    def values(self) -> ValuesView[MutableOrderedMapping[Term, TripleStatus]]:
        return self.map.values()

    def __contains__(self, x: Any) -> bool:
        return x in self.map


_TrunkMappingType = DefaultSortedMapping[Term, TrunkPayload]


def _TrunkMapping(store: Union["VersionedInMemoryHexastore", "InMemoryHexastore"], natural: bool) -> MutableIndex:
    return _TrunkMappingType(lambda leading_term: TrunkPayload(map=store._branch(natural, leading_term)), key=Key)


class _VersionedBranch:
    def __init__(self, factory):
        self._mapping = DefaultSortedMapping[Term, MutableOrderedMapping[Term, TripleStatus]](factory, key=Key)

    def __repr__(self) -> str:
        return f"_VersionedBranch({self._mapping})"

    def iter(self, order, triple_counter=None):
        for o, status in self.items(order=order):
            if triple_counter:
                triple_counter()

            if status.inserted:
                yield o

    def __getitem__(
        self, k: Union[Sequence[Term], Term]
    ) -> Union[
        Sequence[Tuple[Term, MutableOrderedMapping[Term, TripleStatus]]], MutableOrderedMapping[Term, TripleStatus]
    ]:
        return _VersionedListAdapter(self._mapping[k])

    def items(self, order: Order = Order.ASCENDING):
        for k, v in self._mapping.items(order):
            yield k, _VersionedListAdapter(v)

    def __contains__(self, term: Term) -> bool:
        return term in self._mapping

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, _VersionedBranch):
            return self._mapping == other._mapping
        else:
            return self._mapping == other


class _VersionedListAdapter:
    def __init__(self, leaf):
        self._leaf = leaf

    def iter(self, order: Order = Order.ASCENDING, triple_counter=None) -> Iterator[Term]:
        for o, status in self._leaf.items(order):
            if triple_counter:
                triple_counter()

            if status.inserted:
                yield o

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, _VersionedListAdapter):
            return self._leaf == other._leaf
        else:
            return self._leaf == other

    def __contains__(self, other: Any) -> bool:
        return other in self._leaf

    def __setitem__(self, k: Term, v: TripleStatus) -> None:
        self._leaf[k] = v

    def __getitem__(self, x: Term) -> TripleStatus:
        return self._leaf[x]

    def get_or_set(self, o: Term, factory, hint=0):
        return self._leaf.get_or_set(o, lambda: TripleStatus([]), hint)


class VersionedInMemoryHexastore:
    def __init__(self, blank_node_factory: Callable[[], BlankNode]) -> None:
        self.n_triples: int = 0
        self.blank_node_factory = blank_node_factory

        self.spo: MutableIndex = _TrunkMapping(self, True)
        self.pos: MutableIndex = _TrunkMapping(self, True)
        self.osp: MutableIndex = _TrunkMapping(self, True)
        self.sop: MutableIndex = _TrunkMapping(self, False)
        self.ops: MutableIndex = _TrunkMapping(self, False)
        self.pso: MutableIndex = _TrunkMapping(self, False)

        self._lists: Mapping[Term, Mapping[Term, SortedMapping[Term, TripleStatus]]] = defaultdict(
            lambda: defaultdict(lambda: SortedMapping(key=Key))
        )

    def __len__(self) -> int:
        return self.n_triples

    def index(self, triple: Triple) -> Optional[int]:
        for i, t in enumerate(self.triples()):
            if t == triple:
                return i

        return None

    def bulk_insert(self, triples: List[Triple], valid_from: int) -> None:
        sorted_triples = sorted(triples, key=functools.partial(triple_map, Key))

        for s, s_triples in itertools.groupby(sorted_triples, key=lambda t: t[0]):
            assert_tuple_length(s)

            po_index = self.spo[s]
            op_index = self.sop[s]

            for p, p_triples in itertools.groupby(s_triples, key=lambda t: t[1]):
                assert_tuple_length(p)

                o_spo_index = po_index.map[p]

                os_index = self.pos[p]
                so_index = self.pso[p]

                for _, _, o in p_triples:
                    assert_tuple_length(o)

                    _, status = o_spo_index.get_or_set(o, lambda: TripleStatus([]))
                    if status.inserted:
                        continue

                    status.statuses.append(TripleStatusItem(valid_from=valid_from))

                    sp_index = self.osp[o]
                    ps_index = self.ops[o]

                    os_index.map[o][s] = status
                    sp_index.map[s][p] = status

                    assert p in op_index.map[o]
                    assert s in ps_index.map[p]
                    assert o in so_index.map[s]

                    self.n_triples += 1

                    po_index.n += 1
                    op_index.n += 1
                    sp_index.n += 1
                    ps_index.n += 1
                    os_index.n += 1
                    so_index.n += 1

    def insert(self, s: Term, p: Term, o: Term, valid_from: int) -> bool:
        if o in self.spo[s][p]:
            status = self.spo[s][p][o]
            if status.inserted:
                return False
        else:
            status = TripleStatus([])

        assert_tuple_length(s)
        assert_tuple_length(p)
        assert_tuple_length(o)

        status.statuses.append(TripleStatusItem(valid_from=valid_from))

        self.spo[s].map[p][o] = status
        self.pos[p].map[o][s] = status
        self.osp[o].map[s][p] = status

        assert p in self.sop[s].map[o]
        assert s in self.ops[o].map[p]
        assert o in self.pso[p].map[s]

        self.n_triples += 1

        self.spo[s].n += 1
        self.sop[s].n += 1
        self.osp[o].n += 1
        self.ops[o].n += 1
        self.pos[p].n += 1
        self.pso[p].n += 1

        return True

    def delete(self, s: Term, p: Term, o: Term, valid_to: int) -> None:
        if p in self.sop[s][o]:
            self.n_triples -= 1

            self.spo[s].n -= 1
            self.sop[s].n -= 1
            self.osp[o].n -= 1
            self.ops[o].n -= 1
            self.pos[p].n -= 1
            self.pso[p].n -= 1

        if o in self.spo[s][p]:
            status = self.spo[s][p][o]
        else:
            status = TripleStatus([])

        if len(status.statuses):
            status.statuses[-1].valid_to = valid_to
        else:
            status.statuses.append(TripleStatusItem(valid_to=valid_to))

        self.spo[s].map[p][o] = status
        self.pos[p].map[o][s] = status
        self.osp[o].map[s][p] = status

        assert p in self.sop[s][o]
        assert s in self.ops[o][p]
        assert o in self.pso[p][s]

    def terms(self) -> SortedList[Term]:
        return SortedList(set(itertools.chain(self.spo.keys(), self.pos.keys(), self.osp.keys())), key=Key)

    def triples(
        self, index: Optional[MutableIndex] = None, order: Optional[Tuple[Order, Order, Order]] = None
    ) -> Iterable[Triple]:
        if index is None:
            index = self.spo

        if order is None:
            order = (Order.ASCENDING, Order.ASCENDING, Order.ASCENDING)

        for s, po in index.items(order=order[0]):
            for p, o_list in po.items(order=order[1]):
                for o in o_list.iter(order=order[2]):
                    yield (s, p, o)

    def __contains__(self, triple: Triple) -> bool:
        assert isinstance(triple, tuple)
        if triple[2] in self.spo[triple[0]][triple[1]]:
            status = self.spo[triple[0]][triple[1]][triple[2]]
            if len(status.statuses) > 0:
                item = status.statuses[-1]
                if item.valid_to is None:
                    return True

        return False

    def _branch(self, natural: bool, leading_term: Term) -> _VersionedBranch:
        return _VersionedBranch(lambda mid_term: self._list(leading_term, mid_term, natural))

    def _list(self, s: Term, p: Term, natural: bool) -> SortedMapping[Term, TripleStatus]:
        if not natural:
            s, p = p, s

        return self._lists[s][p]


class _Branch:
    def __init__(self, factory):
        self._mapping = DefaultSortedMapping[Term, SortedList[Term]](factory, key=Key)

    def __repr__(self) -> str:
        return f"_Branch({self._mapping})"

    def __getitem__(
        self, k: Union[Sequence[Term], Term]
    ) -> Union[Sequence[Tuple[Term, SortedList[Term]]], SortedList[Term]]:
        return _ListAdapter(self._mapping[k])

    def items(self, order: Order = Order.ASCENDING):
        for k, v in self._mapping.items(order):
            yield k, _ListAdapter(v)

    def __contains__(self, term: Term) -> bool:
        return term in self._mapping

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, _Branch):
            return self._mapping == other._mapping
        else:
            return self._mapping == other


class _ListAdapter:
    def __init__(self, leaf):
        self._leaf = leaf

    def __repr__(self) -> str:
        return f"_ListAdapter({self._leaf})"

    def iter(self, order: Order = Order.ASCENDING, triple_counter=None) -> Iterator[Term]:
        for o in self._leaf.iter(order):
            if triple_counter:
                triple_counter()

            yield o

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, _ListAdapter):
            return self._leaf == other._leaf
        else:
            return self._leaf == other

    def __contains__(self, other: Any) -> bool:
        return other in self._leaf

    def index_or_insert(self, x: Term, hint: Optional[int] = 0) -> Tuple[int, bool]:
        return self._leaf.index_or_insert(x, hint)

    def insert(self, x: Term) -> int:
        return self._leaf.insert(x)

    def delete(self, x: Term) -> None:
        return self._leaf.delete(x)

    def to_list(self):
        return self._leaf.to_list()


class InMemoryHexastore:
    def __init__(self, blank_node_factory: Callable[[], BlankNode]) -> None:
        self.n_triples: int = 0
        self.blank_node_factory = blank_node_factory

        self.spo: MutableIndex = _TrunkMapping(self, True)
        self.pos: MutableIndex = _TrunkMapping(self, True)
        self.osp: MutableIndex = _TrunkMapping(self, True)
        self.sop: MutableIndex = _TrunkMapping(self, False)
        self.ops: MutableIndex = _TrunkMapping(self, False)
        self.pso: MutableIndex = _TrunkMapping(self, False)

        self._lists: Mapping[Term, Mapping[Term, SortedList[Term]]] = defaultdict(
            lambda: defaultdict(lambda: SortedList(key=Key))
        )

    def __len__(self) -> int:
        return self.n_triples

    def index(self, triple: Triple) -> Optional[int]:
        for i, t in enumerate(self.triples()):
            if t == triple:
                return i

        return None

    def bulk_insert(self, triples: List[Triple]) -> None:
        sorted_triples = sorted(triples, key=functools.partial(triple_map, Key))

        for s, s_triples in itertools.groupby(sorted_triples, key=lambda t: t[0]):
            assert_tuple_length(s)

            po_index = self.spo[s]
            op_index = self.sop[s]

            for p, p_triples in itertools.groupby(s_triples, key=lambda t: t[1]):
                assert_tuple_length(p)

                o_spo_index = po_index.map[p]

                os_index = self.pos[p]
                so_index = self.pso[p]

                for _, _, o in p_triples:
                    assert_tuple_length(o)

                    _, inserted = o_spo_index.index_or_insert(o)
                    if not inserted:
                        continue

                    sp_index = self.osp[o]
                    ps_index = self.ops[o]

                    os_index.map[o].index_or_insert(s)
                    sp_index.map[s].index_or_insert(p)

                    assert p in self.sop[s].map[o]
                    assert s in self.ops[o].map[p]
                    assert o in self.pso[p].map[s]

                    self.n_triples += 1

                    po_index.n += 1
                    op_index.n += 1
                    sp_index.n += 1
                    ps_index.n += 1
                    os_index.n += 1
                    so_index.n += 1

    def insert(self, s: Term, p: Term, o: Term) -> bool:
        assert_tuple_length(o)
        _, inserted = self.spo[s].map[p].index_or_insert(o)
        if not inserted:
            return False

        assert_tuple_length(s)
        assert_tuple_length(p)

        self.pos[p].map[o].insert(s)
        self.osp[o].map[s].insert(p)

        assert p in self.sop[s].map[o]
        assert s in self.ops[o].map[p]
        assert o in self.pso[p].map[s]

        self.n_triples += 1

        self.spo[s].n += 1
        self.sop[s].n += 1
        self.osp[o].n += 1
        self.ops[o].n += 1
        self.pos[p].n += 1
        self.pso[p].n += 1

        return True

    def delete(self, s: Term, p: Term, o: Term) -> None:
        if o not in self.spo[s][p]:
            return

        self.n_triples -= 1

        self.spo[s].n -= 1
        self.sop[s].n -= 1
        self.osp[o].n -= 1
        self.ops[o].n -= 1
        self.pos[p].n -= 1
        self.pso[p].n -= 1

        self.spo[s].map[p].delete(o)
        self.pos[p].map[o].delete(s)
        self.osp[o].map[s].delete(p)

        assert p not in self.sop[s][o]
        assert s not in self.ops[o][p]
        assert o not in self.pso[p][s]

    def terms(self) -> SortedList[Term]:
        return SortedList(set(itertools.chain(self.spo.keys(), self.pos.keys(), self.osp.keys())), key=Key)

    def triples(
        self, index: Optional[MutableIndex] = None, order: Optional[Tuple[Order, Order, Order]] = None
    ) -> Iterable[Triple]:
        if index is None:
            index = self.spo

        if order is None:
            order = (Order.ASCENDING, Order.ASCENDING, Order.ASCENDING)

        for s, po in index.items(order=order[0]):
            for p, o_list in po.items(order=order[1]):
                for o in o_list.iter(order=order[2]):
                    yield (s, p, o)

    def __contains__(self, triple: Triple) -> bool:
        s, p, o = triple
        return o in self.spo[s][p]

    def _branch(self, natural: bool, leading_term: Term) -> _VersionedBranch:
        return _Branch(lambda mid_term: self._list(leading_term, mid_term, natural))

    def _list(self, s: Term, p: Term, natural: bool) -> SortedList[Term]:
        if not natural:
            s, p = p, s

        return self._lists[s][p]


def assert_tuple_length(t):
    if isinstance(t, tuple):
        assert len(t) == 3
