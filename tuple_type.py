from pytype import PyType
from instance_type import InstanceType
from class_type import DynamicClassType
from magic_methods import *


class TupleType(InstanceType):
    def __init__(self, builtins, init_contents=None, **kwargs):
        """
        Args:
            init_contents (Optional[tuple[set[pytype.PyType]]])
        """
        super().__init__("tuple", builtins, **kwargs)
        self.__contents = init_contents or set()
        assert isinstance(self.__contents, set)
        assert all(isinstance(x, PyType) for x in self.__contents)

    def contents(self):
        return self.__contents

    def __hash__(self):
        # Tuple hash depends on hashs of contents
        return hash(self.name())

    def __eq__(self, other):
        # Tuples are equal if the contents are equal
        if not isinstance(other, TupleType):
            return False
        return self.contents() == other.contents()

    def __bool__(self):
        return bool(self.contents())

    def __str__(self):
        str_contents = list(set(map(str, types)) for types in self.contents())
        return "tuple{}".format(str_contents)


class TupleGetItemMethod(GetItemMethod):
    def returns(self):
        results = set()
        self_types = self.env().lookup("self")
        key_types = self.env().lookup("key")

        for self_t in self_types:
            for key_t in key_types:
                if key_t.is_type(self.builtins().int()):
                    # Accessing 1 item in the tuple
                    results |= self_t.contents()
                else:
                    raise RuntimeError("Unable to index {} with key {}".format(self_t, key_t))

        return results


class TupleIterMethod(IterMethod):
    def returns(self):
        results = set()
        self_types = self.env().lookup("self")

        for self_t in self_types:
            results |= self_t.contents()

        return {self.builtins().generator_cls().instance(yields=results)}


class TupleClass(DynamicClassType):
    def __init__(self, builtins, **kwargs):
        super().__init__(
            builtins, TupleType,
            init_methods=(
                TupleGetItemMethod(builtins),
                TupleIterMethod(builtins),
            ),
            **kwargs
        )

    def from_tuple(self, tup):
        contents = set()
        for types in tup:
            contents |= types
        return self.instance(init_contents=contents)
