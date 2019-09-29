import logging

import pytest

from hexastore.aggregate_function import Count, Generic, Multi, Sample
from hexastore.ast import IRI, Order, OrderCondition, Variable
from hexastore.blank_node_factory import BlankNodeFactory
from hexastore.engine import execute
from hexastore.engine_ast import BGP, Distinct, Filter, GroupAggregate, LeftJoin, Project, Reduced
from hexastore.memory import InMemoryHexastore

DAVE_SMITH = IRI("http://example.com/dave-smith")
ERIC_MILLER = IRI("http://example.com/eric-miller")
ERIC_MILLER_MBOX = IRI("mailto:e.miller123(at)example")
W3 = IRI("http://example.com/w3")

TYPE = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")

KNOWS = IRI("http://xmlns.com/foaf/0.1/knows")
MBOX = IRI("http://xmlns.com/foaf/0.1/mbox")
NAME = IRI("http://xmlns.com/foaf/0.1/name")
AGE = IRI("http://xmlns.com/foaf/0.1/age")
ORGANIZATION = IRI("https://schema.org/Organization")
PERSON = IRI("http://xmlns.com/foaf/0.1/Person")
TITLE = IRI("http://xmlns.com/foaf/0.1/title")
WORKS_FOR = IRI("https://schema.org/worksFor")


@pytest.fixture
def store():
    blank_node_factory = BlankNodeFactory()
    hexastore = InMemoryHexastore(blank_node_factory)
    hexastore.insert(DAVE_SMITH, TYPE, PERSON)
    hexastore.insert(DAVE_SMITH, NAME, "Dave Smith")
    hexastore.insert(DAVE_SMITH, AGE, 21)

    hexastore.insert(ERIC_MILLER, TYPE, PERSON)
    hexastore.insert(ERIC_MILLER, NAME, "Eric Miller")
    hexastore.insert(ERIC_MILLER, MBOX, ERIC_MILLER_MBOX)
    hexastore.insert(ERIC_MILLER, TITLE, "Dr")
    hexastore.insert(ERIC_MILLER, AGE, 42)

    hexastore.insert(W3, TYPE, ORGANIZATION)
    hexastore.insert(W3, NAME, "W3")

    hexastore.insert(DAVE_SMITH, KNOWS, ERIC_MILLER)
    hexastore.insert(ERIC_MILLER, KNOWS, DAVE_SMITH)
    hexastore.insert(ERIC_MILLER, WORKS_FOR, W3)

    return hexastore


@pytest.mark.engine
def test_engine_with_order(caplog, store):
    caplog.set_level(logging.DEBUG)

    solutions, stats = execute(
        store,
        [(Variable("s"), Variable("p"), Variable("o"))],
        [OrderCondition("s", Order.DESCENDING), OrderCondition("p", Order.ASCENDING)],
    )

    assert solutions == [
        {Variable("s"): W3, Variable("p"): TYPE, Variable("o"): ORGANIZATION},
        {Variable("s"): W3, Variable("p"): NAME, Variable("o"): "W3"},
        {Variable("s"): ERIC_MILLER, Variable("p"): TYPE, Variable("o"): PERSON},
        {Variable("s"): ERIC_MILLER, Variable("p"): AGE, Variable("o"): 42},
        {Variable("s"): ERIC_MILLER, Variable("p"): KNOWS, Variable("o"): DAVE_SMITH},
        {Variable("s"): ERIC_MILLER, Variable("p"): MBOX, Variable("o"): ERIC_MILLER_MBOX},
        {Variable("s"): ERIC_MILLER, Variable("p"): NAME, Variable("o"): "Eric Miller"},
        {Variable("s"): ERIC_MILLER, Variable("p"): TITLE, Variable("o"): "Dr"},
        {Variable("s"): ERIC_MILLER, Variable("p"): WORKS_FOR, Variable("o"): W3},
        {Variable("s"): DAVE_SMITH, Variable("p"): TYPE, Variable("o"): PERSON},
        {Variable("s"): DAVE_SMITH, Variable("p"): AGE, Variable("o"): 21},
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
def test_engine_2_patterns_with_filter(store):
    solutions, stats = execute(
        store,
        Filter(
            BGP([(Variable("person"), TYPE, PERSON), (Variable("person"), NAME, Variable("name"))]),
            lambda s: s.get(Variable("name")).startswith("Eric"),
        ),
        [],
    )

    print(stats)

    assert solutions == [{Variable("person"): ERIC_MILLER, Variable("name"): "Eric Miller"}]


@pytest.mark.engine
def test_engine_2_patterns_with_projection(store):
    solutions, stats = execute(
        store,
        Project(
            [Variable("name")], BGP([(Variable("person"), TYPE, PERSON), (Variable("person"), NAME, Variable("name"))])
        ),
        [],
    )

    print(stats)

    assert solutions == [{Variable("name"): "Dave Smith"}, {Variable("name"): "Eric Miller"}]


@pytest.mark.engine
def test_engine_2_patterns_1_option(store):
    solutions, stats = execute(
        store,
        LeftJoin(
            BGP([(Variable("person"), TYPE, PERSON), (Variable("person"), NAME, Variable("name"))]),
            BGP([(Variable("person"), WORKS_FOR, Variable("works_for"))]),
        ),
        [],
    )

    print(stats)

    assert solutions == [
        {Variable("person"): DAVE_SMITH, Variable("name"): "Dave Smith"},
        {Variable("person"): ERIC_MILLER, Variable("name"): "Eric Miller", Variable("works_for"): W3},
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


@pytest.mark.engine
def test_engine_distinct(store):
    solutions, stats = execute(
        store, Distinct(Project([Variable("type")], BGP([(Variable("person"), TYPE, Variable("type"))]))), []
    )

    print(stats)

    assert solutions == [{Variable("type"): PERSON}, {Variable("type"): ORGANIZATION}]


@pytest.mark.engine
def test_engine_reduced(store):
    solutions, stats = execute(
        store, Reduced(Project([Variable("type")], BGP([(Variable("person"), TYPE, Variable("type"))]))), []
    )

    print(stats)

    assert solutions == [{Variable("type"): PERSON}, {Variable("type"): ORGANIZATION}]


@pytest.mark.engine
def test_engine_group_count(store):
    solutions, stats = execute(
        store,
        GroupAggregate(
            [Variable("type")], Count(Variable("count")), BGP([(Variable("person"), TYPE, Variable("type"))])
        ),
        [],
    )

    print(stats)

    assert solutions == [
        {Variable("type"): PERSON, Variable("count"): 2},
        {Variable("type"): ORGANIZATION, Variable("count"): 1},
    ]


@pytest.mark.engine
def test_engine_group_sample(store):
    solutions, stats = execute(
        store,
        GroupAggregate(
            [Variable("type")],
            Sample(Variable("person"), Variable("person")),
            BGP([(Variable("person"), TYPE, Variable("type"))]),
        ),
        [],
    )

    print(stats)

    assert solutions == [
        {Variable("type"): PERSON, Variable("person"): DAVE_SMITH},
        {Variable("type"): ORGANIZATION, Variable("person"): W3},
    ]


@pytest.mark.engine
def test_engine_group_age_stats(store):
    solutions, stats = execute(
        store,
        GroupAggregate(
            [Variable("type")],
            Multi(
                [
                    Generic(Variable("age"), sum, Variable("sum")),
                    Generic(Variable("age"), min, Variable("min")),
                    Generic(Variable("age"), max, Variable("max")),
                    Generic(Variable("name"), "|".join, Variable("names")),
                ]
            ),
            BGP(
                [
                    (Variable("person"), TYPE, Variable("type")),
                    (Variable("person"), AGE, Variable("age")),
                    (Variable("person"), NAME, Variable("name")),
                ]
            ),
        ),
        [],
    )

    print(stats)

    assert solutions == [
        {
            Variable("type"): PERSON,
            Variable("sum"): 63,
            Variable("min"): 21,
            Variable("max"): 42,
            Variable("names"): "Dave Smith|Eric Miller",
        }
    ]
