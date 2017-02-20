import ast
import inference


class PyType:
    def __init__(self, name, init_attrs=None, parents=None, owner=None):
        """
        Args:
            name (str)
            init_attrs (Optional[dict[str, set[PyType]]])
            parents (Optional[list[PyType]])
            owner (Optional[PyType])
        """
        self.__name = name
        self.__attrs = init_attrs or {}  # dict[str, set[PyType]]
        self.__parents = parents or []
        self.__owner = owner

    def name(self):
        return self.__name

    def __ne__(self, other):
        return not (self == other)




"""
Create builtin variables
"""

class ValueType(PyType):
    def __hash__(self):
        return id(self.name())

    def __eq__(self, other):
        return isinstance(other, type(self))


class IntType(ValueType):
    def __init__(self):
        super().__init__("int")


class BoolType(ValueType):
    def __init__(self):
        super().__init__("bool")


def load_builtin_vars():
    types = [
        IntType(),
        BoolType(),
    ]
    return {t.name(): {t} for t in types}

