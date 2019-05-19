from decimal import Decimal

import pytest

from hexastore.ast import IRI, LangTaggedString
from hexastore.model import Key
from hexastore.memory import InMemoryHexastore
from hexastore.turtle import parse


@pytest.mark.turtle
def test_turtle_example_2():
    document = """
        <http://example.org/#spiderman>
            <http://www.perceive.net/schemas/relationship/enemyOf>
            <http://example.org/#green-goblin> .
    """

    store = InMemoryHexastore()

    parse(document, lambda s, p, o: store.insert(s, p, o, 1))

    assert list(store.triples()) == [
        (
            IRI("http://example.org/#spiderman"),
            IRI("http://www.perceive.net/schemas/relationship/enemyOf"),
            IRI("http://example.org/#green-goblin"),
        )
    ]


@pytest.mark.turtle
def test_turtle_example_3():
    document = """
        <http://example.org/#spiderman>
            <http://www.perceive.net/schemas/relationship/enemyOf> <http://example.org/#green-goblin> ;
            <http://xmlns.com/foaf/0.1/name> "Spiderman" .
    """

    store = InMemoryHexastore()

    parse(document, lambda s, p, o: store.insert(s, p, o, 1))

    assert list(store.triples()) == [
        (
            IRI("http://example.org/#spiderman"),
            IRI("http://www.perceive.net/schemas/relationship/enemyOf"),
            IRI("http://example.org/#green-goblin"),
        ),
        (IRI("http://example.org/#spiderman"), IRI("http://xmlns.com/foaf/0.1/name"), "Spiderman"),
    ]


@pytest.mark.turtle
def test_turtle_example_4():
    document = """
        <http://example.org/#spiderman> <http://xmlns.com/foaf/0.1/name> "Spiderman", "Человек-паук"@ru .
    """

    store = InMemoryHexastore()

    parse(document, lambda s, p, o: store.insert(s, p, o, 1))

    assert list(store.triples()) == [
        (IRI("http://example.org/#spiderman"), IRI("http://xmlns.com/foaf/0.1/name"), "Spiderman"),
        (
            IRI("http://example.org/#spiderman"),
            IRI("http://xmlns.com/foaf/0.1/name"),
            LangTaggedString("Человек-паук", "ru"),
        ),
    ]


@pytest.mark.turtle
def test_turtle_example_7():
    document = """
        @prefix somePrefix: <http://www.perceive.net/schemas/relationship/> .

        <http://example.org/#green-goblin> somePrefix:enemyOf <http://example.org/#spiderman> .
    """

    store = InMemoryHexastore()

    parse(document, lambda s, p, o: store.insert(s, p, o, 1))

    assert list(store.triples()) == [
        (
            IRI("http://example.org/#green-goblin"),
            IRI("http://www.perceive.net/schemas/relationship/enemyOf"),
            IRI("http://example.org/#spiderman"),
        )
    ]


@pytest.mark.turtle
def test_turtle_example_8():
    document = """
        PREFIX somePrefix: <http://www.perceive.net/schemas/relationship/>

        <http://example.org/#green-goblin> somePrefix:enemyOf <http://example.org/#spiderman> .
    """

    store = InMemoryHexastore()

    parse(document, lambda s, p, o: store.insert(s, p, o, 1))

    assert list(store.triples()) == [
        (
            IRI("http://example.org/#green-goblin"),
            IRI("http://www.perceive.net/schemas/relationship/enemyOf"),
            IRI("http://example.org/#spiderman"),
        )
    ]


@pytest.mark.turtle
def test_turtle_example_9():
    document = """
        <http://one.example/subject1> <http://one.example/predicate1> <http://one.example/object1> .

        # @base <http://one.example/> .
        # <subject2> <predicate2> <object2> .

        # BASE <http://one.example/>
        # <subject2> <predicate2> <object2> .

        @prefix p: <http://two.example/> .
        p:subject3 p:predicate3 p:object3 .

        PREFIX p: <http://two.example/>
        p:subject3 p:predicate3 p:object3 .

        # @prefix p: <path/> .
        # p:subject4 p:predicate4 p:object4 .

        @prefix : <http://another.example/> .
        :subject5 :predicate5 :object5 .

        :subject6 a :subject7 .

        <http://伝言.example/?user=أكرم&amp;channel=R%26D> a :subject8 .
    """

    store = InMemoryHexastore()

    parse(document, lambda s, p, o: store.insert(s, p, o, 1))

    assert list(store.triples()) == sorted(
        [
            (
                IRI("http://one.example/subject1"),
                IRI("http://one.example/predicate1"),
                IRI("http://one.example/object1"),
            ),
            # (
            #     IRI("http://one.example/subject2"),
            #     IRI("http://one.example/predicate2"),
            #     IRI("http://one.example/object2"),
            # ),
            (
                IRI("http://two.example/subject3"),
                IRI("http://two.example/predicate3"),
                IRI("http://two.example/object3"),
            ),
            # (
            #     IRI("http://two.example/subject4"),
            #     IRI("http://two.example/predicate4"),
            #     IRI("http://two.example/object4"),
            # ),
            (
                IRI("http://another.example/subject5"),
                IRI("http://another.example/predicate5"),
                IRI("http://another.example/object5"),
            ),
            (
                IRI("http://another.example/subject6"),
                IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                IRI("http://another.example/subject7"),
            ),
            (
                IRI("http://伝言.example/?user=أكرم&amp;channel=R%26D"),
                IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                IRI("http://another.example/subject8"),
            ),
        ],
        key=Key,
    )


@pytest.mark.turtle
def test_turtle_example_10():
    document = """
        @prefix foaf: <http://xmlns.com/foaf/0.1/> .

        <http://example.org/#green-goblin> foaf:name "Green Goblin" .

        <http://example.org/#spiderman> foaf:name "Spiderman" .
    """

    store = InMemoryHexastore()

    parse(document, lambda s, p, o: store.insert(s, p, o, 1))

    assert list(store.triples()) == [
        (IRI("http://example.org/#green-goblin"), IRI("http://xmlns.com/foaf/0.1/name"), "Green Goblin"),
        (IRI("http://example.org/#spiderman"), IRI("http://xmlns.com/foaf/0.1/name"), "Spiderman"),
    ]


@pytest.mark.turtle
def test_turtle_example_11():
    document = """
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix show: <http://example.org/vocab/show/> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        show:218 rdfs:label "That Seventies Show"^^xsd:string .
        show:218 rdfs:label "That Seventies Show"^^<http://www.w3.org/2001/XMLSchema#string> .
        show:218 rdfs:label "That Seventies Show" .
        show:218 show:localName "That Seventies Show"@en .
        show:218 show:localName 'Cette Série des Années Soixante-dix'@fr .
        show:218 show:localName "Cette Série des Années Septante"@fr-be .
        show:218 show:blurb '''This is a multi-line
literal with many quotes (\"\"\"\"\")
and up to two sequential apostrophes ('').''' .
    """

    store = InMemoryHexastore()

    parse(document, lambda s, p, o: store.insert(s, p, o, 1))

    assert (
        IRI("http://example.org/vocab/show/218"),
        IRI("http://www.w3.org/2000/01/rdf-schema#label"),
        "That Seventies Show",
    ) in store


@pytest.mark.turtle
def test_turtle_example_12():
    document = """
        @prefix : <http://example.org/elements#> .

        <http://en.wikipedia.org/wiki/Helium>
            :atomicNumber 2 ;
            :atomicMass 4.002602 ;
            :specificGravity 1.663E-4 .
    """

    store = InMemoryHexastore()

    parse(document, lambda s, p, o: store.insert(s, p, o, 1))

    assert list(store.triples()) == [
        (
            IRI("http://en.wikipedia.org/wiki/Helium"),
            IRI("http://example.org/elements#atomicMass"),
            Decimal("4.002602"),
        ),
        (IRI("http://en.wikipedia.org/wiki/Helium"), IRI("http://example.org/elements#atomicNumber"), 2),
        (IRI("http://en.wikipedia.org/wiki/Helium"), IRI("http://example.org/elements#specificGravity"), 1.663e-4),
    ]