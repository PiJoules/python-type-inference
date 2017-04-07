from builtin_types import *
from class_type import *
from module_type import *

from function_type import FunctionType
import tuple_type
import dict_type


class NoneClass(StaticClassType):
    def __init__(self, builtins):
        super().__init__(
            "None", builtins,
        )


class ExceptionClass(StaticClassType):
    def __init__(self, builtins, **kwargs):
        super().__init__(
            "Exception",
            builtins,
            **kwargs
        )


class ValueErrorClass(StaticClassType):
    def __init__(self, builtins, **kwargs):
        super().__init__(
            "ValueError", builtins,
            parents=[builtins.exception_cls()],
            **kwargs
        )


class BuiltinsManager:
    def __init__(self):
        self.__create_builtins()

    def __create_builtins(self):
        self.__none_cls = NoneClass(self)
        self.__int_cls = IntClass(self)
        self.__float_cls = FloatClass(self)
        self.__bool_cls = BoolClass(self)
        self.__slice_cls = SliceClass(self)
        self.__str_cls = StrClass(self)
        self.__file = FileClass(self).instance()
        self.__tuple_cls = tuple_type.TupleClass(self)
        self.__dict_cls = dict_type.DictClass(self)
        self.__list_cls = ListClass(self)

        self.__generator_cls = GeneratorClass(self)


        self.__create_exceptions()
        self.__create_free_functions()
        self.__initialize_modules()

    def __create_free_functions(self):
        class PrintFunction(FunctionType):
            def __init__(self, builtins):
                super().__init__(
                    "print", builtins,
                    vararg="objects",
                    kwonlyargs=["sep", "end", "file", "flush"],
                    kwonly_defaults=[
                        {builtins.str()},
                        {builtins.str()},
                        {builtins.file()},
                        {builtins.bool()},
                    ]
                )

            def returns(self):
                return {self.builtins().none()}

        self.__print_func = PrintFunction(self)


        class InputFunction(FunctionType):
            def __init__(self, builtins):
                super().__init__(
                    "input", builtins,
                    keywords=["prompt"],
                    keyword_defaults=[{builtins.str()}],
                )

            def returns(self):
                return {self.builtins().str()}

        self.__input_func = InputFunction(self)

    def __create_exceptions(self):
        self.__exception_cls = ExceptionClass(self)
        self.__value_error_cls = ValueErrorClass(self)

    def __initialize_modules(self):
        """Modules will only be built if imported."""
        self.__math_mod = MathModuleType(self)
        self.__loaded_modules = {}

    def exceptions(self):
        return {
            "Exception": {self.exception_cls()},
            "ValueError": {self.value_error_cls()},
        }

    def constants(self):
        """Builtin constants"""
        return {
            "__name__": {self.str()},
        }

    def functions(self):
        return {
            "int": {self.int_cls()},
            "float": {self.float_cls()},
            "bool": {self.bool_cls()},
            "str": {self.str_cls()},
            "tuple": {self.tuple_cls()},
            "dict": {self.dict_cls()},
            "print": {self.print_func()},
            "input": {self.input_func()},
        }

    def variables(self):
        """Builtin variables known to the top level enviornment."""
        builtins = {}
        builtins.update(self.functions())
        builtins.update(self.constants())
        builtins.update(self.exceptions())
        return builtins

    def loaded_modules(self):
        return self.__loaded_modules

    def builtin_modules(self):
        return {
            "math": self.math_mod(),
        }

    def __create_mod(self, name):
        mod_location = module_path_from_name(name)
        if mod_location:
            mod_node = module_node_from_path(mod_location)
            if mod_node:
                return ModuleType.from_node(mod_node)
        return None

    def __lookup_mod(self, name):
        mod = self.__create_mod(name)
        if mod:
            return mod
        elif name in self.builtin_modules():
            return self.builtin_modules()[name]
        else:
            raise RuntimeError("The module '{}' is probably implemented in C and does not have a python implementation. This module should have a pre-built ModuleType.".format(name))

    def load_module(self, name):
        """
        Lookup a module and save it.

        Returns:
            ModuleType
        """
        if name not in self.loaded_modules():
            self.__loaded_modules[name] = self.__lookup_mod(name)
        return self.loaded_modules()[name]

    """
    Getters
    """

    def none(self):
        return self.__none_cls.instance()

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

    def list_cls(self):
        return self.__list_cls

    def list(self):
        """Creates empty list type."""
        return self.list_cls().instance()

    def generator_cls(self):
        return self.__generator_cls

    def slice_cls(self):
        return self.__slice_cls

    def slice(self):
        return self.slice_cls().instance()

    """
    Functions
    """

    def print_func(self):
        return self.__print_func

    def input_func(self):
        return self.__input_func

    """
    Exceptions
    """

    def exception_cls(self):
        return self.__exception_cls

    def value_error_cls(self):
        return self.__value_error_cls

    """
    Modules
    """

    def math_mod(self):
        return self.__math_mod
