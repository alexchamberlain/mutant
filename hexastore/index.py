from .ast import Variable


SUBJECT = 1
PREDICATE = 2
OBJECT = 4


def get_index(pattern):
    index = 0
    key = []
    if not isinstance(pattern[0], Variable):
        index += SUBJECT
        key.append(pattern[0])

    if not isinstance(pattern[1], Variable):
        index += PREDICATE
        key.append(pattern[1])

    if not isinstance(pattern[2], Variable):
        index += OBJECT
        key.append(pattern[2])

    return index, tuple(key)
