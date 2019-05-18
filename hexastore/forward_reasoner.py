from collections import defaultdict
import logging

from .ast import IRI, BlankNode
from .model import Key

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


class DomainRule:
    def __init__(self, type_):
        self._type = type_

    def __call__(self, store, s, p, o, insert):
        insert((s, TYPE, self._type), [(p, DOMAIN, self._type), (s, p, o)])

    def __eq__(self, other: object):
        if not isinstance(other, DomainRule):
            return NotImplemented

        return self._type == other._type


class RangeRule:
    def __init__(self, type_):
        self._type = type_

    def __call__(self, store, s, p, o, insert):
        insert((o, TYPE, self._type), [(p, RANGE, self._type), (s, p, o)])

    def __eq__(self, other: object):
        if not isinstance(other, RangeRule):
            return NotImplemented

        return self._type == other._type


# TODO: Only match this when object is correct
class SubclassRule:
    def __init__(self, subclass, superclass):
        self._subclass = subclass
        self._superclass = superclass

    def __call__(self, store, s, p, o, insert):
        if o == self._subclass:
            insert((s, TYPE, self._superclass), [(self._subclass, SUBCLASS_OF, self._superclass), (s, p, o)])

        def __eq__(self, other: object):
            if not isinstance(other, SubclassRule):
                return NotImplemented

            return self._subclass == other._subclass and self._superclass == other._superclass


class SubpropertyRule:
    def __init__(self, superproperty):
        self._superproperty = superproperty

    def __call__(self, store, s, p, o, insert):
        insert((s, self._superproperty, o), [(p, SUBPROPERTY_OF, self._superproperty), (s, p, o)])

    def __eq__(self, other: object):
        if not isinstance(other, SubpropertyRule):
            return NotImplemented

        return self._superproperty == other._superproperty


def symmetric_rule(store, s, p, o, insert):
    insert((o, p, s), [(p, TYPE, SYMMETRIC_PROPERTY), (s, p, o)])


def transitive_rule(store, s, p, o, insert):
    for s_, status in store.ops[s][p].items():
        if not status.inserted:
            continue

        insert((s_, p, o), [(p, TYPE, TRANSITIVE_PROPERTY), (s_, p, s), (s, p, o)])

    for o_, status in store.spo[o][p].items():
        if not status.inserted:
            continue

        insert((s, p, o_), [(p, TYPE, TRANSITIVE_PROPERTY), (s, p, o), (o, p, o_)])


class InverseRule:
    def __init__(self, inverse, inferred_from):
        self._inverse = inverse
        self.inferred_from = inferred_from

    def __call__(self, store, s, p, o, insert):
        insert((o, self._inverse, s), [self.inferred_from, (s, p, o)])


class ForwardReasoner:
    def __init__(self, store):
        self._store = store

        self._symmetric_properties = set()
        self._inverse_map = {}
        self._predicate_rules = defaultdict(list)

        self.spo = self._store.spo
        self.pos = self._store.pos
        self.osp = self._store.osp
        self.sop = self._store.sop
        self.ops = self._store.ops
        self.pso = self._store.pso

        self.triples = self._store.triples

    def register_predicate_rule(self, p, callback):
        self._predicate_rules[p].append(callback)

    def insert(self, s, p, o, version):
        logger.debug(f"insert {(s, p, o)}")
        # inferred_from = (s, p, o)
        self._store.insert(s, p, o, version)

        delta = {(s, p, o)}
        next_delta = []

        while delta:
            logger.debug(f"delta {delta}")

            def _insert(triple, inferred_from):
                next_delta.append((triple, inferred_from))

            for inferred_from in delta:
                s, p, o = inferred_from
                logger.debug(f"inferred_from {inferred_from}")

                if p == TYPE and o == SYMMETRIC_PROPERTY:
                    self._predicate_rules[s].append(symmetric_rule)
                elif p == TYPE and o == TRANSITIVE_PROPERTY:
                    self._predicate_rules[s].append(transitive_rule)
                elif p == INVERSE_OF:
                    _insert((o, p, s), inferred_from)
                    self._predicate_rules[o].append(InverseRule(s, inferred_from))
                    # self._predicate_rules[o].append(InverseRule(s, inferred_from))
                elif p == DOMAIN:
                    self._predicate_rules[s].append(DomainRule(o))
                elif p == RANGE:
                    self._predicate_rules[s].append(RangeRule(o))
                elif p == SUBCLASS_OF:
                    self._predicate_rules[TYPE].append(SubclassRule(s, o))
                elif p == SUBPROPERTY_OF:
                    self._predicate_rules[s].append(SubpropertyRule(o))

                if p in self._predicate_rules:
                    rules = self._predicate_rules[p]
                    for r in rules:
                        r(self._store, s, p, o, _insert)

            logger.debug(f"next_delta {next_delta}")
            delta = set()
            for triple, inferred_from in next_delta:
                logger.debug(f"triple {triple}")
                if self._insert(triple, inferred_from, version):
                    delta.add(triple)
            next_delta = []

    def _insert(self, triple, inferred_from, version):
        logger.debug(f"_insert {triple} {inferred_from}")
        inserted = self._store.insert(*triple, version)

        if not inserted and self._is_circular(triple, inferred_from):
            logger.debug(f"_insert Rejecting {triple}")
            return False

        if not isinstance(inferred_from, list):
            self._store.insert(triple, INFERRED_FROM, inferred_from, version)
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
        # logger.debug(f"_is_circular {triple} {inferred_from}")

        if not isinstance(inferred_from, list):
            inferred_from = [inferred_from]

        for foo in inferred_from:

            #  TODO Extend to full circular check
            if (foo, INFERRED_FROM, triple) in self._store:
                # logger.debug(f"_is_circular True")
                return True
            # (
            #     (triple, INFERRED_FROM, n) in self._store
            #     and (n, MEMBER, foo) in self._store
            #     and (n, TYPE, BAG) in self._store
            # )

            for s, status in self._store.ops[triple][MEMBER].items():
                if not status.inserted:
                    continue

                # logger.debug(f"_is_circular {(foo, INFERRED_FROM, s)}")
                if (foo, INFERRED_FROM, s) in self._store:
                    # logger.debug(f"_is_circular True")
                    return True

        # logger.debug(f"_is_circular False")
        return False

    def delete(self, s, p, o, version):
        if p == TYPE and o == SYMMETRIC_PROPERTY:
            self._predicate_rules[s].remove(symmetric_rule)
            return
        elif p == TYPE and o == TRANSITIVE_PROPERTY:
            self._predicate_rules[s].remove(transitive_rule)
        elif p == INVERSE_OF:
            self._predicate_rules[s] = [
                r for r in self._predicate_rules[s] if not (isinstance(r, InverseRule) and r.inferred_from == (s, p, o))
            ]
            self._predicate_rules[o] = [
                r for r in self._predicate_rules[o] if not (isinstance(r, InverseRule) and r.inferred_from == (s, p, o))
            ]
        elif p == DOMAIN:
            self._predicate_rules[s].remove(DomainRule(o))
        elif p == RANGE:
            self._predicate_rules[s].remove(RangeRule(o))
        elif p == SUBCLASS_OF:
            self._predicate_rules[TYPE].remove(SubclassRule(s, o))
        elif p == SUBPROPERTY_OF:
            self._predicate_rules[s].remove(SubpropertyRule(o))

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


def _li(n: int):
    return MEMBER
    return IRI(f"http://www.w3.org/1999/02/22-rdf-syntax-ns#_{n}")


def _type(store, s):
    return next((o for o, status in store.spo[s][TYPE].items() if status.inserted), None)


def _delete_node(store, node, version):
    triples = [(node, p, o) for p, os in store.spo[node].items() for o, status in os.items() if status.inserted]
    for t in triples:
        store.delete(*t, version)
