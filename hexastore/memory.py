from collections import defaultdict
import itertools
from typing import Tuple, Optional, Mapping, Iterable

from .ast import Order, TripleStatus, TripleStatusItem
from .model import Key
from .sorted import SortedList, SortedMapping, DefaultSortedMapping
from .typing import Term, Triple, MutableIndex, MutableOrderedMapping


def _BranchMapping(store: "InMemoryHexastore", natural: bool, leading_term: Term) -> MutableIndex:
    return DefaultSortedMapping[Term, MutableOrderedMapping[Term, TripleStatus]](
        lambda mid_term: store._list(leading_term, mid_term, natural), key=Key
    )


def _TrunkMapping(store: "InMemoryHexastore", natural: bool) -> MutableIndex:
    return DefaultSortedMapping[Term, MutableOrderedMapping[Term, MutableOrderedMapping[Term, TripleStatus]]](
        lambda leading_term: _BranchMapping(store, natural, leading_term), key=Key
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

    def insert(self, s: Term, p: Term, o: Term, valid_from: int) -> bool:
        if o in self.spo[s][p]:
            status = self.spo[s][p][o]
            if status.inserted:
                return False
        else:
            status = TripleStatus([])

        asser_tuple_length(s)
        asser_tuple_length(p)
        asser_tuple_length(o)

        self.n_triples += 1

        status.statuses.append(TripleStatusItem(valid_from=valid_from))

        self.spo[s][p][o] = status
        self.pos[p][o][s] = status
        self.osp[o][s][p] = status

        assert p in self.sop[s][o]
        assert s in self.ops[o][p]
        assert o in self.pso[p][s]

        return True

    def delete(self, s: Term, p: Term, o: Term, valid_to: int) -> None:
        if p in self.sop[s][o]:
            self.n_triples -= 1

        if o in self.spo[s][p]:
            status = self.spo[s][p][o]
        else:
            status = TripleStatus([])

        if len(status.statuses):
            status.statuses[-1].valid_to = valid_to
        else:
            status.statuses.append(TripleStatusItem(valid_to=valid_to))

        self.spo[s][p][o] = status
        self.pos[p][o][s] = status
        self.osp[o][s][p] = status

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


def asser_tuple_length(t):
    if isinstance(t, tuple):
        assert len(t) == 3
