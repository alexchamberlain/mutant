from collections import defaultdict
import logging
from typing import List, Optional

from .ast import IRI, BlankNode, Variable
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
        self._predicate_rules = defaultdict(list)
        self._rule_deletion_map = defaultdict(list)

        self.spo = self._store.spo
        self.pos = self._store.pos
        self.osp = self._store.osp
        self.sop = self._store.sop
        self.ops = self._store.ops
        self.pso = self._store.pso

        self.triples = self._store.triples

    def register_predicate_rule(self, p, version, callback, inferred_from: Optional[List[Triple]] = None):
        if inferred_from is None:
            inferred_from = []

        logger.debug(f"Registering predicate rule {p}, {callback}, {inferred_from}")
        self._predicate_rules[p].append(callback)

        if len(inferred_from) == 1:
            assert isinstance(inferred_from[0], tuple)
            self._rule_deletion_map[inferred_from[0]].append((p, callback))
        elif len(inferred_from) > 1:
            assert False

        delta = {(s, p, o) for s, os in self._store.pso[p].items() for o, status in os.items() if status.inserted}
        adaptor = RuleHexastoreAdaptor(self._store, self, version)

        logger.debug(f"delta {delta}")

        for inferred_from in delta:
            s, p, o = inferred_from
            logger.debug(f"inferred_from {inferred_from}")

            callback(adaptor, s, p, o)

        logger.debug(f"next_delta {adaptor.next_delta}")
        delta = set()
        for triple, inferred_from in adaptor.next_delta:
            logger.debug(f"triple {triple}")
            if self._insert(triple, inferred_from, version):
                delta.add(triple)

        self._apply_rules(delta, version)

    def insert(self, s, p, o, version):
        logger.debug(f"insert {(s, p, o)}")
        self._store.insert(s, p, o, version)
        self._apply_rules({(s, p, o)}, version)

    def _apply_rules(self, delta, version):
        while delta:
            adaptor = RuleHexastoreAdaptor(self._store, self, version)
            logger.debug(f"delta {delta}")

            for inferred_from in delta:
                s, p, o = inferred_from
                logger.debug(f"inferred_from {inferred_from}")

                if p in self._predicate_rules:
                    rules = self._predicate_rules[p]
                    for r in rules:
                        r(adaptor, s, p, o)

            logger.debug(f"next_delta {adaptor.next_delta}")
            delta = set()
            for triple, inferred_from in adaptor.next_delta:
                logger.debug(f"triple {triple}")
                if self._insert(triple, inferred_from, version):
                    delta.add(triple)

    def _insert(self, triple, inferred_from, version):
        logger.debug(f"_insert {triple} {inferred_from}")
        assert all(not isinstance(t, Variable) for t in triple)
        inserted = self._store.insert(*triple, version)

        if not inserted and self._is_circular(triple, inferred_from):
            logger.debug(f"_insert Rejecting {triple}")
            return False

        if not isinstance(inferred_from, list):
            self._store.insert(triple, INFERRED_FROM, inferred_from, version)
        elif len(inferred_from) == 1:
            self._store.insert(triple, INFERRED_FROM, inferred_from[0], version)
        else:
            inferred_from = sorted(inferred_from, key=Key)
            for node, status in self._store.ops[BAG][TYPE].items():
                if not status.inserted:
                    continue

                if not (triple, INFERRED_FROM, node) in self._store:
                    continue

                members = [o for o, status in self._store.spo[node][MEMBER].items() if status.inserted]
                logger.debug(f"_insert == {members} {inferred_from}")
                if members == inferred_from:
                    return inserted

            node = BlankNode()
            self._store.insert(node, TYPE, BAG, version)
            self._store.insert(triple, INFERRED_FROM, node, version)
            for i, i_f in enumerate(inferred_from):
                self._store.insert(node, _li(i + 1), i_f, version)

        return inserted

    def _is_circular(self, triple, inferred_from):
        if not isinstance(inferred_from, list):
            inferred_from = [inferred_from]

        for foo in inferred_from:
            #  TODO Extend to full circular check
            if (foo, INFERRED_FROM, triple) in self._store:
                return True

            for s, status in self._store.ops[triple][MEMBER].items():
                if not status.inserted:
                    continue

                if (foo, INFERRED_FROM, s) in self._store:
                    return True

        return False

    def delete(self, s, p, o, version):
        inferred_from = (s, p, o)
        self._store.delete(*inferred_from, version)

        for p, ss in self._store.ops[inferred_from].items():
            for dead_triple, status in ss.items():
                if not status.inserted:
                    continue

                if p == INFERRED_FROM:
                    self._store.delete(*dead_triple, version)
                    self._store.delete(dead_triple, INFERRED_FROM, inferred_from, version)
                elif _type(self._store, dead_triple) == BAG:
                    triples = [
                        s for s, status in self._store.ops[dead_triple][INFERRED_FROM].items() if status.inserted
                    ]
                    for t in triples:
                        self._store.delete(t, INFERRED_FROM, dead_triple, version)

                        still_valid = next(
                            (o for o, status in self._store.spo[t][INFERRED_FROM].items() if status.inserted), None
                        )
                        if not still_valid:
                            self._store.delete(*t, version)

                    _delete_node(self._store, dead_triple, version)

        for p, callback in self._rule_deletion_map[inferred_from]:
            logger.debug(f"Removing predicate rule {p}, {callback}, {inferred_from}")

            self._predicate_rules[p].remove(callback)


def _li(n: int):
    return MEMBER
    return IRI(f"http://www.w3.org/1999/02/22-rdf-syntax-ns#_{n}")


def _type(store, s):
    return next((o for o, status in store.spo[s][TYPE].items() if status.inserted), None)


def _delete_node(store, node, version):
    triples = [(node, p, o) for p, os in store.spo[node].items() for o, status in os.items() if status.inserted]
    for t in triples:
        store.delete(*t, version)


class RuleHexastoreAdaptor:
    def __init__(self, store, forward_reasoner, version):
        self._store = store
        self._forward_reasoner = forward_reasoner
        self._version = version

        self.spo = self._store.spo
        self.pos = self._store.pos
        self.osp = self._store.osp
        self.sop = self._store.sop
        self.ops = self._store.ops
        self.pso = self._store.pso

        self.next_delta = []

    def insert(self, triple, inferred_from):
        logger.debug(f"insert {(triple, inferred_from)}")
        self.next_delta.append((triple, inferred_from))

    def register_predicate_rule(self, p, callback, inferred_from: Optional[List[Triple]] = None):
        self._forward_reasoner.register_predicate_rule(p, self._version, callback, inferred_from)
