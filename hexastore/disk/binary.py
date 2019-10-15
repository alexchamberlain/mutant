import struct

"""
    n-triples
    iri-start-integer
    string-offset
    string-start-integer
    subject-index offset
    n-subjects
    predicate-index offset
    n-predicates
    object-index offset
    n-objects
"""
HEADER = struct.Struct("<IIIIIIIIII")

TERM = struct.Struct("<I")

TRUNK_PAYLOAD = struct.Struct("<IIII")
TERM_PAYLOAD = struct.Struct("<II")

LENGTH_PREFIX = struct.Struct("<H")
