import decimal
import logging
import pkgutil
from typing import Union, Tuple, Optional, Dict

from lark import Lark, Transformer, v_args

from .ast import IRI, Variable, BlankNode, LangTaggedString
from .namespace import Namespace

logger = logging.getLogger(__name__)

# MEMBER = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#member")
TYPE = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")

TermPattern = Union[IRI, str, Variable]
TriplePattern = Tuple[TermPattern, TermPattern, TermPattern]


@v_args(inline=True)
class _Transformer(Transformer):
    def __init__(self, insert, delete):
        self._insert = insert
        self._delete = delete
        self._base_uri: Optional[IRI] = None
        self._namespaces: Dict[str, Namespace] = {}
        self._bnodes: Dict[str, BlankNode] = {}

    def prefix_id(self, name, iri):
        n = name[:-1]
        self._namespaces[n] = Namespace(n, iri)

    def base(self, iri):
        self._base_uri = iri

    def sparql_prefix(self, name, iri):
        n = name[:-1]
        self._namespaces[n] = Namespace(n, iri)

    def sparql_base(self, iri):
        self._base_uri = iri

    def positive_triple(self, triples):
        for t in triples:
            self._insert(*t)

    def negative_triple(self, triples):
        for t in triples:
            self._delete(*t)

    def triples_1(self, subject, predicate_object_list):
        for p, o in predicate_object_list:
            yield (subject, p, o)

    def triples_2(self, blankNodePropertyList, predicate_object_list=None):
        assert False

    def predicate_object_list(self, *args):
        assert len(args) % 2 == 0

        for i in range(0, len(args), 2):
            verb, objectList = args[i : i + 2]
            for o in objectList:
                yield verb, o

    def object_list(self, *args):
        return args

    def verb(self, arg):
        return arg

    def a(self):
        return TYPE

    def subject(self, arg):
        return arg

    def object(self, arg):
        return arg

    def subject_x(self, arg):
        return arg

    def object_x(self, arg):
        return arg

    def literal(self, arg):
        return arg

    def rdf_literal_1(self, s):
        return s

    def rdf_literal_2(self, s, langtag):
        return LangTaggedString(s, langtag[1:])

    def rdf_literal_3(self, s, type):
        if type == IRI(value="http://www.w3.org/2001/XMLSchema#string"):
            return s
        else:
            assert False

    def string(self, s):
        if s.type == "STRING_LITERAL_QUOTE":
            return s[1:-1]
        elif s.type == "STRING_LITERAL_SINGLE_QUOTE":
            return s[1:-1]
        elif s.type == "STRING_LITERAL_LONG_SINGLE_QUOTE":
            return s[3:-3]
        elif s.type == "STRING_LITERAL_LONG_QUOTE":
            return s[3:-3]

    def iriref(self, arg):
        return IRI(arg)

    def prefixed_name(self, pname_ln):
        return IRI(pname_ln)

    def pname_ln(self, ns, pn_local):
        return self._namespaces[ns[:-1]].term(pn_local)

    def numeric_literal(self, arg):
        if arg.type == "INTEGER":
            return int(arg)
        elif arg.type == "DECIMAL":
            return decimal.Decimal(arg)
        elif arg.type == "DOUBLE":
            return float(arg)

    def triple_x(self, subject_x, predicate, object_x):
        t = (subject_x, predicate, object_x)
        self._insert(*t)
        return t


def parse(document, insert, delete):
    turtle_parser = Lark(
        pkgutil.get_data("hexastore", "lark/diff.lark").decode(),
        start="diff_document",
        parser="lalr",
        transformer=_Transformer(insert, delete),
    )
    turtle_parser.parse(document)
