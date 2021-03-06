import pkgutil

import pytest
from lark import Lark

from hexastore import generic_rule
from hexastore.ast import IRI, Variable
from hexastore.blank_node_factory import BlankNodeFactory
from hexastore.forward_reasoner import ForwardReasoner
from hexastore.memory import InMemoryHexastore
from hexastore.namespace import Namespace

A = IRI("http://example.com/A")
B = IRI("http://example.com/B")
C = IRI("http://example.com/C")
D = IRI("http://example.com/D")

FOO = IRI("http://example.com/Foo")
BAR = IRI("http://example.com/Bar")

SIBLING = IRI("https://schema.org/sibling")
PARENT = IRI("https://schema.org/parent")
SPOUSE = IRI("https://schema.org/spouse")
NAME = IRI("https://schema.org/name")
PERSON = IRI("https://schema.org/Person")
ORGANISATION = IRI("https://schema.org/Organisation")

SYMMETRIC_PROPERTY = IRI("http://www.w3.org/2002/07/owl#SymmetricProperty")
TYPE = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
RESOURCE = IRI("http://www.w3.org/2000/01/rdf-schema#Resource")
SUBCLASS_OF = IRI("http://www.w3.org/2000/01/rdf-schema#subclassOf")
INFERRED_FROM = IRI("https://example.com/inferred_from")


@pytest.fixture
def store():
    blank_node_factory = BlankNodeFactory()
    return InMemoryHexastore(blank_node_factory)


@pytest.fixture
def reasoner(store):
    return ForwardReasoner(store)


def make_parse(start, namespaces=None):
    return Lark(
        pkgutil.get_data("hexastore", "lark/rule.lark").decode(),
        start=start,
        parser="lalr",
        transformer=generic_rule._Transformer(namespaces),
    )


@pytest.mark.generic_rule
def test_parse():
    var_parser = make_parse("var")
    var_parser.parse("$child1")


@pytest.mark.generic_rule
def test_triple():
    var_parser = make_parse("triple")
    triple = var_parser.parse("($parent a <https://schema.org/Person>)")

    assert triple == (
        Variable("parent"),
        IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
        IRI("https://schema.org/Person"),
    )


@pytest.mark.generic_rule
def test_triple_member():
    var_parser = make_parse("triple")
    triple = var_parser.parse("($parent ∈ <http://example.com/set1>)")

    assert triple == (
        Variable("parent"),
        IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#member"),
        IRI("http://example.com/set1"),
    )


@pytest.mark.generic_rule
def test_rule_with_constraint():
    rule_parser = make_parse("rule", {"schema": Namespace("schema", IRI("https://schema.org/"))})
    rule = rule_parser.parse(
        """
            ($child1 schema:parent $parent), ($child2 schema:parent $parent) st ($child1 is-not $child2)
                → ($child1 schema:sibling $child2) .
        """
    )

    assert rule == generic_rule.Rule(
        (
            (Variable("child1"), IRI("https://schema.org/parent"), Variable("parent")),
            (Variable("child2"), IRI("https://schema.org/parent"), Variable("parent")),
        ),
        ((generic_rule.ConstraintIsNot((Variable("child1"), Variable("child2")))),),
        ((Variable("child1"), IRI("https://schema.org/sibling"), Variable("child2")),),
    )


@pytest.mark.generic_rule
def test_parent_sibling():
    document = """
        @prefix schema: <https://schema.org/> .

        ($child1 schema:parent $parent), ($child2 schema:parent $parent)
            -> ($child1 schema:sibling $child2) .
    """

    rules = generic_rule.parse(document)

    assert rules == [
        generic_rule.Rule(
            (
                (Variable("child1"), IRI("https://schema.org/parent"), Variable("parent")),
                (Variable("child2"), IRI("https://schema.org/parent"), Variable("parent")),
            ),
            tuple(),
            ((Variable("child1"), IRI("https://schema.org/sibling"), Variable("child2")),),
        )
    ]


@pytest.mark.generic_rule
def test_parent_sibling_2():
    document = """
        @prefix schema: <https://schema.org/> .

        ($child1 schema:parent $parent), ($child2 schema:parent $parent)
            → ($child1 schema:sibling $child2) .
    """

    rules = generic_rule.parse(document)

    assert rules == [
        generic_rule.Rule(
            (
                (Variable("child1"), IRI("https://schema.org/parent"), Variable("parent")),
                (Variable("child2"), IRI("https://schema.org/parent"), Variable("parent")),
            ),
            tuple(),
            ((Variable("child1"), IRI("https://schema.org/sibling"), Variable("child2")),),
        )
    ]


@pytest.mark.generic_rule
def test_symmetric():
    document = """
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix schema: <https://schema.org/> .

        ($p a owl:SymmetricProperty) → (
            ($s $p $o) → ($o $p $s) .
        ) .
    """

    rules = generic_rule.parse(document)

    assert rules == [
        generic_rule.RecursiveRule(
            ((Variable("p"), IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), SYMMETRIC_PROPERTY),),
            tuple(),
            (
                generic_rule.Rule(
                    ((Variable("s"), Variable("p"), Variable("o")),),
                    tuple(),
                    ((Variable("o"), Variable("p"), Variable("s")),),
                ),
            ),
        )
    ]


@pytest.mark.generic_rule
def test_sibling_symmetric_parse_and_register_1(store, reasoner):
    document = """
        @prefix schema: <https://schema.org/> .

        ($child1 schema:sibling $child2)
            → ($child2 schema:sibling $child1) .
    """

    generic_rule.parse_and_register(document, reasoner)

    reasoner.insert(A, SIBLING, B)

    assert (A, SIBLING, B) in store
    assert (B, SIBLING, A) in store


@pytest.mark.generic_rule
def test_sibling_symmetric_parse_and_register_many(store, reasoner):
    document = """
        @prefix schema: <https://schema.org/> .

        ($child1 schema:parent $parent), ($child2 schema:parent $parent) st ($child1 is-not $child2)
            → ($child1 schema:sibling $child2) .
    """

    generic_rule.parse_and_register(document, reasoner)

    reasoner.insert(A, PARENT, C)
    reasoner.insert(B, PARENT, C)

    assert (A, SIBLING, B) in store
    assert (B, SIBLING, A) in store
    assert (A, SIBLING, A) not in store


@pytest.mark.generic_rule
def test_sibling_symmetric_parse_and_register_combined(store, reasoner):
    document = """
        @prefix schema: <https://schema.org/> .

        ($child1 schema:sibling $child2)
            → ($child2 schema:sibling $child1) .
        ($child1 schema:parent $parent), ($child2 schema:parent $parent)
            → ($child1 schema:sibling $child2) .
    """

    generic_rule.parse_and_register(document, reasoner)

    reasoner.insert(A, PARENT, C)
    reasoner.insert(B, PARENT, C)

    assert (A, SIBLING, B) in store
    assert (B, SIBLING, A) in store


@pytest.mark.generic_rule
def test_symmetric_register(store, reasoner):
    document = """
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix schema: <https://schema.org/> .

        ($p a owl:SymmetricProperty) → (
            ($s $p $o) → ($o $p $s) .
        ) .
    """

    generic_rule.parse_and_register(document, reasoner)

    reasoner.insert(SPOUSE, TYPE, SYMMETRIC_PROPERTY)
    reasoner.insert(A, SPOUSE, B)

    assert (B, SPOUSE, A) in store


@pytest.mark.generic_rule
@pytest.mark.xfail
def test_recursive_recursive_rule_fails(store, reasoner):
    document = """
        @prefix example: <http://example.com/> .
        @prefix schema: <https://schema.org/> .

        ($s a example:Widget) → (
            ($p a example:WeirdProperty) → (
                ($s $p $o) → ($o $p $o) .
            ) .
        ) .
    """

    generic_rule.parse_and_register(document, reasoner)


@pytest.mark.generic_rule
def test_fixed_subject(store, reasoner):
    """This rule is arbitrary, as I can't think of a legit
    use case for this."""

    document = """
        @prefix example: <http://example.com/> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        (example:A a $o) → ($o rdfs:subclassOf rdfs:Resource) .
    """

    generic_rule.parse_and_register(document, reasoner)

    reasoner.insert(A, TYPE, FOO)
    reasoner.insert(B, TYPE, BAR)

    assert (FOO, SUBCLASS_OF, RESOURCE) in store
    assert (BAR, SUBCLASS_OF, RESOURCE) not in store


@pytest.mark.generic_rule
def test_fixed_object(store, reasoner):
    document = """
        @prefix example: <http://example.com/> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix schema: <https://schema.org/> .

        ($s a schema:Person) → ($s a example:Person) .
    """

    generic_rule.parse_and_register(document, reasoner)

    reasoner.insert(A, TYPE, PERSON)
    reasoner.insert(B, TYPE, ORGANISATION)

    assert (A, TYPE, IRI("http://example.com/Person")) in store
    assert (B, TYPE, IRI("http://example.com/Person")) not in store
