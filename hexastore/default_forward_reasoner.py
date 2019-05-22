"""
    Forward Reasoner with a default set of mutant rules loaded.
"""
import pkgutil

from . import generic_rule
from .forward_reasoner import ForwardReasoner


def default_forward_reasoner(store):
    reasoner = ForwardReasoner(store)

    rdfs = pkgutil.get_data("hexastore", "rules/rdfs.mtt").decode()
    generic_rule.parse_and_register(rdfs, reasoner)

    owl = pkgutil.get_data("hexastore", "rules/owl.mtt").decode()
    generic_rule.parse_and_register(owl, reasoner)

    return reasoner
