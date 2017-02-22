import pytype


class DictType(pytype.PyType):
    def __init__(self, key_types=None, value_types=None):
        """
        Args:
            key_types (Optional[set[pytype.PyType]])
            value_types (Optional[set[pytype.PyType]])
        """
        super().__init__("dict")

        self.__key_types = key_types or set()
        self.__value_types = value_types or set()

        assert isinstance(self.__key_types, set)
        assert all(isinstance(x, pytype.PyType) for x in self.__key_types)
        assert isinstance(self.__value_types, set)
        assert all(isinstance(x, pytype.PyType) for x in self.__value_types)

    def key_types(self):
        return self.__key_types

    def value_types(self):
        return self.__value_types

    def new_container(self, **kwargs):
        return DictPointer(self, **kwargs)

    def get_idx(self, keys):
        return self.value_types()

    def __hash__(self):
        return hash(self.name())

    def __eq__(self, other):
        if not isinstance(other, DictType):
            return False

        return (self.key_types() == other.key_types() and
                self.value_types() == other.value_types())


class DictPointer(DictType):
    def __init__(self, original, **kwargs):
        super().__init__(**kwargs)
        self.__original = original

    def get_attr(self, attr):
        return self.__original.get_attr(attr)

    def add_attr(self, attr, types):
        return self.__original.add_attr(attr, types)

