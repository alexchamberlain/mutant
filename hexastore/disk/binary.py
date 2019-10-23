import struct

"""
    n-triples
    iri-start-integer
    string-offset
    string-start-integer
    lang-tagged-string-offset
    lang-tagged-string-start-integer
    int-offset
    int-start-integer
    decimal-offset
    decimal-start-integer
    float-offset
    float-start-integer
    typed-literal-offset
    typed-literal-start-integer
    n_terms
    subject-index offset
    n-subjects
    predicate-index offset
    n-predicates
    object-index offset
    n-objects
"""
HEADER = struct.Struct("<IIIIIIIIIIIIIIIIIIIII")

TERM = struct.Struct("<I")

TRUNK_PAYLOAD = struct.Struct("<IIII")
TERM_PAYLOAD = struct.Struct("<II")

LENGTH_PREFIX = struct.Struct("<H")

INT_PAYLOAD = struct.Struct("<q")
DOUBLE_PAYLOAD = struct.Struct("<d")
