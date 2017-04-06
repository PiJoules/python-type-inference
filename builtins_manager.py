from builtin_types import *
from function_type import BuiltinFunction
from tuple_type import create_tuple_class
from dict_type import create_dict_class
from value_error_type import ValueErrorClass


class BuiltinsManager:
    def __init__(self):
        self.__create_builtins()

    def __create_builtins(self):
        self.__none = NoneClass(self).instance()
        self.__int_cls = IntClass(self)
        self.__float_cls = FloatClass(self)
        self.__bool_cls = BoolClass(self)
        self.__str_cls = StrClass(self)
        self.__file = FileClass(self).instance()
        self.__tuple_cls = create_tuple_class(self)
        self.__dict_cls = create_dict_class(self)

        self.__value_error_cls = ValueErrorClass(self)

    def exceptions(self):
        return {
            "ValueError": {self.value_error_cls()},
        }

    def constants(self):
        """Builtin constants"""
        return {
            "__name__": self.str(),
        }

    def functions(self):
        return {
            "int": {self.int_cls()},
            "float": {self.float_cls()},
            "bool": {self.bool_cls()},
            "str": {self.str_cls()},
            "tuple": {self.tuple_cls()},
            "dict": {self.dict_cls()},
            "print": {self.print()},
            "input": {self.input()},
        }

    def variables(self):
        """Builtin variables known to the top level enviornment."""
        builtins = {}
        builtins.update(self.functions())
        builtins.update(self.constants())
        builtins.update(self.exceptions())
        return builtins

    """
    Getters
    """

    def none(self):
        return self.__none

    def int(self):
        return self.int_cls().instance()

    def int_cls(self):
        return self.__int_cls

    def float(self):
        return self.float_cls().instance()

    def float_cls(self):
        return self.__float_cls

    def bool(self):
        return self.bool_cls().instance()

    def bool_cls(self):
        return self.__bool_cls

    def str_cls(self):
        return self.__str_cls

    def str(self):
        return self.str_cls().instance()

    def file(self):
        return self.__file

    def tuple_cls(self):
        return self.__tuple_cls

    def dict_cls(self):
        return self.__dict_cls

    """
    Functions
    """

    def print(self):
        class PrintFunction(BuiltinFunction):
            def __init__(self):
                super().__init__(
                    "print",
                    vararg="objects",
                    kwonlyargs=["sep", "end", "file", "flush"],
                    kwonly_defaults=[
                        {self.builtins().str()},
                        {self.builtins().str()},
                        {self.builtins().file()},
                        {self.builtins().bool()},
                    ]
                )

            def returns(self):
                return {self.builtins().none()}

        return PrintFunction(self)

    def input(self):
        class InputFunction(BuiltinFunction):
            def __init__(self):
                super().__init__(
                    "input",
                    keywords=["prompt"],
                    keyword_defaults=[{self.builtins().str()}],
                )

            def returns(self):
                return {self.builtins().str()}

        return InputFunction(self)

    """
    Exceptions
    """

    def value_error_cls(self):
        return self.__value_error_cls

