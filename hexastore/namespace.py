from .ast import IRI


class Namespace:
    def __init__(self, name: str, prefix: IRI):
        self.name = name
        self.prefix = prefix

    def __str__(self) -> str:
        return f"{self.name}: <{self.prefix}>"

    def __repr__(self) -> str:
        return f"Namespace({self.name}, {repr(self.prefix)})"

    def term(self, name: str) -> IRI:
        return IRI(f"{self.prefix}{name}")
