import pytest

from hexastore.ast import IRI
from hexastore.memory import InMemoryHexastore
from hexastore.default_forward_reasoner import default_forward_reasoner

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
TRANSITIVE_PROPERTY = IRI("http://www.w3.org/2002/07/owl#TransitiveProperty")
MEMBER = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#member")


def parent_sibling_rule(store, s, p, o):
    inferred_from = (s, p, o)
    for s_, status in store.ops[o][p].items():
        if not status.inserted or s == s_:
            continue

        store.insert((s, SIBLING, s_), [inferred_from, (s_, p, o)])
        store.insert((s_, SIBLING, s), [inferred_from, (s_, p, o)])


@pytest.mark.default_forward_reasoner
def test_default_forward_reasoner_symmetric_property():
    store = InMemoryHexastore()
    reasoner = default_forward_reasoner(store)

    reasoner.insert(SPOUSE, TYPE, SYMMETRIC_PROPERTY, 1)
    reasoner.insert(A, SPOUSE, B, 2)

    assert (B, SPOUSE, A) in store


@pytest.mark.default_forward_reasoner
def test_default_forward_reasoner_with_delete():
    store = InMemoryHexastore()
    reasoner = default_forward_reasoner(store)

    reasoner.insert(SPOUSE, TYPE, SYMMETRIC_PROPERTY, 1)
    reasoner.insert(A, SPOUSE, B, 2)

    assert (B, SPOUSE, A) in store

    reasoner.delete(A, SPOUSE, B, 3)

    assert list(store.triples()) == [(SPOUSE, TYPE, SYMMETRIC_PROPERTY)]


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_transitive():
    store = InMemoryHexastore()
    reasoner = default_forward_reasoner(store)

    reasoner.insert(SUBCLASS_OF, TYPE, TRANSITIVE_PROPERTY, 1)
    reasoner.insert(PERSON, SUBCLASS_OF, THING, 1)
    reasoner.insert(THING, SUBCLASS_OF, OWL_THING, 1)

    assert (PERSON, SUBCLASS_OF, OWL_THING) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_transitive_reverse():
    store = InMemoryHexastore()
    reasoner = default_forward_reasoner(store)

    reasoner.insert(SUBCLASS_OF, TYPE, TRANSITIVE_PROPERTY, 1)
    reasoner.insert(THING, SUBCLASS_OF, OWL_THING, 1)
    reasoner.insert(PERSON, SUBCLASS_OF, THING, 1)

    assert (PERSON, SUBCLASS_OF, OWL_THING) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_transitive_with_delete():
    store = InMemoryHexastore()
    reasoner = default_forward_reasoner(store)

    reasoner.insert(SUBCLASS_OF, TYPE, TRANSITIVE_PROPERTY, 1)
    reasoner.insert(PERSON, SUBCLASS_OF, THING, 1)
    reasoner.insert(THING, SUBCLASS_OF, OWL_THING, 1)

    reasoner.delete(SUBCLASS_OF, TYPE, TRANSITIVE_PROPERTY, 1)

    assert list(store.triples()) == [(PERSON, SUBCLASS_OF, THING), (THING, SUBCLASS_OF, OWL_THING)]

    reasoner.insert(ORGANISATION, SUBCLASS_OF, THING, 1)

    assert list(store.triples()) == [
        (ORGANISATION, SUBCLASS_OF, THING),
        (PERSON, SUBCLASS_OF, THING),
        (THING, SUBCLASS_OF, OWL_THING),
    ]


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_subclass_of():
    store = InMemoryHexastore()
    reasoner = default_forward_reasoner(store)

    reasoner.insert(PERSON, SUBCLASS_OF, THING, 1)
    reasoner.insert(A, TYPE, PERSON, 2)

    assert (A, TYPE, THING) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_subproperty_property():
    store = InMemoryHexastore()
    reasoner = default_forward_reasoner(store)

    reasoner.insert(SPOUSE, SUBPROPERTY_OF, RELATED_TO, 1)
    reasoner.insert(A, SPOUSE, B, 2)

    assert (A, RELATED_TO, B) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_domain_property():
    store = InMemoryHexastore()
    reasoner = default_forward_reasoner(store)

    reasoner.insert(SPOUSE, DOMAIN, PERSON, 1)
    reasoner.insert(A, SPOUSE, B, 2)

    assert (A, TYPE, PERSON) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_range_property():
    store = InMemoryHexastore()
    reasoner = default_forward_reasoner(store)

    reasoner.insert(SPOUSE, RANGE, PERSON, 1)
    reasoner.insert(A, SPOUSE, B, 2)

    assert (B, TYPE, PERSON) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_domain_range_property():
    store = InMemoryHexastore()
    reasoner = default_forward_reasoner(store)

    reasoner.insert(SPOUSE, DOMAIN, PERSON, 1)
    reasoner.insert(SPOUSE, RANGE, PERSON, 1)
    reasoner.insert(A, SPOUSE, B, 2)

    assert (A, TYPE, PERSON) in store
    assert (B, TYPE, PERSON) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_with_child():
    store = InMemoryHexastore()
    reasoner = default_forward_reasoner(store)

    reasoner.insert(SPOUSE, TYPE, SYMMETRIC_PROPERTY, 1)
    reasoner.insert(CHILDREN, INVERSE_OF, PARENT, 1)

    reasoner.insert(A, SPOUSE, B, 2)
    reasoner.insert(C, PARENT, A, 3)
    reasoner.insert(C, PARENT, B, 4)

    assert ((PARENT, INVERSE_OF, CHILDREN), INFERRED_FROM, (CHILDREN, INVERSE_OF, PARENT)) in store
    assert (A, CHILDREN, C) in store
    assert (A, SPOUSE, B) in store
    assert (B, CHILDREN, C) in store
    assert (B, SPOUSE, A) in store
    assert (C, PARENT, A) in store
    assert (C, PARENT, B) in store
    assert (CHILDREN, INVERSE_OF, PARENT) in store
    assert (PARENT, INVERSE_OF, CHILDREN) in store
    assert (SPOUSE, TYPE, SYMMETRIC_PROPERTY) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_with_children_1():
    store = InMemoryHexastore()
    reasoner = default_forward_reasoner(store)

    reasoner.insert(CHILDREN, INVERSE_OF, PARENT, 1)
    reasoner.register_predicate_rule(PARENT, 1, parent_sibling_rule)

    reasoner.insert(A, CHILDREN, C, 3)
    reasoner.insert(A, CHILDREN, D, 4)

    assert ((PARENT, INVERSE_OF, CHILDREN), INFERRED_FROM, (CHILDREN, INVERSE_OF, PARENT)) in store
    assert (A, CHILDREN, C) in store
    assert (A, CHILDREN, D) in store
    assert (C, PARENT, A) in store
    assert (CHILDREN, INVERSE_OF, PARENT) in store
    assert (PARENT, INVERSE_OF, CHILDREN) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_with_children():
    store = InMemoryHexastore()
    reasoner = default_forward_reasoner(store)

    reasoner.insert(SPOUSE, TYPE, SYMMETRIC_PROPERTY, 1)
    reasoner.insert(CHILDREN, INVERSE_OF, PARENT, 1)
    reasoner.register_predicate_rule(PARENT, 1, parent_sibling_rule)

    reasoner.insert(A, SPOUSE, B, 2)
    reasoner.insert(C, PARENT, A, 3)
    reasoner.insert(C, PARENT, B, 4)
    reasoner.insert(D, PARENT, A, 5)
    reasoner.insert(D, PARENT, B, 6)

    assert (SPOUSE, TYPE, SYMMETRIC_PROPERTY) in store
    assert (CHILDREN, INVERSE_OF, PARENT) in store
    assert (PARENT, INVERSE_OF, CHILDREN) in store
    assert ((PARENT, INVERSE_OF, CHILDREN), INFERRED_FROM, (CHILDREN, INVERSE_OF, PARENT)) in store
    assert (A, SPOUSE, B) in store
    assert (B, SPOUSE, A) in store
    assert (C, PARENT, A) in store
    assert (A, CHILDREN, C) in store
    assert (C, PARENT, B) in store
    assert (B, CHILDREN, C) in store
    assert (D, PARENT, A) in store
    assert (A, CHILDREN, D) in store
    assert (C, SIBLING, D) in store
    assert (D, SIBLING, C) in store
