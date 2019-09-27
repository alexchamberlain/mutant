from .ast import BlankNode


class BlankNodeFactory:
    def __init__(self, initial_counter: int = 0):
        self.counter = initial_counter

    def __call__(self):
        node = BlankNode(self.counter, self)
        self.counter += 1
        return node
