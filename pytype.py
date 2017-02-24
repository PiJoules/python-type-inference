import ast
import inference


class PyType:
    def __init__(self, name, init_attrs=None, parents=None):
        """
        Args:
            name (str)
            init_attrs (Optional[dict[str, set[PyType]]])
            parents (Optional[list[PyType]])
        """
        self.__name = name
        self.__attrs = init_attrs or {}  # dict[str, set[PyType]]
        self.__parents = parents or []

    def name(self):
        return self.__name

    def attrs(self):
        return self.__attrs

    def add_attr(self, attr, types):
        assert isinstance(types, set)
        assert all(isinstance(x, PyType) for x in types)

        if attr in self.__attrs:
            self.__attrs[attr] |= types
        else:
            self.__attrs[attr] = set(types)

    def get_attr(self, attr):
        return self.__attrs[attr]

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        raise NotImplementedError("Must implement __hash__ for pytype '{}'".format(type(self)))

    def __eq__(self, other):
        raise NotImplementedError("Must implement __eq__ for pytype '{}'".format(type(self)))




"""
Create builtin variables
"""

class ValueType(PyType):
    def __init__(self, name, *args, value=None, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.__value = value

    def value(self):
        return self.__value

    def __hash__(self):
        return id(self.name())

    def __eq__(self, other):
        return isinstance(other, type(self))


class IntType(ValueType):
    def __init__(self, *args, **kwargs):
        super().__init__("int", *args, **kwargs)


class BoolType(ValueType):
    def __init__(self):
        super().__init__("bool")


class NoneType(ValueType):
    def __init__(self):
        super().__init__("None")


class StrType(ValueType):
    def __init__(self):
        super().__init__("str")


def load_builtin_vars():
    from function_type import BuiltinFunction
    from tuple_type import TupleType
    from dict_type import DictType

    int_type = IntType()
    bool_type = BoolType()
    none_type = NoneType()
    str_type = StrType()
    tuple_type = TupleType()
    dict_type = DictType()

    class FileType(ValueType):
        def __init__(self):
            super().__init__("File")
    file_type = FileType()

    class PrintFunction(BuiltinFunction):
        def __init__(self):
            super().__init__(None, None,
                             vararg="objects",
                             kwonlyargs=["sep", "end", "file", "flush"],
                             kwonly_defaults=[
                                 {str_type}, {str_type}, {file_type}, {bool_type},
                             ])

        def call_and_update(self, args):
            return {none_type}
    print_func = PrintFunction()

    return {
        "int": {int_type},
        "bool": {bool_type},
        "None": {none_type},
        "str": {str_type},
        "tuple": {tuple_type},
        "dict": {dict_type},
        "print": {print_func},
    }


def load_builtin_modules():
    """
    Returns:
        dict[str, ModuleType]
    """
    from module_type import ModuleType



    return {}

