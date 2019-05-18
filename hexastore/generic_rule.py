import pkgutil

import attr
from lark import Lark, Transformer, v_args

from .ast import IRI, Variable
from .namespace import Namespace

MEMBER = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#member")
TYPE = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")

rule_parser = Lark(pkgutil.get_data("hexastore", "lark/rule.lark").decode(), start="document", parser="lalr")


def parse(document):
    tree = rule_parser.parse(document)

    print(tree.pretty())

    transformer = _Transformer()
    return transformer.transform(tree)


@attr.s
class Rule:
    body = attr.ib()
    head = attr.ib()


class _Transformer(Transformer):
    def __init__(self):
        self._namespaces = {}

    @v_args(inline=True)
    def document(self, preamble, rules):
        return rules.children

    @v_args(inline=True)
    def prefix(self, prefix, iri):
        n = Namespace(prefix, iri)
        self._namespaces[prefix] = n
        return n

    @v_args(inline=True)
    def rule(self, body, head):
        return Rule(body.children, head.children)

    @v_args(inline=True)
    def triple(self, s, p, o):
        return (s, p, o)

    @v_args(inline=True)
    def prefixed_name(self, prefix, local):
        n = self._namespaces[prefix]
        return n.term(local)

    @v_args(inline=True)
    def var(self, name):
        return Variable(str(name))

    @v_args(inline=True)
    def iriref(self, iri):
        return IRI(str(iri))

    @v_args(inline=True)
    def predicate(self, p):
        return p

    @v_args(inline=True)
    def a(self):
        return TYPE

    @v_args(inline=True)
    def member_of(self):
        return MEMBER
