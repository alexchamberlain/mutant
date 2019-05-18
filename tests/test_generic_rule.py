import pkgutil

from lark import Lark
import pytest

from hexastore import generic_rule
from hexastore.ast import Variable, IRI


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
