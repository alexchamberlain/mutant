import pytest

from hexastore.ast import IRI, TripleStatus, TripleStatusItem, BlankNode
from hexastore.memory import InMemoryHexastore


DAVE_SMITH = IRI("http://example.com/dave-smith")
ERIC_MILLER = IRI("http://example.com/eric-miller")
ERIC_MILLER_MBOX = IRI("mailto:e.miller123(at)example")

A = IRI("http://example.com/A")
B = IRI("http://example.com/B")
C = IRI("http://example.com/C")
D = IRI("http://example.com/D")

KNOWS = IRI("http://xmlns.com/foaf/0.1/knows")
MBOX = IRI("http://xmlns.com/foaf/0.1/mbox")
NAME = IRI("http://xmlns.com/foaf/0.1/name")
PERSON = IRI("http://xmlns.com/foaf/0.1/Person")
TITLE = IRI("http://xmlns.com/foaf/0.1/title")

CHILDREN = IRI("https://schema.org/children")
PARENT = IRI("https://schema.org/parent")
SIBLING = IRI("https://schema.org/sibling")
SPOUSE = IRI("https://schema.org/spouse")

BAG = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#Bag")
INFERRED_FROM = IRI("https://example.com/inferred_from")
TYPE = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")


@pytest.fixture
def store():
    hexastore = InMemoryHexastore()
    hexastore.insert(DAVE_SMITH, TYPE, PERSON, 0)
    hexastore.insert(DAVE_SMITH, NAME, "Dave Smith", 1)

    hexastore.insert(ERIC_MILLER, TYPE, PERSON, 2)
    hexastore.insert(ERIC_MILLER, NAME, "Eric Miller", 3)
    hexastore.insert(ERIC_MILLER, MBOX, ERIC_MILLER_MBOX, 4)
    hexastore.insert(ERIC_MILLER, TITLE, "Dr", 5)

    hexastore.insert(DAVE_SMITH, KNOWS, ERIC_MILLER, 6)
    hexastore.insert(ERIC_MILLER, KNOWS, DAVE_SMITH, 7)

    return hexastore


@pytest.mark.memory
def test_store(store):
    assert len(store) == 8


@pytest.mark.memory
def test_insert_existing_triple(store):
    assert len(store) == 8
    # Inserting duplicate triple should not increment length
    store.insert(DAVE_SMITH, NAME, "Dave Smith", 8)
    assert len(store) == 8


@pytest.mark.memory
def test_triples(store):
    assert list(store.triples()) == [
        (DAVE_SMITH, TYPE, PERSON),
        (DAVE_SMITH, KNOWS, ERIC_MILLER),
        (DAVE_SMITH, NAME, "Dave Smith"),
        (ERIC_MILLER, TYPE, PERSON),
        (ERIC_MILLER, KNOWS, DAVE_SMITH),
        (ERIC_MILLER, MBOX, ERIC_MILLER_MBOX),
        (ERIC_MILLER, NAME, "Eric Miller"),
        (ERIC_MILLER, TITLE, "Dr"),
    ]


@pytest.mark.memory
def test_index(store):
    assert store.index((DAVE_SMITH, NAME, "Dave Smith")) == 2
    assert store.index((DAVE_SMITH, NAME, "Eric Miller")) is None


@pytest.mark.memory
def test_contains(store):
    assert (ERIC_MILLER, NAME, "Eric Miller") in store
    assert (ERIC_MILLER, NAME, "Dave Smith") not in store
    assert (ERIC_MILLER, TYPE, "Eric Miller") not in store


@pytest.mark.memory
def test_terms(store):
    assert list(store.terms()) == [
        DAVE_SMITH,
        ERIC_MILLER,
        TYPE,
        PERSON,
        KNOWS,
        MBOX,
        NAME,
        TITLE,
        ERIC_MILLER_MBOX,
        "Dave Smith",
        "Dr",
        "Eric Miller",
    ]


def _make_status(index, valid_to=None):
    return TripleStatus([TripleStatusItem(valid_from=index, valid_to=valid_to)])


@pytest.mark.memory
def test_spo(store):
    assert store.spo == {
        DAVE_SMITH: {
            TYPE: {PERSON: _make_status(0)},
            NAME: {"Dave Smith": _make_status(1)},
            KNOWS: {ERIC_MILLER: _make_status(6)},
        },
        ERIC_MILLER: {
            TYPE: {PERSON: _make_status(2)},
            NAME: {"Eric Miller": _make_status(3)},
            KNOWS: {DAVE_SMITH: _make_status(7)},
            MBOX: {ERIC_MILLER_MBOX: _make_status(4)},
            TITLE: {"Dr": _make_status(5)},
        },
    }


@pytest.mark.memory
def test_sop(store):
    assert store.sop == {
        DAVE_SMITH: {
            PERSON: {TYPE: _make_status(0)},
            "Dave Smith": {NAME: _make_status(1)},
            ERIC_MILLER: {KNOWS: _make_status(6)},
        },
        ERIC_MILLER: {
            "Dr": {TITLE: _make_status(5)},
            "Eric Miller": {NAME: _make_status(3)},
            DAVE_SMITH: {KNOWS: _make_status(7)},
            ERIC_MILLER_MBOX: {MBOX: _make_status(4)},
            PERSON: {TYPE: _make_status(2)},
        },
    }


@pytest.mark.memory
def test_pos(store):
    assert store.pos == {
        KNOWS: {ERIC_MILLER: {DAVE_SMITH: _make_status(6)}, DAVE_SMITH: {ERIC_MILLER: _make_status(7)}},
        MBOX: {ERIC_MILLER_MBOX: {ERIC_MILLER: _make_status(4)}},
        NAME: {"Dave Smith": {DAVE_SMITH: _make_status(1)}, "Eric Miller": {ERIC_MILLER: _make_status(3)}},
        TITLE: {"Dr": {ERIC_MILLER: _make_status(5)}},
        TYPE: {PERSON: {DAVE_SMITH: _make_status(0), ERIC_MILLER: _make_status(2)}},
    }


@pytest.mark.memory
def test_pso(store):
    assert store.pso == {
        KNOWS: {ERIC_MILLER: {DAVE_SMITH: _make_status(7)}, DAVE_SMITH: {ERIC_MILLER: _make_status(6)}},
        MBOX: {ERIC_MILLER: {ERIC_MILLER_MBOX: _make_status(4)}},
        NAME: {DAVE_SMITH: {"Dave Smith": _make_status(1)}, ERIC_MILLER: {"Eric Miller": _make_status(3)}},
        TITLE: {ERIC_MILLER: {"Dr": _make_status(5)}},
        TYPE: {DAVE_SMITH: {PERSON: _make_status(0)}, ERIC_MILLER: {PERSON: _make_status(2)}},
    }


@pytest.mark.memory
def test_osp(store):
    assert store.osp == {
        "Dave Smith": {DAVE_SMITH: {NAME: _make_status(1)}},
        "Dr": {ERIC_MILLER: {TITLE: _make_status(5)}},
        "Eric Miller": {ERIC_MILLER: {NAME: _make_status(3)}},
        DAVE_SMITH: {ERIC_MILLER: {KNOWS: _make_status(7)}},
        ERIC_MILLER: {DAVE_SMITH: {KNOWS: _make_status(6)}},
        ERIC_MILLER_MBOX: {ERIC_MILLER: {MBOX: _make_status(4)}},
        PERSON: {DAVE_SMITH: {TYPE: _make_status(0)}, ERIC_MILLER: {TYPE: _make_status(2)}},
    }


@pytest.mark.memory
def test_ops(store):
    assert store.ops == {
        "Dave Smith": {NAME: {DAVE_SMITH: _make_status(1)}},
        "Dr": {TITLE: {ERIC_MILLER: _make_status(5)}},
        "Eric Miller": {NAME: {ERIC_MILLER: _make_status(3)}},
        DAVE_SMITH: {KNOWS: {ERIC_MILLER: _make_status(7)}},
        ERIC_MILLER: {KNOWS: {DAVE_SMITH: _make_status(6)}},
        ERIC_MILLER_MBOX: {MBOX: {ERIC_MILLER: _make_status(4)}},
        PERSON: {TYPE: {DAVE_SMITH: _make_status(0), ERIC_MILLER: _make_status(2)}},
    }


@pytest.mark.memory
def test_delete(store):
    assert len(store) == 8

    store.delete(DAVE_SMITH, KNOWS, ERIC_MILLER, 8)
    store.delete(ERIC_MILLER, KNOWS, DAVE_SMITH, 9)

    assert len(store) == 6

    assert store.spo[DAVE_SMITH][KNOWS][ERIC_MILLER] == _make_status(6, 8)
    assert store.pos[KNOWS][ERIC_MILLER][DAVE_SMITH] == _make_status(6, 8)
    assert store.osp[ERIC_MILLER][DAVE_SMITH][KNOWS] == _make_status(6, 8)
    assert store.sop[DAVE_SMITH][ERIC_MILLER][KNOWS] == _make_status(6, 8)
    assert store.pso[KNOWS][DAVE_SMITH][ERIC_MILLER] == _make_status(6, 8)
    assert store.ops[ERIC_MILLER][KNOWS][DAVE_SMITH] == _make_status(6, 8)

    assert store.spo[ERIC_MILLER][KNOWS][DAVE_SMITH] == _make_status(7, 9)
    assert store.pos[KNOWS][DAVE_SMITH][ERIC_MILLER] == _make_status(7, 9)
    assert store.osp[DAVE_SMITH][ERIC_MILLER][KNOWS] == _make_status(7, 9)
    assert store.sop[ERIC_MILLER][DAVE_SMITH][KNOWS] == _make_status(7, 9)
    assert store.pso[KNOWS][ERIC_MILLER][DAVE_SMITH] == _make_status(7, 9)
    assert store.ops[DAVE_SMITH][KNOWS][ERIC_MILLER] == _make_status(7, 9)


@pytest.mark.memory
def test_delete_non_existent_triple_inserts_tombstone(store):
    assert len(store) == 8

    store.delete(DAVE_SMITH, KNOWS, A, 8)

    assert len(store) == 8
    assert not store.spo[DAVE_SMITH][KNOWS][A].inserted


@pytest.fixture
def store_with_inference():
    hexastore = InMemoryHexastore()
    hexastore.insert(DAVE_SMITH, TYPE, PERSON, 0)
    hexastore.insert(DAVE_SMITH, NAME, "Dave Smith", 1)

    hexastore.insert(ERIC_MILLER, TYPE, PERSON, 2)
    hexastore.insert(ERIC_MILLER, NAME, "Eric Miller", 3)
    hexastore.insert(ERIC_MILLER, MBOX, ERIC_MILLER_MBOX, 4)
    hexastore.insert(ERIC_MILLER, TITLE, "Dr", 5)

    hexastore.insert(DAVE_SMITH, KNOWS, ERIC_MILLER, 6)
    hexastore.insert(ERIC_MILLER, KNOWS, DAVE_SMITH, 7)
    hexastore.insert((ERIC_MILLER, KNOWS, DAVE_SMITH), INFERRED_FROM, (DAVE_SMITH, KNOWS, ERIC_MILLER), 8)

    return hexastore


@pytest.mark.memory
def test_store_with_inference(store_with_inference):
    assert len(store_with_inference) == 9
    assert ((ERIC_MILLER, KNOWS, DAVE_SMITH), INFERRED_FROM, (DAVE_SMITH, KNOWS, ERIC_MILLER)) in store_with_inference


@pytest.fixture
def store_family_tree():
    hexastore = InMemoryHexastore()
    hexastore.insert(A, SPOUSE, B, 1)
    hexastore.insert(B, SPOUSE, A, 1)
    hexastore.insert((B, SPOUSE, A), INFERRED_FROM, (A, SPOUSE, B), 1)

    hexastore.insert(C, PARENT, A, 2)
    hexastore.insert(A, CHILDREN, C, 2)
    hexastore.insert((A, CHILDREN, C), INFERRED_FROM, (C, PARENT, A), 2)

    hexastore.insert(C, PARENT, B, 3)
    hexastore.insert(B, CHILDREN, C, 3)
    hexastore.insert((B, CHILDREN, C), INFERRED_FROM, (C, PARENT, B), 3)

    hexastore.insert(D, PARENT, A, 4)
    hexastore.insert(A, CHILDREN, D, 4)
    hexastore.insert(C, SIBLING, D, 4)
    hexastore.insert(D, SIBLING, C, 4)
    hexastore.insert((A, CHILDREN, D), INFERRED_FROM, (D, PARENT, A), 4)

    node = BlankNode()
    hexastore.insert(node, TYPE, BAG, 4)
    hexastore.insert((C, SIBLING, D), INFERRED_FROM, node, 4)
    hexastore.insert(node, _li(1), (D, PARENT, A), 4)
    hexastore.insert(node, _li(2), (C, PARENT, A), 4)

    node = BlankNode()
    hexastore.insert(node, TYPE, BAG, 4)
    hexastore.insert((D, SIBLING, C), INFERRED_FROM, node, 4)
    hexastore.insert(node, _li(1), (D, PARENT, A), 4)
    hexastore.insert(node, _li(2), (C, PARENT, A), 4)

    hexastore.insert(D, PARENT, B, 5)
    hexastore.insert(B, CHILDREN, D, 5)
    hexastore.insert((B, CHILDREN, D), INFERRED_FROM, (D, PARENT, B), 5)

    node = BlankNode()
    hexastore.insert(node, TYPE, BAG, 5)
    hexastore.insert((C, SIBLING, D), INFERRED_FROM, node, 5)
    hexastore.insert(node, _li(1), (D, PARENT, B), 5)
    hexastore.insert(node, _li(2), (C, PARENT, B), 5)

    node = BlankNode()
    hexastore.insert(node, TYPE, BAG, 5)
    hexastore.insert((D, SIBLING, C), INFERRED_FROM, node, 5)
    hexastore.insert(node, _li(1), (D, PARENT, B), 5)
    hexastore.insert(node, _li(2), (C, PARENT, B), 5)

    return hexastore


def _li(n: int):
    return IRI(f"http://www.w3.org/1999/02/22-rdf-syntax-ns#_{n}")


@pytest.mark.memory
def test_store_family_tree(store_family_tree):
    assert len(store_family_tree) == 33
