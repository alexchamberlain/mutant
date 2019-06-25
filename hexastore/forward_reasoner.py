import logging
from collections import defaultdict
from typing import List, Optional

from . import engine
from .ast import IRI, Order, Variable
from .bulk_inserter import BulkInserter
from .index import get_index
from .model import Key
from .typing import Triple

BAG = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#Bag")
INFERRED_FROM = IRI("https://example.com/inferred_from")
TYPE = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")

CHILDREN = IRI("https://schema.org/children")
PARENT = IRI("https://schema.org/parent")
SIBLING = IRI("https://schema.org/sibling")
SPOUSE = IRI("https://schema.org/spouse")

SYMMETRIC_PROPERTY = IRI("http://www.w3.org/2002/07/owl#SymmetricProperty")
INVERSE_OF = IRI("http://www.w3.org/2002/07/owl#inverseOf")
DOMAIN = IRI("http://www.w3.org/2000/01/rdf-schema#domain")
RANGE = IRI("http://www.w3.org/2000/01/rdf-schema#range")
SUBCLASS_OF = IRI("http://www.w3.org/2000/01/rdf-schema#subclassOf")
SUBPROPERTY_OF = IRI("http://www.w3.org/2000/01/rdf-schema#subpropertyOf")
MEMBER = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#member")

TRANSITIVE_PROPERTY = IRI("http://example.com/transitive-property")

logger = logging.getLogger(__name__)


class ForwardReasoner:
    def __init__(self, store):
        self._store = store

        self._symmetric_properties = set()
        self._inverse_map = {}

        self._rules = [
            #  _ = variable, x = fixed term
            set(),  #  (_, _, _)
            defaultdict(set),  # (x, _, _)
            defaultdict(set),  # (_, x, _)
            defaultdict(set),  # (x, x, _)
            defaultdict(set),  # (_, _, x)
            defaultdict(set),  # (x, _, x)
            defaultdict(set),  # (_, x, x)
            defaultdict(set),  # (x, x, x)
        ]
        self._rule_deletion_map = defaultdict(set)

        self.spo = self._store.spo
        self.pos = self._store.pos
        self.osp = self._store.osp
        self.sop = self._store.sop
        self.ops = self._store.ops
        self.pso = self._store.pso

        self.triples = self._store.triples

    def register_rule(self, pattern, callback, inferred_from: Optional[List[Triple]] = None):
        assert callable(callback)

        if inferred_from is None:
            inferred_from = []

        index, key = get_index(pattern)

        logger.debug(f"Registering rule pattern={pattern} index={index}")

        rule_set = self._rules[index]
        if key:
            rule_set = rule_set[key]

        rule_set.add(callback)

        if len(inferred_from) == 1:
            assert isinstance(inferred_from[0], tuple)
            self._rule_deletion_map[inferred_from[0]].add((pattern, callback))
        elif len(inferred_from) > 1:
            assert False

        solutions, stats = engine.execute(self._store, [pattern], [])

        adaptor = RuleHexastoreAdaptor(self._store, self)

        # TODO: Can we make rules talk "solutions" rather than triples?
        for s in solutions:
            assert len(s.triples) == 1
            callback(adaptor, *s.triples[0])

        with BulkInserter(self._store) as store:
            logger.debug(f"next_delta {adaptor.next_delta}")
            delta = set()
            for triple, inferred_from in adaptor.next_delta:
                logger.debug(f"triple {triple}")
                if self._insert(triple, inferred_from, store):
                    delta.add(triple)

            self._apply_rules(delta, store)

    def insert(self, s, p, o):
        with BulkInserter(self._store) as store:
            logger.debug(f"insert {(s, p, o)}")
            store.insert(s, p, o)
            self._apply_rules({(s, p, o)}, store)

    def bulk_insert(self, triples):
        with BulkInserter(self._store) as store:
            store.bulk_insert(triples)
            self._apply_rules(set(triples), store)

    def _apply_rules(self, delta, store):
        while delta:
            adaptor = RuleHexastoreAdaptor(store, self)
            logger.debug(f"delta {delta}")

            for inferred_from in delta:
                s, p, o = inferred_from
                logger.debug(f"inferred_from {inferred_from} {self._rules}")

                rules = self._rules[0]
                for r in rules:
                    r(adaptor, s, p, o)

                rules = self._rules[1][(s,)]  # (x, _, _)
                for r in rules:
                    r(adaptor, s, p, o)

                rules = self._rules[2][(p,)]  # (_, x, _)
                for r in rules:
                    r(adaptor, s, p, o)

                rules = self._rules[3][(s, p)]  # (x, x, _)
                for r in rules:
                    r(adaptor, s, p, o)

                rules = self._rules[4][(o,)]  # (_, _, x)
                for r in rules:
                    r(adaptor, s, p, o)

                rules = self._rules[5][(s, o)]  # (x, _, x)
                for r in rules:
                    r(adaptor, s, p, o)

                rules = self._rules[6][(p, o)]  # (_, x, x)
                for r in rules:
                    r(adaptor, s, p, o)

                rules = self._rules[7][(s, p, o)]  # (x, x, x)
                for r in rules:
                    r(adaptor, s, p, o)

            logger.debug(f"next_delta {adaptor.next_delta}")
            delta = set()
            for triple, inferred_from in adaptor.next_delta:
                logger.debug(f"triple {triple}")
                if self._insert(triple, inferred_from, store):
                    delta.add(triple)

    def _insert(self, triple, inferred_from, store):
        logger.debug(f"_insert {triple} {inferred_from}")
        assert all(not isinstance(t, Variable) for t in triple)
        inserted = store.insert(*triple)

        if not inserted and self._is_circular(triple, inferred_from, store):
            logger.debug(f"_insert Rejecting {triple}")
            return False

        if not isinstance(inferred_from, list) and not isinstance(inferred_from, tuple):
            store.insert(triple, INFERRED_FROM, inferred_from)
        elif len(inferred_from) == 1:
            store.insert(triple, INFERRED_FROM, inferred_from[0])
        else:
            if not inserted:
                inferred_from = sorted(inferred_from, key=Key)
                # for node, status in store.ops[BAG][TYPE].items():
                for node in store.spo[triple][INFERRED_FROM].iter():
                    if not (node, TYPE, BAG) in store:
                        continue

                    members = store.spo[node][MEMBER].to_list()
                    logger.debug(f"_insert == {members} {inferred_from}")
                    if members == inferred_from:
                        return inserted

            node = store.blank_node_factory()
            store.insert(node, TYPE, BAG)
            store.insert(triple, INFERRED_FROM, node)
            for i, i_f in enumerate(inferred_from):
                store.insert(node, _li(i + 1), i_f)

        return inserted

    def _is_circular(self, triple, inferred_from, store):
        if not isinstance(inferred_from, list) and not isinstance(inferred_from, tuple):
            inferred_from = [inferred_from]

        for foo in inferred_from:
            #  TODO Extend to full circular check
            if (foo, INFERRED_FROM, triple) in store:
                return True

            for s in store.ops[triple][MEMBER].iter(Order.ASCENDING):
                if (foo, INFERRED_FROM, s) in store:
                    return True

        return False

    def delete(self, s, p, o):
        inferred_from = (s, p, o)
        self._store.delete(*inferred_from)

        for p, ss in self._store.ops[inferred_from].items():
            for dead_triple in ss.iter():
                if p == INFERRED_FROM:
                    self._store.delete(*dead_triple)
                    self._store.delete(dead_triple, INFERRED_FROM, inferred_from)
                elif _type(self._store, dead_triple) == BAG:
                    triples = [s for s in self._store.ops[dead_triple][INFERRED_FROM].iter()]
                    for t in triples:
                        self._store.delete(t, INFERRED_FROM, dead_triple)

                        still_valid = next(self._store.spo[t][INFERRED_FROM].iter(), None)
                        if not still_valid:
                            self._store.delete(*t)

                    _delete_node(self._store, dead_triple)

        for p, callback in self._rule_deletion_map[inferred_from]:
            logger.debug(f"Removing predicate rule {p}, {callback}, {inferred_from}")

            index, key = get_index(p)

            logger.debug(f"Removing rule pattern={p} index={index}")

            rule_set = self._rules[index]
            if key:
                rule_set = rule_set[key]

            rule_set.remove(callback)

        del self._rule_deletion_map[inferred_from]


def _li(n: int):
    return MEMBER
    return IRI(f"http://www.w3.org/1999/02/22-rdf-syntax-ns#_{n}")


def _type(store, s):
    return next(store.spo[s][TYPE].iter(), None)


def _delete_node(store, node):
    triples = [(node, p, o) for p, os in store.spo[node].items() for o in os.iter()]
    for t in triples:
        store.delete(*t)


class RuleHexastoreAdaptor:
    def __init__(self, store, forward_reasoner):
        self._store = store
        self._forward_reasoner = forward_reasoner

        self.spo = self._store.spo
        self.pos = self._store.pos
        self.osp = self._store.osp
        self.sop = self._store.sop
        self.ops = self._store.ops
        self.pso = self._store.pso

        self.triples = self._store.triples

        self.next_delta = []

    def __repr__(self) -> str:
        return f"<RuleHexastoreAdaptor({repr(self._store)})>"

    def insert(self, triple, inferred_from):
        logger.debug(f"insert {(triple, inferred_from)}")
        self.next_delta.append((triple, inferred_from))

    def register_rule(self, pattern, callback, inferred_from: Optional[List[Triple]] = None):
        self._forward_reasoner.register_rule(pattern, callback, inferred_from)
