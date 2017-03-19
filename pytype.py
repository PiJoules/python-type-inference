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
            raise KeyError("Attribute '{}' not in pytype '{}'".format(attr, self.name()))

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


class FileType(ValueType):
    def __init__(self):
        super().__init__("File")

"""
Exceptions
"""

class ExceptionType(ValueType):
    def __init__(self, name="Exception", *args, **kwargs):
        super().__init__(name, *args, **kwargs)


class ValueErrorType(ExceptionType):
    def __init__(self):
        super().__init__("ValueError")



class StrType(ValueType):
    def __init__(self):
        super().__init__("str")

    def slice(self):
        return self

    def get_idx(self):
        return {self}


"""
Builtin types
"""
INT_TYPE = IntType()
FLOAT_TYPE = FloatType()
STR_TYPE = StrType()
BOOL_TYPE = BoolType()
NONE_TYPE = NoneType()
FILE_TYPE = FileType()


"""
Exceptions
"""
VALUE_ERROR = ValueErrorType()


def load_builtin_vars():
    from function_type import BuiltinFunction
    from class_type import BuiltinClass
    from instance_type import InstanceType
    from tuple_type import TupleType
    from dict_type import DictType

    tuple_type = TupleType()
    dict_type = DictType()


    """
    Add methods to types
    """
    class StripMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                keywords=["chars"],
                keyword_defaults=[{STR_TYPE}],
            )
        def call_and_update(self, args):
            return {STR_TYPE}
    STR_TYPE.add_attr("strip", {StripMethod()})

    class FormatMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                vararg="args",
                kwarg="kwargs",
            )
        def call_and_update(self, args):
            return {STR_TYPE}
    STR_TYPE.add_attr("format", {FormatMethod()})


    """
    Builtin functions
    """
    class PrintFunction(BuiltinFunction):
        def __init__(self):
            super().__init__(
                vararg="objects",
                kwonlyargs=["sep", "end", "file", "flush"],
                kwonly_defaults=[
                    {STR_TYPE}, {STR_TYPE}, {FILE_TYPE}, {BOOL_TYPE},
                ]
            )

        def call_and_update(self, args):
            return {NONE_TYPE}
    print_func = PrintFunction()


    class InputFunction(BuiltinFunction):
        def __init__(self):
            super().__init__(
                keywords=["prompt"],
                keyword_defaults=[{STR_TYPE}],
            )
        def call_and_update(self, args):
            return {STR_TYPE}
    input_func = InputFunction()


    """
    Builtin classes

    TODO: Add the other builtin classes for builtin types
    """
    class FloatClass(BuiltinClass):
        def create_and_init(self, args):
            return {FLOAT_TYPE}
    float_cls = FloatClass()

    class IntClass(BuiltinClass):
        def create_and_init(self, args):
            return {INT_TYPE}
    int_cls = IntClass()

    class BoolClass(BuiltinClass):
        def create_and_init(self, args):
            return {BOOL_TYPE}
    bool_cls = BoolClass()

    class StrClass(BuiltinClass):
        def create_and_init(self, args):
            return {STR_TYPE}
    str_cls = StrClass()


    """
    Exception classes
    """
    class ValueErrorClass(BuiltinClass):
        def create_and_init(self, args):
            return {VALUE_ERROR}
    value_err_cls = ValueErrorClass()


    return {
        "int": {int_cls},
        "float": {float_cls},
        "bool": {bool_cls},
        "str": {str_cls},
        "tuple": {tuple_type},
        "dict": {dict_type},
        "print": {print_func},
        "input": {input_func},

        "ValueError": {value_err_cls},
    }

