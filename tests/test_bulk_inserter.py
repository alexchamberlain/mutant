import pytest

from hexastore.ast import IRI, BlankNode, TripleStatus, TripleStatusItem
from hexastore.bulk_inserter import BulkInserter
from hexastore.memory import InMemoryHexastore, TrunkPayload, VersionedInMemoryHexastore

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
def versioned_store():
    hexastore = VersionedInMemoryHexastore()
    hexastore.insert(DAVE_SMITH, TYPE, PERSON, 0)
    hexastore.insert(DAVE_SMITH, NAME, "Dave Smith", 1)

    return hexastore


@pytest.fixture
def bulk_inserter(versioned_store):

    inserter = BulkInserter(versioned_store)

    inserter.bulk_insert(
        [
            (ERIC_MILLER, TYPE, PERSON),
            (ERIC_MILLER, NAME, "Eric Miller"),
            (ERIC_MILLER, MBOX, ERIC_MILLER_MBOX),
            (ERIC_MILLER, TITLE, "Dr"),
            (DAVE_SMITH, KNOWS, ERIC_MILLER),
            (ERIC_MILLER, KNOWS, DAVE_SMITH),
        ]
    )

    return inserter


@pytest.mark.bulk_inserter
@pytest.mark.skip("Length not currently tracked")
def test_store(bulk_inserter):
    assert len(bulk_inserter) == 8


@pytest.mark.bulk_inserter
@pytest.mark.skip("Length not currently tracked")
def test_insert_existing_triple(bulk_inserter):
    assert len(bulk_inserter) == 8
    # Inserting duplicate triple should not increment length
    bulk_inserter.insert(DAVE_SMITH, NAME, "Dave Smith", 8)
    assert len(bulk_inserter) == 8


@pytest.mark.bulk_inserter
def test_triples(bulk_inserter):
    assert list(bulk_inserter.triples()) == [
        (DAVE_SMITH, TYPE, PERSON),
        (DAVE_SMITH, KNOWS, ERIC_MILLER),
        (DAVE_SMITH, NAME, "Dave Smith"),
        (ERIC_MILLER, TYPE, PERSON),
        (ERIC_MILLER, KNOWS, DAVE_SMITH),
        (ERIC_MILLER, MBOX, ERIC_MILLER_MBOX),
        (ERIC_MILLER, NAME, "Eric Miller"),
        (ERIC_MILLER, TITLE, "Dr"),
    ]


@pytest.mark.bulk_inserter
@pytest.mark.skip("bulk_inserter doesn't support index")
def test_index(bulk_inserter):
    assert bulk_inserter.index((DAVE_SMITH, NAME, "Dave Smith")) == 2
    assert bulk_inserter.index((DAVE_SMITH, NAME, "Eric Miller")) is None


@pytest.mark.bulk_inserter
def test_contains(bulk_inserter):
    assert (ERIC_MILLER, NAME, "Eric Miller") in bulk_inserter
    assert (ERIC_MILLER, NAME, "Dave Smith") not in bulk_inserter
    assert (ERIC_MILLER, TYPE, "Eric Miller") not in bulk_inserter


@pytest.mark.bulk_inserter
@pytest.mark.skip("bulk_inserter doesn't support terms.")
def test_terms(bulk_inserter):
    assert list(bulk_inserter.terms()) == [
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


@pytest.mark.bulk_inserter
def test_spo(bulk_inserter):
    assert bulk_inserter.spo == {
        DAVE_SMITH: TrunkPayload({TYPE: [PERSON], NAME: ["Dave Smith"], KNOWS: [ERIC_MILLER]}, 3),
        ERIC_MILLER: TrunkPayload(
            {TYPE: [PERSON], NAME: ["Eric Miller"], KNOWS: [DAVE_SMITH], MBOX: [ERIC_MILLER_MBOX], TITLE: ["Dr"]}, 5
        ),
    }


@pytest.mark.bulk_inserter
def test_sop(bulk_inserter):
    assert bulk_inserter.sop == {
        DAVE_SMITH: TrunkPayload({PERSON: [TYPE], "Dave Smith": [NAME], ERIC_MILLER: [KNOWS]}, 3),
        ERIC_MILLER: TrunkPayload(
            {"Dr": [TITLE], "Eric Miller": [NAME], DAVE_SMITH: [KNOWS], ERIC_MILLER_MBOX: [MBOX], PERSON: [TYPE]}, 5
        ),
    }


@pytest.mark.bulk_inserter
def test_pos(bulk_inserter):
    assert bulk_inserter.pos == {
        KNOWS: TrunkPayload({ERIC_MILLER: [DAVE_SMITH], DAVE_SMITH: [ERIC_MILLER]}, 2),
        MBOX: TrunkPayload({ERIC_MILLER_MBOX: [ERIC_MILLER]}, 1),
        NAME: TrunkPayload({"Dave Smith": [DAVE_SMITH], "Eric Miller": [ERIC_MILLER]}, 2),
        TITLE: TrunkPayload({"Dr": [ERIC_MILLER]}, 1),
        TYPE: TrunkPayload({PERSON: [DAVE_SMITH, ERIC_MILLER]}, 2),
    }


@pytest.mark.bulk_inserter
def test_pso(bulk_inserter):
    assert bulk_inserter.pso == {
        KNOWS: TrunkPayload({ERIC_MILLER: [DAVE_SMITH], DAVE_SMITH: [ERIC_MILLER]}, 2),
        MBOX: TrunkPayload({ERIC_MILLER: [ERIC_MILLER_MBOX]}, 1),
        NAME: TrunkPayload({DAVE_SMITH: ["Dave Smith"], ERIC_MILLER: ["Eric Miller"]}, 2),
        TITLE: TrunkPayload({ERIC_MILLER: ["Dr"]}, 1),
        TYPE: TrunkPayload({DAVE_SMITH: [PERSON], ERIC_MILLER: [PERSON]}, 2),
    }


@pytest.mark.bulk_inserter
def test_osp(bulk_inserter):
    assert bulk_inserter.osp == {
        "Dave Smith": TrunkPayload({DAVE_SMITH: [NAME]}, 1),
        "Dr": TrunkPayload({ERIC_MILLER: [TITLE]}, 1),
        "Eric Miller": TrunkPayload({ERIC_MILLER: [NAME]}, 1),
        DAVE_SMITH: TrunkPayload({ERIC_MILLER: [KNOWS]}, 1),
        ERIC_MILLER: TrunkPayload({DAVE_SMITH: [KNOWS]}, 1),
        ERIC_MILLER_MBOX: TrunkPayload({ERIC_MILLER: [MBOX]}, 1),
        PERSON: TrunkPayload({DAVE_SMITH: [TYPE], ERIC_MILLER: [TYPE]}, 2),
    }


@pytest.mark.bulk_inserter
def test_ops(bulk_inserter):
    assert bulk_inserter.ops == {
        "Dave Smith": TrunkPayload({NAME: [DAVE_SMITH]}, 1),
        "Dr": TrunkPayload({TITLE: [ERIC_MILLER]}, 1),
        "Eric Miller": TrunkPayload({NAME: [ERIC_MILLER]}, 1),
        DAVE_SMITH: TrunkPayload({KNOWS: [ERIC_MILLER]}, 1),
        ERIC_MILLER: TrunkPayload({KNOWS: [DAVE_SMITH]}, 1),
        ERIC_MILLER_MBOX: TrunkPayload({MBOX: [ERIC_MILLER]}, 1),
        PERSON: TrunkPayload({TYPE: [DAVE_SMITH, ERIC_MILLER]}, 2),
    }


@pytest.mark.bulk_inserter
def test_get_iterm(bulk_inserter):
    spo = bulk_inserter.spo

    assert spo[DAVE_SMITH][TYPE] == [PERSON]  # Underlying only
    assert spo[ERIC_MILLER][TYPE] == [PERSON]  # Overlay only

    pos = bulk_inserter.pos

    assert pos[TYPE][PERSON] == [DAVE_SMITH, ERIC_MILLER]


@pytest.mark.bulk_inserter
@pytest.mark.skip("bulk_inserter doesn't support delete")
def test_delete(bulk_inserter):
    assert len(bulk_inserter) == 8

    bulk_inserter.delete(DAVE_SMITH, KNOWS, ERIC_MILLER, 8)
    bulk_inserter.delete(ERIC_MILLER, KNOWS, DAVE_SMITH, 9)

    assert len(bulk_inserter) == 6

    assert bulk_inserter.spo[DAVE_SMITH][KNOWS][ERIC_MILLER] == _make_status(6, 8)
    assert bulk_inserter.pos[KNOWS][ERIC_MILLER][DAVE_SMITH] == _make_status(6, 8)
    assert bulk_inserter.osp[ERIC_MILLER][DAVE_SMITH][KNOWS] == _make_status(6, 8)
    assert bulk_inserter.sop[DAVE_SMITH][ERIC_MILLER][KNOWS] == _make_status(6, 8)
    assert bulk_inserter.pso[KNOWS][DAVE_SMITH][ERIC_MILLER] == _make_status(6, 8)
    assert bulk_inserter.ops[ERIC_MILLER][KNOWS][DAVE_SMITH] == _make_status(6, 8)

    assert bulk_inserter.spo[ERIC_MILLER][KNOWS][DAVE_SMITH] == _make_status(7, 9)
    assert bulk_inserter.pos[KNOWS][DAVE_SMITH][ERIC_MILLER] == _make_status(7, 9)
    assert bulk_inserter.osp[DAVE_SMITH][ERIC_MILLER][KNOWS] == _make_status(7, 9)
    assert bulk_inserter.sop[ERIC_MILLER][DAVE_SMITH][KNOWS] == _make_status(7, 9)
    assert bulk_inserter.pso[KNOWS][ERIC_MILLER][DAVE_SMITH] == _make_status(7, 9)
    assert bulk_inserter.ops[DAVE_SMITH][KNOWS][ERIC_MILLER] == _make_status(7, 9)


@pytest.mark.bulk_inserter
@pytest.mark.skip("bulk_inserter doesn't support delete")
def test_delete_non_existent_triple_inserts_tombstone(bulk_inserter):
    assert len(bulk_inserter) == 8

    bulk_inserter.delete(DAVE_SMITH, KNOWS, A, 8)

    assert len(bulk_inserter) == 8
    assert not bulk_inserter.spo[DAVE_SMITH][KNOWS][A].inserted
