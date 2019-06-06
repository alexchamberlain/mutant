from collections import defaultdict
from dataclasses import dataclass
import itertools
import functools
from typing import Any, Tuple, Optional, Mapping, Iterable, Union, Sequence, ValuesView, AbstractSet, Iterator, List

from .ast import Order, TripleStatus, TripleStatusItem
from .model import Key
from .sorted import SortedList, SortedMapping, DefaultSortedMapping
from .typing import Term, Triple, MutableIndex, MutableOrderedMapping
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


_BranchMappingType = DefaultSortedMapping[Term, MutableOrderedMapping[Term, TripleStatus]]
_TrunkMappingType = DefaultSortedMapping[Term, TrunkPayload]


def _BranchMapping(store: "InMemoryHexastore", natural: bool, leading_term: Term) -> MutableIndex:
    return _BranchMappingType(lambda mid_term: store._list(leading_term, mid_term, natural), key=Key)


def _TrunkMapping(store: "InMemoryHexastore", natural: bool) -> MutableIndex:
    return _TrunkMappingType(
        lambda leading_term: TrunkPayload(map=_BranchMapping(store, natural, leading_term)), key=Key
    )


class InMemoryHexastore:
    def __init__(self) -> None:
        self.n_triples: int = 0

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
                for o, status in o_list.items(order=order[2]):
                    if status.inserted:
                        yield (s, p, o)

    def __contains__(self, triple: Triple) -> bool:
        if triple[2] in self.spo[triple[0]][triple[1]]:
            status = self.spo[triple[0]][triple[1]][triple[2]]
            if len(status.statuses) > 0:
                item = status.statuses[-1]
                if item.valid_to is None:
                    return True

        return False

    def _list(self, s: Term, p: Term, natural: bool) -> SortedMapping[Term, TripleStatus]:
        if not natural:
            s, p = p, s

        return self._lists[s][p]


def assert_tuple_length(t):
    if isinstance(t, tuple):
        assert len(t) == 3
