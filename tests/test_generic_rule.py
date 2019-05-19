import pkgutil

from lark import Lark
import pytest

from hexastore import generic_rule
from hexastore.ast import Variable, IRI
from hexastore.memory import InMemoryHexastore
from hexastore.forward_reasoner import ForwardReasoner

A = IRI("http://example.com/A")
B = IRI("http://example.com/B")
C = IRI("http://example.com/C")
D = IRI("http://example.com/D")

SIBLING = IRI("https://schema.org/sibling")
PARENT = IRI("https://schema.org/parent")
INFERRED_FROM = IRI("https://example.com/inferred_from")


def make_parse(start):
    return Lark(
        pkgutil.get_data("hexastore", "lark/rule.lark").decode(),
        start=start,
        parser="lalr",
        transformer=generic_rule._Transformer(),
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
def test_parent_sibling():
    document = """
        @prefix schema: <https://schema.org/> .

        ($child1 schema:parent $parent), ($child2 schema:parent $parent)
            -> ($child1 schema:sibling $child2) .
    """

    rules = generic_rule.parse(document)

    assert rules == [
        generic_rule.Rule(
            [
                (Variable("child1"), IRI("https://schema.org/parent"), Variable("parent")),
                (Variable("child2"), IRI("https://schema.org/parent"), Variable("parent")),
            ],
            [(Variable("child1"), IRI("https://schema.org/sibling"), Variable("child2"))],
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
            [
                (Variable("child1"), IRI("https://schema.org/parent"), Variable("parent")),
                (Variable("child2"), IRI("https://schema.org/parent"), Variable("parent")),
            ],
            [(Variable("child1"), IRI("https://schema.org/sibling"), Variable("child2"))],
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
        generic_rule.Rule(
            [
                (
                    Variable("p"),
                    IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                    IRI("http://www.w3.org/2002/07/owl#SymmetricProperty"),
                )
            ],
            [
                generic_rule.Rule(
                    [(Variable("s"), Variable("p"), Variable("o"))], [(Variable("o"), Variable("p"), Variable("s"))]
                )
            ],
        )
    ]


@pytest.mark.generic_rule
def test_sibling_symmetric_parse_and_register_1():
    document = """
        @prefix schema: <https://schema.org/> .

        ($child1 schema:sibling $child2)
            → ($child2 schema:sibling $child1) .
    """

    store = InMemoryHexastore()
    reasoner = ForwardReasoner(store)

    generic_rule.parse_and_register(document, reasoner)

    reasoner.insert(A, SIBLING, B, 1)

    assert (A, SIBLING, B) in store
    assert (B, SIBLING, A) in store


@pytest.mark.generic_rule
def test_sibling_symmetric_parse_and_register_many():
    document = """
        @prefix schema: <https://schema.org/> .

        ($child1 schema:parent $parent), ($child2 schema:parent $parent)
            → ($child1 schema:sibling $child2) .
    """

    store = InMemoryHexastore()
    reasoner = ForwardReasoner(store)

    generic_rule.parse_and_register(document, reasoner)

    reasoner.insert(A, PARENT, C, 1)
    reasoner.insert(B, PARENT, C, 1)

    assert (A, SIBLING, B) in store
    assert (B, SIBLING, A) in store


@pytest.mark.generic_rule
def test_sibling_symmetric_parse_and_register_combined():
    document = """
        @prefix schema: <https://schema.org/> .

        ($child1 schema:sibling $child2)
            → ($child2 schema:sibling $child1) .
        ($child1 schema:parent $parent), ($child2 schema:parent $parent)
            → ($child1 schema:sibling $child2) .
    """

    store = InMemoryHexastore()
    reasoner = ForwardReasoner(store)

    generic_rule.parse_and_register(document, reasoner)

    reasoner.insert(A, PARENT, C, 1)
    reasoner.insert(B, PARENT, C, 1)

    assert (A, SIBLING, B) in store
    assert (B, SIBLING, A) in store
