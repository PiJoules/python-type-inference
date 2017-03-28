import pytype
import class_type


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

    def add_keys(self, keys):
        self.__key_types |= keys

    def add_values(self, values):
        self.__value_types |= values

    def merge_dict(self, dict_type):
        self.add_keys(dict_type.key_types())
        self.add_values(dict_type.value_types())

    def new_container(self, **kwargs):
        return DictPointer(self, **kwargs)

    def call_getitem(self):
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


class DictClass(class_type.ClassType):
    def __init__(self):
        super().__init__("dict")
        self.__dict = DictType()

    def instance(self):
        return self.__dict

    def call(self, args=None):
        """
        Arguments can be nothing, **kwargs, a dict and **kwargs, or an iterable and
        **kwargs where the iterable is a list of pairs (like the output of zip).
        """
        from tuple_type import TUPLE_CLASS

        if not args:
            return {self.instance().new_container()}
        else:
            kwargs_dict = self.instance().new_container(
                key_types=args.kwarg().key_types(),
                value_types=args.kwarg().value_types()
            )

            pos_args = args.pos_args()
            if len(pos_args) != 1:
                raise RuntimeError("dict expects 1 positional argument")

            types = pos_args[0]
            ret_types = set()
            for t in types:
                if isinstance(t, type(self.instance())):
                    # Dict type
                    new_d = self.instance().new_container(
                        key_types=t.key_types(),
                        value_types=t.value_types()
                    )
                    new_d.merge_dict(kwargs_dict)
                    ret_types.add(new_d)
                elif isinstance(t, type(TUPLE_CLASS.instance())):
                    # Iterable type
                    raise NotImplementedError("TODO: Implement logic for creating dict from an iterable type")
                else:
                    raise RuntimeError("Expected either mapping or iterable for dict argument")
            return ret_types


def create_class():
    cls = DictClass()

    return cls


DICT_CLASS = create_class()
