import pytype
import class_type


class TupleType(pytype.PyType):
    def __init__(self, init_contents=None):
        """
        Args:
            init_contents (Optional[tuple[set[pytype.PyType]]])
        """
        super().__init__("tuple")

        self.__contents = init_contents or tuple()

        assert isinstance(self.__contents, tuple)
        for types in self.__contents:
            assert isinstance(types, set)
            assert all(isinstance(x, pytype.PyType) for x in types)

    def call(self, args=None):
        return {
            TuplePointer(
                init_contents=self.contents(),
            )
        }

    def contents(self):
        return self.__contents

    def all_contents(self):
        """
        Returns:
            set[pytype.PyType]: Set of all types in the contents
        """
        ret_types = set()
        for types in self.contents():
            ret_types |= types
        return ret_types

    def new_container(self, **kwargs):
        """
        Create a new tuple that points to the original tuple when adding/getting
        attributes so that all attributes added to any tuple affect all tuples.
        """
        return TuplePointer(self, **kwargs)

    def call_getitem(self, args):
        types = set()
        for content_types in self.contents():
            types |= content_types
        return types

    def __hash__(self):
        # Tuple hash depends on hashs of contents
        return hash(tuple(hash(frozenset(x)) for x in self.contents()))

    def __eq__(self, other):
        # Tuples are equal if the contents are equal
        if not isinstance(other, TupleType):
            return False

        own_contents = self.contents()
        other_contents = other.contents()

        if len(own_contents) != len(other_contents):
            return False

        for i in range(len(own_contents)):
            if own_contents[i] != other_contents[i]:
                return False

        return True


class TuplePointer(TupleType):
    def __init__(self, original, **kwargs):
        super().__init__(**kwargs)
        self.__original = original

    def get_attr(self, attr):
        return self.__original.get_attr(attr)

    def set_attr(self, attr, types):
        return self.__original.set_attr(attr, types)


class TupleClass(class_type.ClassType):
    def __init__(self):
        super().__init__("tuple")
        self.__tup = TupleType()

    def instance(self):
        return self.__tup

    def call(self, args=None):
        if args:
            if len(args.pos_args()) != 1:
                raise RuntimeError("Tuple only accepts up to 1 argument.")
            types = args.pos_args()[0]
            return {self.instance().new_container(init_contents=t.contents()) for t in types}
        else:
            return {self.instance().new_container()}


def create_class():
    cls = TupleClass()

    return cls


TUPLE_CLASS = create_class()
