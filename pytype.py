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
        if attr in self.__attrs:
            return self.__attrs[attr]
        else:
            raise KeyError("Attr '{}' not in type '{}'".format(attr, self.name()))

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


class FloatType(ValueType):
    def __init__(self, *args, **kwargs):
        super().__init__("float", *args, **kwargs)


class BoolType(ValueType):
    def __init__(self):
        super().__init__("bool")


class NoneType(ValueType):
    def __init__(self):
        super().__init__("None")


class StrType(ValueType):
    def __init__(self):
        super().__init__("str")

    def slice(self):
        return self


def load_builtin_vars():
    from function_type import BuiltinFunction
    from class_type import ClassType
    from tuple_type import TupleType
    from dict_type import DictType

    int_type = IntType()
    float_type = FloatType()
    bool_type = BoolType()
    none_type = NoneType()
    str_type = StrType()
    tuple_type = TupleType()
    dict_type = DictType()

    class FileType(ValueType):
        def __init__(self):
            super().__init__("File")
    file_type = FileType()


    """
    Add methods to types
    """
    class StripMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                None, None,
                keywords=["chars"],
                keyword_defaults=[{str_type}],
            )
        def call_and_update(self, args):
            return {str_type}
    strip_method = StripMethod()
    str_type.add_attr("strip", {strip_method})


    """
    Builtin functions
    """
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


    class InputFunction(BuiltinFunction):
        def __init__(self):
            super().__init__(
                None, None,
                keywords=["prompt"],
                keyword_defaults=[{str_type}],
            )
        def call_and_update(self, args):
            return {str_type}
    input_func = InputFunction()


    """
    Builtin classes

    TODO: Add the other builtin classes for builtin types
    """
    class FloatClass(ClassType):
        def __init__(self):
            super().__init__(None)

        def create_and_init(self, args):
            return {float_type}
    float_cls = FloatClass()


    return {
        "int": {int_type},
        "float": {float_cls},
        "bool": {bool_type},
        "None": {none_type},
        "str": {str_type},
        "tuple": {tuple_type},
        "dict": {dict_type},
        "print": {print_func},
        "input": {input_func},
    }

