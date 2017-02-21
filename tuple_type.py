import pytype


class TupleType(pytype.PyType):
    def __init__(self, init_contents=None):
        super().__init__("tuple")

        self.__contents = init_contents or tuple()

        assert isinstance(self.__contents, tuple)
        for types in self.__contents:
            assert isinstance(types, set)
            assert all(isinstance(x, pytype.PyType) for x in types)

    def contents(self):
        return self.__contents

    def new_container(self, **kwargs):
        """
        Create a new tuple that points to the original tuple when adding/getting
        attributes so that all attributes added to any tuple affect all tuples.
        """
        return TuplePointer(self, **kwargs)

    def get_idx(self, keys):
        types = set()
        for key in keys:
            if not isinstance(key, pytype.IntType):
                raise TypeError("Tuple indeces must be IntTypes")
            else:
                print(key.value())
        raise NotImplementedError
        return types

    def __hash__(self):
        # Tuple hash depends on hashs of contents
        #return hash(tuple(map(hash, self.contents())))
        return hash(tuple(hash(frozenset(x)) for x in self.contents()))

    def __eq__(self, other):
        # Tuples are equal if the contents are equal
        if not isinstance(other, type(self)):
            return False

        own_contents = self.contents()
        other_contents = other.contents()

        if len(own_contents) != len(other_contents):
            return False

        for i in range(own_contents):
            if own_contents[i] != other_contents[i]:
                return False

        return True


class TuplePointer(TupleType):
    def __init__(self, original, **kwargs):
        super().__init__(**kwargs)
        self.__original = original

    def get_attr(self, attr):
        return self.__original.get_attr(attr)

    def add_attr(self, attr, types):
        return self.__original.add_attr(attr, types)

