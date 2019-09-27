import pytest

from hexastore.ast import IRI, Order, OrderCondition, Variable
from hexastore.blank_node_factory import BlankNodeFactory
from hexastore.engine import execute
from hexastore.memory import VersionedInMemoryHexastore

DAVE_SMITH = IRI("http://example.com/dave-smith")
ERIC_MILLER = IRI("http://example.com/eric-miller")
ERIC_MILLER_MBOX = IRI("mailto:e.miller123(at)example")
W3 = IRI("http://example.com/w3")

TYPE = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")

KNOWS = IRI("http://xmlns.com/foaf/0.1/knows")
MBOX = IRI("http://xmlns.com/foaf/0.1/mbox")
NAME = IRI("http://xmlns.com/foaf/0.1/name")
ORGANIZATION = IRI("https://schema.org/Organization")
PERSON = IRI("http://xmlns.com/foaf/0.1/Person")
TITLE = IRI("http://xmlns.com/foaf/0.1/title")
WORKS_FOR = IRI("https://schema.org/worksFor")


@pytest.fixture
def store():
    blank_node_factory = BlankNodeFactory()
    hexastore = VersionedInMemoryHexastore(blank_node_factory)
    hexastore.insert(DAVE_SMITH, TYPE, PERSON, 0)
    hexastore.insert(DAVE_SMITH, NAME, "Dave Smith", 1)

    hexastore.insert(ERIC_MILLER, TYPE, PERSON, 2)
    hexastore.insert(ERIC_MILLER, NAME, "Eric Miller", 3)
    hexastore.insert(ERIC_MILLER, MBOX, ERIC_MILLER_MBOX, 4)
    hexastore.insert(ERIC_MILLER, TITLE, "Dr", 5)

    hexastore.insert(W3, TYPE, ORGANIZATION, 6)
    hexastore.insert(W3, NAME, "W3", 7)

    hexastore.insert(DAVE_SMITH, KNOWS, ERIC_MILLER, 8)
    hexastore.insert(ERIC_MILLER, KNOWS, DAVE_SMITH, 9)
    hexastore.insert(ERIC_MILLER, WORKS_FOR, W3, 10)

    return hexastore


@pytest.mark.engine
def test_engine_with_order(store):
    solutions, stats = execute(
        store,
        [(Variable("s"), Variable("p"), Variable("o"))],
        [OrderCondition("s", Order.DESCENDING), OrderCondition("p", Order.ASCENDING)],
    )

    assert solutions == [
        {Variable("s"): W3, Variable("p"): TYPE, Variable("o"): ORGANIZATION},
        {Variable("s"): W3, Variable("p"): NAME, Variable("o"): "W3"},
        {Variable("s"): ERIC_MILLER, Variable("p"): TYPE, Variable("o"): PERSON},
        {Variable("s"): ERIC_MILLER, Variable("p"): KNOWS, Variable("o"): DAVE_SMITH},
        {Variable("s"): ERIC_MILLER, Variable("p"): MBOX, Variable("o"): ERIC_MILLER_MBOX},
        {Variable("s"): ERIC_MILLER, Variable("p"): NAME, Variable("o"): "Eric Miller"},
        {Variable("s"): ERIC_MILLER, Variable("p"): TITLE, Variable("o"): "Dr"},
        {Variable("s"): ERIC_MILLER, Variable("p"): WORKS_FOR, Variable("o"): W3},
        {Variable("s"): DAVE_SMITH, Variable("p"): TYPE, Variable("o"): PERSON},
        {Variable("s"): DAVE_SMITH, Variable("p"): KNOWS, Variable("o"): ERIC_MILLER},
        {Variable("s"): DAVE_SMITH, Variable("p"): NAME, Variable("o"): "Dave Smith"},
    ]

    # In this case, we ask for all triples, so we should visit each triple once.
    assert stats.triples_visited == len(solutions)


@pytest.mark.engine
def test_engine_2_patterns(store):
    solutions, stats = execute(
        store, [(Variable("person"), TYPE, PERSON), (Variable("person"), NAME, Variable("name"))], []
    )

    print(stats)

    assert solutions == [
        {Variable("person"): DAVE_SMITH, Variable("name"): "Dave Smith"},
        {Variable("person"): ERIC_MILLER, Variable("name"): "Eric Miller"},
    ]


@pytest.mark.engine
def test_engine_2_patterns_with_order(store):
    solutions, stats = execute(
        store,
        [(Variable("person"), TYPE, PERSON), (Variable("person"), NAME, Variable("name"))],
        [OrderCondition("name", Order.DESCENDING)],
    )

    print(stats)

    assert solutions == [
        {Variable("person"): ERIC_MILLER, Variable("name"): "Eric Miller"},
        {Variable("person"): DAVE_SMITH, Variable("name"): "Dave Smith"},
    ]
