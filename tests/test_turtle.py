import io
import pkgutil
import textwrap
from decimal import Decimal

import pytest
from lark import Lark, Token

from hexastore.ast import IRI, BlankNode, LangTaggedString, TypedLiteral
from hexastore.blank_node_factory import BlankNodeFactory
from hexastore.memory import InMemoryHexastore
from hexastore.model import Key
from hexastore.turtle import parse
from hexastore.turtle_serialiser import serialise


@pytest.fixture
def store():
    blank_node_factory = BlankNodeFactory()
    return InMemoryHexastore(blank_node_factory)


@pytest.mark.turtle
def test_turtle_escaped_string():
    document = """
        "Stiftung \\"Langmatt\\" Sidney und Jenny Brown"
    """

    turtle_parser = Lark(pkgutil.get_data("hexastore", "lark/turtle.lark").decode(), start="string", parser="lalr")
    ast = turtle_parser.parse(document)
    print(ast)
    assert ast.children[0] == Token("STRING_LITERAL_QUOTE", '"Stiftung \\"Langmatt\\" Sidney und Jenny Brown"')


@pytest.mark.turtle
def test_typed_literal(store):
    document = """
        <http://bnb.data.bl.uk/id/person/%C3%96zbayKaan1964-/birth> <http://purl.org/vocab/bio/0.1/date> "1964"^^<http://www.w3.org/2001/XMLSchema#gYear> .
    """

    parse(document, store.insert, store.blank_node_factory)

    assert list(store.triples()) == [
        (
            IRI("http://bnb.data.bl.uk/id/person/%C3%96zbayKaan1964-/birth"),
            IRI("http://purl.org/vocab/bio/0.1/date"),
            TypedLiteral("1964", IRI("http://www.w3.org/2001/XMLSchema#gYear")),
        )
    ]


@pytest.mark.turtle
def test_turtle_example_2(store):
    document = """
        <http://example.org/#spiderman>
            <http://www.perceive.net/schemas/relationship/enemyOf>
            <http://example.org/#green-goblin> .
    """

    parse(document, store.insert, store.blank_node_factory)

    assert list(store.triples()) == [
        (
            IRI("http://example.org/#spiderman"),
            IRI("http://www.perceive.net/schemas/relationship/enemyOf"),
            IRI("http://example.org/#green-goblin"),
        )
    ]


@pytest.mark.turtle
def test_turtle_example_3(store):
    document = """
        <http://example.org/#spiderman>
            <http://www.perceive.net/schemas/relationship/enemyOf> <http://example.org/#green-goblin> ;
            <http://xmlns.com/foaf/0.1/name> "Spiderman" .
    """

    parse(document, store.insert, store.blank_node_factory)

    assert list(store.triples()) == [
        (
            IRI("http://example.org/#spiderman"),
            IRI("http://www.perceive.net/schemas/relationship/enemyOf"),
            IRI("http://example.org/#green-goblin"),
        ),
        (IRI("http://example.org/#spiderman"), IRI("http://xmlns.com/foaf/0.1/name"), "Spiderman"),
    ]


@pytest.mark.turtle
def test_turtle_example_4(store):
    document = """
        <http://example.org/#spiderman> <http://xmlns.com/foaf/0.1/name> "Spiderman", "Человек-паук"@ru .
    """

    parse(document, store.insert, store.blank_node_factory)

    assert list(store.triples()) == [
        (IRI("http://example.org/#spiderman"), IRI("http://xmlns.com/foaf/0.1/name"), "Spiderman"),
        (
            IRI("http://example.org/#spiderman"),
            IRI("http://xmlns.com/foaf/0.1/name"),
            LangTaggedString("Человек-паук", "ru"),
        ),
    ]


@pytest.mark.turtle
def test_turtle_example_7(store):
    document = """
        @prefix somePrefix: <http://www.perceive.net/schemas/relationship/> .

        <http://example.org/#green-goblin> somePrefix:enemyOf <http://example.org/#spiderman> .
    """

    parse(document, store.insert, store.blank_node_factory)

    assert list(store.triples()) == [
        (
            IRI("http://example.org/#green-goblin"),
            IRI("http://www.perceive.net/schemas/relationship/enemyOf"),
            IRI("http://example.org/#spiderman"),
        )
    ]


@pytest.mark.turtle
def test_turtle_example_8(store):
    document = """
        PREFIX somePrefix: <http://www.perceive.net/schemas/relationship/>

        <http://example.org/#green-goblin> somePrefix:enemyOf <http://example.org/#spiderman> .
    """

    parse(document, store.insert, store.blank_node_factory)

    assert list(store.triples()) == [
        (
            IRI("http://example.org/#green-goblin"),
            IRI("http://www.perceive.net/schemas/relationship/enemyOf"),
            IRI("http://example.org/#spiderman"),
        )
    ]


@pytest.mark.turtle
def test_turtle_example_9(store):
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

    parse(document, store.insert, store.blank_node_factory)

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
def test_turtle_example_10(store):
    document = """
        @prefix foaf: <http://xmlns.com/foaf/0.1/> .

        <http://example.org/#green-goblin> foaf:name "Green Goblin" .

        <http://example.org/#spiderman> foaf:name "Spiderman" .
    """

    parse(document, store.insert, store.blank_node_factory)

    assert list(store.triples()) == [
        (IRI("http://example.org/#green-goblin"), IRI("http://xmlns.com/foaf/0.1/name"), "Green Goblin"),
        (IRI("http://example.org/#spiderman"), IRI("http://xmlns.com/foaf/0.1/name"), "Spiderman"),
    ]


@pytest.mark.turtle
def test_turtle_example_11(store):
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

    parse(document, store.insert, store.blank_node_factory)

    assert (
        IRI("http://example.org/vocab/show/218"),
        IRI("http://www.w3.org/2000/01/rdf-schema#label"),
        "That Seventies Show",
    ) in store


@pytest.mark.turtle
def test_turtle_example_12(store):
    document = """
        @prefix : <http://example.org/elements#> .

        <http://en.wikipedia.org/wiki/Helium>
            :atomicNumber 2 ;
            :atomicMass 4.002602 ;
            :specificGravity 1.663E-4 .
    """

    parse(document, store.insert, store.blank_node_factory)

    assert list(store.triples()) == [
        (
            IRI("http://en.wikipedia.org/wiki/Helium"),
            IRI("http://example.org/elements#atomicMass"),
            Decimal("4.002602"),
        ),
        (IRI("http://en.wikipedia.org/wiki/Helium"), IRI("http://example.org/elements#atomicNumber"), 2),
        (IRI("http://en.wikipedia.org/wiki/Helium"), IRI("http://example.org/elements#specificGravity"), 1.663e-4),
    ]


@pytest.mark.turtle
def test_turtle_example_15(store):
    document = """
        @prefix foaf: <http://xmlns.com/foaf/0.1/> .

        # Someone knows someone else, who has the name "Bob".
        [] foaf:knows [ foaf:name "Bob" ] .
    """

    parse(document, store.insert, store.blank_node_factory)

    assert list(store.triples()) == [
        (BlankNode(0, store.blank_node_factory), IRI("http://xmlns.com/foaf/0.1/knows"), BlankNode(1, store.blank_node_factory)),
        (BlankNode(1, store.blank_node_factory), IRI("http://xmlns.com/foaf/0.1/name"), "Bob"),
    ]


@pytest.mark.turtle
def test_turtleX_example_3(store):
    document = """
        @prefix : <http://example.org/> .
        @prefix foaf: <http://xmlns.com/foaf/0.1/> .
        @prefix dct: <http://purl.org/dc/elements/1.1/> .

        :bob foaf:name "Bob" .
        <<:bob foaf:age 23>> dct:creator <http://example.com/crawlers#c1> ;
            dct:source <http://example.net/homepage-listing.html> .
    """
    parse(document, store.insert, store.blank_node_factory)

    assert list(store.triples()) == [
        (
            (IRI("http://example.org/bob"), IRI("http://xmlns.com/foaf/0.1/age"), 23),
            IRI("http://purl.org/dc/elements/1.1/creator"),
            IRI("http://example.com/crawlers#c1"),
        ),
        (
            (IRI("http://example.org/bob"), IRI("http://xmlns.com/foaf/0.1/age"), 23),
            IRI("http://purl.org/dc/elements/1.1/source"),
            IRI("http://example.net/homepage-listing.html"),
        ),
        (IRI("http://example.org/bob"), IRI("http://xmlns.com/foaf/0.1/age"), 23),
        (IRI("http://example.org/bob"), IRI("http://xmlns.com/foaf/0.1/name"), "Bob"),
    ]


@pytest.mark.turtle_serialiser
def test_turtleX_example_3_serialise(store):
    document = """
        @prefix : <http://example.org/> .
        @prefix foaf: <http://xmlns.com/foaf/0.1/> .
        @prefix dct: <http://purl.org/dc/elements/1.1/> .

        :bob foaf:name "Bob" .
        <<:bob foaf:age 23>> dct:creator <http://example.com/crawlers#c1> ;
            dct:source <http://example.net/homepage-listing.html> .
    """

    parse(document, store.insert, store.blank_node_factory)

    out = io.StringIO()
    serialise(
        store,
        out,
        [
            ("", IRI("http://example.org/")),
            ("foaf", IRI("http://xmlns.com/foaf/0.1/")),
            ("dct", IRI("http://purl.org/dc/elements/1.1/")),
        ],
    )
    doc_out = out.getvalue()
    print(doc_out)
    assert (
        doc_out
        == textwrap.dedent(
            """
        @prefix : <http://example.org/> .
        @prefix foaf: <http://xmlns.com/foaf/0.1/> .
        @prefix dct: <http://purl.org/dc/elements/1.1/> .

        :bob foaf:age 23 ;
            foaf:name "Bob" .

        << :bob foaf:age 23 >> dct:creator <http://example.com/crawlers#c1> ;
            dct:source <http://example.net/homepage-listing.html> .

    """
        ).lstrip()
    )
