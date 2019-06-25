from pprint import pprint

import pytest

from hexastore.ast import IRI, BlankNode
from hexastore.blank_node_factory import BlankNodeFactory
from hexastore.forward_reasoner import ForwardReasoner
from hexastore.memory import InMemoryHexastore
from hexastore.model import Key
from hexastore.util import triple_map

A = IRI("http://example.com/A")
B = IRI("http://example.com/B")
C = IRI("http://example.com/C")
D = IRI("http://example.com/D")

CHILDREN = IRI("https://schema.org/children")
PARENT = IRI("https://schema.org/parent")
SIBLING = IRI("https://schema.org/sibling")
SPOUSE = IRI("https://schema.org/spouse")
OWL_THING = IRI("http://www.w3.org/2002/07/owl#Thing")
THING = IRI("https://schema.org/Thing")
PERSON = IRI("https://schema.org/Person")
ORGANISATION = IRI("https://schema.org/Organisation")
RELATED_TO = IRI("http://example.com/relatedTo")

BAG = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#Bag")
INFERRED_FROM = IRI("https://example.com/inferred_from")
TYPE = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")

SYMMETRIC_PROPERTY = IRI("http://www.w3.org/2002/07/owl#SymmetricProperty")
INVERSE_OF = IRI("http://www.w3.org/2002/07/owl#inverseOf")
DOMAIN = IRI("http://www.w3.org/2000/01/rdf-schema#domain")
RANGE = IRI("http://www.w3.org/2000/01/rdf-schema#range")
SUBCLASS_OF = IRI("http://www.w3.org/2000/01/rdf-schema#subclassOf")
SUBPROPERTY_OF = IRI("http://www.w3.org/2000/01/rdf-schema#subpropertyOf")
TRANSITIVE_PROPERTY = IRI("http://example.com/transitive-property")
MEMBER = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#member")


@pytest.fixture
def store():
    return InMemoryHexastore()


@pytest.fixture
def reasoner(store):
    return ForwardReasoner(store)


def parent_sibling_rule(store, s, p, o, insert):
    inferred_from = (s, p, o)
    for s_, status in store.ops[o][p].items():
        if not status.inserted or s == s_:
            continue

        insert((s, SIBLING, s_), [inferred_from, (s_, p, o)])
        insert((s_, SIBLING, s), [inferred_from, (s_, p, o)])


@pytest.mark.forward_reasoner
@pytest.mark.skip
def test_forward_reasoner_with_one_parent_delete(store, reasoner):
    reasoner.insert(SPOUSE, TYPE, SYMMETRIC_PROPERTY)
    reasoner.insert(CHILDREN, INVERSE_OF, PARENT)
    reasoner.register_predicate_rule(PARENT, parent_sibling_rule)

    reasoner.insert(C, PARENT, A)
    reasoner.insert(D, PARENT, A)

    assert (C, SIBLING, D) in store
    assert (D, SIBLING, C) in store

    reasoner.delete(C, PARENT, A)

    pprint(list(store.triples()))

    blank_node_factory = BlankNodeFactory()
    expected_store = VersionedInMemoryHexastore(blank_node_factory)
    expected_store.insert(SPOUSE, TYPE, SYMMETRIC_PROPERTY, 1)
    expected_store.insert(CHILDREN, INVERSE_OF, PARENT, 1)
    expected_store.insert(PARENT, INVERSE_OF, CHILDREN, 1)
    expected_store.insert((PARENT, INVERSE_OF, CHILDREN), INFERRED_FROM, (CHILDREN, INVERSE_OF, PARENT), 1)

    expected_store.insert(D, PARENT, A, 3)
    expected_store.insert(A, CHILDREN, D, 3)

    node = blank_node_factory()
    expected_store.insert(node, TYPE, BAG, 2)
    expected_store.insert((A, CHILDREN, D), INFERRED_FROM, node, 2)
    expected_store.insert(node, _li(1), (CHILDREN, INVERSE_OF, PARENT), 2)
    expected_store.insert(node, _li(2), (D, PARENT, A), 2)

    assert_equivalent(store, expected_store)


@pytest.mark.forward_reasoner
@pytest.mark.skip
def test_forward_reasoner_with_children_and_delete(store, reasoner):
    reasoner.insert(SPOUSE, TYPE, SYMMETRIC_PROPERTY)
    reasoner.insert(CHILDREN, INVERSE_OF, PARENT)
    reasoner.register_predicate_rule(PARENT, parent_sibling_rule)

    reasoner.insert(A, SPOUSE, B)
    reasoner.insert(C, PARENT, A)
    reasoner.insert(C, PARENT, B)
    reasoner.insert(D, PARENT, A)
    reasoner.insert(D, PARENT, B)

    print(len(store))

    reasoner.delete(D, PARENT, A)

    blank_node_factory = BlankNodeFactory()
    expected_store = VersionedInMemoryHexastore(blank_node_factory)
    expected_store.insert(SPOUSE, TYPE, SYMMETRIC_PROPERTY, 1)
    expected_store.insert(CHILDREN, INVERSE_OF, PARENT, 1)
    expected_store.insert(PARENT, INVERSE_OF, CHILDREN, 1)
    expected_store.insert((PARENT, INVERSE_OF, CHILDREN), INFERRED_FROM, (CHILDREN, INVERSE_OF, PARENT), 1)

    expected_store.insert(A, SPOUSE, B, 1)
    expected_store.insert(B, SPOUSE, A, 1)

    node = blank_node_factory()
    expected_store.insert(node, TYPE, BAG, 1)
    expected_store.insert((B, SPOUSE, A), INFERRED_FROM, node, 1)
    expected_store.insert(node, _li(1), (SPOUSE, TYPE, SYMMETRIC_PROPERTY), 1)
    expected_store.insert(node, _li(2), (A, SPOUSE, B), 1)

    expected_store.insert(C, PARENT, A, 2)
    expected_store.insert(A, CHILDREN, C, 2)

    expected_store.insert(C, PARENT, B, 3)
    expected_store.insert(B, CHILDREN, C, 3)

    expected_store.insert(D, PARENT, B, 5)
    expected_store.insert(B, CHILDREN, D, 5)
    expected_store.insert(C, SIBLING, D, 5)
    expected_store.insert(D, SIBLING, C, 5)

    node = blank_node_factory()
    expected_store.insert(node, TYPE, BAG, 5)
    expected_store.insert((C, SIBLING, D), INFERRED_FROM, node, 5)
    expected_store.insert(node, _li(1), (D, PARENT, B), 5)
    expected_store.insert(node, _li(2), (C, PARENT, B), 5)

    node = blank_node_factory()
    expected_store.insert(node, TYPE, BAG, 5)
    expected_store.insert((D, SIBLING, C), INFERRED_FROM, node, 5)
    expected_store.insert(node, _li(1), (D, PARENT, B), 5)
    expected_store.insert(node, _li(2), (C, PARENT, B), 5)

    node = blank_node_factory()
    expected_store.insert(node, TYPE, BAG, 2)
    expected_store.insert((A, CHILDREN, C), INFERRED_FROM, node, 2)
    expected_store.insert(node, _li(1), (CHILDREN, INVERSE_OF, PARENT), 2)
    expected_store.insert(node, _li(2), (C, PARENT, A), 2)

    node = blank_node_factory()
    expected_store.insert(node, TYPE, BAG, 2)
    expected_store.insert((B, CHILDREN, C), INFERRED_FROM, node, 2)
    expected_store.insert(node, _li(1), (CHILDREN, INVERSE_OF, PARENT), 2)
    expected_store.insert(node, _li(2), (C, PARENT, B), 2)

    node = blank_node_factory()
    expected_store.insert(node, TYPE, BAG, 2)
    expected_store.insert((B, CHILDREN, D), INFERRED_FROM, node, 2)
    expected_store.insert(node, _li(1), (CHILDREN, INVERSE_OF, PARENT), 2)
    expected_store.insert(node, _li(2), (D, PARENT, B), 2)

    assert_equivalent(store, expected_store)


def assert_equivalent(lhs, rhs):
    """Assert 2 hexastores contain the same information, albeit with different BlankNodes"""

    # TODO: Check number of active nodes

    assert len(lhs) == len(rhs)

    blank_node_map = _BlankNodeMap()

    for o, ps in lhs.ops.items():
        #  TODO: Use the fact that all BlankNodes appear together
        if not isinstance(o, BlankNode):
            continue

        for p, ss in ps.items():
            for s, status in ss.items():
                if not status.inserted:
                    continue

                # TODO: Support many...
                # rhs_o = _get_one(rhs, s, p)

                # if rhs_o is None:
                #     assert False, f"LHS has ({s}, {p}, {o}), but RHS does not."

                # blank_node_map.add(o, rhs_o)

                print(f"Searching for {s}, {p}...")
                possible_nodes = _get_many(rhs, s, p)

                if len(possible_nodes) == 0:
                    assert False, f"LHS has ({s}, {p}, {o}), but RHS does not."
                elif len(possible_nodes) == 1:
                    # Only 1 possible match
                    blank_node_map.add(o, possible_nodes[0])
                else:
                    lhs_ps = [(p, s) for p, ss in ps.items() for s, status in ss.items() if status.inserted]
                    for rhs_o in possible_nodes:
                        if rhs_o in blank_node_map:
                            continue

                        rhs_ps = [
                            (p, s) for p, ss in rhs.ops[rhs_o].items() for s, status in ss.items() if status.inserted
                        ]
                        if rhs_ps == lhs_ps:
                            blank_node_map.add(o, rhs_o)
                            break
                    else:
                        assert False, f"LHS has ({s}, {p}, {o}), but RHS does not."

    for o, ps in rhs.ops.items():
        # TODO: Support object deletions
        if not isinstance(o, BlankNode):
            continue

        if o not in blank_node_map:
            p, s = next((p, s) for p, ss in ps.items() for s, status in ss.items() if status.inserted)
            assert False, f"RHS has ({s}, {p}, {o}), but LHS does not."

    lhs_triples = sorted((triple_map(blank_node_map, t) for t in lhs.triples()), key=Key)

    for lhs_t, rhs_t in zip(lhs_triples, rhs.triples()):
        assert lhs_t == rhs_t


class _BlankNodeMap:
    def __init__(self):
        self._map = {}
        self._rhs_found = set()

    def add(self, lhs_o, rhs_o):
        assert rhs_o not in self._rhs_found
        print(f"{lhs_o} -> {rhs_o}")
        self._map[lhs_o] = rhs_o
        self._rhs_found.add(rhs_o)

    def __contains__(self, rhs_o):
        return rhs_o in self._rhs_found

    def __call__(self, term):
        if isinstance(term, BlankNode):
            return self._map[term]

        return term


def _li(n: int):
    return MEMBER
    return IRI(f"http://www.w3.org/1999/02/22-rdf-syntax-ns#_{n}")


def _get_one(hexastore, s, p):
    return next((o for o, status in hexastore.spo[s][p].items() if status.inserted), None)


def _get_many(hexastore, s, p):
    return [o for o, status in hexastore.spo[s][p].items() if status.inserted]


@pytest.mark.forward_reasoner
def test_forward_reasoner_inferred_child_with_delete(store, reasoner):
    reasoner.insert(A, SPOUSE, B)
    reasoner.insert(C, PARENT, A)
    reasoner.insert(C, PARENT, B)

    # assert list(store.triples()) == [((B, SPOUSE, A), INFERRED_FROM, (A, SPOUSE, B)), (A, SPOUSE, B), (B, SPOUSE, A)]
