from collections import defaultdict

from .ast import IRI, BlankNode

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

TRANSITIVE_PROPERTY = IRI("http://example.com/transitive-property")


class DomainRule:
    def __init__(self, type_):
        self._type = type_

    def __call__(self, store, s, p, o, version, insert):
        insert((s, TYPE, self._type), [(p, DOMAIN, self._type), (s, p, o)], version)

    def __eq__(self, other: object):
        if not isinstance(other, DomainRule):
            return NotImplemented

        return self._type == other._type


class RangeRule:
    def __init__(self, type_):
        self._type = type_

    def __call__(self, store, s, p, o, version, insert):
        insert((o, TYPE, self._type), [(p, RANGE, self._type), (s, p, o)], version)

    def __eq__(self, other: object):
        if not isinstance(other, RangeRule):
            return NotImplemented

        return self._type == other._type


# TODO: Only match this when object is correct
class SubclassRule:
    def __init__(self, subclass, superclass):
        self._subclass = subclass
        self._superclass = superclass

    def __call__(self, store, s, p, o, version, insert):
        if o == self._subclass:
            insert((s, TYPE, self._superclass), [(self._subclass, SUBCLASS_OF, self._superclass), (s, p, o)], version)

        def __eq__(self, other: object):
            if not isinstance(other, SubclassRule):
                return NotImplemented

            return self._subclass == other._subclass and self._superclass == other._superclass


class SubpropertyRule:
    def __init__(self, superproperty):
        self._superproperty = superproperty

    def __call__(self, store, s, p, o, version, insert):
        insert((s, self._superproperty, o), [(p, SUBPROPERTY_OF, self._superproperty), (s, p, o)], version)

    def __eq__(self, other: object):
        if not isinstance(other, SubpropertyRule):
            return NotImplemented

        return self._superproperty == other._superproperty


def symmetric_rule(store, s, p, o, version, insert):
    insert((o, p, s), [(p, TYPE, SYMMETRIC_PROPERTY), (s, p, o)], version)


def transitive_rule(store, s, p, o, version, insert):
    for s_, status in store.ops[s][p].items():
        if not status.inserted:
            continue

        insert((s_, p, o), [(p, TYPE, TRANSITIVE_PROPERTY), (s_, p, s), (s, p, o)], version)

    for o_, status in store.spo[o][p].items():
        if not status.inserted:
            continue

        insert((s, p, o_), [(p, TYPE, TRANSITIVE_PROPERTY), (s, p, o), (o, p, o_)], version)


class InverseRule:
    def __init__(self, inverse, inferred_from):
        self._inverse = inverse
        self.inferred_from = inferred_from

    def __call__(self, store, s, p, o, version, insert):
        insert((o, self._inverse, s), [self.inferred_from, (s, p, o)], version)


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
        inferred_from = (s, p, o)
        self._store.insert(s, p, o, version)

        if p == TYPE and o == SYMMETRIC_PROPERTY:
            self._predicate_rules[s].append(symmetric_rule)
            return
        elif p == TYPE and o == TRANSITIVE_PROPERTY:
            self._predicate_rules[s].append(transitive_rule)
            return
        elif p == INVERSE_OF:
            self._insert((o, p, s), inferred_from, version)
            self._predicate_rules[s].append(InverseRule(o, inferred_from))
            self._predicate_rules[o].append(InverseRule(s, inferred_from))
            return
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
                r(self._store, s, p, o, version, self._insert)

    def _insert(self, triple, inferred_from, version):
        self._store.insert(*triple, version)

        if not isinstance(inferred_from, list):
            self._store.insert(triple, INFERRED_FROM, inferred_from, version)
        else:
            node = BlankNode()
            self._store.insert(node, TYPE, BAG, version)
            self._store.insert(triple, INFERRED_FROM, node, version)
            for i, i_f in enumerate(inferred_from):
                self._store.insert(node, _li(i + 1), i_f, version)

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
    return IRI(f"http://www.w3.org/1999/02/22-rdf-syntax-ns#_{n}")


def _type(store, s):
    return next((o for o, status in store.spo[s][TYPE].items() if status.inserted), None)


def _delete_node(store, node, version):
    triples = [(node, p, o) for p, os in store.spo[node].items() for o, status in os.items() if status.inserted]
    for t in triples:
        store.delete(*t, version)
