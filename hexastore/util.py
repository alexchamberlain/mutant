from typing import TypeVar, Callable, Tuple

T = TypeVar("T")
U = TypeVar("U")


def triple_map(func: Callable[[U], T], triple: Tuple[U, U, U]) -> Tuple[T, T, T]:
    return func(triple[0]), func(triple[1]), func(triple[2])
