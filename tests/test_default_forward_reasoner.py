import pytest

from hexastore.ast import IRI, Variable
from hexastore.blank_node_factory import BlankNodeFactory
from hexastore.default_forward_reasoner import make_default_forward_reasoner
from hexastore.memory import InMemoryHexastore

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


@pytest.fixture
def store():
    blank_node_factory = BlankNodeFactory()
    return InMemoryHexastore(blank_node_factory)


@pytest.fixture
def reasoner(store):
    return make_default_forward_reasoner(store)


def parent_sibling_rule(store, s, p, o):
    inferred_from = (s, p, o)
    for s_ in store.ops[o][p].iter():
        if s == s_:
            continue

        store.insert((s, SIBLING, s_), [inferred_from, (s_, p, o)])
        store.insert((s_, SIBLING, s), [inferred_from, (s_, p, o)])


@pytest.mark.default_forward_reasoner
def test_default_forward_reasoner_symmetric_property(store, reasoner):
    reasoner.insert(SPOUSE, TYPE, SYMMETRIC_PROPERTY)
    reasoner.insert(A, SPOUSE, B)

    assert (B, SPOUSE, A) in store


@pytest.mark.default_forward_reasoner
def test_default_forward_reasoner_with_delete(store, reasoner):
    reasoner.insert(SPOUSE, TYPE, SYMMETRIC_PROPERTY)
    reasoner.insert(A, SPOUSE, B)

    assert (B, SPOUSE, A) in store

    reasoner.delete(A, SPOUSE, B)

    assert list(store.triples()) == [(SPOUSE, TYPE, SYMMETRIC_PROPERTY)]


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_transitive(store, reasoner):
    reasoner.insert(SUBCLASS_OF, TYPE, TRANSITIVE_PROPERTY)
    print(reasoner)

    reasoner.insert(PERSON, SUBCLASS_OF, THING)

    print(reasoner)

    reasoner.insert(THING, SUBCLASS_OF, OWL_THING)

    assert (PERSON, SUBCLASS_OF, OWL_THING) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_transitive_reverse(store, reasoner):
    reasoner.insert(SUBCLASS_OF, TYPE, TRANSITIVE_PROPERTY)
    reasoner.insert(THING, SUBCLASS_OF, OWL_THING)
    reasoner.insert(PERSON, SUBCLASS_OF, THING)

    assert (PERSON, SUBCLASS_OF, OWL_THING) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_transitive_with_delete(store, reasoner):
    reasoner.insert(SUBCLASS_OF, TYPE, TRANSITIVE_PROPERTY)
    reasoner.insert(PERSON, SUBCLASS_OF, THING)
    reasoner.insert(THING, SUBCLASS_OF, OWL_THING)

    reasoner.delete(SUBCLASS_OF, TYPE, TRANSITIVE_PROPERTY)

    assert list(store.triples()) == [(PERSON, SUBCLASS_OF, THING), (THING, SUBCLASS_OF, OWL_THING)]

    reasoner.insert(ORGANISATION, SUBCLASS_OF, THING)

    assert list(store.triples()) == [
        (ORGANISATION, SUBCLASS_OF, THING),
        (PERSON, SUBCLASS_OF, THING),
        (THING, SUBCLASS_OF, OWL_THING),
    ]


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_subclass_of(store, reasoner):
    reasoner.insert(PERSON, SUBCLASS_OF, THING)
    reasoner.insert(A, TYPE, PERSON)

    assert (A, TYPE, THING) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_subproperty_property(store, reasoner):
    reasoner.insert(SPOUSE, SUBPROPERTY_OF, RELATED_TO)
    reasoner.insert(A, SPOUSE, B)

    assert (A, RELATED_TO, B) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_domain_property(store, reasoner):
    reasoner.insert(SPOUSE, DOMAIN, PERSON)
    reasoner.insert(A, SPOUSE, B)

    assert (A, TYPE, PERSON) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_range_property(store, reasoner):
    reasoner.insert(SPOUSE, RANGE, PERSON)
    reasoner.insert(A, SPOUSE, B)

    assert (B, TYPE, PERSON) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_domain_range_property(store, reasoner):
    reasoner.insert(SPOUSE, DOMAIN, PERSON)
    reasoner.insert(SPOUSE, RANGE, PERSON)
    reasoner.insert(A, SPOUSE, B)

    assert (A, TYPE, PERSON) in store
    assert (B, TYPE, PERSON) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_with_child(store, reasoner):
    reasoner.insert(SPOUSE, TYPE, SYMMETRIC_PROPERTY)
    reasoner.insert(CHILDREN, INVERSE_OF, PARENT)

    reasoner.insert(A, SPOUSE, B)
    reasoner.insert(C, PARENT, A)
    reasoner.insert(C, PARENT, B)

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
def test_forward_reasoner_with_children_1(store, reasoner):
    reasoner.insert(CHILDREN, INVERSE_OF, PARENT)
    reasoner.register_rule((Variable("s"), PARENT, Variable("o")), parent_sibling_rule)

    reasoner.insert(A, CHILDREN, C)
    reasoner.insert(A, CHILDREN, D)

    assert ((PARENT, INVERSE_OF, CHILDREN), INFERRED_FROM, (CHILDREN, INVERSE_OF, PARENT)) in store
    assert (A, CHILDREN, C) in store
    assert (A, CHILDREN, D) in store
    assert (C, PARENT, A) in store
    assert (CHILDREN, INVERSE_OF, PARENT) in store
    assert (PARENT, INVERSE_OF, CHILDREN) in store


@pytest.mark.default_forward_reasoner
def test_forward_reasoner_with_children(store, reasoner):
    reasoner.insert(SPOUSE, TYPE, SYMMETRIC_PROPERTY)
    reasoner.insert(CHILDREN, INVERSE_OF, PARENT)
    reasoner.register_rule((Variable("s"), PARENT, Variable("o")), parent_sibling_rule)

    reasoner.insert(A, SPOUSE, B)
    reasoner.insert(C, PARENT, A)
    reasoner.insert(C, PARENT, B)
    reasoner.insert(D, PARENT, A)
    reasoner.insert(D, PARENT, B)

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
